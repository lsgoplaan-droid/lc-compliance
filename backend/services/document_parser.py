import logging
from typing import Dict, Tuple

from models.enums import DocumentType
from models.schemas import ExtractedField
from services.text_extractor import text_extractor
from services.ocr_extractor import ocr_extractor
from config import OCR_MIN_CHARS_PER_PAGE

logger = logging.getLogger(__name__)


class DocumentParser:
    def __init__(self):
        self._extractors = {}

    def _get_field_extractor(self, document_type: DocumentType):
        if not self._extractors:
            from extractors.lc_advice_extractor import LCAdviceExtractor
            from extractors.invoice_extractor import InvoiceExtractor
            from extractors.certificate_origin_extractor import CertificateOfOriginExtractor
            from extractors.bill_of_lading_extractor import BillOfLadingExtractor
            from extractors.packing_list_extractor import PackingListExtractor

            self._extractors = {
                DocumentType.LC_ADVICE: LCAdviceExtractor(),
                DocumentType.COMMERCIAL_INVOICE: InvoiceExtractor(),
                DocumentType.CERTIFICATE_OF_ORIGIN: CertificateOfOriginExtractor(),
                DocumentType.BILL_OF_LADING: BillOfLadingExtractor(),
                DocumentType.PACKING_LIST: PackingListExtractor(),
            }
        return self._extractors[document_type]

    def parse(
        self, file_path: str, document_type: DocumentType
    ) -> Tuple[str, str, Dict[str, ExtractedField]]:
        # Handle plain text files directly
        if file_path.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
            extraction_method = "text"
        else:
            # PDF: try text extraction first
            raw_text = text_extractor.extract(file_path)
            extraction_method = "text"

            # Check if text is too sparse (likely scanned)
            pages = text_extractor.extract_per_page(file_path)
            page_count = max(len(pages), 1)
            avg_chars = len(raw_text.strip()) / page_count

            if avg_chars < OCR_MIN_CHARS_PER_PAGE:
                logger.info(
                    f"Sparse text ({avg_chars:.0f} chars/page), attempting OCR for {file_path}"
                )
                ocr_text = ocr_extractor.extract(file_path)
                if len(ocr_text.strip()) > len(raw_text.strip()):
                    raw_text = ocr_text
                    extraction_method = "ocr"

        # Extract fields using document-type-specific extractor
        extractor = self._get_field_extractor(document_type)
        fields = extractor.extract_fields(raw_text)

        return raw_text, extraction_method, fields


document_parser = DocumentParser()
