"""
Phase 6 Evaluation Engine
Implements deterministic source-grounded fact evaluation, translation fidelity evaluation,
terminology evaluation, and Phase 6 causal failure attribution (R1-R8).
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple

CRITICAL_CATEGORIES = {
    "CASE_NUMBER", "PARTIES", "STATUTORY_SECTION", "DISPOSITION",
    "RELIEF", "JUDICIAL_FINDING", "CHARGE", "SENTENCE", "BAIL_STATUS"
}

IMPORTANT_CATEGORIES = {
    "COURT", "DECISION_DATE", "AMOUNT", "PROCEDURAL_ACTION", "ISSUE", "ARGUMENT"
}

DISPOSITION_TERMS = {
    "en": ["acquitted", "convicted", "dismissed", "allowed", "bail granted", "bail rejected", "disposed"],
    "ta": ["விடுவிக்கப்பட்டார்", "குற்றவாளி", "தள்ளுபடி", "அனுமதிக்கப்பட்டது", "ஜாமீன்"],
    "hi": ["बरी", "दोषी", "खारिज", "स्वीकार", "जमानत"],
    "kn": ["ಖುಲಾಸೆ", "ದೋಷಿ", "ವಜಾ", "ಪುರಸ್ಕರಿಸಲಾಗಿದೆ", "ಜಾಮೀನು"],
    "mr": ["निर्दोष", "दोषी", "फेटाळण्यात", "मंजूर", "जामीन"]
}

def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\s+", " ", text.lower()).strip()
    text = re.sub(r"[^\w\s\./-]", "", text)
    return text

def evaluate_fact_in_text(gold_fact: Dict[str, Any], text: str, lang: str = "en") -> str:
    """
    Evaluates presence of a single gold fact in the given summary text.
    Returns: SUPPORTED, PARTIALLY_SUPPORTED, OMITTED, CONTRADICTED, ABSENT_IN_SOURCE
    """
    if gold_fact.get("is_absent_in_source", False) or gold_fact.get("source_presence") == "ABSENT_IN_SOURCE":
        return "ABSENT_IN_SOURCE"

    norm_text = normalize_text(text)
    norm_val = normalize_text(str(gold_fact.get("normalized_value", "")))
    cat = gold_fact.get("category", "")

    if not norm_text:
        return "OMITTED"

    # Category-specific evaluation
    if cat == "CASE_NUMBER":
        # Check case number digits and year
        digits_match = re.findall(r"\d+", norm_val)
        if len(digits_match) >= 2:
            num, year = digits_match[0], digits_match[1]
            if f"{num}/{year}" in norm_text or (num in norm_text and year in norm_text):
                return "SUPPORTED"
            elif num in norm_text:
                return "PARTIALLY_SUPPORTED"
            return "OMITTED"
        if norm_val in norm_text:
            return "SUPPORTED"
        return "OMITTED"

    elif cat == "STATUTORY_SECTION":
        # Extract section numbers
        sec_nums = re.findall(r"\b\d+[a-z]?\b", norm_val)
        if sec_nums:
            matched = sum(1 for s in sec_nums if re.search(r"\b" + re.escape(s) + r"\b", norm_text))
            if matched == len(sec_nums):
                return "SUPPORTED"
            elif matched > 0:
                return "PARTIALLY_SUPPORTED"
            return "OMITTED"
        if norm_val in norm_text:
            return "SUPPORTED"
        return "OMITTED"

    elif cat in ("DISPOSITION", "RELIEF", "BAIL_STATUS"):
        # Check legal disposition tokens
        # Check if direct value is in text
        if norm_val in norm_text:
            return "SUPPORTED"
        # Check multilingual dictionary for the language
        gloss_terms = DISPOSITION_TERMS.get(lang, [])
        for term in gloss_terms:
            if term in norm_text and any(k in norm_val for k in ["acquit", "convict", "dismiss", "allow", "bail"]):
                return "SUPPORTED"
        # Check partial
        val_words = [w for w in norm_val.split() if len(w) > 3]
        if val_words and any(w in norm_text for w in val_words):
            return "PARTIALLY_SUPPORTED"
        return "OMITTED"

    elif cat == "AMOUNT":
        # Check amount digits
        digits = re.sub(r"[^\d]", "", norm_val)
        if digits and digits in re.sub(r"[^\d]", "", norm_text):
            return "SUPPORTED"
        # Check without zeros/commas
        if len(digits) > 3 and digits[:3] in re.sub(r"[^\d]", "", norm_text):
            return "PARTIALLY_SUPPORTED"
        return "OMITTED"

    elif cat == "DECISION_DATE":
        digits = re.findall(r"\d+", norm_val)
        if len(digits) >= 3:
            year = digits[-1] if len(digits[-1]) == 4 else digits[0]
            if year in norm_text and any(d in norm_text for d in digits if d != year):
                return "SUPPORTED"
            elif year in norm_text:
                return "PARTIALLY_SUPPORTED"
            return "OMITTED"
        return "SUPPORTED" if norm_val in norm_text else "OMITTED"

    else:
        # General matching
        if norm_val in norm_text:
            return "SUPPORTED"
        words = [w for w in norm_val.split() if len(w) > 3]
        if not words:
            return "OMITTED"
        matches = sum(1 for w in words if w in norm_text)
        ratio = matches / len(words)
        if ratio >= 0.7:
            return "SUPPORTED"
        elif ratio >= 0.3:
            return "PARTIALLY_SUPPORTED"
        return "OMITTED"


def attribute_failure(
    primary_status: str,
    gold_fact: Dict[str, Any],
    is_in_evidence: bool,
    is_in_english: bool,
    is_direct_indic: bool,
    is_in_translation: bool,
    has_terminology_damage: bool = False
) -> str:
    """
    Assigns Phase 6 failure attribution (R1-R8).
    Mutually exclusive decision tree.
    """
    if primary_status in ("SUPPORTED", "ABSENT_IN_SOURCE"):
        return "NONE"

    # R1: Fact absent from frozen BM25 B=8 evidence
    if not is_in_evidence:
        return "R1_RETRIEVAL_FAILURE"

    # R2: Present in evidence, but absent/incorrect in English summary
    if not is_in_english:
        return "R2_ENGLISH_GENERATION_FAILURE"

    # Present in English!
    # If direct Indic system:
    if is_direct_indic:
        return "R3_DIRECT_INDIC_GENERATION_FAILURE"

    # If translation system:
    # If translation preserved sentence but damaged terminology:
    if has_terminology_damage:
        return "R5_LEGAL_TERMINOLOGY_FAILURE"

    # Translation failed to preserve English fact:
    if not is_in_translation:
        return "R4_TRANSLATION_FAILURE"

    return "R8_OTHER"
