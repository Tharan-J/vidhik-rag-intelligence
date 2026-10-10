"""
Dense Embedding Subsystem (BAAI/bge-m3)
=======================================
Generates 1024-dimensional normalized dense embeddings for document chunks and queries.
Supports FlagEmbedding with high-performance local ONNX Runtime CPU fallback.
Configurable batching and sequence length (up to 8,192 tokens).
Strictly responsible for dense vector representation (sparse retrieval is handled via BM25).
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("VidhikIngestion.Embed")


class BGEM3EmbeddingEngine:
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        local_model_dir: Optional[Path] = None,
        onnx_model_file: str = "BAAI-bge-m3_quantized.onnx",
        tokenizer_file: str = "tokenizer.json",
        dense_dim: int = 1024,
        max_length: int = 8192,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.local_model_dir = Path(local_model_dir) if local_model_dir else None
        self.onnx_model_file = onnx_model_file
        self.tokenizer_file = tokenizer_file
        self.dense_dim = dense_dim
        self.max_length = max_length
        self.batch_size = batch_size

        self._flag_model = None
        self._onnx_session = None
        self._tokenizer = None
        self._init_backend()

    def _init_backend(self):
        """Initialize FlagEmbedding if available, or fall back to local ONNX runtime."""
        # 1. Try FlagEmbedding if installed
        try:
            from FlagEmbedding import BGEM3FlagModel
            logger.info(f"Initializing FlagEmbedding BGEM3FlagModel ({self.model_name})...")
            self._flag_model = BGEM3FlagModel(
                self.model_name,
                use_fp16=False,
                max_length=self.max_length
            )
            logger.info("FlagEmbedding BGEM3FlagModel initialized successfully.")
            return
        except (ImportError, Exception) as e:
            logger.debug(f"FlagEmbedding BGEM3FlagModel not available ({e}); using ONNX Runtime backend.")

        # 2. Use local ONNX Runtime model
        candidate_dirs = []
        if self.local_model_dir:
            candidate_dirs.append(self.local_model_dir)

        # Check standard cache snapshots
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-m3" / "snapshots"
        if hf_cache.exists():
            for snap in hf_cache.iterdir():
                if (snap / "onnx").exists():
                    candidate_dirs.append(snap / "onnx")
                candidate_dirs.append(snap)

        for c_dir in candidate_dirs:
            for m_name in [self.onnx_model_file, "model.onnx", "BAAI-bge-m3_quantized.onnx"]:
                model_path = c_dir / m_name
                tok_path = c_dir / self.tokenizer_file
                if not tok_path.exists():
                    tok_path = c_dir.parent / self.tokenizer_file

                if model_path.exists() and tok_path.exists():
                    logger.info(f"Loading local BGE-M3 ONNX model from {model_path}...")
                    import onnxruntime as ort
                    from tokenizers import Tokenizer

                    self._tokenizer = Tokenizer.from_file(str(tok_path))
                    self._tokenizer.enable_truncation(max_length=min(self.max_length, 512))
                    self._tokenizer.enable_padding(pad_id=1, pad_token="<pad>")

                    opts = ort.SessionOptions()
                    opts.intra_op_num_threads = 4
                    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

                    self._onnx_session = ort.InferenceSession(
                        str(model_path),
                        sess_options=opts,
                        providers=["CPUExecutionProvider"]
                    )
                    self._onnx_input_names = [i.name for i in self._onnx_session.get_inputs()]
                    self._onnx_output_names = [o.name for o in self._onnx_session.get_outputs()]
                    logger.info("Local BGE-M3 ONNX session initialized successfully.")
                    return

        raise RuntimeError(
            f"Could not initialize BGE-M3 embedding engine: neither FlagEmbedding nor valid local ONNX model files found."
        )

    def encode_dense_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of texts into 1024-d normalized dense vectors."""
        if not texts:
            return []

        # If using FlagModel
        if self._flag_model is not None:
            output = self._flag_model.encode(
                texts,
                batch_size=self.batch_size,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=False,
            )
            dense_vecs = output["dense_vecs"]
            return [v.tolist() for v in dense_vecs]

        # If using local ONNX with batched execution
        dense_results = []
        eff_batch_size = min(self.batch_size, 16)
        for i in range(0, len(texts), eff_batch_size):
            batch = texts[i:i + eff_batch_size]
            encodings = self._tokenizer.encode_batch(batch)
            input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)

            feed = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
            if "token_type_ids" in getattr(self, "_onnx_input_names", []):
                feed["token_type_ids"] = np.zeros_like(input_ids, dtype=np.int64)

            # Prefer precomputed sentence_embedding, fallback to CLS pooling
            if "sentence_embedding" in getattr(self, "_onnx_output_names", []):
                outputs = self._onnx_session.run(["sentence_embedding"], feed)
                vecs = outputs[0]
            else:
                outputs = self._onnx_session.run(["last_hidden_state"], feed)
                vecs = outputs[0][:, 0, :]

            # L2 normalize
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            vecs = vecs / norms
            dense_results.extend(vecs.astype(np.float32).tolist())

        return dense_results

    def encode_query(self, query: str) -> List[float]:
        """Encode a single query string into a 1024-d normalized dense vector."""
        dense_vecs = self.encode_dense_batch([query])
        return dense_vecs[0] if dense_vecs else []

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of texts into 1024-d normalized dense vectors."""
        return self.encode_dense_batch(texts)
