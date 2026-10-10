"""
Conservative Legal Text Normalization Subsystem
================================================
Normalizes mechanical formatting artifacts while strictly preserving all legal substance.
Explicitly forbids paraphrasing, summarization, lowercase mutation, or stripping of statutory sections/citations.
"""

import re
import logging

logger = logging.getLogger("VidhikIngestion.Normalize")

# Pattern to repair hyphenated words split across line breaks
# Example: "procedur-\nal" -> "procedural", but not "Section 438-A"
HYPHENATED_WRAP_RE = re.compile(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)")

# Pattern to collapse repeated spaces and tabs horizontally without flattening newlines
HORIZONTAL_WHITESPACE_RE = re.compile(r"[^\S\r\n]+")

# Pattern to collapse 3 or more consecutive newlines into 2 (paragraph boundary)
EXCESS_NEWLINES_RE = re.compile(r"\n{3,}")


def normalize_legal_text(text: str) -> str:
    """
    Apply conservative legal text normalization.
    
    Allowed transformations:
    - Normalizes repeated horizontal whitespace
    - Repairs hyphenated line wraps (e.g., 'jurisdic-\\ntion' -> 'jurisdiction')
    - Standardizes carriage returns (\\r\\n -> \\n)
    - Normalizes excessive blank lines (3+ -> 2)
    
    Strictly forbidden:
    - Altering casing (preserves exact case)
    - Stripping citation markers or statute provisions
    - Paraphrasing or removing text
    """
    if not text:
        return ""

    # 1. Normalize line endings
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Repair hyphenated word-break artifacts across newlines
    normalized = HYPHENATED_WRAP_RE.sub(r"\1\2", normalized)

    # 3. Collapse multiple horizontal whitespace within lines
    lines = normalized.split("\n")
    cleaned_lines = [HORIZONTAL_WHITESPACE_RE.sub(" ", line).strip() for line in lines]
    normalized = "\n".join(cleaned_lines)

    # 4. Collapse multiple blank lines to at most 2 newlines (paragraph separator)
    normalized = EXCESS_NEWLINES_RE.sub("\n\n", normalized)

    return normalized.strip()
