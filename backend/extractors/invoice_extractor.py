import re
from typing import Dict

from models.schemas import ExtractedField
from extractors.base import BaseFieldExtractor


class InvoiceExtractor(BaseFieldExtractor):
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        fields = {}
        text = raw_text

        # Invoice Number
        val, conf = self._find_pattern_confidence(text, [
            r"(?:INVOICE\s*(?:No\.?|NUMBER|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:INV\.?\s*(?:No\.?|#))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["invoice_number"] = self._make_field(val, conf)

        # Invoice Date
        val, conf = self._find_pattern_confidence(text, [
            r"(?:INVOICE\s*DATE|DATE\s*OF\s*INVOICE)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            r"(?:INVOICE\s*DATE|DATE)\s*[:.]?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:DATE)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        ])
        fields["invoice_date"] = self._make_field(val, conf)

        # LC Reference
        val, conf = self._find_pattern_confidence(text, [
            r"(?:L/?C\s*(?:No\.?|Ref|Number))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
            r"(?:CREDIT\s*(?:No\.?|Number))\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]+)",
        ])
        fields["lc_reference"] = self._make_field(val, conf)

        # Seller (Beneficiary)
        val = self._extract_block_after_keyword(text, [
            "SELLER", "EXPORTER", "SHIPPER", "FROM", "BENEFICIARY"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["seller_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["seller_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["seller_address"] = self._make_field(None)
        else:
            fields["seller_name"] = self._make_field(None)
            fields["seller_address"] = self._make_field(None)

        # Buyer (Applicant)
        val = self._extract_block_after_keyword(text, [
            "BUYER", "IMPORTER", "CONSIGNEE", "TO", "BILL TO", "SOLD TO"
        ], max_lines=4)
        if val:
            lines = val.strip().split("\n")
            fields["buyer_name"] = self._make_field(lines[0], 0.8)
            if len(lines) > 1:
                fields["buyer_address"] = self._make_field("\n".join(lines[1:]), 0.7)
            else:
                fields["buyer_address"] = self._make_field(None)
        else:
            fields["buyer_name"] = self._make_field(None)
            fields["buyer_address"] = self._make_field(None)

        # Currency
        val, conf = self._find_pattern_confidence(text, [
            r"(?:CURRENCY)\s*[:.]?\s*([A-Z]{3})",
            r"(?:TOTAL|AMOUNT|GRAND\s*TOTAL)\s*[:.]?\s*([A-Z]{3})",
        ])
        if not val:
            # Try to find currency in amount line
            match = re.search(r"([A-Z]{3})\s*[\d,]+\.?\d*", text)
            if match:
                val, conf = match.group(1), 0.6
        fields["currency"] = self._make_field(val, conf)

        # Total Amount
        val, conf = self._find_pattern_confidence(text, [
            r"(?:TOTAL\s*(?:AMOUNT|VALUE)|GRAND\s*TOTAL|NET\s*TOTAL)\s*[:.]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
            r"(?:TOTAL)\s*[:.]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
        ])
        fields["total_amount"] = self._make_field(val, conf)

        # Goods Description
        val = self._extract_block_after_keyword(text, [
            "DESCRIPTION", "GOODS", "ITEMS", "PARTICULARS",
            "DESCRIPTION OF GOODS"
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
            r"(?:QUANTITY|QTY|TOTAL\s*QTY)\s*[:.]?\s*([\d,]+\.?\d*\s*\w+)",
            r"(\d[\d,]*\.?\d*)\s*(?:PCS|PIECES|SETS|UNITS|TONS|KGS?|MTS?|CTNS?|CARTONS)",
        ])
        fields["quantity"] = self._make_field(val, conf)

        # Unit Price
        val, conf = self._find_pattern_confidence(text, [
            r"(?:UNIT\s*PRICE|PRICE\s*PER\s*UNIT|RATE)\s*[:.]?\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)",
            r"(?:@|AT)\s*(?:[A-Z]{3}\s*)?([\d,]+\.?\d*)\s*(?:PER|/)",
        ])
        fields["unit_price"] = self._make_field(val, conf)

        # Incoterms
        val, conf = self._find_pattern_confidence(text, [
            r"\b(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b",
        ])
        fields["incoterms"] = self._make_field(val, conf)

        # Port of Loading (if present)
        val, conf = self._find_pattern_confidence(text, [
            r"(?:PORT\s*OF\s*LOADING|LOADING\s*PORT)\s*[:.]?\s*(.+)",
        ])
        fields["port_of_loading"] = self._make_field(val, conf)

        # Port of Discharge (if present)
        val, conf = self._find_pattern_confidence(text, [
            r"(?:PORT\s*OF\s*DISCHARGE|DESTINATION|DISCHARGE\s*PORT)\s*[:.]?\s*(.+)",
        ])
        fields["port_of_discharge"] = self._make_field(val, conf)

        return fields
