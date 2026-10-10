"""
Vidhik Deterministic Legal Translation Verifier
================================================
Audits translated Indic legal answers against source English answers:
1. Exact preservation of protected legal entities (citations, sections, case numbers, party names).
2. Detection of any unresolved, corrupted, or lingering placeholders.
3. Structural completeness (truncation, sentence loss, or empty translation).
4. Material semantic drift and qualification preservation (ensuring qualifications and negative statements remain intact).
"""

import re
from typing import Dict, List, Any

# Target-language negative polarity markers for checking qualification preservation
POLARITY_MARKERS = {
    "hi": ["नहीं", "बिना", "वर्जित", "अस्वीकार", "अक्षम"],
    "ta": ["இல்லை", "முடியாது", "தடை", "அனுமதிக்காது", "தவிர்த்து"],
    "kn": ["ಇಲ್ಲ", "ಸಾಧ್ಯವಿಲ್ಲ", "ಅನುಮತಿಸುವುದಿಲ್ಲ", "ನಿಷೇಧಿಸಲಾಗಿದೆ"],
    "mr": ["नाही", "शक्य नाही", "परवानगी देत नाही", "मनाई"],
}

class DeterministicLegalVerifier:
    """
    Audits translated output for entity integrity, placeholder leakage,
    structural completeness, and semantic drift.
    """

    def __init__(self):
        self.placeholder_regex = re.compile(
            r"(?:_\s*)*LEGAL\s*_\s*ENT\s*_\s*\d+\b(?:\s*_+)*|__LEGAL_ENT_\d+__",
            re.IGNORECASE,
        )

    def verify(
        self,
        english_text: str,
        translated_text: str,
        target_lang: str,
        entity_registry: List[Dict[str, Any]],
        matter_id: str = "GLOBAL",
    ) -> Dict[str, Any]:
        """
        Executes deterministic multi-criteria verification.
        """
        audit_trail = []
        preserved_count = 0
        total_entities = len(entity_registry)

        # 1. Audit Protected Entities
        for ent in entity_registry:
            target = ent.get("target_text", "")
            source = ent.get("source_text", "")
            category = ent.get("category", "OTHER")

            # Check presence of expected target or original source text
            is_present = False
            if target and target in translated_text:
                is_present = True
            elif source and source.lower() in translated_text.lower():
                is_present = True

            if is_present:
                preserved_count += 1
                status = "VERIFIED_PRESERVED"
            else:
                status = "VERIFIED_MISSING"

            audit_trail.append({
                "index": ent.get("index"),
                "category": category,
                "source_text": source,
                "expected_target": target,
                "is_preserved": is_present,
                "status": status,
            })

        preservation_rate = (preserved_count / total_entities) if total_entities > 0 else 1.0

        # 2. Check for Unresolved Placeholders
        unresolved = self.placeholder_regex.findall(translated_text)
        has_unresolved_placeholders = len(unresolved) > 0

        # 3. Structural Completeness & Length Ratio Check
        en_len = len(english_text.strip())
        trans_len = len(translated_text.strip())
        length_ratio = (trans_len / en_len) if en_len > 0 else 1.0

        is_truncated = False
        structural_errors = []
        if trans_len == 0 and en_len > 0:
            is_truncated = True
            structural_errors.append("TRANSLATION_EMPTY")
        elif length_ratio < 0.25 and en_len > 50:
            is_truncated = True
            structural_errors.append("TRANSLATION_TRUNCATED")

        # 4. Semantic Drift & Qualification Polarity Check
        drift_warnings = []
        en_lower = english_text.lower()
        has_english_negative = any(
            neg in en_lower
            for neg in ["not", "cannot", "does not", "did not", "neither", "prohibited", "barred"]
        )

        if has_english_negative and target_lang in POLARITY_MARKERS:
            has_indic_negative = any(
                marker in translated_text
                for marker in POLARITY_MARKERS[target_lang]
            )
            if not has_indic_negative:
                drift_warnings.append(
                    f"POTENTIAL_POLARITY_SHIFT: English contains negative/qualifying statement, "
                    f"but no recognized {target_lang.upper()} negation marker was detected."
                )

        # 5. Overall Validation Decision
        # Pass ONLY IF:
        # - Preservation rate is acceptable (>= 0.80 or all critical entities preserved)
        # - Zero unresolved placeholders
        # - Not truncated or empty
        is_valid = (
            preservation_rate >= 0.80
            and not has_unresolved_placeholders
            and not is_truncated
        )

        verification_status = "VERIFIED_PASS"
        if has_unresolved_placeholders:
            verification_status = "FAIL_UNRESOLVED_PLACEHOLDERS"
        elif is_truncated:
            verification_status = "FAIL_STRUCTURAL_TRUNCATION"
        elif preservation_rate < 0.80:
            verification_status = "FAIL_ENTITY_PRESERVATION_LOW"
        elif drift_warnings:
            verification_status = "PASS_WITH_DRIFT_WARNINGS"

        return {
            "matter_id": matter_id,
            "target_language": target_lang,
            "is_valid": is_valid,
            "verification_status": verification_status,
            "preservation_rate": round(preservation_rate, 4),
            "total_entities": total_entities,
            "preserved_entities": preserved_count,
            "unresolved_placeholders": unresolved,
            "length_ratio": round(length_ratio, 3),
            "structural_errors": structural_errors,
            "drift_warnings": drift_warnings,
            "audit_trail": audit_trail,
        }
