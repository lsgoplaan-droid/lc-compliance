import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

try:
    from rapidocr_onnxruntime import RapidOCR
    import numpy as np
    import io

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("rapidocr-onnxruntime not installed. OCR will be unavailable.")


class OCRExtractor:
    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None and OCR_AVAILABLE:
            self._engine = RapidOCR()
        return self._engine

    def extract(self, file_path: str) -> str:
        if not OCR_AVAILABLE:
            logger.warning("OCR not available, returning empty text")
            return ""

        engine = self._get_engine()
        if not engine:
            return ""

        doc = fitz.open(file_path)
        pages_text = []

        for page in doc:
            # Render page to image at 300 DPI as numpy array
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )

            # Run OCR (rapidocr accepts numpy arrays)
            try:
                result, _ = engine(img_array)
                if result:
                    text = "\n".join([line[1] for line in result])
                    pages_text.append(text)
                else:
                    pages_text.append("")
            except Exception as e:
                logger.error(f"OCR failed on page {page.number}: {e}")
                pages_text.append("")

        doc.close()
        return "\n\n".join(pages_text)


ocr_extractor = OCRExtractor()
