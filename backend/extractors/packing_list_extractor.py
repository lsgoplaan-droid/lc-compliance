import re
from typing import Dict, Optional

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class PackingListExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text
        lines = text.split("\n")

        # LC Reference — handle concatenated format "141325010091DTD30JUL2025"
        val, conf = self._find_pattern_confidence(text, [
            r"(\d{10,})\s*(?:DTD|DATED|DT)",                        # Number before DTD
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.&]?\s*\n?\s*(\d{6,})",
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.&]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_reference"] = self._make_field(val, conf)

        # Shipper (Beneficiary) — look for "SHIPPER:" in shipping marks or signature
        shipper_name = None
        shipper_addr = None
        # First look for explicit "SHIPPER:" label
        m = re.search(r"SHIPPER\s*:\s*(.+)", text, re.IGNORECASE)
        if m:
            shipper_name = m.group(1).strip()
            # Get address from next lines
            match_pos = m.end()
            remaining = text[match_pos:].split("\n")
            addr_lines = []
            for line in remaining:
                line = line.strip()
                if not line:
                    break
                if re.match(r"(?:ADDRESS)\s*:", line, re.IGNORECASE):
                    addr_part = re.split(r":\s*", line, maxsplit=1)
                    if len(addr_part) > 1:
                        addr_lines.append(addr_part[1].strip())
                    continue
                if re.search(r"[A-Z]{2,}\s+\d{4,}", line) or re.search(r"SINGAPORE|CHINA|BANGLADESH", line, re.IGNORECASE):
                    addr_lines.append(line)
                    break
                addr_lines.append(line)
            if addr_lines:
                shipper_addr = "\n".join(addr_lines)
        if not shipper_name:
            # Fallback: look for "FOR <company>" pattern
            for pattern in [
                r"FOR\s+(HARESH[A-Z\s.,()]+(?:PTE\.?\s*LTD\.?|LTD\.?))",
                r"FOR\s+([A-Z][A-Z\s&.,]+(?:PTE\.?\s*LTD|LTD|INC|CORP|LLC))",
            ]:
                m_fb = re.search(pattern, text, re.IGNORECASE)
                if m_fb:
                    shipper_name = m_fb.group(1).strip()
                    break
        fields["shipper_name"] = self._make_field(shipper_name, 0.8 if shipper_name else 0.0)
        # If address not found from SHIPPER: label, look for ADDRESS: label
        if not shipper_addr:
            m_addr = re.search(r"ADDRESS\s*:\s*(.+?)(?:\n\n|\nContinued|\nPACKING)", text, re.IGNORECASE | re.DOTALL)
            if m_addr:
                addr_text = m_addr.group(1).strip()
                # Clean up multi-line address
                addr_text = re.sub(r"\n\s*", " ", addr_text).strip()
                if addr_text:
                    shipper_addr = addr_text
        fields["shipper_address"] = self._make_field(shipper_addr, 0.7 if shipper_addr else 0.0)

        # Consignee (Applicant/Buyer) — look after "Buyer / Importer" or "Consignee"
        consignee_name = self._find_company_after_label(lines, [
            r"Buyer\s*/?\s*Importer", r"Consignee", r"BUYER", r"IMPORTER"
        ])
        consignee_addr = None
        if consignee_name:
            for i, line in enumerate(lines):
                if consignee_name in line:
                    addr_lines = []
                    for j in range(i + 1, min(i + 8, len(lines))):
                        al = lines[j].strip()
                        if not al:
                            break
                        if re.match(r"(?:L/?C|Invoice|Vessel|Port|Date|Name|Haresh|HPS/|DHAKA|\d{1,2}-\d{1,2}-\d{4})", al, re.IGNORECASE):
                            continue
                        if re.match(r"^\d{6,}", al):
                            continue
                        if re.search(r"(?:ESTATE|ROAD|STREET|FLOOR|CENTRE|BSCIC|KUSHTIA|BANGLADESH|SINGAPORE|CHINA|DHAKA|\d{4,}\s)", al, re.IGNORECASE):
                            addr_lines.append(al)
                    if addr_lines:
                        consignee_addr = "\n".join(addr_lines)
                    break
        fields["consignee_name"] = self._make_field(consignee_name, 0.8 if consignee_name else 0.0)
        fields["consignee_address"] = self._make_field(consignee_addr, 0.7 if consignee_addr else 0.0)

        # Goods Description — find the main product name
        val = self._find_product_description(lines)
        if not val:
            val_block = self._extract_block_after_keyword(text, [
                "DESCRIPTION OF GOODS", "DESCRIPTIONOFGOODS",
            ], max_lines=5)
            if val_block:
                good_lines = []
                for l in val_block.split("\n"):
                    l = l.strip()
                    if l and not re.match(r"^(?:QUANTITY|PRICE|AMOUNT|IN MTS|[\d,.]+)$", l, re.IGNORECASE):
                        good_lines.append(l)
                val = "\n".join(good_lines[:3]) if good_lines else None
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # Quantity — prefer explicit QUANTITY label, then net weight
        val, conf = self._find_pattern_confidence(text, [
            r"(?:TOTAL\s*QUANTITY|QUANTITY|QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*(?:PCS|PIECES?|METRIC\s*TONS?|MT|MTS|KGS?|BAGS?)?)",
            r"(?:TOTAL\s*(?:PACKAGES|CTNS|CARTONS)|NO\.?\s*OF\s*(?:PACKAGES|CTNS))\s*[:.]?\s*([\d,]+\s*\w*)",
        ])
        if not val:
            # Look for total net weight (prefer full word "NET WEIGHT" over abbreviation "NETWT")
            m = re.search(r"NET\s+WEIGHT\s*:\s*([\d,]+\.?\d*)\s*(METRIC\s*TONS?|KGS?|MTS?)", text, re.IGNORECASE)
            if not m:
                m = re.search(r"NETWEIGHT\s*:\s*([\d,]+\.?\d*)\s*(METRIC\s*TONS?|KGS?|MTS?)", text, re.IGNORECASE)
            if m:
                val = f"{m.group(1)} {m.group(2)}"
                conf = 0.85
        fields["quantity"] = self._make_field(val, conf)

        # Net Weight
        val, conf = self._find_pattern_confidence(text, [
            r"NET\s*WEIGHT\s*:\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
            r"NETWEIGHT\s*:\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
            r"NETWT\s*:\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
            r"(?:NET\s*(?:WEIGHT|WT\.?))\s*[:.]?\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
        ])
        fields["net_weight"] = self._make_field(val, conf)

        # Gross Weight
        val, conf = self._find_pattern_confidence(text, [
            r"GROSS\s*WEIGHT\s*:\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
            r"GROSS\s*WT\.?\s*:\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
            r"(?:GROSS\s*(?:WEIGHT|WT\.?))\s*[:.]?\s*([\d,]+\.?\d*\s*(?:METRIC\s*TONS?|KGS?|MTS?|LBS?))",
        ])
        fields["gross_weight"] = self._make_field(val, conf)

        # Dimensions / Measurements
        val, conf = self._find_pattern_confidence(text, [
            r"(?:DIMENSIONS?|MEASUREMENTS?|CBM|VOLUME)\s*[:.]?\s*([\d,]+\.?\d*\s*(?:CBM|M3|CU\.?\s*M))",
        ])
        fields["dimensions"] = self._make_field(val, conf)

        # Marks and Numbers
        val = self._extract_block_after_keyword(text, [
            "MARKS AND NUMBERS", "SHIPPING MARKS", "MARKS & NOS",
            "Shipping Marks"
        ], max_lines=5)
        fields["marks_and_numbers"] = self._make_field(val, 0.7 if val else 0.0)

        return fields

    def _find_company_after_label(self, lines: list, label_patterns: list) -> Optional[str]:
        """Find a company name in lines following a label header."""
        for i, line in enumerate(lines):
            for pattern in label_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    for j in range(i + 1, min(i + 6, len(lines))):
                        candidate = lines[j].strip()
                        if re.search(r"(?:LIMITED|LTD|INC|CORP|LLC)\b", candidate, re.IGNORECASE):
                            return candidate
                    return None
        return None

    def _find_product_description(self, lines: list) -> Optional[str]:
        """Find the main product description line."""
        # Try "PRODUCT:" label first
        for line in lines:
            m = re.match(r"PRODUCT\s*:\s*(.+)", line.strip(), re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if len(val) > 5:
                    return val
        # Try block after "DESCRIPTION OF GOODS"
        for i, line in enumerate(lines):
            if re.search(r"DESCRIPTION\s*OF\s*GOODS", line, re.IGNORECASE):
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and not re.match(r"^(?:QUANTITY|QTY|PRICE|AMOUNT|PACKED|CROP|H\.?S|L/?C|[\d,.]+\s*$)", candidate, re.IGNORECASE):
                        return candidate
                break
        # Keyword scan fallback
        product_keywords = r"GLYCOL|CHEMICAL|STEEL|\bCOTTON\b|\bRICE\b|\bOIL\b|SUGAR|CEMENT|POLYMER|CRUDE|PETROLEUM|FUEL|DIESEL|LNG|NAPHTHA|T-SHIRT|GARMENT|KNITTED|WOVEN|JASMINE|BASMATI"
        for line in lines:
            line_s = line.strip()
            if re.search(product_keywords, line_s, re.IGNORECASE):
                if not re.match(r"(?:DESCRIPTION|QUANTITY|PRICE|AMOUNT|TOTAL|PACKING|FOB|TRADE|SHIPPING|CERTIFIED|COUNTRY)", line_s, re.IGNORECASE):
                    if not re.search(r"\b(?:LLC|LTD|LIMITED|INC|CORP|PTE)\b", line_s, re.IGNORECASE):
                        return line_s
        return None
