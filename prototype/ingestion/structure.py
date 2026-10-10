"""
Legal Document Structure Reconstruction Subsystem
==================================================
Builds hierarchical, provenance-linked structures:
Document -> Page -> Paragraph -> Sentence
Protects all legal citations, statutory sections, dates, and docket identifiers.
"""

import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .normalize import normalize_legal_text

logger = logging.getLogger("VidhikIngestion.Structure")

# Indian legal abbreviations that must NOT trigger sentence breaks
LEGAL_ABBREVIATIONS = [
    r"Mr\.", r"Mrs\.", r"Ms\.", r"Dr\.", r"Hon\'ble", r"Honble\.", r"Sh\.", r"Smt\.",
    r"v\.", r"vs\.", r"viz\.", r"i\.e\.", r"e\.g\.", r"etc\.", r"al\.",
    r"u/s", r"u/sec\.", r"sec\.", r"secs\.", r"para\.", r"paras\.",
    r"art\.", r"no\.", r"nos\.", r"pvt\.", r"ltd\.", r"co\.", r"corp\.",
    r"cr\.p\.c\.", r"c\.p\.c\.", r"i\.p\.c\.", r"c\.r\.p\.", r"w\.p\.",
    r"anr\.", r"ors\.", r"mohd\.", r"syed\.", r"govt\.", r"dept\.",
    r"adv\.", r"sr\.", r"jr\.", r"spl\.", r"addl\.", r"asst\.", r"st\.",
    r"scr", r"scc", r"air", r"manu", r"scale", r"itr", r"ilr"
]

_SPACY_NLP = None


def get_spacy_nlp():
    """Lazily load spaCy model if available."""
    global _SPACY_NLP
    if _SPACY_NLP is None:
        try:
            import spacy
            try:
                _SPACY_NLP = spacy.load("en_core_web_sm", disable=["ner", "tagger"])
            except Exception:
                _SPACY_NLP = spacy.blank("en")
                _SPACY_NLP.add_pipe("sentencizer")
        except ImportError:
            _SPACY_NLP = False
    return _SPACY_NLP if _SPACY_NLP is not False else None


def split_legal_sentences(text: str) -> List[str]:
    """
    Deterministically segment text into sentences while protecting
    legal abbreviations, section codes, citations, and dates.
    """
    if not text.strip():
        return []

    protected = text
    placeholder_map = {}

    # 1. Protect legal abbreviations
    for i, abbr in enumerate(LEGAL_ABBREVIATIONS):
        pat = re.compile(r"\b" + abbr, re.IGNORECASE)
        for m in list(pat.finditer(protected)):
            orig = m.group(0)
            token = f"__ABBR_{i}_{abs(hash(orig)) % 1000000}__"
            placeholder_map[token] = orig
            protected = protected.replace(orig, token)

    # 2. Protect dates (e.g. 15.08.2023 or 1.1.20)
    date_pat = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")
    for m in list(date_pat.finditer(protected)):
        orig = m.group(0)
        token = f"__DATE_{abs(hash(orig)) % 1000000}__"
        placeholder_map[token] = orig
        protected = protected.replace(orig, token)

    # 3. Protect docket citations with slashes (e.g. No. 12/2021)
    cite_pat = re.compile(r"\b\d+/\d+\b")
    for m in list(cite_pat.finditer(protected)):
        orig = m.group(0)
        token = f"__CITE_{abs(hash(orig)) % 1000000}__"
        placeholder_map[token] = orig
        protected = protected.replace(orig, token)

    # Try spaCy if installed
    nlp = get_spacy_nlp()
    if nlp is not None:
        try:
            doc = nlp(protected)
            raw_sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        except Exception:
            raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", protected) if s.strip()]
    else:
        # Fallback to deterministic regex segmentation on sentence boundary [.!?]
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", protected) if s.strip()]

    # Restore placeholders
    sentences = []
    for s in raw_sentences:
        if not s:
            continue
        for token, orig in placeholder_map.items():
            s = s.replace(token, orig)
        sentences.append(s)

    return sentences if sentences else [text.strip()]


@dataclass
class SentenceUnit:
    sentence_id: str
    sentence_index: int
    paragraph_id: str
    page_number: int
    document_id: str
    text: str
    word_count: int
    char_count: int


@dataclass
class ParagraphUnit:
    paragraph_id: str
    paragraph_index: int
    page_number: int
    document_id: str
    text: str
    word_count: int
    sentences: List[SentenceUnit] = field(default_factory=list)


@dataclass
class PageUnit:
    page_number: int
    extraction_method: str
    text: str
    paragraphs: List[ParagraphUnit] = field(default_factory=list)


@dataclass
class DocumentStructure:
    document_id: str
    source_file: str
    document_sha256: str
    metadata: Dict[str, Any]
    pages: List[PageUnit]
    paragraphs: List[ParagraphUnit]
    sentences: List[SentenceUnit]


def build_document_structure(
    document_id: str,
    pages_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    source_file: str,
    document_sha256: str,
    pre_extracted_json: Optional[Path] = None
) -> DocumentStructure:
    """
    Construct full Page -> Paragraph -> Sentence hierarchy with exact provenance links.
    Reuses existing verified JSON if available.
    """
    # 1. Reuse existing verified JSON structure if available
    if pre_extracted_json and pre_extracted_json.exists():
        try:
            with open(pre_extracted_json, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if "structure" in cached and "pages" in cached["structure"] and cached["structure"]["pages"]:
                doc_pages = []
                doc_paragraphs = []
                doc_sentences = []

                for p_idx, p_data in enumerate(cached["structure"]["pages"]):
                    p_num = p_data.get("page_number", p_idx + 1)
                    page_unit = PageUnit(
                        page_number=p_num,
                        extraction_method=p_data.get("extraction_method", "cached_verified"),
                        text=""
                    )
                    page_pars = []
                    for par_idx, par_data in enumerate(p_data.get("paragraphs", []), start=1):
                        par_id = par_data.get("paragraph_id", f"{document_id}_P{p_num:03d}_PAR{par_idx:03d}")
                        par_text = normalize_legal_text(par_data.get("text", ""))
                        par_unit = ParagraphUnit(
                            paragraph_id=par_id,
                            paragraph_index=par_idx,
                            page_number=p_num,
                            document_id=document_id,
                            text=par_text,
                            word_count=len(par_text.split()),
                        )
                        for sen_idx, sen_data in enumerate(par_data.get("sentences", []), start=1):
                            sen_id = sen_data.get("sentence_id", f"{par_id}_SEN{sen_idx:03d}")
                            sen_text = sen_data.get("text", "")
                            sen_unit = SentenceUnit(
                                sentence_id=sen_id,
                                sentence_index=sen_idx,
                                paragraph_id=par_id,
                                page_number=p_num,
                                document_id=document_id,
                                text=sen_text,
                                word_count=len(sen_text.split()),
                                char_count=len(sen_text),
                            )
                            par_unit.sentences.append(sen_unit)
                            doc_sentences.append(sen_unit)

                        page_pars.append(par_unit)
                        doc_paragraphs.append(par_unit)

                    page_unit.paragraphs = page_pars
                    page_unit.text = "\n\n".join([p.text for p in page_pars])
                    doc_pages.append(page_unit)

                if doc_pages:
                    return DocumentStructure(
                        document_id=document_id,
                        source_file=source_file,
                        document_sha256=document_sha256,
                        metadata=metadata,
                        pages=doc_pages,
                        paragraphs=doc_paragraphs,
                        sentences=doc_sentences,
                    )
        except Exception as e:
            logger.warning(f"Error loading structure from {pre_extracted_json}: {e}; computing afresh.")

    # 2. Compute structure from extracted pages
    doc_pages = []
    doc_paragraphs = []
    doc_sentences = []

    for page_dict in pages_data:
        p_num = page_dict["page_number"]
        method = page_dict.get("extraction_method", "native")
        raw_text = page_dict.get("text", "")
        norm_page_text = normalize_legal_text(raw_text)

        page_unit = PageUnit(
            page_number=p_num,
            extraction_method=method,
            text=norm_page_text
        )

        # Paragraph split on double newlines
        raw_pars = [p.strip() for p in re.split(r"\n\s*\n", norm_page_text) if p.strip()]
        page_pars = []

        for par_idx, par_text in enumerate(raw_pars, start=1):
            par_id = f"{document_id}_P{p_num:03d}_PAR{par_idx:03d}"
            par_unit = ParagraphUnit(
                paragraph_id=par_id,
                paragraph_index=par_idx,
                page_number=p_num,
                document_id=document_id,
                text=par_text,
                word_count=len(par_text.split()),
            )

            # Segment into sentences
            sentences = split_legal_sentences(par_text)
            for sen_idx, sen_text in enumerate(sentences, start=1):
                sen_id = f"{par_id}_SEN{sen_idx:03d}"
                sen_unit = SentenceUnit(
                    sentence_id=sen_id,
                    sentence_index=sen_idx,
                    paragraph_id=par_id,
                    page_number=p_num,
                    document_id=document_id,
                    text=sen_text,
                    word_count=len(sen_text.split()),
                    char_count=len(sen_text),
                )
                par_unit.sentences.append(sen_unit)
                doc_sentences.append(sen_unit)

            page_pars.append(par_unit)
            doc_paragraphs.append(par_unit)

        page_unit.paragraphs = page_pars
        doc_pages.append(page_unit)

    return DocumentStructure(
        document_id=document_id,
        source_file=source_file,
        document_sha256=document_sha256,
        metadata=metadata,
        pages=doc_pages,
        paragraphs=doc_paragraphs,
        sentences=doc_sentences,
    )
