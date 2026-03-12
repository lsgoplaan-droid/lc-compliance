import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class LCAdviceExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # LC Number — handle both SWIFT `:20:` and spaced `20   DC NO:` formats
        val, conf = self._find_pattern_confidence(text, [
            r":20:\s*(.+)",                                          # SWIFT MT700 field 20
            r"20\s+DC\s*NO\s*:\s*(.+)",                              # Spaced SWIFT format
            r"DC\s*NO\s*:\s*(\S+)",                                  # Generic DC NO
            r"(?:L/?C\s*(?:No\.?|Number|Ref)?\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:CREDIT\s*(?:No\.?|Number)\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:DOCUMENTARY\s*CREDIT\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
        ])
        if val:
            val = val.strip()
        fields["lc_number"] = self._make_field(val, conf)

        # Beneficiary — handle SWIFT `:59:` and spaced `59   BENEFICIARY:` formats
        val = self._extract_swift_block(text, [
            r"59\s+BENEFICIARY\s*:", r":59:", r"BENEFICIARY\s*(?:NAME)?\s*:"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["beneficiary_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["beneficiary_address"] = self._make_field(
                    "\n".join(lines[1:]), 0.7
                )
            else:
                fields["beneficiary_address"] = self._make_field(None)
        else:
            fields["beneficiary_name"] = self._make_field(None)
            fields["beneficiary_address"] = self._make_field(None)

        # Applicant — handle SWIFT `:50:` and spaced `50   APPLICANT:` formats
        val = self._extract_swift_block(text, [
            r"50\s+APPLICANT\s*:", r":50:", r"APPLICANT\s*:", r"ACCOUNT\s*PARTY\s*:"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["applicant_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["applicant_address"] = self._make_field(
                    "\n".join(lines[1:]), 0.7
                )
            else:
                fields["applicant_address"] = self._make_field(None)
        else:
            fields["applicant_name"] = self._make_field(None)
            fields["applicant_address"] = self._make_field(None)

        # Currency and Amount — extract separately to avoid group(1)-only limitation
        # First try to find the full currency+amount string, then parse it
        curr_amt_match = None
        for pattern in [
            r":32B:\s*([A-Z]{3}\s*[\d,]+\.?\d*)",
            r"DC\s*AMT\s*:\s*([A-Z]{3}\s*[\d,]+\.?\d*)",            # Spaced SWIFT
            r"DC\s*AMT\s*:\s*([A-Z]{3}[\d,]+\.?\d*)",               # No space: USD15640.00
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                curr_amt_match = m.group(1)
                break

        if curr_amt_match:
            m2 = re.match(r"([A-Z]{3})\s*([\d,]+\.?\d*)", curr_amt_match)
            if m2:
                fields["currency"] = self._make_field(m2.group(1), 0.9)
                fields["amount"] = self._make_field(m2.group(2).replace(",", ""), 0.9)
            else:
                fields["currency"] = self._make_field(curr_amt_match[:3], 0.9)
                fields["amount"] = self._make_field(None)
        else:
            # Try separate patterns
            curr, curr_conf = self._find_pattern_confidence(text, [
                r":32B:\s*([A-Z]{3})",
                r"DC\s*AMT\s*:\s*([A-Z]{3})",
                r"(?:CURRENCY)\s*[:.]?\s*([A-Z]{3})",
            ])
            amt, amt_conf = self._find_pattern_confidence(text, [
                r"DC\s*AMT\s*:\s*[A-Z]{3}\s*([\d,]+\.?\d*)",
                r"(?:AMOUNT|VALUE)\s*[:.]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
            ])
            fields["currency"] = self._make_field(curr, curr_conf)
            fields["amount"] = self._make_field(amt.replace(",", "") if amt else None, amt_conf)

        # Expiry Date — handle DDMMMYY format (21SEP25) and standard formats
        val, conf = self._find_pattern_confidence(text, [
            r":31D:\s*(\d{6})",                                      # SWIFT YYMMDD
            r"EXPIRY\s*DATE\s*AND\s*PLACE\s*:\s*(\d{2}[A-Z]{3}\d{2})",  # 21SEP25 (spaced SWIFT)
            r"31D\s+EXPIRY\s*DATE\s*AND\s*PLACE\s*:\s*(\d{2}[A-Z]{3}\d{2})",
            r"(?:EXPIRY|EXPIRATION)\s*(?:DATE)?\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:EXPIRY|EXPIRATION)\s*(?:DATE)?\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:VALID\s*(?:UNTIL|TILL|TO))\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        ])
        fields["expiry_date"] = self._make_field(val, conf)

        # Goods Description — handle `:45A:` and spaced `45A  GOODS:` formats
        val = self._extract_swift_block(text, [
            r"45A\s+GOODS\s*:", r":45A:", r"GOODS\s*(?:AND/?OR\s*SERVICES)?\s*:"
        ], max_lines=10)
        if not val:
            val = self._extract_block_after_keyword(text, [
                "DESCRIPTION OF GOODS", "GOODS", "MERCHANDISE", "COMMODITY",
            ], max_lines=10)
        if val:
            # Clean: keep only actual product description lines,
            # remove quantity/price/HS code/value/trade term detail lines
            clean_lines = []
            for line in val.split("\n"):
                line_stripped = line.strip()
                if not line_stripped or line_stripped == ".":
                    continue
                # Skip lines that are quantity/price/value/trade term details
                if re.match(r"^(?:QUANTITY|QTY|PRICE|UNIT\s*PRICE|H\.?S\.?\s*CODE|FOB\s*VALUE|TRADE\s*TERM|ALL\s*OTHER)", line_stripped, re.IGNORECASE):
                    continue
                clean_lines.append(line_stripped)
            val = "\n".join(clean_lines) if clean_lines else val
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # HS Codes — filter out false positives from monetary amounts
        hs_matches = re.findall(r"\b(\d{4}\.\d{2}(?:\.\d{2})?)\b", text)
        if hs_matches:
            # Filter out amounts — exclude matches preceded by currency/USD/$ context
            filtered = []
            for hs in set(hs_matches):
                # Check if this number appears in a monetary context
                monetary_pattern = rf"(?:USD|US\$|\$|EUR|GBP)\s*{re.escape(hs)}"
                charge_pattern = rf"(?:CHARGE|FREIGHT|VALUE|TOTAL)\s*[:.]?\s*(?:USD\s*)?{re.escape(hs)}"
                if not re.search(monetary_pattern, text, re.IGNORECASE) and \
                   not re.search(charge_pattern, text, re.IGNORECASE):
                    filtered.append(hs)
            if filtered:
                fields["hs_codes"] = self._make_field(", ".join(sorted(filtered)), 0.9)
            else:
                fields["hs_codes"] = self._make_field(None)
        else:
            fields["hs_codes"] = self._make_field(None)

        # Quantity
        val, conf = self._find_pattern_confidence(text, [
            r"(?:QUANTITY|QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*\w+)",
            r"(\d[\d,]*\.?\d*)\s*(?:PCS|PIECES|SETS|UNITS|TONS|KGS?|MTS?|CTNS?|CARTONS|BAGS|ROLLS|BALES)",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Unit Price — handle `PRICE USD 850/MT` format
        val, conf = self._find_pattern_confidence(text, [
            r"PRICE\s+(?:USD\s+)?([\d,]+\.?\d*)\s*/\s*\w+",        # PRICE USD 850/MT
            r"(?:UNIT\s*PRICE|PRICE\s*PER\s*UNIT)\s*[:.]?\s*([A-Z]{3}\s*[\d,]+\.?\d*)",
            r"(?:@|AT)\s*([A-Z]{3}\s*[\d,]+\.?\d*\s*(?:PER|/)\s*\w+)",
        ])
        fields["unit_price"] = self._make_field(val, conf)

        # Port of Loading — handle multiline `44E  LOADING PORT/DEPART AIRPORT:\n     VALUE`
        val = self._extract_swift_field_value(text, [
            r"44E\s+LOADING\s*PORT",
            r":44E:",
            r"PORT\s*OF\s*LOADING",
            r"LOADING\s*PORT",
            r"PLACE\s*OF\s*RECEIPT",
        ])
        fields["port_of_loading"] = self._make_field(val, 0.9 if val else 0.0)

        # Port of Discharge — same multiline handling
        val = self._extract_swift_field_value(text, [
            r"44F\s+DISCHARGE\s*PORT",
            r":44F:",
            r"PORT\s*OF\s*DISCHARGE",
            r"DISCHARGE\s*PORT",
            r"PLACE\s*OF\s*DELIVERY",
            r"FINAL\s*DESTINATION",
        ])
        fields["port_of_discharge"] = self._make_field(val, 0.9 if val else 0.0)

        # Latest Shipment Date — handle DDMMMYY (31AUG25) and `44C  LATEST DATE OF SHIPMENT:`
        val, conf = self._find_pattern_confidence(text, [
            r":44C:\s*(\d{6})",                                      # SWIFT YYMMDD
            r"44C\s+LATEST\s*DATE\s*OF\s*SHIPMENT\s*:\s*(\d{2}[A-Z]{3}\d{2})",
            r"LATEST\s*DATE\s*OF\s*SHIPMENT\s*:\s*(\d{2}[A-Z]{3}\d{2})",
            r"LATEST\s*DATE\s*OF\s*SHIPMENT\s*:\s*(.+)",
            r"(?:LATEST\s*SHIPMENT|LAST\s*SHIPMENT|SHIP\s*(?:BY|ON\s*OR\s*BEFORE))\s*[:.]?\s*(.+)",
        ])
        if val:
            val = val.strip()
        fields["latest_shipment_date"] = self._make_field(val, conf)

        # Partial Shipments
        val, conf = self._find_pattern_confidence(text, [
            r":43P:\s*(.+)",
            r"43P\s+PARTIAL\s*SHIPMENTS?\s*:\s*(.+)",
            r"(?:PARTIAL\s*SHIPMENTS?)\s*[:.]?\s*(ALLOWED|PERMITTED|NOT\s*ALLOWED|PROHIBITED|CONDITIONAL)",
        ])
        if val:
            val = val.strip()
        fields["partial_shipments"] = self._make_field(val, conf)

        # Transhipment
        val, conf = self._find_pattern_confidence(text, [
            r":43T:\s*(.+)",
            r"43T\s+TRANS?SHIPMENT\s*:\s*(.+)",
            r"(?:TRANS?SHIPMENT)\s*[:.]?\s*(ALLOWED|PERMITTED|NOT\s*ALLOWED|PROHIBITED|CONDITIONAL)",
        ])
        if val:
            val = val.strip()
        fields["transhipment"] = self._make_field(val, conf)

        # Incoterms — prefer TRADE TERM line over random FOB/CFR mentions
        val = None
        conf = 0.0
        # First: look for explicit "TRADE TERM" line
        m = re.search(r"TRADE\s*TERM\s*:\s*(\w+)", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).upper()
            if candidate in ("EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"):
                val, conf = candidate, 1.0
        # Fallback: look for incoterm NOT in "FOB VALUE" context
        if not val:
            for m in re.finditer(r"\b(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b", text):
                # Skip "FOB VALUE" — that's just a pricing breakdown, not the trade term
                start = max(0, m.start() - 5)
                end = min(len(text), m.end() + 10)
                context = text[start:end].upper()
                if "FOB VALUE" in context or "FOB VALU" in context:
                    continue
                val, conf = m.group(1), 0.9
                break
        fields["incoterms"] = self._make_field(val, conf)

        return fields

    def _extract_swift_block(self, text: str, patterns: list, max_lines: int = 4) -> str | None:
        """Extract a multi-line block from SWIFT-style fields.

        Handles both `:NN:` and spaced `NN   FIELD:` formats where the value
        may start on the same line (after large whitespace gap) or continue on
        indented lines below.
        """
        lines = text.split("\n")
        for i, line in enumerate(lines):
            for pattern in patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    # Check for value on same line after the field label
                    # In spaced format, values are right-padded: "50   APPLICANT:                         BRB CABLE..."
                    after_match = line[m.end():]
                    # Strip leading whitespace to find the value
                    value_on_line = after_match.strip()

                    block_lines = []
                    if value_on_line:
                        block_lines.append(value_on_line)

                    # Collect continuation lines (indented with spaces)
                    for j in range(i + 1, min(i + 1 + max_lines, len(lines))):
                        next_line = lines[j]
                        # Stop at next SWIFT field (e.g., "32B  DC AMT:" or ":32B:")
                        if re.match(r"^\d{2}[A-Z]?\s+\w", next_line) or re.match(r"^:\d{2}[A-Z]?:", next_line):
                            break
                        stripped = next_line.strip()
                        if not stripped or stripped == ".":
                            break
                        block_lines.append(stripped)

                    if block_lines:
                        return "\n".join(block_lines)
        return None

    def _extract_swift_field_value(self, text: str, patterns: list) -> str | None:
        """Extract a single-value SWIFT field that may span onto the next line.

        For fields like:
            44E  LOADING PORT/DEPART AIRPORT:
                 ANY SEAPORT OF CHINA
        """
        lines = text.split("\n")
        for i, line in enumerate(lines):
            for pattern in patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    # Check for value after colon on same line
                    colon_split = line.split(":", 1)
                    if len(colon_split) > 1:
                        # For patterns that include "PORT/DEPART AIRPORT:", split on last colon
                        after_last_colon = line.rsplit(":", 1)[1].strip()
                        if after_last_colon:
                            return after_last_colon

                    # Value is on the next line (indented)
                    if i + 1 < len(lines):
                        next_val = lines[i + 1].strip()
                        if next_val and not re.match(r"^\d{2}[A-Z]?\s+\w", lines[i + 1]):
                            return next_val
        return None
