"""
Phase 6 System C: Raw English -> IndicTrans2 Translation Pipeline
Translates frozen English legal summaries to Tamil, Hindi, Kannada, and Marathi.
"""

import sys
import types
import re
import time
import hashlib
import torch
from typing import List, Dict, Any

try:
    import transformers.onnx
except (ImportError, AttributeError):
    m = types.ModuleType('transformers.onnx')
    m.OnnxConfig = object
    m.OnnxConfigWithPast = object
    m.OnnxSeq2SeqConfigWithPast = object
    sys.modules['transformers.onnx'] = m
    m_utils = types.ModuleType('transformers.onnx.utils')
    m_utils.compute_effective_axis_dimension = lambda *a, **k: None
    sys.modules['transformers.onnx.utils'] = m_utils

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from IndicTransToolkit import IndicProcessor

LANG_CODE_MAP = {
    "en": "eng_Latn",
    "ta": "tam_Taml",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "mr": "mar_Deva"
}

class IndicTrans2Translator:
    def __init__(self, model_id: str = "ai4bharat/indictrans2-en-indic-dist-200M", device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[System C] Loading IndicTrans2 model from {model_id} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, token=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        self.model.eval()
        self.processor = IndicProcessor(inference=True)
        self.model_id = model_id
        print(f"[System C] IndicTrans2 loaded successfully.")

    def split_sentences(self, text: str) -> List[str]:
        # Split text into clean sentences
        # Handle decimal numbers and section dots gracefully
        raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n+", text)
        clean = [s.strip() for s in raw_sents if s.strip()]
        return clean if clean else [text]

    def translate_sentences(self, sentences: List[str], tgt_lang: str, batch_size: int = 1) -> List[str]:
        if not sentences:
            return []
        src_code = LANG_CODE_MAP["en"]
        tgt_code = LANG_CODE_MAP.get(tgt_lang, tgt_lang)

        translated = []
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            preprocessed = self.processor.preprocess_batch(batch, src_lang=src_code, tgt_lang=tgt_code)
            inputs = self.tokenizer(
                preprocessed,
                padding="longest",
                truncation=True,
                max_length=256,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    use_cache=False,
                    min_length=0,
                    max_length=256,
                    num_beams=4,
                    num_return_sequences=1
                )
            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            postprocessed = self.processor.postprocess_batch(decoded, lang=tgt_code)
            translated.extend(postprocessed)
            if self.device == "cuda":
                torch.cuda.empty_cache()

        return translated

    def translate_summary(self, english_summary: str, tgt_lang: str) -> Dict[str, Any]:
        t0 = time.time()
        sentences = self.split_sentences(english_summary)
        translated_sents = self.translate_sentences(sentences, tgt_lang)
        full_translation = " ".join(translated_sents)
        latency = time.time() - t0

        return {
            "summary_text": full_translation,
            "sentence_count": len(sentences),
            "latency_seconds": round(latency, 3),
            "output_hash": hashlib.sha256(full_translation.encode("utf-8")).hexdigest()
        }
