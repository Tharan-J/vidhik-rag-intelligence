"""
Budget and Cost Efficiency Evaluator for Vidhik Phase 5.2
Calculates:
  - Total selected windows
  - Total sentences
  - Word count
  - Character count
  - Estimated LLM context tokens
  - Fact Coverage / Evidence Tokens (per 1k tokens)
  - Critical Fact Coverage / Evidence Tokens (per 1k tokens)
"""

from typing import Dict, Any, List
import pandas as pd


def compute_evidence_budget_metrics(
    selected_windows_df: pd.DataFrame,
    overall_recall: float,
    critical_recall: float
) -> Dict[str, Any]:
    """
    Computes token counts, word counts, and efficiency ratios for selected evidence windows.

    Args:
        selected_windows_df: DataFrame of selected evidence windows across the 9 benchmark docs.
        overall_recall: Overall fact recall in [0, 1].
        critical_recall: Critical fact recall in [0, 1].

    Returns:
        Dict of evidence budget and efficiency metrics.
    """
    num_windows = len(selected_windows_df)
    
    # Sentences count: sum of unique sentence_ids per document
    unique_sentences = 0
    for _, grp in selected_windows_df.groupby("document_id"):
        doc_sids = set()
        for _, r in grp.iterrows():
            sids = r["sentence_ids"]
            if hasattr(sids, "tolist"):
                sids = sids.tolist()
            elif isinstance(sids, (list, tuple)):
                sids = list(sids)
            else:
                sids = [str(sids)]
            doc_sids.update(sids)
        unique_sentences += len(doc_sids)

    # Word count and character count
    all_texts = selected_windows_df["evidence_text"].tolist()
    total_chars = sum(len(t) for t in all_texts)
    total_words = sum(len(t.split()) for t in all_texts)

    # Approximate LLM context tokens:
    # Standard legal subword tokenization is approximately 1.30 tokens per English/legal word
    # or ~4 characters per token. We compute both and use word-based 1.30x factor.
    est_llm_tokens = int(round(total_words * 1.30))

    # Efficiency ratios (Recall per 1,000 evidence tokens)
    recall_per_1k_tokens = (
        round((overall_recall / est_llm_tokens) * 1000.0, 4)
        if est_llm_tokens > 0 else 0.0
    )
    critical_recall_per_1k_tokens = (
        round((critical_recall / est_llm_tokens) * 1000.0, 4)
        if est_llm_tokens > 0 else 0.0
    )

    return {
        "num_windows": num_windows,
        "unique_sentences": unique_sentences,
        "word_count": total_words,
        "character_count": total_chars,
        "estimated_llm_tokens": est_llm_tokens,
        "avg_tokens_per_doc": round(est_llm_tokens / 9.0, 1),
        "recall_per_1k_tokens": recall_per_1k_tokens,
        "critical_recall_per_1k_tokens": critical_recall_per_1k_tokens
    }
