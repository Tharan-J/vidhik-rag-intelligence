"""
Phase 6 Deterministic Legal Entity Verifier (System E)
Audits whether translated Indic summaries preserve legally critical entities
from the English intermediate summary.
Does NOT rewrite or generate summaries (deterministic auditor only).
"""

import re
from typing import Dict, List, Any

class DeterministicLegalVerifier:
    def __init__(self):
        pass

    def verify(
        self,
        doc_id: str,
        language: str,
        english_summary: str,
        indic_summary: str,
        protected_entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deterministically verifies presence of protected entities and key legal facts
        in the translated Indic summary compared to the English source summary.
        """
        verification_records = []
        preserved_count = 0
        total_count = len(protected_entities)

        for ent in protected_entities:
            target = ent.get("target_text", "")
            source = ent.get("source_text", "")
            category = ent.get("category", "OTHER")

            # Check if target text or source text is present in the Indic summary
            # Case-insensitive search for latin tokens; exact for Indic tokens
            is_present = False
            if target and target in indic_summary:
                is_present = True
            elif source and source.lower() in indic_summary.lower():
                is_present = True

            if is_present:
                preserved_count += 1
                status = "VERIFIED_PRESERVED"
            else:
                status = "VERIFIED_MISSING"

            verification_records.append({
                "doc_id": doc_id,
                "language": language,
                "category": category,
                "source_text": source,
                "expected_target": target,
                "is_preserved": is_present,
                "status": status
            })

        preservation_rate = (preserved_count / total_count) if total_count > 0 else 1.0

        return {
            "doc_id": doc_id,
            "language": language,
            "total_entities": total_count,
            "preserved_entities": preserved_count,
            "preservation_rate": round(preservation_rate, 4),
            "audit_trail": verification_records
        }
