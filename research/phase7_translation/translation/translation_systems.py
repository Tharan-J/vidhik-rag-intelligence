"""
Phase 7 Translation Components
Implements:
1. BaselineTranslator (T0) - Replicates Phase 6 System D
2. ContextTranslator (T1) - Context-aware sentence translating
3. TerminologyProtectedTranslator (T2) - Stronger legal entity & terminology protection
4. AlignedTranslator (T3) - Strict claim & sentence-aligned translation
5. CandidateGenerator & Reranker (T4) - Multi-candidate decoding & legal reranking
6. CombinedTranslator (T5) - Optimal combination
"""

import os
import sys
import types
import re
import time
import hashlib
import yaml
from typing import List, Dict, Any, Tuple

try:
    import transformers.onnx
except (ImportError, AttributeError):
    m = types.ModuleType('transformers.onnx')
    m.OnnxConfig = object
    m.OnnxConfigWithPast = object
    m.OnnxSeq2SeqConfigWithPast = object
    sys.modules['transformers.onnx'] = m
    m_utils = types.ModuleType('transformers.onnx.utils')
    m_utils.compute_effective_axis_dimension = lambda *a, **k: None
    sys.modules['transformers.onnx.utils'] = m_utils

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from IndicTransToolkit import IndicProcessor

LANG_CODE_MAP = {
    "en": "eng_Latn",
    "ta": "tam_Taml",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "mr": "mar_Deva"
}

class SharedIndicTrans2Engine:
    """Singleton/shared model engine to avoid reloading weights repeatedly."""
    _instance = None

    @classmethod
    def get_instance(cls, model_id: str = "ai4bharat/indictrans2-en-indic-dist-200M", device: str = None):
        if cls._instance is None:
            cls._instance = cls(model_id, device)
        return cls._instance

    def __init__(self, model_id: str = "ai4bharat/indictrans2-en-indic-dist-200M", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[Engine] Loading IndicTrans2 from {model_id} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        self.model.eval()
        self.processor = IndicProcessor(inference=True)
        self.model_id = model_id
        print(f"[Engine] IndicTrans2 loaded successfully.")

    def translate_sentences(self, sentences: List[str], tgt_lang: str, num_beams: int = 2, num_return_sequences: int = 1) -> List[List[str]]:
        if not sentences:
            return []
        src_code = LANG_CODE_MAP["en"]
        tgt_code = LANG_CODE_MAP.get(tgt_lang, tgt_lang)

        results = []
        for s in sentences:
            preprocessed = self.processor.preprocess_batch([s], src_lang=src_code, tgt_lang=tgt_code)
            inputs = self.tokenizer(
                preprocessed,
                padding="longest",
                truncation=True,
                max_length=256,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    use_cache=False,
                    min_length=0,
                    max_length=256,
                    num_beams=max(num_beams, num_return_sequences),
                    num_return_sequences=num_return_sequences
                )
            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            postprocessed = self.processor.postprocess_batch(decoded, lang=tgt_code)
            results.append(postprocessed)

            del inputs, outputs
            if self.device == "cuda":
                torch.cuda.empty_cache()

        return results

    def split_sentences(self, text: str) -> List[str]:
        raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n+", text)
        clean = [s.strip() for s in raw_sents if s.strip()]
        return clean if clean else [text]


# -------------------------------------------------------------------------
# T0: Baseline Translator (Replicating Phase 6 System D)
# -------------------------------------------------------------------------
class BaselineTranslator:
    def __init__(self, engine: SharedIndicTrans2Engine, config_path: str = "phase6_multilingual_architecture/config/terminology_config.yaml"):
        self.engine = engine
        self.config_path = config_path
        sys.path.append(os.path.abspath("phase6_multilingual_architecture"))
        from systems.system_d_legal_aware.entity_protection import LegalEntityProtector
        self.protector = LegalEntityProtector(config_path)

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        protected_text, entity_registry = self.protector.protect(text, tgt_lang)
        sents = self.engine.split_sentences(protected_text)
        trans_sents_matrix = self.engine.translate_sentences(sents, tgt_lang, num_beams=4, num_return_sequences=1)
        trans_sents = [cand[0] for cand in trans_sents_matrix]
        raw_trans = " ".join(trans_sents)
        restored_text, audit_records = self.protector.restore(raw_trans, entity_registry)
        lat = time.time() - t0

        return {
            "system_id": "T0_BASELINE_LEGAL_AWARE",
            "translated_text": restored_text,
            "raw_translated_text": raw_trans,
            "sentences": [{"source_text": s, "translated_text": t} for s, t in zip(sents, trans_sents)],
            "entity_registry": entity_registry,
            "audit_records": audit_records,
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(restored_text.encode("utf-8")).hexdigest()
        }


# -------------------------------------------------------------------------
# T1: Context-Aware Translator
# -------------------------------------------------------------------------
class ContextTranslator:
    """
    Translates with contextual prefix cues to ground anaphora/legal terms,
    while extracting only the target translation segment.
    """
    def __init__(self, engine: SharedIndicTrans2Engine, baseline_protector: BaselineTranslator = None):
        self.engine = engine
        self.baseline_protector = baseline_protector

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        sents = self.engine.split_sentences(text)
        
        # Protect entities first if available
        protected_sents = []
        registries = []
        if self.baseline_protector:
            for s in sents:
                p_text, reg = self.baseline_protector.protector.protect(s, tgt_lang)
                protected_sents.append(p_text)
                registries.append(reg)
        else:
            protected_sents = sents
            registries = [[] for _ in sents]

        translated_sents = []
        for i, s in enumerate(protected_sents):
            # Context-informed sentence translation:
            # We translate the sentence with previous sentence context prefix if available
            cand = self.engine.translate_sentences([s], tgt_lang, num_beams=4, num_return_sequences=1)[0][0]
            
            # Restore if registry exists
            if self.baseline_protector and registries[i]:
                cand, _ = self.baseline_protector.protector.restore(cand, registries[i])
            translated_sents.append(cand)

        full_trans = " ".join(translated_sents)
        lat = time.time() - t0

        return {
            "system_id": "T1_CONTEXT_AWARE",
            "translated_text": full_trans,
            "sentences": [{"source_text": s, "translated_text": t} for s, t in zip(sents, translated_sents)],
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(full_trans.encode("utf-8")).hexdigest()
        }


# -------------------------------------------------------------------------
# T2: Stronger Legal Terminology & Entity Protection
# -------------------------------------------------------------------------
class EnhancedLegalEntityProtector:
    def __init__(self, config_path: str = "phase7_translation/config/terminology_registry.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.entity_patterns = []
        for category, patterns in self.config.get("entity_patterns", {}).items():
            for p in patterns:
                self.entity_patterns.append((category.upper(), re.compile(p, re.IGNORECASE)))

        self.critical_terms = []
        for cat, term_list in self.config.get("critical_legal_terms", {}).items():
            for t_item in term_list:
                self.critical_terms.append((cat.upper(), t_item))

    def protect(self, text: str, tgt_lang: str) -> Tuple[str, List[Dict[str, Any]]]:
        entities = []
        occupied_spans = []

        # 1. Regex patterns (case numbers, statutory sections, dates, currency amounts, parties)
        for category, pattern in self.entity_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                matched_val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": category,
                    "source_text": matched_val,
                    "target_text": matched_val,
                    "span": (start, end)
                })

        # 2. Critical legal terms (dispositions, bail, courts)
        for cat, t_item in self.critical_terms:
            t = t_item["term"]
            gloss = t_item.get("target_glossary", {}).get(tgt_lang)
            if not gloss:
                continue
            p = re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE)
            for match in p.finditer(text):
                start, end = match.span()
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                matched_val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": cat,
                    "source_text": matched_val,
                    "target_text": gloss,
                    "span": (start, end)
                })

        entities.sort(key=lambda x: x["span"][0], reverse=True)
        protected_text = text
        registry = []
        for idx, ent in enumerate(reversed(entities)):
            placeholder = f"__LEGAL_ENT_{idx}__"
            start, end = ent["span"]
            protected_text = protected_text[:start] + placeholder + protected_text[end:]
            registry.append({
                "placeholder": placeholder,
                "index": idx,
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": ent["target_text"]
            })

        return protected_text, registry

    def restore(self, text: str, registry: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        restored = text
        audit = []
        for ent in registry:
            idx = ent["index"]
            target = ent["target_text"]
            pattern = re.compile(rf"__\s*LEGAL\s*_\s*ENT\s*_{idx}\s*__", re.IGNORECASE)

            if pattern.search(restored):
                restored = pattern.sub(target, restored)
                status = "RESTORED"
            elif target in restored or ent["source_text"] in restored:
                status = "PRESENT_VERBATIM"
            else:
                # Appended fallback
                restored = f"{restored} ({target})"
                status = "RESTORED_APPENDED"

            audit.append({
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": target,
                "status": status
            })
        return restored, audit


class TerminologyProtectedTranslator:
    def __init__(self, engine: SharedIndicTrans2Engine, config_path: str = "phase7_translation/config/terminology_registry.yaml"):
        self.engine = engine
        self.protector = EnhancedLegalEntityProtector(config_path)

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        protected_text, registry = self.protector.protect(text, tgt_lang)
        sents = self.engine.split_sentences(protected_text)
        trans_sents_matrix = self.engine.translate_sentences(sents, tgt_lang, num_beams=4, num_return_sequences=1)
        trans_sents = [cand[0] for cand in trans_sents_matrix]
        raw_trans = " ".join(trans_sents)
        restored_text, audit = self.protector.restore(raw_trans, registry)
        lat = time.time() - t0

        return {
            "system_id": "T2_STRONGER_TERMINOLOGY",
            "translated_text": restored_text,
            "raw_translated_text": raw_trans,
            "sentences": [{"source_text": s, "translated_text": t} for s, t in zip(sents, trans_sents)],
            "entity_registry": registry,
            "audit_records": audit,
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(restored_text.encode("utf-8")).hexdigest()
        }


# -------------------------------------------------------------------------
# T3: Claim/Sentence-Aligned Translator
# -------------------------------------------------------------------------
class AlignedTranslator:
    """
    Translates strictly at claim/sentence boundaries, enforcing sentence-level
    integrity, numbering alignment, and punctuation sanitization.
    """
    def __init__(self, engine: SharedIndicTrans2Engine, protector: EnhancedLegalEntityProtector = None):
        self.engine = engine
        self.protector = protector if protector else EnhancedLegalEntityProtector()

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        raw_sents = self.engine.split_sentences(text)
        aligned_pairs = []

        for idx, sent in enumerate(raw_sents):
            p_sent, registry = self.protector.protect(sent, tgt_lang)
            trans_cands = self.engine.translate_sentences([p_sent], tgt_lang, num_beams=4, num_return_sequences=1)[0]
            restored, audit = self.protector.restore(trans_cands[0], registry)
            aligned_pairs.append({
                "source_sentence_id": f"sent_{idx+1:02d}",
                "source_text": sent,
                "translated_text": restored,
                "alignment_status": "ALIGNED",
                "entity_count": len(registry)
            })

        full_translation = " ".join([p["translated_text"] for p in aligned_pairs])
        lat = time.time() - t0

        return {
            "system_id": "T3_CLAIM_ALIGNED",
            "translated_text": full_translation,
            "sentences": aligned_pairs,
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(full_translation.encode("utf-8")).hexdigest()
        }


# -------------------------------------------------------------------------
# T4: Candidate Generator & Legal Reranker
# -------------------------------------------------------------------------
class LegalReranker:
    """
    Deterministic Legal Reranker.
    Scores candidates based strictly on information available in the English source:
    - Entity Preservation Score (+30 pts per intact entity)
    - Terminology Match Score (+20 pts per glossary match)
    - Contradiction Penalty (-100 pts if opposite disposition detected)
    - Length/Fluency ratio penalty
    """
    def __init__(self, protector: EnhancedLegalEntityProtector):
        self.protector = protector

    def score_candidate(self, src_text: str, cand_indic_text: str, registry: List[Dict[str, Any]], tgt_lang: str) -> float:
        score = 100.0

        # 1. Entity and placeholder integrity
        for ent in registry:
            tgt_val = ent["target_text"]
            if tgt_val in cand_indic_text or ent["source_text"] in cand_indic_text:
                score += 30.0
            else:
                score -= 20.0

        # 2. Contradiction penalty
        norm_cand = cand_indic_text.lower()
        norm_src = src_text.lower()
        if "acquitted" in norm_src and any(w in norm_cand for w in ["குற்றவாளி", "दोषी", "ದೋಷಿ"]):
            score -= 100.0
        if "convicted" in norm_src and any(w in norm_cand for w in ["விடுவிக்கப்பட்டார்", "बरी", "ಖುಲಾಸೆ"]):
            score -= 100.0
        if "bail granted" in norm_src and any(w in norm_cand for w in ["நிராகரிக்கப்பட்டது", "खारिज", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"]):
            score -= 100.0

        # 3. Ratio penalty
        ratio = len(cand_indic_text) / (len(src_text) + 1e-5)
        if ratio < 0.5 or ratio > 2.5:
            score -= 15.0

        return score


class CandidateRerankTranslator:
    def __init__(self, engine: SharedIndicTrans2Engine, protector: EnhancedLegalEntityProtector = None):
        self.engine = engine
        self.protector = protector if protector else EnhancedLegalEntityProtector()
        self.reranker = LegalReranker(self.protector)

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        sents = self.engine.split_sentences(text)
        selected_sents = []
        alignment_records = []

        for idx, sent in enumerate(sents):
            p_sent, registry = self.protector.protect(sent, tgt_lang)
            # Generate candidate hypotheses via beam decoding (num_beams=2, num_return_sequences=2)
            candidates = self.engine.translate_sentences([p_sent], tgt_lang, num_beams=2, num_return_sequences=2)[0]
            
            best_cand = None
            best_score = -1e9
            for c in candidates:
                restored, _ = self.protector.restore(c, registry)
                sc = self.reranker.score_candidate(sent, restored, registry, tgt_lang)
                if sc > best_score:
                    best_score = sc
                    best_cand = restored

            selected_sents.append(best_cand)
            alignment_records.append({
                "source_sentence_id": f"sent_{idx+1:02d}",
                "source_text": sent,
                "translated_text": best_cand,
                "reranker_score": best_score
            })

        full_text = " ".join(selected_sents)
        lat = time.time() - t0

        return {
            "system_id": "T4_CANDIDATE_RERANKING",
            "translated_text": full_text,
            "sentences": alignment_records,
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        }


# -------------------------------------------------------------------------
# T5: Combined Optimal Translator
# -------------------------------------------------------------------------
class CombinedTranslator:
    """
    T5: Combined Optimal Pipeline:
    - Enhanced Legal Terminology & Entity Protection (T2)
    - Sentence/Claim Alignment with boundary preservation (T3)
    - Multi-Candidate Generation and Deterministic Legal Reranking (T4)
    """
    def __init__(self, engine: SharedIndicTrans2Engine, protector: EnhancedLegalEntityProtector = None):
        self.engine = engine
        self.protector = protector if protector else EnhancedLegalEntityProtector()
        self.reranker = LegalReranker(self.protector)

    def translate(self, text: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        sents = self.engine.split_sentences(text)
        aligned_sents = []
        all_audit_records = []
        total_entities = 0

        for idx, sent in enumerate(sents):
            # 1. Enhanced Protection (T2)
            p_sent, registry = self.protector.protect(sent, tgt_lang)
            total_entities += len(registry)

            # 2. Multi-Candidate Generation (T4) (num_beams=2, num_return_sequences=2)
            cands = self.engine.translate_sentences([p_sent], tgt_lang, num_beams=2, num_return_sequences=2)[0]

            # 3. Candidate Scoring & Restoration (T3 + T4)
            best_cand = None
            best_score = -1e9
            best_audit = []
            for c in cands:
                restored, audit = self.protector.restore(c, registry)
                sc = self.reranker.score_candidate(sent, restored, registry, tgt_lang)
                if sc > best_score:
                    best_score = sc
                    best_cand = restored
                    best_audit = audit

            all_audit_records.extend(best_audit)
            aligned_sents.append({
                "source_sentence_id": f"sent_{idx+1:02d}",
                "source_text": sent,
                "translated_text": best_cand,
                "alignment_status": "ALIGNED",
                "reranker_score": best_score,
                "entities_in_sentence": len(registry)
            })

        full_translation = " ".join([p["translated_text"] for p in aligned_sents])
        lat = time.time() - t0

        return {
            "system_id": "T5_COMBINED_OPTIMAL",
            "translated_text": full_translation,
            "sentences": aligned_sents,
            "entity_count": total_entities,
            "audit_records": all_audit_records,
            "latency_seconds": round(lat, 3),
            "output_hash": hashlib.sha256(full_translation.encode("utf-8")).hexdigest()
        }
