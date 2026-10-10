"""
Phase 6 System D: Legal-Aware Translation Pipeline
Integrates LegalEntityProtector with IndicTrans2 to safeguard
case numbers, statutory sections, currency amounts, dates, and legal disposition phrases.
"""

import sys
import os
import time
import hashlib
from typing import Dict, Any, List

sys.path.append(os.path.abspath("phase6_multilingual_architecture"))
from systems.system_d_legal_aware.entity_protection import LegalEntityProtector
from systems.system_c_indictrans2.translator import IndicTrans2Translator

class LegalAwareTranslator:
    def __init__(self, indictrans_translator: IndicTrans2Translator = None, config_path: str = None):
        if indictrans_translator is None:
            self.translator = IndicTrans2Translator()
        else:
            self.translator = indictrans_translator
            
        if config_path:
            self.protector = LegalEntityProtector(config_path)
        else:
            self.protector = LegalEntityProtector()

    def translate_summary(self, english_summary: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        
        # 1. Protect legal entities & terminology
        protected_text, entity_registry = self.protector.protect(english_summary, tgt_lang)
        
        # 2. Translate using IndicTrans2
        translation_res = self.translator.translate_summary(protected_text, tgt_lang)
        raw_translated = translation_res["summary_text"]
        
        # 3. Restore protected entities & terminology
        restored_text, audit_records = self.protector.restore(raw_translated, entity_registry)
        latency = time.time() - t0

        return {
            "summary_text": restored_text,
            "raw_translated_text": raw_translated,
            "protected_entities_count": len(entity_registry),
            "entity_registry": entity_registry,
            "audit_records": audit_records,
            "latency_seconds": round(latency, 3),
            "output_hash": hashlib.sha256(restored_text.encode("utf-8")).hexdigest()
        }
