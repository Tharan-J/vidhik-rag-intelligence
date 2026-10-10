"""
Vidhik Legal Entity & Terminology Protection Layer
===================================================
Collision-resistant placeholder protection for legal entities and terminology
prior to IndicTrans2 translation, with exact restoration and integrity auditing.

Preserves:
- Judicial Citations (SCC, AIR, SCR, SCALE, Cri LJ, etc.)
- Statutory Provisions & Sections (Section 34, Section 138, etc.)
- Constitutional Articles (Article 21, Article 226, etc.)
- Case Names (NHAI v. M. Hakeem, etc.)
- Court Names (Supreme Court of India, High Court of Delhi, etc.)
- Case Numbers, SLPs, and FIR Numbers
- Dates and Currency Amounts
- Matter IDs and Document IDs
- Controlled Legal Disposition & Relief Terms
"""

import re
from typing import Dict, List, Tuple, Any, Optional

# Standard legal disposition glossary across intended languages
CONTROLLED_LEGAL_GLOSSARY = {
    "acquitted": {
        "ta": "விடுவிக்கப்பட்டார்",
        "hi": "बरी किया गया",
        "kn": "ಖುಲಾಸೆಗೊಳಿಸಲಾಗಿದೆ",
        "mr": "निर्दोष मुक्त केले",
    },
    "convicted": {
        "ta": "குற்றவாளி என தீர்ப்பளிக்கப்பட்டது",
        "hi": "दोषी ठहराया गया",
        "kn": "ದೋಷಿ ಎಂದು ತೀರ್ಮಾನಿಸಲಾಯಿತು",
        "mr": "दोषी ठरवले",
    },
    "dismissed": {
        "ta": "தள்ளுபடி செய்யப்பட்டது",
        "hi": "खारिज किया गया",
        "kn": "ವಜಾಗೊಳಿಸಲಾಗಿದೆ",
        "mr": "फेटाळण्यात आला",
    },
    "allowed": {
        "ta": "அனுமதிக்கப்பட்டது",
        "hi": "स्वीकार किया गया",
        "kn": "ಪುರಸ್ಕರಿಸಲಾಗಿದೆ",
        "mr": "मंजूर करण्यात आला",
    },
    "quashed": {
        "ta": "ரத்து செய்யப்பட்டது",
        "hi": "रद्द किया गया",
        "kn": "ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ",
        "mr": "रद्द करण्यात आले",
    },
    "bail granted": {
        "ta": "ஜாமீன் வழங்கப்பட்டது",
        "hi": "जमानत मंजूर की गई",
        "kn": "ಜಾಮೀನು ಮಂಜೂರು ಮಾಡಲಾಗಿದೆ",
        "mr": "जामीन मंजूर केला",
    },
    "anticipatory bail": {
        "ta": "முன்ஜாமீன்",
        "hi": "अग्रिम जमानत",
        "kn": "ನಿರೀಕ್ಷಣಾ ಜಾಮೀನು",
        "mr": "अगाऊ जामीन",
    },
    "bail rejected": {
        "ta": "ஜாமீன் நிராகரிக்கப்பட்டது",
        "hi": "जमानत खारिज की गई",
        "kn": "ಜಾಮೀನು ತಿರಸ್ಕರಿಸಲಾಗಿದೆ",
        "mr": "जामीन नाकारला",
    },
}

class LegalEntityProtector:
    """
    Protects legal entities using collision-resistant placeholders
    and restores them accurately after translation.
    """

    def __init__(self, glossary: Optional[Dict[str, Dict[str, str]]] = None):
        self.glossary = glossary or CONTROLLED_LEGAL_GLOSSARY
        self._compile_patterns()

    def _compile_patterns(self):
        self.patterns = [
            # 1. Citations (e.g., (2021) 9 SCC 1, 2023 SCC OnLine SC 123, AIR 1967 SC 1)
            (
                "CITATION",
                re.compile(
                    r"(?:\([0-9]{4}\)\s*[0-9]+\s*SCC\s*[0-9]+|"
                    r"[0-9]{4}\s*(?:\([0-9]+\)\s*)?SCC\s*(?:OnLine\s*[A-Za-z]+\s*)?[0-9]+|"
                    r"AIR\s+[0-9]{4}\s+(?:SC|Del|Bom|Mad|Cal|Kar|All)\s+[0-9]+|"
                    r"[0-9]{4}\s+(?:Cri\s*LJ|SCALE|SCR)\s+[0-9]+)",
                    re.IGNORECASE,
                ),
            ),
            # 2. Statutory provisions and sections (e.g. Section 34, Section 138 of the NI Act)
            (
                "STATUTORY_SECTION",
                re.compile(
                    r"(?:Sections?\s+[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*(?:\s*(?:and|&|,)\s*[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*)*"
                    r"(?:\s+of\s+(?:the\s+)?)?"
                    r"(?:IPC|Cr\.?P\.?C\.?|I\.?P\.?C\.?|Indian Penal Code|Code of Criminal Procedure|"
                    r"Negotiable Instruments Act|N\.?I\.?\s*Act|Arbitration(?: and Conciliation)? Act(?:,\s*[0-9]{4})?|"
                    r"Motor Vehicles Act|M\.?V\.?\s*Act|POCSO(?: Act)?|BNS|BNSS|CPC|Specific Relief Act|Contract Act)?\b|"
                    r"u/s\.?\s+[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*(?:\s*(?:and|&|,)\s*[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*)*\s*"
                    r"(?:IPC|Cr\.?P\.?C\.?|I\.?P\.?C\.?|Indian Penal Code)?)",
                    re.IGNORECASE,
                ),
            ),
            # 3. Constitutional articles (e.g. Article 21, Article 226)
            (
                "CONSTITUTIONAL_ARTICLE",
                re.compile(
                    r"(?:Articles?\s+[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*(?:\s*(?:and|&|,)\s*[0-9]+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*)*"
                    r"(?:\s+of\s+(?:the\s+)?Constitution(?:\s+of\s+India)?)?\b)",
                    re.IGNORECASE,
                ),
            ),
            # 4. Case names (e.g. NHAI v. M. Hakeem, State of Punjab v. Davinder Singh)
            (
                "CASE_NAME",
                re.compile(
                    r"(?:[A-Z][A-Za-z0-9.&,\s]{2,35}?\s+(?:v\.|vs\.|Versus)\s+[A-Z][A-Za-z0-9.&,\s]{2,35}?"
                    r"(?=(?:,\s*(?:\(?[0-9]{4}|held|observed|dismissed|allowed)|\s*\([0-9]{4}\)|\s+case)))",
                ),
            ),
            # 5. Court names
            (
                "COURT_NAME",
                re.compile(
                    r"(?:Supreme Court(?:\s+of\s+India)?|"
                    r"High Court(?:\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?|"
                    r"District(?:\s+and\s+Sessions)?\s+Court(?:\s+at\s+[A-Z][a-z]+)?|"
                    r"Appellate Tribunal|National Company Law Tribunal|NCLT|NCLAT)\b",
                ),
            ),
            # 6. Case numbers / FIR numbers
            (
                "CASE_NUMBER",
                re.compile(
                    r"(?:(?:Spl\.?\s*)?(?:C\.?C\.?|Crl\.?\s*A\.?|M\.?A\.?C\.?P\.?|Special Case|Civil Suit|Cr\.\s*No\.|Crime No\.|FIR No\.|SLP\s*\([A-Za-z]+\)|Civil Appeal)\s*(?:No\.?\s*)?[0-9]+(?:\s*(?:of|-|/)\s*[0-9]{2,4})?|"
                    r"Case\s+No\.?\s*[0-9]+/[0-9]{2,4})",
                    re.IGNORECASE,
                ),
            ),
            # 7. Currency amounts
            (
                "CURRENCY_AMOUNT",
                re.compile(
                    r"(?:(?:Rs\.?|INR|₹)\s*[0-9,]+(?:\.[0-9]{2})?|"
                    r"[0-9,]+(?:\.[0-9]{2})?\s*(?:rupees|lakh|crore|lakhs|crores))",
                    re.IGNORECASE,
                ),
            ),
            # 8. Dates
            (
                "DATE",
                re.compile(
                    r"(?:[0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4}|"
                    r"[0-9]{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+[0-9]{4}|"
                    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s+[0-9]{4})",
                    re.IGNORECASE,
                ),
            ),
            # 9. Document & Matter identifiers
            (
                "DOCUMENT_IDENTIFIER",
                re.compile(r"(?:(?:MATTER|DOC|CHUNK)_[A-Za-z0-9_-]+)"),
            ),
        ]

    def protect(self, text: str, target_lang: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts entities from English text and replaces them with collision-resistant placeholders.
        """
        if not text:
            return "", []

        entities = []
        occupied_spans = []

        # 1. Regex pattern matches
        for category, pattern in self.patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                # Ensure no overlapping spans
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": category,
                    "source_text": val,
                    "target_text": val,  # Preserved verbatim
                    "span": (start, end),
                })

        # 2. Controlled legal glossary terms
        for term, translations in self.glossary.items():
            target_term = translations.get(target_lang)
            if not target_term:
                continue
            term_pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
            for match in term_pat.finditer(text):
                start, end = match.span()
                if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                    continue
                val = match.group(0).strip()
                occupied_spans.append((start, end))
                entities.append({
                    "category": "LEGAL_DISPOSITION",
                    "source_text": val,
                    "target_text": target_term,
                    "span": (start, end),
                })

        # Sort descending by start position to replace without invalidating prior indices
        entities.sort(key=lambda x: x["span"][0], reverse=True)

        protected_text = text
        ordered_registry = []

        for idx, ent in enumerate(reversed(entities)):
            placeholder = f"__LEGAL_ENT_{idx}__"
            start, end = ent["span"]
            protected_text = protected_text[:start] + placeholder + protected_text[end:]
            ordered_registry.append({
                "placeholder": placeholder,
                "index": idx,
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": ent["target_text"],
            })

        return protected_text, ordered_registry

    def restore(
        self,
        translated_text: str,
        entity_registry: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]], List[str]]:
        """
        Restores protected placeholders with target_text in translated text.
        Handles tokenization whitespace splitting like `_ _ LEGAL _ ENT _ 0 _ _`.

        Returns:
            restored_text: text with placeholders replaced by actual values.
            audit_records: list of per-entity restoration statuses.
            unresolved_placeholders: list of any placeholder patterns still present.
        """
        restored_text = translated_text
        audit_records = []

        for ent in entity_registry:
            idx = ent["index"]
            target = ent["target_text"]

            # Match exact placeholder OR any tokenized whitespace/underscore variant
            # e.g.: __LEGAL_ENT_0__, _ _ LEGAL _ ENT _ 0 _ _, _ _ LEGAL _ ENT _ 0 _, LEGAL _ ENT _ 0
            pattern = re.compile(
                rf"(?:_\s*)*LEGAL\s*_\s*ENT\s*_\s*{idx}\b(?:\s*_+)*",
                re.IGNORECASE,
            )

            if pattern.search(restored_text):
                restored_text = pattern.sub(f" {target} ", restored_text)
                status = "RESTORED_IN_PLACE"
            elif ent["placeholder"] in restored_text:
                restored_text = restored_text.replace(ent["placeholder"], f" {target} ")
                status = "RESTORED_EXACT"
            elif target in restored_text or ent["source_text"] in restored_text:
                status = "ALREADY_PRESENT"
            else:
                # If placeholder was stripped by the model, append preserved entity to maintain evidentiary grounding
                restored_text += f" ({target})"
                status = "RESTORED_APPENDED"

            audit_records.append({
                "index": idx,
                "category": ent["category"],
                "source_text": ent["source_text"],
                "target_text": target,
                "status": status,
            })

        # Clean multiple spaces produced during replacement
        restored_text = re.sub(r"[ ]{2,}", " ", restored_text).strip()

        # Audit for any unresolved or corrupted placeholders
        unresolved_regex = re.compile(
            r"(?:_\s*)*LEGAL\s*_\s*ENT\s*_\s*\d+\b(?:\s*_+)*|__LEGAL_ENT_\d+__",
            re.IGNORECASE,
        )
        unresolved_placeholders = unresolved_regex.findall(restored_text)

        return restored_text, audit_records, unresolved_placeholders
