import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class BillOfLadingExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # B/L Number
        val, conf = self._find_pattern_confidence(text, [
            r"(?:B/?L\s*(?:No\.?|Number|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:BILL\s*OF\s*LADING\s*(?:No\.?|Number|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["bl_number"] = self._make_field(val, conf)

        # LC Reference
        val, conf = self._find_pattern_confidence(text, [
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_reference"] = self._make_field(val, conf)

        # Shipper (Beneficiary)
        val = self._extract_block_after_keyword(text, [
            "SHIPPER", "CONSIGNOR", "EXPORTER"
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
            "CONSIGNEE", "CONSIGNED TO"
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

        # Port of Loading
        val, conf = self._find_pattern_confidence(text, [
            r"(?:PORT\s*OF\s*LOADING|PLACE\s*OF\s*RECEIPT|LOADED\s*(?:AT|ON\s*BOARD\s*AT))\s*[:.]?\s*(.+)",
        ])
        fields["port_of_loading"] = self._make_field(val, conf)

        # Port of Discharge
        val, conf = self._find_pattern_confidence(text, [
            r"(?:PORT\s*OF\s*DISCHARGE|PLACE\s*OF\s*DELIVERY|FINAL\s*DESTINATION)\s*[:.]?\s*(.+)",
        ])
        fields["port_of_discharge"] = self._make_field(val, conf)

        # Vessel Name
        val, conf = self._find_pattern_confidence(text, [
            r"(?:VESSEL|SHIP|OCEAN\s*VESSEL|VESSEL\s*NAME)\s*[:.]?\s*(.+)",
            r"(?:M/?V|S/?S)\s+(.+)",
        ])
        fields["vessel_name"] = self._make_field(val, conf)

        # Shipped On Board Date
        val, conf = self._find_pattern_confidence(text, [
            r"(?:SHIPPED\s*ON\s*BOARD|ON\s*BOARD\s*DATE|LADEN\s*ON\s*BOARD)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:SHIPPED\s*ON\s*BOARD|ON\s*BOARD)\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:DATE\s*OF\s*SHIPMENT|SHIPMENT\s*DATE)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        ])
        fields["shipped_on_board_date"] = self._make_field(val, conf)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "DESCRIPTION OF GOODS", "DESCRIPTION OF PACKAGES",
            "PARTICULARS", "GOODS DESCRIPTION", "DESCRIPTION"
        ], max_lines=10)
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # Quantity (number of packages/containers)
        val, conf = self._find_pattern_confidence(text, [
            r"(?:NO\.?\s*OF\s*(?:PACKAGES|CONTAINERS|CTNS)|QUANTITY)\s*[:.]?\s*([\d,]+\s*\w*)",
            r"(\d+)\s*(?:PACKAGES|CONTAINERS|CTNS|CARTONS|PALLETS|PIECES)\b",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Gross Weight
        val, conf = self._find_pattern_confidence(text, [
            r"(?:GROSS\s*WEIGHT)\s*[:.]?\s*([\d,]+\.?\d*\s*(?:KGS?|MTS?|LBS?))",
        ])
        fields["gross_weight"] = self._make_field(val, conf)

        # Partial Shipments (inferred)
        # If multiple B/L numbers found, partial shipments may be indicated
        fields["partial_shipments"] = self._make_field(None)

        # Transhipment (inferred from route)
        val, conf = self._find_pattern_confidence(text, [
            r"(?:TRANS?SHIPMENT)\s*[:.]?\s*(ALLOWED|PERMITTED|NOT\s*ALLOWED|PROHIBITED|YES|NO)",
        ])
        fields["transhipment"] = self._make_field(val, conf)

        return fields
