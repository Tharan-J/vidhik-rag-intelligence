"""
Structure-Aware Legal Document Chunking Subsystem
=================================================
Target: ~500 tokens (Min: ~250, Max: ~700, Overlap: ~75 tokens)
Adheres strictly to the structural hierarchy: Paragraph -> Sentence -> Token count.
Never splits through the middle of a sentence.
Preserves complete provenance back to sentences, paragraphs, pages, document, and source PDF.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from .structure import DocumentStructure, SentenceUnit

logger = logging.getLogger("VidhikIngestion.Chunk")

_TOKENIZER = None


def get_tokenizer(model_dir: Optional[Path] = None):
    """Lazily load BGE-M3 tokenizer or fallback to whitespace word tokenizer."""
    global _TOKENIZER
    if _TOKENIZER is None:
        try:
            from tokenizers import Tokenizer
            if model_dir is not None:
                tok_file = model_dir / "tokenizer.json"
                if tok_file.exists():
                    _TOKENIZER = Tokenizer.from_file(str(tok_file))
                    return _TOKENIZER
            # Try default repo path
            default_path = Path(__file__).resolve().parent.parent.parent / "research" / "rag_experiments" / "indexes" / "models" / "bge-m3" / "tokenizer.json"
            if default_path.exists():
                _TOKENIZER = Tokenizer.from_file(str(default_path))
                return _TOKENIZER
        except Exception as e:
            logger.debug(f"BGE-M3 tokenizer not loaded from file: {e}")

        # Fallback pseudo-tokenizer
        class WordTokenizer:
            def encode(self, text: str):
                class Enc:
                    ids = [0] * max(1, int(len(text.split()) * 1.3))
                return Enc()
        _TOKENIZER = WordTokenizer()

    return _TOKENIZER


def count_tokens(text: str, tokenizer: Any) -> int:
    """Return token count using loaded tokenizer."""
    if not text:
        return 0
    try:
        encoded = tokenizer.encode(text)
        return len(encoded.ids)
    except Exception:
        return max(1, int(len(text.split()) * 1.3))


@dataclass
class LegalChunk:
    document_id: str
    chunk_id: str
    court_level: Optional[str]
    court: Optional[str]
    case_title: Optional[str]
    case_number: Optional[str]
    decision_date: Optional[str]
    year: Optional[int]
    language: str
    text: str
    page_start: int
    page_end: int
    paragraph_start: str
    paragraph_end: str
    sentence_start: str
    sentence_end: str
    source_file: str
    document_sha256: str
    token_count: int
    sentence_ids: List[str] = field(default_factory=list)
    paragraph_ids: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        """Convert chunk into Qdrant-ready payload format."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "court_level": self.court_level,
            "court": self.court,
            "case_title": self.case_title,
            "case_number": self.case_number,
            "decision_date": self.decision_date,
            "year": self.year,
            "language": self.language,
            "text": self.text,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "paragraph_start": self.paragraph_start,
            "paragraph_end": self.paragraph_end,
            "sentence_start": self.sentence_start,
            "sentence_end": self.sentence_end,
            "source_file": self.source_file,
            "document_sha256": self.document_sha256,
            "token_count": self.token_count,
            "sentence_ids": self.sentence_ids,
            "paragraph_ids": self.paragraph_ids,
        }


def chunk_document(
    doc_struct: DocumentStructure,
    target_tokens: int = 500,
    min_tokens: int = 250,
    max_tokens: int = 700,
    overlap_tokens: int = 75,
    tokenizer_dir: Optional[Path] = None,
) -> List[LegalChunk]:
    """
    Perform structure-aware chunking on a DocumentStructure object.
    
    Groups consecutive sentences respecting paragraph coherence:
    - Builds chunks aiming for target_tokens (~500)
    - Upper bound clamped at max_tokens (~700)
    - If final chunk is below min_tokens, merges into previous chunk if within max_tokens
    - Overlap: retains trailing sentences totaling ~75 tokens into next chunk
    """
    all_sentences = doc_struct.sentences
    if not all_sentences:
        # Edge case: No sentences extracted (empty document)
        return []

    tok = get_tokenizer(tokenizer_dir)
    chunks = []
    
    current_sentences: List[SentenceUnit] = []
    current_tokens = 0
    chunk_index = 1

    def make_chunk_obj(sents: List[SentenceUnit], c_idx: int) -> LegalChunk:
        c_text = " ".join([s.text for s in sents])
        tok_cnt = count_tokens(c_text, tok)
        p_ids = list(dict.fromkeys([s.paragraph_id for s in sents]))
        s_ids = [s.sentence_id for s in sents]
        
        meta = doc_struct.metadata
        return LegalChunk(
            document_id=doc_struct.document_id,
            chunk_id=f"chunk_{c_idx:04d}",
            court_level=meta.get("court_level"),
            court=meta.get("court") or meta.get("court_name"),
            case_title=meta.get("case_title") or meta.get("title"),
            case_number=meta.get("case_number") or meta.get("case_id"),
            decision_date=str(meta.get("decision_date")) if meta.get("decision_date") is not None else None,
            year=int(meta.get("year") or meta.get("decision_year")) if meta.get("year") or meta.get("decision_year") else None,
            language=meta.get("language", "en"),
            text=c_text,
            page_start=sents[0].page_number,
            page_end=sents[-1].page_number,
            paragraph_start=sents[0].paragraph_id,
            paragraph_end=sents[-1].paragraph_id,
            sentence_start=sents[0].sentence_id,
            sentence_end=sents[-1].sentence_id,
            source_file=doc_struct.source_file,
            document_sha256=doc_struct.document_sha256,
            token_count=tok_cnt,
            sentence_ids=s_ids,
            paragraph_ids=p_ids,
        )

    i = 0
    n = len(all_sentences)

    while i < n:
        sent = all_sentences[i]
        s_tokens = count_tokens(sent.text, tok)

        # If adding this sentence exceeds max_tokens and we already have enough tokens:
        if current_sentences and (current_tokens + s_tokens > max_tokens) and (current_tokens >= min_tokens):
            # Emit current chunk
            chunk_obj = make_chunk_obj(current_sentences, chunk_index)
            chunks.append(chunk_obj)
            chunk_index += 1

            # Compute overlap sentences (up to overlap_tokens from the end)
            overlap_sents = []
            overlap_accum = 0
            for back_s in reversed(current_sentences):
                st = count_tokens(back_s.text, tok)
                if overlap_accum + st <= overlap_tokens or not overlap_sents:
                    overlap_sents.insert(0, back_s)
                    overlap_accum += st
                else:
                    break

            current_sentences = list(overlap_sents)
            current_tokens = overlap_accum

        # Add current sentence
        current_sentences.append(sent)
        current_tokens += s_tokens
        i += 1

        # If reached target_tokens and at a paragraph boundary, create chunk early
        if current_tokens >= target_tokens and current_tokens <= max_tokens:
            # Check if next sentence is in a different paragraph or EOF
            is_par_boundary = (i == n) or (all_sentences[i].paragraph_id != sent.paragraph_id)
            if is_par_boundary:
                chunk_obj = make_chunk_obj(current_sentences, chunk_index)
                chunks.append(chunk_obj)
                chunk_index += 1

                # Overlap
                overlap_sents = []
                overlap_accum = 0
                for back_s in reversed(current_sentences):
                    st = count_tokens(back_s.text, tok)
                    if overlap_accum + st <= overlap_tokens or not overlap_sents:
                        overlap_sents.insert(0, back_s)
                        overlap_accum += st
                    else:
                        break
                current_sentences = list(overlap_sents)
                current_tokens = overlap_accum

    # Flush remaining sentences
    if current_sentences:
        # If very small and previous chunk exists, merge if total <= max_tokens
        if chunks and current_tokens < min_tokens:
            prev_chunk = chunks[-1]
            merged_sents = [s for s in all_sentences if s.sentence_id in prev_chunk.sentence_ids]
            for s in current_sentences:
                if s.sentence_id not in prev_chunk.sentence_ids:
                    merged_sents.append(s)
            merged_tok = count_tokens(" ".join([s.text for s in merged_sents]), tok)
            if merged_tok <= max_tokens:
                chunks[-1] = make_chunk_obj(merged_sents, len(chunks))
            else:
                chunks.append(make_chunk_obj(current_sentences, chunk_index))
        else:
            chunks.append(make_chunk_obj(current_sentences, chunk_index))

    return chunks
