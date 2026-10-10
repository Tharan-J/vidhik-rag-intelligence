"""
Vidhik Legal Translation Pipeline Orchestrator
===============================================
Executes the full protected legal translation workflow:
1. Receive evidence-grounded English legal answer.
2. Protect legal entities (citations, statutory sections, case numbers, party names, etc.).
3. Translate via IndicTrans2 service.
4. Restore protected entities without corruption.
5. Deterministically verify entity preservation, placeholder integrity, and semantic drift.
6. Return structured result with original English answer, evidence provenance, and validation report.
"""

import time
import hashlib
from typing import Dict, List, Any, Optional

from .entity_protector import LegalEntityProtector
from .indictrans_service import IndicTrans2Service, SUPPORTED_LANGUAGES
from .verifier import DeterministicLegalVerifier

class LegalTranslationPipeline:
    """
    Production-grade multilingual pipeline for Vidhik legal representation.
    """

    def __init__(
        self,
        service: Optional[IndicTrans2Service] = None,
        protector: Optional[LegalEntityProtector] = None,
        verifier: Optional[DeterministicLegalVerifier] = None,
    ):
        self.service = service or IndicTrans2Service()
        self.protector = protector or LegalEntityProtector()
        self.verifier = verifier or DeterministicLegalVerifier()

    def translate_legal_answer(
        self,
        english_answer: str,
        target_language: str,
        matter_id: str = "GLOBAL",
        evidence: Optional[List[Dict[str, Any]]] = None,
        claims: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end legal translation with verification and evidence preservation.
        """
        t0 = time.time()
        target_lang = target_language.lower().strip()

        # 1. Validate Input
        if not english_answer or not english_answer.strip():
            raise ValueError("English legal answer cannot be empty or whitespace only.")

        if not self.service.is_language_supported(target_lang):
            raise ValueError(
                f"Unsupported language code '{target_language}'. "
                f"Configured languages are: {list(SUPPORTED_LANGUAGES.keys())}"
            )

        # 2. Protect Legally Critical Entities
        protected_text, entity_registry = self.protector.protect(english_answer, target_lang)

        # 3. Translate via IndicTrans2
        trans_res = self.service.translate_text(protected_text, target_lang)
        raw_translation = trans_res["translated_text"]

        # 4. Restore Entities Exactly
        restored_text, audit_records, unresolved = self.protector.restore(
            raw_translation, entity_registry
        )

        # 5. Deterministic Verification & Drift Audit
        v_report = self.verifier.verify(
            english_text=english_answer,
            translated_text=restored_text,
            target_lang=target_lang,
            entity_registry=entity_registry,
            matter_id=matter_id,
        )

        latency = round(time.time() - t0, 3)

        return {
            "matter_id": matter_id,
            "target_language": target_lang,
            "language_name": SUPPORTED_LANGUAGES[target_lang]["name"],
            "original_english_answer": english_answer,
            "translated_answer": restored_text,
            "raw_translated_text": raw_translation,
            "protected_entities_count": len(entity_registry),
            "preserved_entities": entity_registry,
            "restoration_audit": audit_records,
            "unresolved_placeholders": unresolved,
            "verification": v_report,
            "is_valid": v_report["is_valid"],
            "evidence": evidence or [],
            "claims": claims or [],
            "latency_seconds": latency,
            "output_hash": hashlib.sha256(restored_text.encode("utf-8")).hexdigest(),
        }
