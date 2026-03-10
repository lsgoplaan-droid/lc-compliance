import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class PackingListExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # LC Reference
        val, conf = self._find_pattern_confidence(text, [
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_reference"] = self._make_field(val, conf)

        # Shipper (Beneficiary)
        val = self._extract_block_after_keyword(text, [
            "SHIPPER", "EXPORTER", "FROM", "SELLER"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["shipper_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["shipper_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["shipper_address"] = self._make_field(None)
        else:
            fields["shipper_name"] = self._make_field(None)
            fields["shipper_address"] = self._make_field(None)

        # Consignee (Applicant)
        val = self._extract_block_after_keyword(text, [
            "CONSIGNEE", "BUYER", "IMPORTER", "TO", "SHIP TO"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["consignee_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["consignee_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["consignee_address"] = self._make_field(None)
        else:
            fields["consignee_name"] = self._make_field(None)
            fields["consignee_address"] = self._make_field(None)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "DESCRIPTION", "GOODS", "ITEMS", "PARTICULARS",
            "DESCRIPTION OF GOODS"
        ], max_lines=10)
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # Quantity / Number of Packages
        val, conf = self._find_pattern_confidence(text, [
            r"(?:TOTAL\s*(?:PACKAGES|CTNS|CARTONS|QUANTITY)|NO\.?\s*OF\s*(?:PACKAGES|CTNS))\s*[:.]?\s*([\d,]+\s*\w*)",
            r"(?:QUANTITY|QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*\w+)",
            r"(\d[\d,]*)\s*(?:PCS|PIECES|SETS|UNITS|CTNS?|CARTONS|PACKAGES|PALLETS)",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Net Weight
        val, conf = self._find_pattern_confidence(text, [
            r"(?:NET\s*(?:WEIGHT|WT\.?))\s*[:.]?\s*([\d,]+\.?\d*\s*(?:KGS?|MTS?|LBS?))",
        ])
        fields["net_weight"] = self._make_field(val, conf)

        # Gross Weight
        val, conf = self._find_pattern_confidence(text, [
            r"(?:GROSS\s*(?:WEIGHT|WT\.?))\s*[:.]?\s*([\d,]+\.?\d*\s*(?:KGS?|MTS?|LBS?))",
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
            "MARKS"
        ], max_lines=5)
        fields["marks_and_numbers"] = self._make_field(val, 0.7 if val else 0.0)

        return fields
