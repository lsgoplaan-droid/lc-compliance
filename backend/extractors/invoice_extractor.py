import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class InvoiceExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text
        lines = text.split("\n")

        # Invoice Number - check standalone line first (most reliable for OCR)
        val, conf = None, 0.0
        for line in lines:
            line = line.strip()
            m = re.match(r"^([A-Z]{2,}/INV/[\w/\-]+)$", line)
            if m:
                val, conf = m.group(1), 0.95
                break
        if not val:
            val, conf = self._find_pattern_confidence(text, [
                r"(HPS/INV/\S+)",
                r"(?:INV\.?\s*(?:No\.?|#))\s*[:.&]?\s*([A-Z0-9][A-Z0-9/\-]+)",
                r"(?:INVOICE\s*(?:NUMBER|#))\s*[:.&]?\s*([A-Z0-9][A-Z0-9/\-]+)",
                r"INVOICE\s*NO\s*[:.&]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            ])
        fields["invoice_number"] = self._make_field(val, conf)

        # Invoice Date - look for standalone date line or after invoice number
        val, conf = self._find_pattern_confidence(text, [
            r"(?:INVOICE\s*DATE|DATE\s*OF\s*INVOICE)\s*[:.&]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:INVOICE\s*DATE|DATE\s*OF\s*INVOICE)\s*[:.&]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"^DATE\s*:\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"DATE\s*:\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"DATE\s*:\s*(\d{1,2}\s+\w+\s+\d{4})",
        ])
        if not val:
            # Look for date on its own line (e.g. "25-8-2025")
            for line in lines:
                line = line.strip()
                m = re.match(r"^(\d{1,2}-\d{1,2}-\d{4})$", line)
                if m:
                    val, conf = m.group(1), 0.85
                    break
        fields["invoice_date"] = self._make_field(val, conf)

        # LC Reference - look for long number before DTD/DATED, or concatenated with DTD
        val, conf = self._find_pattern_confidence(text, [
            r"(\d{10,})\s*(?:DTD|DATED|DT)",                        # 141325010091DTD30JUL2025
            r"(?:L/?C\s*(?:No\.?|Ref|Number|#))\s*[:.&]?\s*(?:Date)?\s*\n?\s*(\d{6,})",
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.&]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_reference"] = self._make_field(val, conf)

        # Seller - look for "FOR <company>", "A/c. Name:", or signature block
        seller_name = None
        for pattern in [
            r"A/c\.?\s*Name\s*:\s*(.+)",
            r"(?:FOR\s+)(HARESH[A-Z\s.,()]+(?:PTE\.?\s*LTD\.?|LTD\.?|INC|CORP))",
            r"(?:FOR\s*)([A-Z][A-Z\s&.,]+(?:PTE\.?\s*LTD|LTD|INC|CORP|LLC|CO\.?))",
            r"(?:SELLER|EXPORTER|SHIPPER|BENEFICIARY)\s*[:.&]?\s*\n?\s*(.+)",
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                seller_name = m.group(1).strip()
                break
        fields["seller_name"] = self._make_field(seller_name, 0.8 if seller_name else 0.0)
        # Seller address — look for explicit ADDRESS: label (not bank address)
        seller_addr = None
        m_addr = re.search(r"ADDRESS\s*:\s*(.+?)(?:\n\n|\nContinued)", text, re.IGNORECASE | re.DOTALL)
        if m_addr:
            addr_text = re.sub(r"\n\s*", " ", m_addr.group(1).strip()).strip()
            # Skip if it's clearly a bank/SWIFT address
            if not re.search(r"SWIFT|HSBC|BANK|BRANCH", addr_text, re.IGNORECASE):
                seller_addr = addr_text
        fields["seller_address"] = self._make_field(seller_addr, 0.7 if seller_addr else 0.0)

        # Buyer - look after "Buyer / Importer" keyword, skip header noise
        buyer_name = None
        buyer_addr = None
        buyer_idx = None
        for i, line in enumerate(lines):
            if re.search(r"Buyer\s*/?\s*Importer|BUYER|IMPORTER", line, re.IGNORECASE):
                buyer_idx = i
                break
        if buyer_idx is not None:
            # Scan following lines for a company name (skip headers like "Haresh Ref.", "Invoice No.")
            for j in range(buyer_idx + 1, min(buyer_idx + 6, len(lines))):
                line = lines[j].strip()
                if re.search(r"(?:LIMITED|LTD|INC|CORP|LLC)\b", line, re.IGNORECASE):
                    buyer_name = line
                    # Grab address: skip junk lines (invoice refs, dates), keep location lines
                    addr_lines = []
                    for k in range(j + 1, min(j + 8, len(lines))):
                        al = lines[k].strip()
                        if not al:
                            break
                        # Skip headers, invoice numbers, dates, bank names
                        if re.match(r"(?:L/?C|Invoice|Vessel|Port|Date|Name|Haresh|HPS/|DHAKA|DHANMONDI|\d{1,2}-\d{1,2}-\d{4})", al, re.IGNORECASE):
                            continue
                        # Skip lines that are mostly numbers (LC refs, dates)
                        if re.match(r"^\d{6,}", al):
                            continue
                        # Keep location-like lines (addresses, cities, countries)
                        if re.search(r"(?:ESTATE|ROAD|STREET|FLOOR|CENTRE|BSCIC|KUSHTIA|BANGLADESH|SINGAPORE|CHINA|DHAKA|TOWER|PLACE|AVENUE|ISLAND|HARBOURFRONT|BUILDING|BLOCK|UNIT|SUITE|\d{4,}\s)", al, re.IGNORECASE):
                            addr_lines.append(al)
                    if addr_lines:
                        buyer_addr = "\n".join(addr_lines)
                    break
        fields["buyer_name"] = self._make_field(buyer_name, 0.8 if buyer_name else 0.0)
        fields["buyer_address"] = self._make_field(buyer_addr, 0.7 if buyer_addr else 0.0)

        # Currency
        if re.search(r"US\s*\$|US\$|USD|US\s*DOLLAR", text, re.IGNORECASE):
            val, conf = "USD", 0.9
        else:
            val, conf = self._find_pattern_confidence(text, [
                r"\b(EUR|GBP|JPY|CNY|INR|BDT|SGD)\b",
            ])
        fields["currency"] = self._make_field(val, conf)

        # Total Amount - look for TOTAL followed by amount on same or next line
        val = None
        conf = 0.0
        for i, line in enumerate(lines):
            if re.match(r"^\s*TOTAL\s*$", line, re.IGNORECASE):
                # Collect all standalone numbers on the lines following TOTAL
                # In tabular invoices, TOTAL is followed by quantity, unit price, then total amount
                # The total amount is the largest number among them
                candidates = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    m = re.match(r"^([\d,]+\.\d{2,})\s*$", next_line)
                    if m:
                        candidates.append(m.group(1))
                    elif next_line and not re.match(r"^[\d,.\s]+$", next_line):
                        break  # stop at non-numeric line
                if candidates:
                    # Pick the largest numeric value (the total amount)
                    best = max(candidates, key=lambda x: float(x.replace(",", "")))
                    val, conf = best, 0.95
                    break
        if not val:
            val, conf = self._find_pattern_confidence(text, [
                r"(?:TOTAL\s*(?:AMOUNT|VALUE)|GRAND\s*TOTAL)\s*[:.&]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
                r"(?:TOTAL)\s*[:.&]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d{2})",
                r"CFR\s+(?:USD\s+)?([\d,]+\.\d{2})",
            ])
        fields["total_amount"] = self._make_field(val, conf)

        # Goods Description - extract main product name
        val = None
        for line in lines:
            line_s = line.strip()
            # Look for product name (e.g. "MONOETHYLENEGLYCOL" or "MONO ETHYLENE GLYCOL")
            if re.search(r"(?:GLYCOL|CHEMICAL\b|\bSTEEL\b|\bCOTTON\b|\bRICE\b|\bSUGAR\b|\bCEMENT\b|POLYMER|\bCRUDE\b|\bOIL\b|PETROLEUM|\bFUEL\b|\bDIESEL\b|\bGASOLINE\b|\bLNG\b|\bLPG\b|\bNAPHTHA\b|\bBITUMEN\b)", line_s, re.IGNORECASE):
                if not re.match(r"(?:DESCRIPTION|QUANTITY|PRICE|AMOUNT|TOTAL|PACKING|FOB|TRADE|SHIPPING)", line_s, re.IGNORECASE):
                    # Skip company names (e.g. "ARABIAN GULF PETROLEUM LLC")
                    if not re.search(r"\b(?:LLC|LTD|LIMITED|INC|CORP|PTE)\b", line_s, re.IGNORECASE):
                        val = line_s
                        break
        if not val:
            val_block = self._extract_block_after_keyword(text, [
                "DESCRIPTION OF GOODS", "DESCRIPTIONOFGOODS", "DESCRIPTION"
            ], max_lines=8)
            if val_block:
                # Filter noise lines
                good_lines = []
                for l in val_block.split("\n"):
                    l = l.strip()
                    if l and not re.match(r"^(?:IN MTS|QUANTITY|PRICE|AMOUNT|US\$|Unit Price|Description|[\d,.]+)", l, re.IGNORECASE):
                        good_lines.append(l)
                val = "\n".join(good_lines[:5]) if good_lines else None
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # HS Codes — filter out monetary false positives
        hs_matches = re.findall(r"\b(\d{4}\.\d{2}(?:\.\d{2})?)\b", text)
        if hs_matches:
            filtered = []
            for hs in sorted(set(hs_matches)):
                monetary_pattern = rf"(?:USD|US\$|\$|EUR|GBP|CHARGE|FREIGHT|VALUE|TOTAL)\s*[:.]?\s*(?:USD\s*)?{re.escape(hs)}"
                if not re.search(monetary_pattern, text, re.IGNORECASE):
                    filtered.append(hs)
            fields["hs_codes"] = self._make_field(", ".join(filtered) if filtered else None, 0.9 if filtered else 0.0)
        else:
            fields["hs_codes"] = self._make_field(None)

        # Quantity — handle tabular format where quantity appears as standalone number
        val, conf = self._find_pattern_confidence(text, [
            r"QUANTITY\s+([\d,.]+)\s*(?:MT|MTS)\b",
            r"(\d[\d,]*\.\d+)\s*(?:MTS?|MT|KGS?)\b",
            r"(?:QUANTITY|QTY)\s*[:.&]?\s*([\d,]+\.?\d*\s*\w+)",
        ])
        if not val:
            # Look for quantity in table context: after "IN MTS" column header
            for i, line in enumerate(lines):
                if re.search(r"IN\s*MTS", line, re.IGNORECASE) or re.search(r"QUANTITY", line, re.IGNORECASE):
                    # Scan next few lines for a decimal number (the quantity value)
                    for j in range(i + 1, min(i + 5, len(lines))):
                        candidate = lines[j].strip()
                        m = re.match(r"^([\d,]+\.\d{2,})$", candidate)
                        if m:
                            val, conf = m.group(1), 0.85
                            break
                    if val:
                        break
        fields["quantity"] = self._make_field(val, conf)

        # Unit Price — try explicit patterns first, then extract from table
        val, conf = self._find_pattern_confidence(text, [
            r"PRICE\s+USD\s+([\d,]+\.?\d*)\s*/\s*MT",
            r"PRICE\s+(?:USD\s+)?([\d,]+\.?\d*)\s*/\s*(?:MT|MTS|KG)",
            r"(?:UNIT\s*PRICE|PRICE\s*PER)\s*[:.&]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
            r"(?:@|AT)\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)\s*(?:PER|/)",
        ])
        if not val:
            # Extract from tabular format: look for PRICE/ or "Unit Price" column header, then value below
            for i, line in enumerate(lines):
                if re.search(r"PRICE\s*/|Unit\s*Price", line, re.IGNORECASE):
                    # Scan next lines for a decimal number that looks like a unit price
                    for j in range(i + 1, min(i + 15, len(lines))):
                        candidate = lines[j].strip()
                        # Stop at TOTAL line
                        if re.match(r"^\s*TOTAL\s*$", candidate, re.IGNORECASE):
                            break
                        m = re.match(r"^([\d,]+\.\d{2,})$", candidate)
                        if m:
                            price_val = float(m.group(1).replace(",", ""))
                            # Unit prices are typically < 5000; skip totals and quantities
                            if price_val < 5000:
                                val, conf = m.group(1), 0.8
                                break
                    break
        fields["unit_price"] = self._make_field(val, conf)

        # Incoterms — prefer TRADE TERM line over random mentions
        val = None
        conf = 0.0
        m = re.search(r"TRADE\s*TERM\s*:\s*(\w+)", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).upper()
            if candidate in ("EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"):
                val, conf = candidate, 1.0
        if not val:
            # Look for "Terms of Delivery" section
            m = re.search(r"Terms\s*of\s*Delivery\s*\n\s*(\w+)", text, re.IGNORECASE)
            if m:
                candidate = m.group(1).upper()
                if candidate in ("EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"):
                    val, conf = candidate, 0.95
        if not val:
            for m_iter in re.finditer(r"\b(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b", text):
                start = max(0, m_iter.start() - 5)
                end = min(len(text), m_iter.end() + 10)
                context = text[start:end].upper()
                if "FOB VALUE" in context or "FOB VALU" in context:
                    continue
                val, conf = m_iter.group(1), 0.9
                break
        fields["incoterms"] = self._make_field(val, conf)

        # Port of Loading - look for line after "Port of Loading"
        val = None
        conf = 0.0
        for i, line in enumerate(lines):
            if re.search(r"Port\s*of\s*Loading", line, re.IGNORECASE):
                # Check remaining text on same line first
                after = re.split(r"Port\s*of\s*Loading", line, flags=re.IGNORECASE)[-1].strip()
                # Strip leading colon/separator
                after = re.sub(r"^[:\s]+", "", after).strip()
                if after and re.search(r"[A-Z]{3,}", after):
                    val, conf = after, 0.9
                    break
                # Check next line(s) for the actual port
                for j in range(i + 1, min(i + 3, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and not re.match(r"(?:Port|Vessel|Final|Consignee|Name)", candidate, re.IGNORECASE):
                        if re.search(r"[A-Z]{3,}", candidate) and not re.search(r"^TERAT", candidate, re.IGNORECASE):
                            val, conf = candidate, 0.9
                            break
                break
        fields["port_of_loading"] = self._make_field(val, conf)

        # Port of Discharge - look for line after "Port of Discharge"
        val = None
        conf = 0.0
        for i, line in enumerate(lines):
            if re.search(r"Port\s*of\s*Discharge", line, re.IGNORECASE):
                # Check for value on the same line after colon
                after = re.split(r"Port\s*of\s*Discharge", line, flags=re.IGNORECASE)[-1].strip()
                after = re.sub(r"^[:\s]+", "", after).strip()
                if after and re.search(r"[A-Z]{3,}", after):
                    val, conf = after, 0.9
                    break
                # Check following lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    if re.match(r"(?:Port|Final|Country|Bill|Name|BRB|BSC)", candidate, re.IGNORECASE):
                        continue
                    if re.search(r"(?:SEAPORT|PORT|HARBOR|TERMINAL|,\s*[A-Z]+$)", candidate, re.IGNORECASE):
                        val, conf = candidate, 0.9
                        break
                break
        if not val:
            val, conf = self._find_pattern_confidence(text, [
                r"(?:DESTINATION)\s*[:.&]?\s*\n?\s*(.+?)(?:\n|$)",
            ])
        fields["port_of_discharge"] = self._make_field(val, conf)

        return fields
