import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class CertificateOfOriginExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # Certificate Number
        val, conf = self._find_pattern_confidence(text, [
            r"(?:CERTIFICATE\s*(?:No\.?|Number|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:CERT\.?\s*(?:No\.?|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["certificate_number"] = self._make_field(val, conf)

        # Exporter (Beneficiary)
        val = self._extract_block_after_keyword(text, [
            "EXPORTER", "SHIPPER", "CONSIGNOR", "MANUFACTURER"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["exporter_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["exporter_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["exporter_address"] = self._make_field(None)
        else:
            fields["exporter_name"] = self._make_field(None)
            fields["exporter_address"] = self._make_field(None)

        # Importer (Applicant)
        val = self._extract_block_after_keyword(text, [
            "IMPORTER", "CONSIGNEE", "BUYER"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["importer_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["importer_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["importer_address"] = self._make_field(None)
        else:
            fields["importer_name"] = self._make_field(None)
            fields["importer_address"] = self._make_field(None)

        # Country of Origin
        val, conf = self._find_pattern_confidence(text, [
            r"(?:COUNTRY\s*OF\s*ORIGIN)\s*[:.]?\s*(.+)",
            r"(?:ORIGIN)\s*[:.]?\s*(.+)",
            r"(?:MADE\s*IN|MANUFACTURED\s*IN|PRODUCED\s*IN)\s+(.+)",
        ])
        fields["country_of_origin"] = self._make_field(val, conf)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "DESCRIPTION OF GOODS", "GOODS", "DESCRIPTION",
            "COMMODITY", "MERCHANDISE"
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
            r"(\d[\d,]*\.?\d*)\s*(?:PCS|PIECES|SETS|UNITS|TONS|KGS?|MTS?|CTNS?)",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Certifying Authority
        val, conf = self._find_pattern_confidence(text, [
            r"(?:CERTIFIED\s*BY|CERTIFYING\s*(?:AUTHORITY|BODY)|CHAMBER\s*OF\s*COMMERCE)\s*[:.]?\s*(.+)",
            r"(?:ISSUED\s*BY)\s*[:.]?\s*(.+)",
        ])
        fields["certifying_authority"] = self._make_field(val, conf)

        return fields
