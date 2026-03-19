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
        val = self._extract_shipper_block(text)
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
        val = self._extract_consignee(text)
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
            # "VESSEL / VOYAGE: MT DESERT ROSE / V.042" — extract vessel name before voyage
            r"VESSEL\s*/\s*VOYAGE\s*[:.]?\s*(.+?)\s*/\s*V\.",
            # "VESSEL: MT DESERT ROSE" — simple label
            r"(?:VESSEL\s*NAME|OCEAN\s*VESSEL)\s*[:.]?\s*(.+)",
            r"(?:VESSEL)\s*[:.]?\s*(.+)",
            r"(?:M/?V|S/?S)\s+(.+)",
        ])
        fields["vessel_name"] = self._make_field(val, conf)

        # Shipped On Board Date
        val, conf = self._find_pattern_confidence(text, [
            r"(?:SHIPPED\s*ON\s*BOARD|ON\s*BOARD\s*DATE|LADEN\s*ON\s*BOARD)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            # "SHIPPED ON BOARD DATE: 14 MAY 2025" — with optional "DATE" keyword
            r"(?:SHIPPED\s*ON\s*BOARD(?:\s*DATE)?|ON\s*BOARD(?:\s*DATE)?)\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:DATE\s*OF\s*SHIPMENT|SHIPMENT\s*DATE)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:DATE\s*OF\s*SHIPMENT|SHIPMENT\s*DATE)\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
        ])
        fields["shipped_on_board_date"] = self._make_field(val, conf)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "DESCRIPTION OF GOODS", "DESCRIPTION OF PACKAGES",
            "PARTICULARS", "GOODS DESCRIPTION", "DESCRIPTION"
        ], max_lines=10)
        fields["goods_description"] = self._make_field(val, 0.7 if val else 0.0)

        # Quantity (number of packages/containers, or bulk weight from goods description)
        val, conf = self._find_pattern_confidence(text, [
            # Bulk oil: "60,000.000 METRIC TONS" in goods description
            r"([\d,]+\.?\d*)\s*METRIC\s*TONS?\b",
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

    def _extract_shipper_block(self, text: str) -> str | None:
        """Extract shipper block, filtering out interleaved B/L NO and DATE lines."""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            if "SHIPPER" in line_upper or "CONSIGNOR" in line_upper or "EXPORTER" in line_upper:
                # Check if value is on the same line after a colon
                after_kw = re.split(r"[:]\s*", line, maxsplit=1)
                if len(after_kw) > 1 and after_kw[1].strip():
                    block_lines = [after_kw[1].strip()]
                else:
                    block_lines = []

                # Collect subsequent lines, skipping B/L NO, DATE, BOOKING NO lines
                for j in range(i + 1, min(i + 1 + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    # Stop at another major section keyword
                    if re.match(r"^(?:CONSIGNEE|NOTIFY|VESSEL|PORT|DESCRIPTION)", next_line, re.IGNORECASE):
                        break
                    # Skip interleaved reference fields (B/L NO, DATE, BOOKING NO)
                    if re.match(r"^(?:B/?L\s*(?:NO|NUMBER|#)|DATE\s*:|BOOKING\s*(?:NO|NUMBER|#)|REF)", next_line, re.IGNORECASE):
                        continue
                    block_lines.append(next_line)

                if block_lines:
                    return "\n".join(block_lines[:4])
        # Fall back to base method
        return self._extract_block_after_keyword(text, ["SHIPPER", "CONSIGNOR", "EXPORTER"], max_lines=4)

    def _extract_consignee(self, text: str) -> str | None:
        """Extract consignee, handling 'TO THE ORDER OF <bank>' by falling back to notify party."""
        lines = text.split("\n")

        # Find consignee and notify party sections
        consignee_val = None
        notify_val = None

        for i, line in enumerate(lines):
            line_upper = line.upper().strip()

            # Look for "TO THE ORDER OF" line — this is a bank consignment
            if "TO THE ORDER OF" in line_upper or "ORDER OF" in line_upper:
                # Fall through to notify party extraction below
                consignee_val = "ORDER_OF_BANK"
                continue

            # Look for NOTIFY PARTY and collect company names after it
            if "NOTIFY" in line_upper and "PARTY" in line_upper:
                block_lines = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    if re.match(r"^(?:VESSEL|PORT|DESCRIPTION|PLACE|LOADED)", next_line, re.IGNORECASE):
                        break
                    # Skip "TO THE ORDER OF" line from consignee column
                    if "TO THE ORDER OF" in next_line.upper():
                        continue
                    block_lines.append(next_line)
                if block_lines:
                    notify_val = "\n".join(block_lines)

            # Standard consignee (not "TO THE ORDER OF")
            if ("CONSIGNEE" in line_upper or "CONSIGNED TO" in line_upper) and consignee_val is None:
                block_lines = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    if re.match(r"^(?:NOTIFY|VESSEL|PORT|DESCRIPTION|PLACE)", next_line, re.IGNORECASE):
                        break
                    if "TO THE ORDER OF" in next_line.upper():
                        consignee_val = "ORDER_OF_BANK"
                        continue
                    block_lines.append(next_line)
                if block_lines and consignee_val != "ORDER_OF_BANK":
                    consignee_val = "\n".join(block_lines)

        # If consignee is a bank order, use notify party
        if consignee_val == "ORDER_OF_BANK" and notify_val:
            return notify_val
        if consignee_val and consignee_val != "ORDER_OF_BANK":
            return consignee_val
        if notify_val:
            return notify_val
        return None
