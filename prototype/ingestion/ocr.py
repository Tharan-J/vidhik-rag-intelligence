"""
OCR Fallback Subsystem (PaddleOCR PP-OCRv4 / RapidOCR)
=====================================================
Performs deterministic local optical character recognition on scanned pages.
Strict Rule: Operates entirely locally; never transmits PDFs or page images to external APIs.
"""

import logging
from typing import Tuple, Optional
import numpy as np
import pymupdf

logger = logging.getLogger("VidhikIngestion.OCR")

_OCR_ENGINE = None


def get_ocr_engine():
    """Lazily initialize the local OCR engine."""
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        try:
            # 1. Prefer RapidOCR (ONNX Runtime implementation of PP-OCRv4)
            from rapidocr_onnxruntime import RapidOCR
            logger.info("Initializing local RapidOCR (PaddleOCR PP-OCRv4 ONNX)...")
            _OCR_ENGINE = RapidOCR()
        except ImportError:
            try:
                # 2. Fallback to paddleocr package
                from paddleocr import PaddleOCR
                logger.info("Initializing PaddleOCR package...")
                _OCR_ENGINE = PaddleOCR(use_angle_cls=True, lang="en")
            except ImportError:
                logger.warning("Neither rapidocr-onnxruntime nor paddleocr is available.")
                _OCR_ENGINE = False
    return _OCR_ENGINE if _OCR_ENGINE is not False else None


def ocr_page(page: pymupdf.Page, dpi: int = 200) -> Tuple[str, float]:
    """
    Render a PyMuPDF page to image and perform local OCR.
    
    Returns:
        (extracted_text, average_confidence)
    """
    engine = get_ocr_engine()
    if engine is None:
        logger.error("OCR requested but no local OCR engine is installed.")
        return "", 0.0

    try:
        # Render page to pixmap
        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")

        # Handle RapidOCR vs PaddleOCR API
        text_lines = []
        scores = []

        if hasattr(engine, "__call__"):
            # RapidOCR accepts bytes, numpy array, or file path
            result, elapse = engine(img_bytes)
            if result:
                for line in result:
                    # line format: [[box], text, score]
                    text_lines.append(line[1])
                    scores.append(float(line[2]))
        elif hasattr(engine, "ocr"):
            # PaddleOCR accepts numpy array
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            np_img = np.array(img)
            result = engine.ocr(np_img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    text_lines.append(line[1][0])
                    scores.append(float(line[1][1]))

        full_text = "\n".join(text_lines).strip()
        avg_score = float(np.mean(scores)) if scores else 0.0
        return full_text, avg_score

    except Exception as e:
        logger.error(f"Error during OCR execution: {e}")
        return "", 0.0
