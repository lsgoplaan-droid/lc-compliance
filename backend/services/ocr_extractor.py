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
            # Render page to image at 150 DPI (fast enough for cloud free tier)
            pix = page.get_pixmap(dpi=150)

            # Limit image size: resize if too large (max 2000px on longest side)
            max_dim = max(pix.width, pix.height)
            if max_dim > 2000:
                scale = 2000 / max_dim
                pix = page.get_pixmap(dpi=int(150 * scale))

            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )

            # Convert RGBA to RGB if needed (rapidocr expects 3 channels)
            if pix.n == 4:
                img_array = img_array[:, :, :3]

            # Run OCR (rapidocr accepts numpy arrays)
            try:
                logger.info(f"OCR page {page.number}: {pix.width}x{pix.height} ({pix.n}ch)")
                result, _ = engine(img_array)
                if result:
                    text = "\n".join([line[1] for line in result])
                    pages_text.append(text)
                    logger.info(f"OCR page {page.number}: extracted {len(text)} chars")
                else:
                    pages_text.append("")
                    logger.info(f"OCR page {page.number}: no text found")
            except Exception as e:
                logger.error(f"OCR failed on page {page.number}: {e}")
                pages_text.append("")

        doc.close()
        return "\n\n".join(pages_text)


ocr_extractor = OCRExtractor()
