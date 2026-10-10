"""
Context Assembly Subsystem
==========================
Constructs a token-bounded, structured context prompt from selected legal evidence units.
Enforces maximum context limits and preserves citation landmarks [E1], [E2], ...
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

from .evidence import EvidenceItem
from .config import ContextConfig

logger = logging.getLogger("VidhikRAG.Context")


def estimate_token_count(text: str) -> int:
    """Fast conservative word-based token estimation for context budgeting."""
    if not text:
        return 0
    words = text.split()
    return max(1, int(len(words) * 1.35))


@dataclass
class ContextBundle:
    """Structured representation of assembled prompt context."""
    query: str
    formatted_context: str
    included_evidence: List[EvidenceItem]
    estimated_tokens: int


class ContextBuilder:
    """
    Builds structured, token-bounded evidence context for Qwen.
    """

    def __init__(self, config: Optional[ContextConfig] = None, max_tokens: int = 3500):
        self.max_tokens = config.max_tokens if config else max_tokens

    def build(
        self,
        query: str,
        evidence_items: List[EvidenceItem],
        max_tokens: Optional[int] = None,
    ) -> ContextBundle:
        """
        Assemble user query and evidence blocks within the token budget.
        """
        budget = max_tokens if max_tokens is not None else self.max_tokens
        clean_query = query.strip()
        
        query_header = f"USER QUESTION:\n{clean_query}\n\nRELEVANT LEGAL EVIDENCE:\n"
        accumulated_text = query_header
        current_tokens = estimate_token_count(query_header)
        
        included_evidence: List[EvidenceItem] = []

        for item in evidence_items:
            evidence_block = item.format_for_prompt() + "\n" + ("-" * 60) + "\n\n"
            block_tokens = estimate_token_count(evidence_block)

            # Check if adding this evidence block would exceed the budget
            if current_tokens + block_tokens > budget:
                # If we haven't included any evidence yet, include at least the top one truncated
                if not included_evidence:
                    logger.warning("First evidence block exceeds context budget; including top chunk.")
                    included_evidence.append(item)
                    accumulated_text += evidence_block
                    current_tokens += block_tokens
                else:
                    logger.debug(
                        f"Context budget reached ({current_tokens}/{budget} tokens). "
                        f"Stopping at evidence {len(included_evidence)}."
                    )
                break

            accumulated_text += evidence_block
            current_tokens += block_tokens
            included_evidence.append(item)

        logger.debug(
            f"Assembled context with {len(included_evidence)} evidence blocks "
            f"(~{current_tokens} estimated tokens)."
        )

        return ContextBundle(
            query=clean_query,
            formatted_context=accumulated_text.strip(),
            included_evidence=included_evidence,
            estimated_tokens=current_tokens,
        )
