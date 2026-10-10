"""
Deterministic Source Verification and Context Reconstruction Engine
=====================================================================
Module: prototype.rag.source_verifier
Author: Vidhik Engineering

Responsibilities:
1. Cryptographic PDF Integrity (SHA-256 checksum tracking).
2. Page-level extraction with stable paragraph identifiers and character offsets.
3. Strict coordinate verification (verifying page and paragraph landmarks without hallucination).
4. Boundary-aware context reconstruction (recovering parent paragraph and configurable ±N surrounding context).
5. Defect detection:
   - Coordinate Mismatch (passage on different page than claimed)
   - Passage Not Found (hallucinated or deleted quote)
   - Document Stale (hash mismatch between indexed and current file)
   - Document Deleted (file missing from persistent storage)
   - OCR Uncertainty (noisy scan text / broken ligatures / character confusion)
6. Clear separation between source integrity verification and semantic legal support (SUPPORTS/CONTRADICTS).
"""

import os
import re
import json
import hashlib
import unicodedata
from difflib import SequenceMatcher
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


# Verification status enum values
STATUS_VERIFIED_EXACT = "VERIFIED_EXACT"
STATUS_VERIFIED_NORMALIZED = "VERIFIED_NORMALIZED"
STATUS_OCR_UNCERTAINTY = "OCR_UNCERTAINTY"
STATUS_COORDINATE_MISMATCH = "COORDINATE_MISMATCH"
STATUS_PASSAGE_NOT_FOUND = "PASSAGE_NOT_FOUND"
STATUS_DOCUMENT_STALE = "DOCUMENT_STALE"
STATUS_DOCUMENT_DELETED = "DOCUMENT_DELETED"
STATUS_HISTORICAL_UNVERIFIED = "HISTORICAL_UNVERIFIED"


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file reading in chunks."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return ""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_text_for_comparison(text: str) -> str:
    """
    Standardize Unicode characters, whitespace, soft hyphens, and linebreaks
    without claiming modified character offsets.
    """
    if not text:
        return ""
    # Unicode NFKC normalization (handles ligatures like 'fi' -> 'f' 'i')
    normalized = unicodedata.normalize("NFKC", text)
    # Remove soft hyphens and zero-width spaces
    normalized = normalized.replace("\xad", "").replace("\u200b", "")
    # Normalize common quotes and dashes
    normalized = normalized.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("—", "-").replace("–", "-")
    # Collapse multiple whitespace and newlines to single space
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


@dataclass
class ExtractedParagraph:
    paragraph_id: str
    page_number: int
    paragraph_index: int
    raw_text: str
    normalized_text: str
    char_start: int
    char_end: int


@dataclass
class ExtractedPage:
    page_number: int
    raw_text: str
    normalized_text: str
    char_count: int
    paragraphs: List[ExtractedParagraph] = field(default_factory=list)


@dataclass
class ExtractionManifest:
    document_id: str
    document_sha256: str
    source_path: str
    total_pages: int
    total_paragraphs: int
    pages: List[ExtractedPage] = field(default_factory=list)
    paragraphs: List[ExtractedParagraph] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_sha256": self.document_sha256,
            "source_path": self.source_path,
            "total_pages": self.total_pages,
            "total_paragraphs": self.total_paragraphs,
            "pages": [
                {
                    "page_number": p.page_number,
                    "char_count": p.char_count,
                    "raw_text": p.raw_text,
                    "paragraph_count": len(p.paragraphs),
                }
                for p in self.pages
            ],
            "paragraphs": [
                {
                    "paragraph_id": p.paragraph_id,
                    "page_number": p.page_number,
                    "paragraph_index": p.paragraph_index,
                    "char_start": p.char_start,
                    "char_end": p.char_end,
                    "text": p.raw_text,
                }
                for p in self.paragraphs
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionManifest":
        pages = []
        all_paras = []
        for p_data in data.get("pages", []):
            p = ExtractedPage(
                page_number=p_data["page_number"],
                raw_text=p_data["raw_text"],
                normalized_text=normalize_text_for_comparison(p_data["raw_text"]),
                char_count=p_data.get("char_count", len(p_data["raw_text"])),
            )
            pages.append(p)

        for para_data in data.get("paragraphs", []):
            para = ExtractedParagraph(
                paragraph_id=para_data["paragraph_id"],
                page_number=para_data["page_number"],
                paragraph_index=para_data["paragraph_index"],
                raw_text=para_data["text"],
                normalized_text=normalize_text_for_comparison(para_data["text"]),
                char_start=para_data.get("char_start", 0),
                char_end=para_data.get("char_end", len(para_data["text"])),
            )
            all_paras.append(para)
            # associate with page
            for page in pages:
                if page.page_number == para.page_number:
                    page.paragraphs.append(para)

        return cls(
            document_id=data["document_id"],
            document_sha256=data["document_sha256"],
            source_path=data.get("source_path", ""),
            total_pages=data.get("total_pages", len(pages)),
            total_paragraphs=data.get("total_paragraphs", len(all_paras)),
            pages=pages,
            paragraphs=all_paras,
        )


@dataclass
class ReconstructedContext:
    target_paragraph_id: str
    target_page: int
    target_text: str
    preceding_context: List[Dict[str, Any]]
    succeeding_context: List[Dict[str, Any]]
    full_context_text: str
    paragraph_range: Tuple[str, str]
    page_span: Tuple[int, int]


@dataclass
class ProvenanceVerificationResult:
    verification_status: str
    document_id: str
    document_sha256: str
    reported_page: Optional[int]
    verified_page: Optional[int]
    reported_paragraph: Optional[str]
    verified_paragraph: Optional[str]
    similarity_score: float
    is_exact_match: bool
    char_offset_in_page: Optional[Tuple[int, int]]
    reconstructed_context: Optional[ReconstructedContext]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_status": self.verification_status,
            "document_id": self.document_id,
            "document_sha256": self.document_sha256,
            "reported_page": self.reported_page,
            "verified_page": self.verified_page,
            "reported_paragraph": self.reported_paragraph,
            "verified_paragraph": self.verified_paragraph,
            "similarity_score": round(self.similarity_score, 4),
            "is_exact_match": self.is_exact_match,
            "char_offset_in_page": list(self.char_offset_in_page) if self.char_offset_in_page else None,
            "reconstructed_context": asdict(self.reconstructed_context) if self.reconstructed_context else None,
            "notes": self.notes,
        }


class DocumentManifestStore:
    """
    Manages deterministic extraction manifests on disk.
    Allows caching of page/paragraph extraction to avoid repeatedly re-parsing large PDFs.
    """

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = store_dir or (Path(__file__).resolve().parent.parent / "manifests")
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _manifest_path(self, document_id: str) -> Path:
        safe_name = re.sub(r"[^\w\-.]", "_", document_id)
        return self.store_dir / f"{safe_name}.manifest.json"

    def get_manifest(self, document_id: str) -> Optional[ExtractionManifest]:
        p = self._manifest_path(document_id)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ExtractionManifest.from_dict(data)
        except Exception:
            return None

    def save_manifest(self, manifest: ExtractionManifest):
        p = self._manifest_path(manifest.document_id)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)


def extract_manifest_from_pdf(pdf_path: Path, document_id: Optional[str] = None) -> ExtractionManifest:
    """
    Extracts text page-by-page from an actual court PDF, computes SHA-256,
    identifies paragraph boundaries, and computes exact character offsets within each page.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF parsing.")

    doc_id = document_id or pdf_path.name
    doc_sha = compute_file_sha256(pdf_path)

    doc = fitz.open(str(pdf_path))
    pages: List[ExtractedPage] = []
    all_paras: List[ExtractedParagraph] = []

    global_para_counter = 1

    for pno in range(len(doc)):
        page_num = pno + 1
        page = doc[pno]
        raw_text = page.get_text("text") or ""
        norm_text = normalize_text_for_comparison(raw_text)

        extracted_page = ExtractedPage(
            page_number=page_num,
            raw_text=raw_text,
            normalized_text=norm_text,
            char_count=len(raw_text),
            paragraphs=[],
        )

        # Segment paragraphs based on double line breaks or numbered legal paragraph markers
        # e.g., \n\n or \n12. or \n(a)
        # We track exact start/end character offsets in raw_text
        para_splits = list(re.finditer(r"(?:\n\s*\n|\n(?=\d+\.\s)|\n(?=[A-Z\s]{4,}\n))", raw_text))
        
        last_idx = 0
        page_paras = []
        for match in para_splits:
            split_start = match.start()
            split_end = match.end()
            p_text = raw_text[last_idx:split_start].strip()
            if len(p_text) > 10:  # Skip trivial whitespace fragments
                para_id = f"P{page_num:03d}_PAR{len(page_paras) + 1:03d}"
                p_norm = normalize_text_for_comparison(p_text)
                para_obj = ExtractedParagraph(
                    paragraph_id=para_id,
                    page_number=page_num,
                    paragraph_index=global_para_counter,
                    raw_text=p_text,
                    normalized_text=p_norm,
                    char_start=last_idx,
                    char_end=split_start,
                )
                page_paras.append(para_obj)
                all_paras.append(para_obj)
                global_para_counter += 1
            last_idx = split_end

        # Trailing paragraph on page
        trailing = raw_text[last_idx:].strip()
        if len(trailing) > 10:
            para_id = f"P{page_num:03d}_PAR{len(page_paras) + 1:03d}"
            para_obj = ExtractedParagraph(
                paragraph_id=para_id,
                page_number=page_num,
                paragraph_index=global_para_counter,
                raw_text=trailing,
                normalized_text=normalize_text_for_comparison(trailing),
                char_start=last_idx,
                char_end=len(raw_text),
            )
            page_paras.append(para_obj)
            all_paras.append(para_obj)
            global_para_counter += 1

        extracted_page.paragraphs = page_paras
        pages.append(extracted_page)

    doc.close()

    return ExtractionManifest(
        document_id=doc_id,
        document_sha256=doc_sha,
        source_path=str(pdf_path.resolve()),
        total_pages=len(pages),
        total_paragraphs=len(all_paras),
        pages=pages,
        paragraphs=all_paras,
    )


class LegalEvidenceVerifier:
    """
    Deterministic Verification and Context Reconstruction Engine.
    Ensures no source quote is accepted without verifiable landmarks and integrity checks.
    """

    def __init__(self, manifest_store: Optional[DocumentManifestStore] = None):
        self.manifest_store = manifest_store or DocumentManifestStore()

    def get_or_build_manifest(self, pdf_path: Path, document_id: Optional[str] = None) -> ExtractionManifest:
        doc_id = document_id or pdf_path.name
        existing = self.manifest_store.get_manifest(doc_id)
        if existing:
            # Check if source file has drifted by comparing SHA-256
            if pdf_path.exists():
                curr_sha = compute_file_sha256(pdf_path)
                if curr_sha == existing.document_sha256:
                    return existing
        # Build fresh manifest
        manifest = extract_manifest_from_pdf(pdf_path, doc_id)
        self.manifest_store.save_manifest(manifest)
        return manifest

    def reconstruct_context(
        self,
        manifest: ExtractionManifest,
        target_para_id: Optional[str] = None,
        target_page: Optional[int] = None,
        passage_text: Optional[str] = None,
        context_window_paragraphs: int = 1,
    ) -> Optional[ReconstructedContext]:
        """
        Reconstructs the target paragraph and surrounding context (±N paragraphs)
        with strict paragraph boundaries.
        """
        if not manifest.paragraphs:
            return None

        # Find target paragraph index
        target_idx = -1
        if target_para_id:
            for idx, p in enumerate(manifest.paragraphs):
                if p.paragraph_id == target_para_id:
                    target_idx = idx
                    break

        if target_idx == -1 and passage_text:
            # Locate by text inclusion
            norm_target = normalize_text_for_comparison(passage_text)
            best_sim = 0.0
            best_idx = -1
            for idx, p in enumerate(manifest.paragraphs):
                if norm_target in p.normalized_text:
                    target_idx = idx
                    break
                sim = SequenceMatcher(None, norm_target, p.normalized_text).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_idx = idx
            if target_idx == -1 and best_sim >= 0.75:
                target_idx = best_idx

        if target_idx == -1:
            # Default to first paragraph on reported page if given
            if target_page:
                for idx, p in enumerate(manifest.paragraphs):
                    if p.page_number == target_page:
                        target_idx = idx
                        break

        if target_idx == -1:
            return None

        target_para = manifest.paragraphs[target_idx]
        start_idx = max(0, target_idx - context_window_paragraphs)
        end_idx = min(len(manifest.paragraphs), target_idx + context_window_paragraphs + 1)

        preceding = [
            {
                "paragraph_id": manifest.paragraphs[i].paragraph_id,
                "page_number": manifest.paragraphs[i].page_number,
                "text": manifest.paragraphs[i].raw_text,
            }
            for i in range(start_idx, target_idx)
        ]
        succeeding = [
            {
                "paragraph_id": manifest.paragraphs[i].paragraph_id,
                "page_number": manifest.paragraphs[i].page_number,
                "text": manifest.paragraphs[i].raw_text,
            }
            for i in range(target_idx + 1, end_idx)
        ]

        full_blocks = []
        for i in range(start_idx, end_idx):
            p = manifest.paragraphs[i]
            marker = " [TARGET]" if i == target_idx else ""
            full_blocks.append(f"[{p.paragraph_id} | Page {p.page_number}{marker}]\n{p.raw_text}")

        first_p = manifest.paragraphs[start_idx]
        last_p = manifest.paragraphs[end_idx - 1]

        return ReconstructedContext(
            target_paragraph_id=target_para.paragraph_id,
            target_page=target_para.page_number,
            target_text=target_para.raw_text,
            preceding_context=preceding,
            succeeding_context=succeeding,
            full_context_text="\n\n".join(full_blocks),
            paragraph_range=(first_p.paragraph_id, last_p.paragraph_id),
            page_span=(first_p.page_number, last_p.page_number),
        )

    def verify_passage(
        self,
        passage_text: str,
        reported_page: Optional[int] = None,
        reported_paragraph: Optional[str] = None,
        pdf_path: Optional[Path] = None,
        manifest: Optional[ExtractionManifest] = None,
        expected_sha256: Optional[str] = None,
        context_window: int = 1,
    ) -> ProvenanceVerificationResult:
        """
        Validates whether a passage exists on the claimed page and document,
        detecting coordinate mismatches, stale files, missing text, and OCR noise.
        """
        # 1. Document Existence Check
        if manifest is None and (pdf_path is None or not pdf_path.exists()):
            return ProvenanceVerificationResult(
                verification_status=STATUS_DOCUMENT_DELETED,
                document_id=pdf_path.name if pdf_path else "UNKNOWN_DOC",
                document_sha256="",
                reported_page=reported_page,
                verified_page=None,
                reported_paragraph=reported_paragraph,
                verified_paragraph=None,
                similarity_score=0.0,
                is_exact_match=False,
                char_offset_in_page=None,
                reconstructed_context=None,
                notes="CRITICAL: Source document does not exist on disk or in storage.",
            )

        # 2. Document Stale / Hash Check
        if pdf_path is not None and pdf_path.exists():
            curr_sha = compute_file_sha256(pdf_path)
            if expected_sha256 and expected_sha256 != curr_sha:
                return ProvenanceVerificationResult(
                    verification_status=STATUS_DOCUMENT_STALE,
                    document_id=pdf_path.name,
                    document_sha256=curr_sha,
                    reported_page=reported_page,
                    verified_page=None,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=None,
                    similarity_score=0.0,
                    is_exact_match=False,
                    char_offset_in_page=None,
                    reconstructed_context=None,
                    notes=f"DOCUMENT_STALE: File SHA-256 ({curr_sha[:10]}...) diverges from expected indexed hash ({expected_sha256[:10]}...).",
                )

        # Resolve Manifest
        if manifest is None:
            manifest = self.get_or_build_manifest(pdf_path)

        doc_id = manifest.document_id
        doc_sha = manifest.document_sha256

        clean_passage = passage_text.strip()
        norm_passage = normalize_text_for_comparison(clean_passage)

        if not norm_passage:
            return ProvenanceVerificationResult(
                verification_status=STATUS_PASSAGE_NOT_FOUND,
                document_id=doc_id,
                document_sha256=doc_sha,
                reported_page=reported_page,
                verified_page=None,
                reported_paragraph=reported_paragraph,
                verified_paragraph=None,
                similarity_score=0.0,
                is_exact_match=False,
                char_offset_in_page=None,
                reconstructed_context=None,
                notes="Passage text is empty or invalid.",
            )

        # 3. Check Reported Page (Exact match)
        if reported_page and 1 <= reported_page <= manifest.total_pages:
            rep_page_obj = manifest.pages[reported_page - 1]
            raw_page_text = rep_page_obj.raw_text

            # Exact verbatim substring search
            exact_pos = raw_page_text.find(clean_passage)
            if exact_pos != -1:
                # Find matching paragraph on that page
                matched_para = None
                for p in rep_page_obj.paragraphs:
                    if clean_passage in p.raw_text or p.raw_text in clean_passage:
                        matched_para = p
                        break
                matched_pid = matched_para.paragraph_id if matched_para else (
                    f"P{reported_page:03d}_PAR001" if rep_page_obj.paragraphs else None
                )

                ctx = self.reconstruct_context(
                    manifest,
                    target_para_id=matched_pid,
                    target_page=reported_page,
                    passage_text=clean_passage,
                    context_window_paragraphs=context_window,
                )

                return ProvenanceVerificationResult(
                    verification_status=STATUS_VERIFIED_EXACT,
                    document_id=doc_id,
                    document_sha256=doc_sha,
                    reported_page=reported_page,
                    verified_page=reported_page,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=matched_pid,
                    similarity_score=1.0,
                    is_exact_match=True,
                    char_offset_in_page=(exact_pos, exact_pos + len(clean_passage)),
                    reconstructed_context=ctx,
                    notes=f"Passage verified verbatim on Page {reported_page}.",
                )

            # Normalized substring search (whitespace/newline normalization)
            norm_pos = rep_page_obj.normalized_text.find(norm_passage)
            if norm_pos != -1:
                matched_para = None
                for p in rep_page_obj.paragraphs:
                    if norm_passage in p.normalized_text:
                        matched_para = p
                        break
                matched_pid = matched_para.paragraph_id if matched_para else None

                ctx = self.reconstruct_context(
                    manifest,
                    target_para_id=matched_pid,
                    target_page=reported_page,
                    passage_text=clean_passage,
                    context_window_paragraphs=context_window,
                )

                return ProvenanceVerificationResult(
                    verification_status=STATUS_VERIFIED_NORMALIZED,
                    document_id=doc_id,
                    document_sha256=doc_sha,
                    reported_page=reported_page,
                    verified_page=reported_page,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=matched_pid,
                    similarity_score=0.99,
                    is_exact_match=False,
                    char_offset_in_page=None,  # Do not falsely claim raw offsets for normalized match
                    reconstructed_context=ctx,
                    notes=f"Passage verified after whitespace/line-wrap normalization on Page {reported_page}.",
                )

            # OCR / Fuzzy Match on Reported Page
            # Check highest ratio against paragraphs on this page
            best_page_sim = 0.0
            best_page_para = None
            for p in rep_page_obj.paragraphs:
                ratio = SequenceMatcher(None, norm_passage, p.normalized_text).ratio()
                if ratio > best_page_sim:
                    best_page_sim = ratio
                    best_page_para = p

            if best_page_sim >= 0.85:
                ctx = self.reconstruct_context(
                    manifest,
                    target_para_id=best_page_para.paragraph_id if best_page_para else None,
                    target_page=reported_page,
                    passage_text=clean_passage,
                    context_window_paragraphs=context_window,
                )
                return ProvenanceVerificationResult(
                    verification_status=STATUS_OCR_UNCERTAINTY,
                    document_id=doc_id,
                    document_sha256=doc_sha,
                    reported_page=reported_page,
                    verified_page=reported_page,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=best_page_para.paragraph_id if best_page_para else None,
                    similarity_score=best_page_sim,
                    is_exact_match=False,
                    char_offset_in_page=None,
                    reconstructed_context=ctx,
                    notes=f"OCR_UNCERTAINTY: Passage matches with {round(best_page_sim*100, 1)}% fuzzy similarity on Page {reported_page} (possible scan or OCR noise).",
                )

        # 4. Check for Coordinate Mismatch across ALL other pages
        for other_page in manifest.pages:
            if reported_page and other_page.page_number == reported_page:
                continue

            # Exact search on other page
            exact_other = other_page.raw_text.find(clean_passage)
            if exact_other != -1:
                ctx = self.reconstruct_context(
                    manifest,
                    target_page=other_page.page_number,
                    passage_text=clean_passage,
                    context_window_paragraphs=context_window,
                )
                return ProvenanceVerificationResult(
                    verification_status=STATUS_COORDINATE_MISMATCH,
                    document_id=doc_id,
                    document_sha256=doc_sha,
                    reported_page=reported_page,
                    verified_page=other_page.page_number,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=ctx.target_paragraph_id if ctx else None,
                    similarity_score=1.0,
                    is_exact_match=True,
                    char_offset_in_page=(exact_other, exact_other + len(clean_passage)),
                    reconstructed_context=ctx,
                    notes=f"COORDINATE_MISMATCH: Passage was claimed on Page {reported_page}, but physically located on Page {other_page.page_number}.",
                )

            # Normalized search on other page
            if norm_passage in other_page.normalized_text:
                ctx = self.reconstruct_context(
                    manifest,
                    target_page=other_page.page_number,
                    passage_text=clean_passage,
                    context_window_paragraphs=context_window,
                )
                return ProvenanceVerificationResult(
                    verification_status=STATUS_COORDINATE_MISMATCH,
                    document_id=doc_id,
                    document_sha256=doc_sha,
                    reported_page=reported_page,
                    verified_page=other_page.page_number,
                    reported_paragraph=reported_paragraph,
                    verified_paragraph=ctx.target_paragraph_id if ctx else None,
                    similarity_score=0.98,
                    is_exact_match=False,
                    char_offset_in_page=None,
                    reconstructed_context=ctx,
                    notes=f"COORDINATE_MISMATCH: Normalized passage was claimed on Page {reported_page}, but found on Page {other_page.page_number}.",
                )

        # 5. Not Found Anywhere
        return ProvenanceVerificationResult(
            verification_status=STATUS_PASSAGE_NOT_FOUND,
            document_id=doc_id,
            document_sha256=doc_sha,
            reported_page=reported_page,
            verified_page=None,
            reported_paragraph=reported_paragraph,
            verified_paragraph=None,
            similarity_score=0.0,
            is_exact_match=False,
            char_offset_in_page=None,
            reconstructed_context=None,
            notes=f"PASSAGE_NOT_FOUND: The queried passage does not exist anywhere within document {doc_id} ({manifest.total_pages} pages inspected).",
        )
