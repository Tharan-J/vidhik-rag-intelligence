"""
Retrieval Evaluation Engine for Vidhik Phase 3
Calculates:
- Recall@K and Precision@K (K = 1, 3, 5, 10)
- Mean Reciprocal Rank (MRR)
- nDCG@K with Graded Relevance (Grade 3 = Exact Sentence, 2 = Parent Chunk, 1 = Document)
- Evidence Recall (exact supporting sentence found in top-K)
- Document Retrieval Accuracy
- Page Retrieval Accuracy
- Provenance Chain Integrity Accuracy
- Document-Level Retrieval Mismatch (DRM Rate)
- Latency profiling
"""

import math
import numpy as np
import pandas as pd


def compute_dcg(relevance_scores: list[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        dcg += (2.0 ** rel - 1.0) / math.log2(i + 2)
    return dcg


def compute_idcg(num_rel_items: int, max_grade: int, k: int) -> float:
    # Ideal ranking places highest grades first
    ideal_scores = [max_grade] * min(num_rel_items, k)
    return compute_dcg(ideal_scores, k)


class RetrievalEvaluator:
    def __init__(self, qrels: list[dict]):
        # Map: query_id -> {entity_id: relevance_level}
        self.qrels = qrels
        self.qrel_map = {}
        self.target_doc_map = {}
        self.target_page_map = {}
        self.target_sen_map = {}

        for qr in qrels:
            qid = qr["query_id"]
            if qid not in self.qrel_map:
                self.qrel_map[qid] = {}
            self.qrel_map[qid][qr["entity_id"]] = qr["relevance_level"]
            
            if qr["relevance_level"] == 1:
                self.target_doc_map[qid] = qr["document_id"]
                self.target_page_map[qid] = qr["page_number"]
            elif qr["relevance_level"] == 3:
                self.target_sen_map[qid] = qr["entity_id"]

    def evaluate_results(self, retrieval_results: dict[str, list[dict]], k_values: list[int] = [1, 3, 5, 10]) -> dict:
        """
        retrieval_results: query_id -> list of hit dicts (ordered by rank)
        Each hit dict contains: chunk_id, document_id, page_number, sentence_ids, source_sha256, score
        """
        per_query_metrics = []

        for qid, hits in retrieval_results.items():
            if qid not in self.qrel_map:
                continue

            q_qrels = self.qrel_map[qid]
            target_doc = self.target_doc_map.get(qid)
            target_page = self.target_page_map.get(qid)
            target_sen = self.target_sen_map.get(qid)

            # Map hits to relevance grades
            grades = []
            doc_matches = []
            page_matches = []
            sen_matches = []
            prov_valid = []

            for h in hits:
                chunk_id = h.get("chunk_id", "")
                doc_id = h.get("document_id", "")
                page_no = h.get("page_number", -1)
                sen_ids = h.get("sentence_ids", [])
                sha = h.get("source_sha256", "")

                # Provenance validity check: chunk_id and SHA must exist and match format
                is_prov = bool(sha and len(sha) == 64 and chunk_id.startswith("CHK_"))
                prov_valid.append(is_prov)

                # Check relevance
                grade = 0
                if target_sen and target_sen in sen_ids:
                    grade = 3
                elif chunk_id in q_qrels:
                    grade = q_qrels[chunk_id]
                elif doc_id == target_doc:
                    grade = 1

                grades.append(grade)
                doc_matches.append(doc_id == target_doc)
                page_matches.append(doc_id == target_doc and page_no == target_page)
                sen_matches.append(bool(target_sen and target_sen in sen_ids))

            # Metric computations
            q_metrics = {"query_id": qid}

            # 1. Document Retrieval Accuracy @ K
            for k in k_values:
                q_metrics[f"doc_acc@{k}"] = 1.0 if any(doc_matches[:k]) else 0.0

            # 2. Page Retrieval Accuracy @ K
            for k in k_values:
                q_metrics[f"page_acc@{k}"] = 1.0 if any(page_matches[:k]) else 0.0

            # 3. Evidence Recall @ K (Exact sentence retrieved)
            for k in k_values:
                q_metrics[f"evidence_recall@{k}"] = 1.0 if any(sen_matches[:k]) else 0.0

            # 4. Precision @ K (Relevant chunks: grade >= 2)
            for k in k_values:
                hits_k = grades[:k]
                rel_k = sum(1 for g in hits_k if g >= 2)
                q_metrics[f"precision@{k}"] = rel_k / k if k > 0 else 0.0

            # 5. Recall @ K (Any relevant chunk retrieved: grade >= 2)
            for k in k_values:
                q_metrics[f"recall@{k}"] = 1.0 if any(g >= 2 for g in grades[:k]) else 0.0

            # 6. MRR (First hit with grade >= 2)
            first_rel_rank = 0
            for rank, g in enumerate(grades, start=1):
                if g >= 2:
                    first_rel_rank = rank
                    break
            q_metrics["mrr"] = 1.0 / first_rel_rank if first_rel_rank > 0 else 0.0

            # 7. nDCG @ K
            for k in k_values:
                dcg = compute_dcg(grades, k)
                idcg = compute_idcg(1, 3, k) # Ideal is 1 relevant item with grade 3
                q_metrics[f"ndcg@{k}"] = dcg / idcg if idcg > 0 else 0.0

            # 8. Document-Level Retrieval Mismatch (DRM):
            # Defined as: Top-1 retrieved hit has wrong document (doc_id != target_doc)
            top1_wrong_doc = (len(doc_matches) > 0 and not doc_matches[0])
            q_metrics["drm"] = 1.0 if top1_wrong_doc else 0.0

            # 9. Provenance Accuracy @ K
            for k in k_values:
                q_metrics[f"prov_acc@{k}"] = sum(prov_valid[:k]) / k if k > 0 else 0.0

            per_query_metrics.append(q_metrics)

        # Aggregate across queries
        df = pd.DataFrame(per_query_metrics)
        agg_metrics = {}
        for col in df.columns:
            if col != "query_id":
                agg_metrics[col] = float(df[col].mean())

        return {
            "aggregate": agg_metrics,
            "per_query_df": df
        }
