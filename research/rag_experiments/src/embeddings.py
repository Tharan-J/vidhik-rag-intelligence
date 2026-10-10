"""
BGE-M3 ONNX Dense Embedding Engine for Vidhik Phase 3
Uses local quantized ONNX model with tokenizers for high-speed, zero-GPU-overhead embedding.
Produces 1024-dimensional normalized dense vectors.
"""

import time
import logging
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

logger = logging.getLogger("BGEM3_Embedder")


class BGEM3Embedder:
    def __init__(self, model_dir: Path | str = None, num_threads: int = 4):
        if model_dir is None:
            model_dir = Path(__file__).resolve().parent.parent / "indexes" / "models" / "bge-m3"
        self.model_dir = Path(model_dir)
        
        tokenizer_path = self.model_dir / "tokenizer.json"
        model_path = self.model_dir / "BAAI-bge-m3_quantized.onnx"
        
        if not tokenizer_path.exists() or not model_path.exists():
            raise FileNotFoundError(f"BGE-M3 model files missing in {self.model_dir}")
            
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.enable_truncation(max_length=8192)
        
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        self.dimension = 1024
        self._cache = {}

    def embed_texts(self, texts: list[str], batch_size: int = 16) -> list[np.ndarray]:
        """Generate normalized 1024-d dense embeddings for a list of texts."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embs = []
            
            uncached_indices = []
            uncached_texts = []
            
            for idx, t in enumerate(batch_texts):
                if t in self._cache:
                    batch_embs.append((idx, self._cache[t]))
                else:
                    uncached_indices.append(idx)
                    uncached_texts.append(t)
                    
            if uncached_texts:
                for idx, t in zip(uncached_indices, uncached_texts):
                    encoded = self.tokenizer.encode(t)
                    input_ids = np.array([encoded.ids], dtype=np.int64)
                    attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
                    token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
                    
                    feed = {
                        "input_ids": input_ids,
                        "attention_mask": attention_mask,
                        "token_type_ids": token_type_ids
                    }
                    outputs = self.session.run(["last_hidden_state"], feed)
                    # CLS pooling
                    vec = outputs[0][0, 0]
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    vec = vec.astype(np.float32)
                    self._cache[t] = vec
                    batch_embs.append((idx, vec))
                    
            batch_embs.sort(key=lambda x: x[0])
            embeddings.extend([emb for _, emb in batch_embs])
            
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]
