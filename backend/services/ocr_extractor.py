import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
    import io
    from config import TESSERACT_CMD

    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract or Pillow not installed. OCR will be unavailable.")


class OCRExtractor:
    def extract(self, file_path: str) -> str:
        if not OCR_AVAILABLE:
            logger.warning("OCR not available, returning empty text")
            return ""

        doc = fitz.open(file_path)
        pages_text = []

        for page in doc:
            # Render page to image at 300 DPI
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            # Convert to grayscale for better OCR
            img = img.convert("L")

            # Run OCR
            try:
                text = pytesseract.image_to_string(img)
                pages_text.append(text)
            except Exception as e:
                logger.error(f"OCR failed on page {page.number}: {e}")
                pages_text.append("")

        doc.close()
        return "\n\n".join(pages_text)


ocr_extractor = OCRExtractor()
