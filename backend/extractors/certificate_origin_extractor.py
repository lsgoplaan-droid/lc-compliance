import re
from typing import Dict, Optional

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class CertificateOfOriginExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text
        lines = text.split("\n")

        # Certificate Number
        val, conf = self._find_pattern_confidence(text, [
            r"(?:CERTIFICATE\s*(?:No\.?|Number|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:CERT\.?\s*(?:No\.?|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["certificate_number"] = self._make_field(val, conf)

        # Exporter (Beneficiary/Seller)
        exporter_name = self._extract_exporter(lines, text)
        fields["exporter_name"] = self._make_field(exporter_name, 0.8 if exporter_name else 0.0)

        # Exporter address — look for ADDRESS: label or known address patterns
        exporter_addr = None
        m_addr = re.search(r"ADDRESS\s*:\s*(.+?)(?:\n\n|\nContinued)", text, re.IGNORECASE | re.DOTALL)
        if m_addr:
            exporter_addr = re.sub(r"\n\s*", " ", m_addr.group(1).strip()).strip()
        fields["exporter_address"] = self._make_field(exporter_addr, 0.7 if exporter_addr else 0.0)

        # Importer (Applicant/Buyer)
        importer_name = self._extract_importer(lines, text)
        fields["importer_name"] = self._make_field(importer_name, 0.8 if importer_name else 0.0)

        # Importer address — look for address lines after importer name
        importer_addr = None
        if importer_name:
            for i, line in enumerate(lines):
                if importer_name in line:
                    addr_lines = []
                    for j in range(i + 1, min(i + 8, len(lines))):
                        al = lines[j].strip()
                        if not al:
                            break
                        if re.match(r"(?:L/?C|Invoice|Vessel|Port|Date|Name|Haresh|HPS/|DHAKA|\d{1,2}-\d{1,2}-\d{4})", al, re.IGNORECASE):
                            continue
                        if re.match(r"^\d{6,}", al):
                            continue
                        if re.search(r"(?:ESTATE|ROAD|STREET|FLOOR|CENTRE|BSCIC|KUSHTIA|BANGLADESH|SINGAPORE|CHINA|DHAKA|PLACE|TOWER|HARBOUR|\d{4,}\s)", al, re.IGNORECASE):
                            addr_lines.append(al)
                    if addr_lines:
                        importer_addr = "\n".join(addr_lines)
                    break
        fields["importer_address"] = self._make_field(importer_addr, 0.7 if importer_addr else 0.0)

        # Country of Origin
        val = None
        conf = 0.0
        # Try "CERTIFIED THAT THE GOODS ARE OF <COUNTRY> ORIGIN" pattern first
        m = re.search(r"GOODS\s*ARE\s*OF\s+([A-Z]+)\s+ORIGIN", text, re.IGNORECASE)
        if m:
            val, conf = m.group(1).strip(), 1.0
        if not val:
            # "COUNTRY OF ORIGIN: UNITED ARAB EMIRATES" — capture full multi-word value to end of line
            m = re.search(r"COUNTRY\s*OF\s*ORIGIN\s*:\s*([A-Z][A-Z\s]+[A-Z])\s*$", text, re.IGNORECASE | re.MULTILINE)
            if m:
                candidate = m.group(1).strip()
                if candidate.upper() not in ("OF", "THE", "GOODS"):
                    val, conf = candidate, 0.95
        if not val:
            # Fallback: "ORIGIN: CHINA" single-word country
            m = re.search(r"ORIGIN\s*:\s*([A-Z]{2,})\b", text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate.upper() not in ("OF", "THE", "GOODS"):
                    val, conf = candidate, 0.9
        if not val:
            # Look for "Country of Origin of Goods" header, then find country on subsequent lines
            for i, line in enumerate(lines):
                if re.search(r"Country\s*of\s*Origin", line, re.IGNORECASE):
                    # Scan next lines for a standalone country name
                    for j in range(i + 1, min(i + 5, len(lines))):
                        candidate = lines[j].strip()
                        if candidate and re.match(r"^[A-Z]{2,}$", candidate):
                            val, conf = candidate, 0.85
                            break
                    break
        fields["country_of_origin"] = self._make_field(val, conf)

        # Goods Description — try block extraction first, then keyword scan
        val = None
        val_block = self._extract_block_after_keyword(text, [
            "DESCRIPTION OF GOODS", "DESCRIPTIONOFGOODS",
        ], max_lines=5)
        if val_block:
            good_lines = []
            for l in val_block.split("\n"):
                l = l.strip()
                if l and not re.match(r"^(?:QUANTITY|QTY|PRICE|AMOUNT|IN MTS|PACKED|CROP|H\.?S\.?\s*CODE|L/?C|INVOICE|[\d,.]+\s*$)", l, re.IGNORECASE):
                    good_lines.append(l)
            if good_lines:
                val = good_lines[0]
        if not val:
            val = self._find_product_description(lines)
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

        # Quantity — look for explicit quantity or net weight
        val, conf = self._find_pattern_confidence(text, [
            r"(?:QUANTITY|QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*(?:PCS|PIECES?|METRIC\s*TONS?|MT|MTS|KGS?|BAGS?)?)",
            r"NETWEIGHT\s*:\s*([\d,]+\.?\d*\s*(?:KGS?|MTS?))",
            r"NET\s*WEIGHT\s*:\s*([\d,]+\.?\d*\s*(?:KGS?|MTS?))",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Certifying Authority
        val, conf = self._find_pattern_confidence(text, [
            r"(?:CERTIFIED\s*BY|CERTIFYING\s*(?:AUTHORITY|BODY)|CHAMBER\s*OF\s*COMMERCE)\s*[:.]?\s*(.+)",
            r"(?:ISSUED\s*BY)\s*[:.]?\s*(.+)",
        ])
        fields["certifying_authority"] = self._make_field(val, conf)

        return fields

    def _extract_exporter(self, lines: list, text: str) -> Optional[str]:
        """Extract exporter name, handling two-column layouts."""
        # Try "FOR <company>" signature pattern first (original format)
        for pattern in [
            r"FOR\s+(HARESH[A-Z\s.,()]+(?:PTE\.?\s*LTD\.?|LTD\.?))",
            r"FOR\s+([A-Z][A-Z\s&.,]+(?:PTE\.?\s*LTD|LTD|INC|CORP|LLC))",
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        # Try standard "EXPORTER:" label with value on same line
        m = re.search(r"(?:^|\n)\s*(?:EXPORTER|SHIPPER|CONSIGNOR|MANUFACTURER)\s*[:.]?\s*\n?\s*(.+)", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # If the value is another label (e.g. "CONSIGNEE / IMPORTER:"), it's a two-column layout
            if not re.search(r"(?:CONSIGNEE|IMPORTER|BUYER)\s*[/:]", candidate, re.IGNORECASE):
                return candidate

        # Two-column layout: EXPORTER: and CONSIGNEE/IMPORTER: on adjacent lines,
        # values follow below. Find first company name after these labels.
        exporter_label_idx = None
        for i, line in enumerate(lines):
            if re.search(r"^EXPORTER\s*:", line.strip(), re.IGNORECASE):
                exporter_label_idx = i
                break
        if exporter_label_idx is not None:
            # Scan lines after the label block for company names
            for j in range(exporter_label_idx + 1, min(exporter_label_idx + 8, len(lines))):
                candidate = lines[j].strip()
                # Skip other label lines
                if re.match(r"^(?:CONSIGNEE|IMPORTER|BUYER|EXPORTER|DATE|CERTIFICATE|ISSUED)", candidate, re.IGNORECASE):
                    continue
                if not candidate:
                    continue
                # First line with a company name (LLC, LTD, etc.)
                if re.search(r"(?:LIMITED|LTD|INC|CORP|LLC|PTE)\b", candidate, re.IGNORECASE):
                    return candidate

        return None

    def _extract_importer(self, lines: list, text: str) -> Optional[str]:
        """Extract importer name, handling two-column layouts."""
        # Check if this is a two-column layout (EXPORTER and CONSIGNEE/IMPORTER
        # labels on adjacent lines). If so, use company-order approach.
        exporter_idx = None
        importer_idx = None
        for i, line in enumerate(lines):
            ls = line.strip().upper()
            if re.match(r"EXPORTER\s*:", ls):
                exporter_idx = i
            if re.search(r"CONSIGNEE\s*/?\s*IMPORTER|IMPORTER\s*/?\s*CONSIGNEE", ls):
                importer_idx = i

        # Two-column layout: both labels within 2 lines of each other
        if exporter_idx is not None and importer_idx is not None and abs(exporter_idx - importer_idx) <= 2:
            # Collect all company names after the labels until a section break
            start = max(exporter_idx, importer_idx) + 1
            companies_found = []
            for j in range(start, min(start + 10, len(lines))):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                if re.match(r"^(?:COUNTRY|TRANSPORT|DESCRIPTION|VESSEL|PORT|H\.?S\.?\s*CODE|L/?C)", candidate, re.IGNORECASE):
                    break
                if re.search(r"(?:LIMITED|LTD|INC|CORP|LLC|PTE)\b", candidate, re.IGNORECASE):
                    companies_found.append(candidate)
            # Second company is the importer (first is exporter)
            if len(companies_found) >= 2:
                return companies_found[1]
            # Only one company found — might be the same entity
            if len(companies_found) == 1:
                return companies_found[0]

        # Standard single-column layout
        importer_name = self._find_company_after_label(lines, [
            r"Buyer\s*/?\s*Importer", r"IMPORTER", r"CONSIGNEE", r"BUYER"
        ])
        if importer_name:
            return importer_name

        return None

    def _find_company_after_label(self, lines: list, label_patterns: list) -> Optional[str]:
        """Find a company name in lines following a label header."""
        for i, line in enumerate(lines):
            for pattern in label_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Scan following lines for a company name
                    for j in range(i + 1, min(i + 6, len(lines))):
                        candidate = lines[j].strip()
                        if re.search(r"(?:LIMITED|LTD|INC|CORP|LLC)\b", candidate, re.IGNORECASE):
                            return candidate
                    return None
        return None

    def _find_product_description(self, lines: list) -> Optional[str]:
        """Find the main product description line (e.g. 'MONO ETHYLENE GLYCOL')."""
        for line in lines:
            line_s = line.strip()
            if re.search(r"GLYCOL|CHEMICAL|STEEL|COTTON|RICE|SUGAR|CEMENT|POLYMER|CRUDE\s*OIL", line_s, re.IGNORECASE):
                if not re.match(r"(?:DESCRIPTION|QUANTITY|PRICE|AMOUNT|TOTAL|PACKING|FOB|TRADE|SHIPPING|CERTIFIED)", line_s, re.IGNORECASE):
                    return line_s
        return None
