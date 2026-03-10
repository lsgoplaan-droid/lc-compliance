import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class LCAdviceExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # LC Number
        val, conf = self._find_pattern_confidence(text, [
            r":20:\s*(.+)",                                          # SWIFT MT700 field 20
            r"(?:L/?C\s*(?:No\.?|Number|Ref)?\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:CREDIT\s*(?:No\.?|Number)\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:DOCUMENTARY\s*CREDIT\s*[:.]?\s*)([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_number"] = self._make_field(val, conf)

        # Beneficiary name
        val = self._extract_block_after_keyword(text, [
            "BENEFICIARY", ":59:", "BENEFICIARY NAME"
        ], max_lines=3)
        if val:
            # Take just the first line as name, rest is address
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

        # Applicant name
        val = self._extract_block_after_keyword(text, [
            "APPLICANT", ":50:", "ACCOUNT PARTY", "OPENER"
        ], max_lines=3)
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

        # Currency and Amount
        val, conf = self._find_pattern_confidence(text, [
            r":32B:\s*([A-Z]{3})\s*([\d,]+\.?\d*)",                  # SWIFT field 32B
            r"(?:AMOUNT|VALUE|CREDIT\s*AMOUNT)\s*[:.]?\s*([A-Z]{3})\s*([\d,]+\.?\d*)",
            r"([A-Z]{3})\s*([\d]{1,3}(?:,\d{3})*(?:\.\d{2})?)\b",
        ])
        if val:
            # The pattern matched currency+amount together, need to re-extract
            match = re.search(r"([A-Z]{3})\s*([\d,]+\.?\d*)", val)
            if match:
                fields["currency"] = self._make_field(match.group(1), conf)
                fields["amount"] = self._make_field(match.group(2).replace(",", ""), conf)
            else:
                fields["currency"] = self._make_field(val[:3] if len(val) >= 3 else val, conf)
                fields["amount"] = self._make_field(None)
        else:
            # Try separate patterns
            curr, curr_conf = self._find_pattern_confidence(text, [
                r":32B:\s*([A-Z]{3})",
                r"(?:CURRENCY)\s*[:.]?\s*([A-Z]{3})",
            ])
            amt, amt_conf = self._find_pattern_confidence(text, [
                r"(?:AMOUNT|VALUE)\s*[:.]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
            ])
            fields["currency"] = self._make_field(curr, curr_conf)
            fields["amount"] = self._make_field(amt, amt_conf)

        # Expiry Date
        val, conf = self._find_pattern_confidence(text, [
            r":31D:\s*(\d{6})",                                       # SWIFT YYMMDD
            r"(?:EXPIRY|EXPIRATION)\s*(?:DATE)?\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:EXPIRY|EXPIRATION)\s*(?:DATE)?\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:VALID\s*(?:UNTIL|TILL|TO))\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        ])
        fields["expiry_date"] = self._make_field(val, conf)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "GOODS", "MERCHANDISE", "COMMODITY", "DESCRIPTION OF GOODS",
            ":45A:", "GOODS AND/OR SERVICES"
        ], max_lines=10)
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # HS Codes
        hs_matches = re.findall(r"\b(\d{4}\.\d{2}(?:\.\d{2})?)\b", text)
        if hs_matches:
            fields["hs_codes"] = self._make_field(", ".join(set(hs_matches)), 0.9)
        else:
            fields["hs_codes"] = self._make_field(None)

        # Quantity
        val, conf = self._find_pattern_confidence(text, [
            r"(?:QUANTITY|QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*\w+)",
            r"(\d[\d,]*\.?\d*)\s*(?:PCS|PIECES|SETS|UNITS|TONS|KGS?|MTS?|CTNS?|CARTONS|BAGS|ROLLS|BALES)",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Unit Price
        val, conf = self._find_pattern_confidence(text, [
            r"(?:UNIT\s*PRICE|PRICE\s*PER\s*UNIT)\s*[:.]?\s*([A-Z]{3}\s*[\d,]+\.?\d*)",
            r"(?:@|AT)\s*([A-Z]{3}\s*[\d,]+\.?\d*\s*(?:PER|/)\s*\w+)",
        ])
        fields["unit_price"] = self._make_field(val, conf)

        # Port of Loading
        val, conf = self._find_pattern_confidence(text, [
            r":44E:\s*(.+)",                                          # SWIFT
            r"(?:PORT\s*OF\s*LOADING|PLACE\s*OF\s*RECEIPT|LOADING\s*PORT)\s*[:.]?\s*(.+)",
        ])
        fields["port_of_loading"] = self._make_field(val, conf)

        # Port of Discharge
        val, conf = self._find_pattern_confidence(text, [
            r":44F:\s*(.+)",                                          # SWIFT
            r"(?:PORT\s*OF\s*DISCHARGE|PLACE\s*OF\s*DELIVERY|FINAL\s*DESTINATION|DISCHARGE\s*PORT)\s*[:.]?\s*(.+)",
        ])
        fields["port_of_discharge"] = self._make_field(val, conf)

        # Latest Shipment Date
        val, conf = self._find_pattern_confidence(text, [
            r":44C:\s*(\d{6})",                                       # SWIFT YYMMDD
            r"(?:LATEST\s*SHIPMENT|LAST\s*SHIPMENT|SHIP\s*(?:BY|ON\s*OR\s*BEFORE))\s*[:.]?\s*(.+)",
        ])
        fields["latest_shipment_date"] = self._make_field(val, conf)

        # Partial Shipments
        val, conf = self._find_pattern_confidence(text, [
            r":43P:\s*(.+)",                                          # SWIFT
            r"(?:PARTIAL\s*SHIPMENTS?)\s*[:.]?\s*(ALLOWED|PERMITTED|NOT\s*ALLOWED|PROHIBITED|CONDITIONAL)",
        ])
        fields["partial_shipments"] = self._make_field(val, conf)

        # Transhipment
        val, conf = self._find_pattern_confidence(text, [
            r":43T:\s*(.+)",                                          # SWIFT
            r"(?:TRANS?SHIPMENT)\s*[:.]?\s*(ALLOWED|PERMITTED|NOT\s*ALLOWED|PROHIBITED|CONDITIONAL)",
        ])
        fields["transhipment"] = self._make_field(val, conf)

        # Incoterms
        val, conf = self._find_pattern_confidence(text, [
            r"\b(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b",
        ])
        fields["incoterms"] = self._make_field(val, conf)

        return fields
