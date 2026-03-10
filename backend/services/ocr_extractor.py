import gc
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

try:
    from rapidocr_onnxruntime import RapidOCR
    import numpy as np

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
            # Use low DPI (100) and cap at 1200px to stay within Render free tier memory
            pix = page.get_pixmap(dpi=100)

            max_dim = max(pix.width, pix.height)
            if max_dim > 1200:
                scale = 1200 / max_dim
                pix = page.get_pixmap(dpi=int(100 * scale))

            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )

            # Convert RGBA to RGB if needed (rapidocr expects 3 channels)
            if pix.n == 4:
                img_array = img_array[:, :, :3].copy()

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
            finally:
                # Free memory between pages
                del img_array, pix
                gc.collect()

        doc.close()
        return "\n\n".join(pages_text)


ocr_extractor = OCRExtractor()
