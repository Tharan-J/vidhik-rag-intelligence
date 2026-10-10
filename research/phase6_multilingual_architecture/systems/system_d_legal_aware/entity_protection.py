"""
Phase 6 Legal Entity & Terminology Protection Layer (System D)
Protects legally critical entities and terminology prior to IndicTrans2 translation,
and deterministically restores them in the target Indic text.
"""

import re
import yaml
from typing import Dict, List, Tuple, Any

class LegalEntityProtector:
    def __init__(self, config_path: str = "phase6_multilingual_architecture/config/terminology_config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.entity_patterns = []
        # Case numbers
        for p in self.config.get("entity_patterns", {}).get("case_numbers", []):
            self.entity_patterns.append(("CASE_NUMBER", re.compile(p, re.IGNORECASE)))
        # Statutory sections
        for p in self.config.get("entity_patterns", {}).get("statutory_sections", []):
            self.entity_patterns.append(("STATUTORY_SECTION", re.compile(p, re.IGNORECASE)))
        # Currency amounts
        for p in self.config.get("entity_patterns", {}).get("currency_amounts", []):
            self.entity_patterns.append(("AMOUNT", re.compile(p, re.IGNORECASE)))
        # Dates
        for p in self.config.get("entity_patterns", {}).get("dates", []):
            self.entity_patterns.append(("DECISION_DATE", re.compile(p, re.IGNORECASE)))

        self.disposition_terms = self.config.get("critical_legal_terms", {}).get("disposition", [])
        self.bail_terms = self.config.get("critical_legal_terms", {}).get("bail", [])

    def protect(self, text: str, target_lang: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts entities from text and replaces them with protected placeholders.
        Returns:
            protected_text: Text with placeholders like __ENTITY_0__
            entity_registry: List of dicts with entity info and target representation
        """
        entities = []
        occupied_spans = []

        # 1. Extract regex pattern entities
        for category, pattern in self.entity_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                # Check overlap
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                matched_val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": category,
                    "source_text": matched_val,
                    "target_text": matched_val, # Alphanumeric / code / date / amount preserved verbatim
                    "span": (start, end)
                })

        # 2. Extract critical legal disposition / bail terms
        for term_def in self.disposition_terms + self.bail_terms:
            t = term_def["term"]
            gloss = term_def.get("target_glossary", {}).get(target_lang)
            if not gloss:
                continue
            pattern = re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                start, end = match.span()
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                matched_val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": "DISPOSITION" if term_def in self.disposition_terms else "BAIL_STATUS",
                    "source_text": matched_val,
                    "target_text": gloss, # Controlled legal glossary translation
                    "span": (start, end)
                })

        # Sort entities by start position descending to replace without altering earlier offsets
        entities.sort(key=lambda x: x["span"][0], reverse=True)

        protected_text = text
        ordered_registry = []
        # Re-assign sequential indices
        for idx, ent in enumerate(reversed(entities)):
            placeholder = f"__ENTITY_{idx}__"
            start, end = ent["span"]
            protected_text = protected_text[:start] + placeholder + protected_text[end:]
            ordered_registry.append({
                "placeholder": placeholder,
                "index": idx,
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": ent["target_text"]
            })

        return protected_text, ordered_registry

    def restore(self, translated_text: str, entity_registry: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """
        Restores protected placeholders with target_text in translated text.
        Robust to spacing and punctuation alterations from translation tokenizers.
        """
        restored_text = translated_text
        audit_records = []

        for ent in entity_registry:
            idx = ent["index"]
            target = ent["target_text"]
            # Flexible regex for placeholder variants (e.g. __ENTITY_0__, __ ENTITY _ 0 __, __entity_0__)
            pattern = re.compile(rf"__\s*ENTITY\s*_{idx}\s*__", re.IGNORECASE)
            
            if pattern.search(restored_text):
                restored_text = pattern.sub(target, restored_text)
                status = "RESTORED"
            else:
                # Fallback: check if the source or target text is already present
                if target in restored_text or ent["source_text"] in restored_text:
                    status = "PRESENT_VERBATIM"
                else:
                    # Append if lost in translation but legally critical
                    # Note: we do not invent facts; we only preserve the existing entity from English
                    status = "RESTORED_APPENDED"
                    restored_text += f" ({target})"
            
            audit_records.append({
                "index": idx,
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": target,
                "status": status
            })

        return restored_text, audit_records
