"""
Deterministic PDF Validation and Page Extraction Subsystem
===========================================================
Primary extractor: PyMuPDF (fitz)
Fallback extractor: Local PaddleOCR / RapidOCR
Preserves strict page boundaries: page_number, raw_text, extraction_method.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pymupdf

from .ocr import ocr_page

logger = logging.getLogger("VidhikIngestion.Extract")


class PDFValidationError(Exception):
    """Raised when PDF fails integrity or structural validation."""
    pass


def validate_pdf(pdf_path: Path) -> Tuple[bool, int, str]:
    """
    Validate that PDF file exists, is openable, not encrypted, and has pages.
    
    Returns:
        (is_valid, page_count, message)
    """
    if not pdf_path.exists():
        return False, 0, f"File does not exist: {pdf_path}"

    if pdf_path.stat().st_size == 0:
        return False, 0, "PDF file is 0 bytes (empty file)"

    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as e:
        return False, 0, f"PDF failed to open: {type(e).__name__} - {e}"

    try:
        page_count = len(doc)
        if page_count == 0:
            doc.close()
            return False, 0, "PDF has 0 pages"

        if doc.is_encrypted:
            doc.close()
            return False, page_count, "PDF is encrypted / password protected"

        doc.close()
        return True, page_count, "VALID"
    except Exception as e:
        return False, 0, f"PDF inspection error: {e}"


def extract_pages_from_pdf(
    pdf_path: Path,
    min_page_chars: int = 30,
    enable_ocr_fallback: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page from PDF.
    
    Returns:
        List of dicts: [
            {
                "page_number": int (1-indexed),
                "text": str,
                "extraction_method": "native" | "ocr"
            },
            ...
        ]
    """
    is_valid, page_count, err_msg = validate_pdf(pdf_path)
    if not is_valid:
        raise PDFValidationError(f"Validation failed for {pdf_path}: {err_msg}")

    doc = pymupdf.open(str(pdf_path))
    pages_data = []

    try:
        for pno in range(page_count):
            page_num = pno + 1
            page = doc[pno]
            native_text = page.get_text("text").strip()

            if len(native_text) >= min_page_chars:
                pages_data.append({
                    "page_number": page_num,
                    "text": native_text,
                    "extraction_method": "native"
                })
            else:
                # Page has insufficient native text; attempt OCR fallback
                if enable_ocr_fallback:
                    ocr_text, conf = ocr_page(page)
                    if len(ocr_text.strip()) > 0:
                        logger.info(f"Page {page_num} of {pdf_path.name} extracted via OCR (confidence: {conf:.2f})")
                        pages_data.append({
                            "page_number": page_num,
                            "text": ocr_text.strip(),
                            "extraction_method": "ocr"
                        })
                    else:
                        # Retain whatever native text existed rather than discarding
                        pages_data.append({
                            "page_number": page_num,
                            "text": native_text,
                            "extraction_method": "native_empty"
                        })
                else:
                    pages_data.append({
                        "page_number": page_num,
                        "text": native_text,
                        "extraction_method": "native"
                    })
    finally:
        doc.close()

    return pages_data


def extract_document(
    pdf_path: Path,
    pre_extracted_json: Optional[Path] = None,
    min_page_chars: int = 30,
    enable_ocr_fallback: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract document pages, reusing pre-extracted structured JSON if verified and available.
    """
    # 1. Reuse existing verified JSON if provided and valid
    if pre_extracted_json and pre_extracted_json.exists():
        try:
            with open(pre_extracted_json, "r", encoding="utf-8") as f:
                cached = json.load(f)
            # Check structure.pages or raw_pages
            if "structure" in cached and "pages" in cached["structure"] and cached["structure"]["pages"]:
                pages = []
                for p in cached["structure"]["pages"]:
                    p_num = p.get("page_number", len(pages) + 1)
                    # Reconstruct text from paragraphs
                    p_text = "\n\n".join([par.get("text", "") for par in p.get("paragraphs", [])])
                    pages.append({
                        "page_number": p_num,
                        "text": p_text,
                        "extraction_method": "cached_verified"
                    })
                if pages:
                    return pages
        except Exception as e:
            logger.warning(f"Failed to load cached JSON {pre_extracted_json}: {e}; falling back to PDF extraction.")

    # 2. Extract directly from PDF
    return extract_pages_from_pdf(
        pdf_path=pdf_path,
        min_page_chars=min_page_chars,
        enable_ocr_fallback=enable_ocr_fallback
    )
