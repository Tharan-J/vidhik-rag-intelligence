"""
Vidhik Phase 2 - Milestone 5
Sub-stages 2.11, 2.12, 2.14: Legal Structure Reconstruction, Provenance Construction, and Final Extraction Manifest.

Creates:
1. Structured JSON for each document: district_extraction/structure/v1/{doc_id}.json
2. Flat paragraph provenance Parquet: district_extraction/structure/v1/paragraphs_provenance_v1.parquet
3. Flat sentence provenance Parquet: district_extraction/structure/v1/sentences_provenance_v1.parquet
4. Master Extraction Manifest JSON: district_extraction/manifests/extraction_manifest_v1.json
5. Master Extraction Manifest Parquet: district_extraction/manifests/extraction_manifest_v1.parquet
6. Milestone 5 structure report: district_extraction/structure/milestone5_structure_report.md
"""

import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Phase2_Milestone5")

ROOT_DIR = Path(__file__).resolve().parent
EXTR_DIR = ROOT_DIR / "district_extraction"
STRUCT_DIR = EXTR_DIR / "structure" / "v1"
STRUCT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR = EXTR_DIR / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

# Common Indian legal abbreviations to protect during sentence splitting
LEGAL_ABBREVIATIONS = [
    r'Mr\.', r'Mrs\.', r'Ms\.', r'Dr\.', r'Hon\'ble', r'Sh\.', r'Smt\.',
    r'v\.', r'vs\.', r'viz\.', r'i\.e\.', r'e\.g\.', r'etc\.',
    r'u/s', r'u/sec\.', r'sec\.', r'secs\.', r'para\.', r'paras\.',
    r'art\.', r'no\.', r'nos\.', r'pvt\.', r'ltd\.', r'co\.', r'corp\.',
    r'cr\.p\.c\.', r'c\.p\.c\.', r'i\.p\.c\.', r'c\.r\.p\.', r'w\.p\.',
    r'anr\.', r'ors\.', r'mohd\.', r'syed\.', r'govt\.', r'dept\.',
    r'adv\.', r'sr\.', r'jr\.', r'spl\.', r'addl\.', r'asst\.', r'st\.'
]


def split_legal_sentences(text: str) -> list[str]:
    """Deterministically segment text into sentences while protecting legal abbreviations, citations, and dates."""
    if not text.strip():
        return []
    
    protected = text
    placeholder_map = {}
    
    # 1. Protect legal abbreviations
    for i, abbr in enumerate(LEGAL_ABBREVIATIONS):
        pat = re.compile(r'\b' + abbr, re.IGNORECASE)
        for m in pat.finditer(protected):
            orig = m.group(0)
            token = f"__ABBR_{i}_{hash(orig) % 100000}__"
            placeholder_map[token] = orig
            protected = protected.replace(orig, token)
            
    # 2. Protect dates (e.g. 15.08.2023 or 1.1.20)
    date_pat = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b')
    for m in date_pat.finditer(protected):
        orig = m.group(0)
        token = f"__DATE_{hash(orig) % 100000}__"
        placeholder_map[token] = orig
        protected = protected.replace(orig, token)

    # 3. Protect case citations (e.g. No. 12/2021)
    cite_pat = re.compile(r'\b\d+/\d+\b')
    for m in cite_pat.finditer(protected):
        orig = m.group(0)
        token = f"__CITE_{hash(orig) % 100000}__"
        placeholder_map[token] = orig
        protected = protected.replace(orig, token)

    # Split on sentence boundaries: (. ! ?) followed by whitespace or quote
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        # Restore placeholders
        for token, orig in placeholder_map.items():
            s = s.replace(token, orig)
        sentences.append(s)
        
    return sentences if sentences else [text.strip()]


def parse_normalized_pages(text: str) -> list[dict]:
    """Parse text formatted with '--- PAGE {n} ---' markers into structured pages."""
    page_chunks = re.split(r'---\s*PAGE\s+(\d+)\s*---', text)
    pages = []
    
    if len(page_chunks) >= 3:
        for i in range(1, len(page_chunks), 2):
            page_num = int(page_chunks[i])
            content = page_chunks[i+1].strip()
            pages.append({"page_number": page_num, "text": content})
    else:
        # Fallback if marker is missing
        pages.append({"page_number": 1, "text": text.strip()})
        
    return pages


def run_milestone5():
    logger.info("Starting Vidhik Phase 2 - Milestone 5 (Structure, Provenance, & Final Manifest)...")
    start_time = time.time()
    
    # Load upstream manifests
    src_manifest = pd.read_parquet(EXTR_DIR / "source_manifest" / "district_source_manifest_v1.parquet")
    routing_df = pd.read_parquet(EXTR_DIR / "diagnostics" / "routing_decisions_v1.parquet")
    selection_df = pd.read_parquet(EXTR_DIR / "diagnostics" / "extraction_selection_v1.parquet")
    raw_pages_df = pd.read_parquet(EXTR_DIR / "raw_extraction" / "final_raw_pages_v1.parquet")
    preservation_df = pd.read_parquet(EXTR_DIR / "validation" / "legal_entity_preservation.parquet")

    # Map lookups
    src_map = src_manifest.set_index("document_id").to_dict(orient="index")
    routing_map = routing_df.set_index("document_id").to_dict(orient="index")
    selection_map = selection_df.set_index("document_id").to_dict(orient="index")
    preservation_map = preservation_df.set_index("document_id").to_dict(orient="index")

    # Group raw pages by document_id
    raw_pages_grouped = {}
    for doc_id, group in raw_pages_df.groupby("document_id"):
        raw_pages_grouped[doc_id] = group.sort_values("page_number").to_dict(orient="records")

    doc_ids = sorted(src_map.keys())
    total_docs = len(doc_ids)
    logger.info("Processing structure and provenance for %d documents...", total_docs)

    all_paragraph_records = []
    all_sentence_records = []
    manifest_doc_summaries = []

    total_corpus_paragraphs = 0
    total_corpus_sentences = 0
    total_corpus_words = 0

    for doc_id in doc_ids:
        src_info = src_map[doc_id]
        route_info = routing_map[doc_id]
        sel_info = selection_map[doc_id]
        pres_info = preservation_map[doc_id]
        raw_pages = raw_pages_grouped.get(doc_id, [])

        # Read normalized text
        norm_file = EXTR_DIR / "normalized" / "v1" / f"{doc_id}.txt"
        with open(norm_file, "r", encoding="utf-8") as f:
            norm_content = f.read()

        norm_pages_data = parse_normalized_pages(norm_content)

        # Match normalized pages to raw pages
        page_structures = []
        doc_paragraphs = []
        doc_sentences = []

        for p_idx, page_dict in enumerate(norm_pages_data):
            page_num = page_dict["page_number"]
            page_text = page_dict["text"]

            # Paragraph splitting on double newlines
            raw_pars = [p.strip() for p in re.split(r'\n\s*\n', page_text) if p.strip()]
            
            page_par_objs = []
            for par_idx, par_text in enumerate(raw_pars, start=1):
                par_id = f"{doc_id}_P{page_num:03d}_PAR{par_idx:03d}"
                sentences = split_legal_sentences(par_text)
                
                sen_objs = []
                for sen_idx, sen_text in enumerate(sentences, start=1):
                    sen_id = f"{par_id}_SEN{sen_idx:03d}"
                    sen_words = len(sen_text.split())
                    sen_chars = len(sen_text)
                    
                    sen_obj = {
                        "sentence_id": sen_id,
                        "sentence_index": sen_idx,
                        "character_count": sen_chars,
                        "word_count": sen_words,
                        "text": sen_text
                    }
                    sen_objs.append(sen_obj)
                    
                    all_sentence_records.append({
                        "document_id": doc_id,
                        "source_sha256": src_info["sha256"],
                        "page_number": page_num,
                        "paragraph_id": par_id,
                        "sentence_id": sen_id,
                        "sentence_index": sen_idx,
                        "sentence_text": sen_text,
                        "character_count": sen_chars,
                        "word_count": sen_words,
                        "extraction_method": sel_info["selected_method"]
                    })
                    doc_sentences.append(sen_obj)

                par_words = len(par_text.split())
                par_chars = len(par_text)

                par_obj = {
                    "paragraph_id": par_id,
                    "paragraph_index": par_idx,
                    "character_count": par_chars,
                    "word_count": par_words,
                    "sentence_count": len(sen_objs),
                    "text": par_text,
                    "sentences": sen_objs
                }
                page_par_objs.append(par_obj)
                doc_paragraphs.append(par_obj)

                all_paragraph_records.append({
                    "document_id": doc_id,
                    "source_sha256": src_info["sha256"],
                    "page_number": page_num,
                    "paragraph_id": par_id,
                    "paragraph_index": par_idx,
                    "paragraph_text": par_text,
                    "character_count": par_chars,
                    "word_count": par_words,
                    "sentence_count": len(sen_objs),
                    "extraction_method": sel_info["selected_method"],
                    "quality_tier": sel_info["final_quality_status"]
                })

            page_structures.append({
                "page_number": page_num,
                "character_count": len(page_text),
                "word_count": len(page_text.split()),
                "paragraph_count": len(page_par_objs),
                "paragraphs": page_par_objs
            })

        total_corpus_paragraphs += len(doc_paragraphs)
        total_corpus_sentences += len(doc_sentences)
        total_corpus_words += sum(p["word_count"] for p in page_structures)

        # Build raw pages representation
        formatted_raw_pages = []
        for rp in raw_pages:
            formatted_raw_pages.append({
                "page_number": int(rp["page_number"]),
                "character_count": int(rp["character_count"]),
                "word_count": int(rp["word_count"]),
                "raw_text": rp["raw_page_text"]
            })

        # Build normalized pages representation
        formatted_norm_pages = []
        for p in page_structures:
            formatted_norm_pages.append({
                "page_number": p["page_number"],
                "character_count": p["character_count"],
                "word_count": p["word_count"],
                "normalized_text": next(item["text"] for item in norm_pages_data if item["page_number"] == p["page_number"])
            })

        # Available metadata (strictly what was present in the corpus or PDF, never inferred)
        available_metadata = {
            "state_code": src_info.get("state_code"),
            "state_name": src_info.get("state_name"),
            "district_code": src_info.get("district_code"),
            "district_name": src_info.get("district_name"),
            "court_complex_code": src_info.get("court_complex_code"),
            "court_complex_name": src_info.get("court_complex_name"),
            "year": src_info.get("year"),
            "case_type": src_info.get("case_type"),
            "case_number": src_info.get("case_number"),
            "pdf_title": src_info.get("pdf_title"),
            "pdf_author": src_info.get("pdf_author"),
            "pdf_creator": src_info.get("pdf_creator"),
            "pdf_producer": src_info.get("pdf_producer"),
            "pdf_creation_date": src_info.get("pdf_creation_date"),
            "pdf_mod_date": src_info.get("pdf_mod_date")
        }
        # Clean None values
        available_metadata = {k: v for k, v in available_metadata.items() if v is not None and not (isinstance(v, float) and pd.isna(v))}

        # Quality anomaly flags
        anomaly_flags = []
        flags_str = pres_info.get("preservation_flags", "")
        if flags_str:
            anomaly_flags = flags_str.split(";")

        # Construct Full Document JSON Object (Section 19 Schema)
        doc_json = {
            "document_id": doc_id,
            "source": {
                "sha256": src_info["sha256"],
                "filename": src_info["source_filename"],
                "source_record_id": src_info.get("source_record_id"),
                "source_archive": src_info.get("source_archive"),
                "page_count": int(src_info["page_count"]),
                "file_size_bytes": int(src_info["file_size_bytes"])
            },
            "routing": {
                "initial_route": route_info["initial_route"],
                "fallback_used": bool(sel_info["fallback_used"]),
                "route_reason": route_info["route_reason"]
            },
            "extraction": {
                "selected_method": sel_info["selected_method"],
                "extractor_name": "RapidOCR-PP-OCRv4" if sel_info["selected_method"] == "paddleocr" else ("PyMuPDF-Tesseract" if sel_info["selected_method"] == "tesseract" else "PyMuPDF-Native"),
                "extractor_version": "1.0.0",
                "quality_score": float(sel_info["selected_quality_score"])
            },
            "raw_pages": formatted_raw_pages,
            "normalized_pages": formatted_norm_pages,
            "structure": {
                "total_paragraphs": len(doc_paragraphs),
                "total_sentences": len(doc_sentences),
                "pages": page_structures
            },
            "metadata": available_metadata,
            "language": {
                "detected_script": sel_info["detected_script"],
                "confidence": float(sel_info["script_confidence"])
            },
            "quality": {
                "extraction_quality": float(sel_info["selected_quality_score"]),
                "quality_tier": sel_info["final_quality_status"],
                "anomaly_flags": anomaly_flags,
                "all_entities_preserved": bool(pres_info["all_entities_preserved"])
            },
            "provenance": {
                "source_sha256": src_info["sha256"],
                "extraction_version": "1.0.0",
                "normalization_version": "1.0.0",
                "structure_version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        }

        # Write individual document structured JSON
        doc_json_path = STRUCT_DIR / f"{doc_id}.json"
        with open(doc_json_path, "w", encoding="utf-8") as f:
            json.dump(doc_json, f, indent=2, ensure_ascii=False)

        # Summary for Master Manifest
        manifest_doc_summaries.append({
            "document_id": doc_id,
            "source_sha256": src_info["sha256"],
            "page_count": int(src_info["page_count"]),
            "initial_route": route_info["initial_route"],
            "fallback_used": bool(sel_info["fallback_used"]),
            "selected_method": sel_info["selected_method"],
            "quality_tier": sel_info["final_quality_status"],
            "quality_score": float(sel_info["selected_quality_score"]),
            "detected_script": sel_info["detected_script"],
            "total_paragraphs": len(doc_paragraphs),
            "total_sentences": len(doc_sentences),
            "word_count": sum(p["word_count"] for p in page_structures),
            "structured_json_path": str(doc_json_path.relative_to(ROOT_DIR))
        })

    # Save flat Parquet tables
    paragraphs_df = pd.DataFrame(all_paragraph_records)
    paragraphs_df.to_parquet(STRUCT_DIR / "paragraphs_provenance_v1.parquet", index=False)
    
    sentences_df = pd.DataFrame(all_sentence_records)
    sentences_df.to_parquet(STRUCT_DIR / "sentences_provenance_v1.parquet", index=False)

    # Master Manifest Construction
    manifest_df = pd.DataFrame(manifest_doc_summaries)
    manifest_df.to_parquet(MANIFEST_DIR / "extraction_manifest_v1.parquet", index=False)

    source_manifest_bytes = (EXTR_DIR / "source_manifest" / "district_source_manifest_v1.parquet").read_bytes()
    source_manifest_hash = hashlib.sha256(source_manifest_bytes).hexdigest()

    master_manifest_json = {
        "pipeline_name": "Vidhik Legal Document Extraction Pipeline",
        "pipeline_version": "1.0.0",
        "phase": "Phase 2 - Legal Document Extraction",
        "generation_timestamp": datetime.now().isoformat(),
        "frozen_corpus_name": "District Court Experimental Corpus (s3_161)",
        "source_manifest_sha256": source_manifest_hash,
        "corpus_statistics": {
            "total_documents": total_docs,
            "total_pages": int(src_manifest["page_count"].sum()),
            "total_paragraphs": total_corpus_paragraphs,
            "total_sentences": total_corpus_sentences,
            "total_words": total_corpus_words,
            "mean_paragraphs_per_doc": round(total_corpus_paragraphs / total_docs, 2),
            "mean_sentences_per_par": round(total_corpus_sentences / total_corpus_paragraphs, 2) if total_corpus_paragraphs else 0,
        },
        "routing_breakdown": routing_df["initial_route"].value_counts().to_dict(),
        "selected_method_breakdown": selection_df["selected_method"].value_counts().to_dict(),
        "quality_tier_breakdown": selection_df["final_quality_status"].value_counts().to_dict(),
        "documents": manifest_doc_summaries
    }

    with open(MANIFEST_DIR / "extraction_manifest_v1.json", "w", encoding="utf-8") as f:
        json.dump(master_manifest_json, f, indent=2, ensure_ascii=False)

    def df_to_md(df, headers):
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join([":---" if i == 0 else "---:" for i in range(len(headers))]) + " |"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
        return "\n".join(lines)

    method_counts_df = pd.DataFrame(list(selection_df['selected_method'].value_counts().items()), columns=['Method', 'Count'])
    tier_counts_df = pd.DataFrame(list(selection_df['final_quality_status'].value_counts().items()), columns=['Quality Tier', 'Count'])

    report_md = f"""# Vidhik Phase 2 - Milestone 5 Legal Structure & Provenance Report

**Execution Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Documents Processed:** {total_docs}  
**Pipeline Version:** 1.0.0  

---

## 1. Corpus Structure & Provenance Statistics

| Metric | Total Count | Mean per Document |
| :--- | ---: | ---: |
| **Documents** | {total_docs} | 1.0 |
| **Pages** | {int(src_manifest['page_count'].sum())} | {round(src_manifest['page_count'].mean(), 2)} |
| **Paragraphs** | {total_corpus_paragraphs:,} | {round(total_corpus_paragraphs / total_docs, 2)} |
| **Sentences** | {total_corpus_sentences:,} | {round(total_corpus_sentences / total_docs, 2)} |
| **Words** | {total_corpus_words:,} | {round(total_corpus_words / total_docs, 2)} |

---

## 2. Provenance Architecture (Traceability Chain)

Every paragraph and sentence in the dataset maintains an unbroken, deterministic provenance link:
```text
Summary Statement (Phase 4 / 5)
      ↓
Retrieved Evidence Chunk (Phase 3)
      ↓
Sentence ID:       {{document_id}}_P{{page:03d}}_PAR{{par:03d}}_SEN{{sen:03d}}
      ↓
Paragraph ID:      {{document_id}}_P{{page:03d}}_PAR{{par:03d}}
      ↓
Page Number:       {{page_number}} (1-indexed)
      ↓
Document ID:       {{document_id}}
      ↓
Source SHA-256:    Bit-exact immutable PDF hash
```

All 161 structured JSON files are stored in:
`district_extraction/structure/v1/{{document_id}}.json`

High-speed columnar provenance lookup tables:
- Paragraphs: `district_extraction/structure/v1/paragraphs_provenance_v1.parquet` ({len(paragraphs_df):,} rows)
- Sentences: `district_extraction/structure/v1/sentences_provenance_v1.parquet` ({len(sentences_df):,} rows)

---

## 3. Final Master Manifest

- JSON Manifest: `district_extraction/manifests/extraction_manifest_v1.json`
- Parquet Manifest: `district_extraction/manifests/extraction_manifest_v1.parquet`
- Source Manifest Hash: `{source_manifest_hash}`

### Method Breakdown
{df_to_md(method_counts_df, ['Method', 'Count'])}

### Final Quality Tier Breakdown
{df_to_md(tier_counts_df, ['Quality Tier', 'Count'])}

---
*Generated by Vidhik Phase 2 Structure & Provenance Engine.*
"""
    with open(EXTR_DIR / "structure" / "milestone5_structure_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    duration = time.time() - start_time
    logger.info("Milestone 5 completed in %.2f seconds.", duration)
    logger.info("Generated %d paragraphs and %d sentences across %d documents.", total_corpus_paragraphs, total_corpus_sentences, total_docs)


if __name__ == "__main__":
    run_milestone5()
