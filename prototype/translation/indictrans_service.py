"""
Vidhik IndicTrans2 Translation Service
=======================================
Direct integration with the IndicTrans2 distilled model:
ai4bharat/indictrans2-en-indic-dist-200M

Supports established target languages:
- Tamil (ta -> tam_Taml)
- Hindi (hi -> hin_Deva)
- Kannada (kn -> kan_Knda)
- Marathi (mr -> mar_Deva)

Preserves paragraph structure and uses GPU acceleration when available.
"""

import sys
import re
import time
import hashlib
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from IndicTransToolkit import IndicProcessor

SUPPORTED_LANGUAGES = {
    "ta": {"name": "Tamil", "code": "tam_Taml"},
    "hi": {"name": "Hindi", "code": "hin_Deva"},
    "kn": {"name": "Kannada", "code": "kan_Knda"},
    "mr": {"name": "Marathi", "code": "mar_Deva"},
}

DEFAULT_MODEL_PATH = "/home/tharan/.cache/huggingface/hub/models--ai4bharat--indictrans2-en-indic-dist-200M/snapshots/173b94239f7c38886b2747b8d4a5db771a7e1232"

class IndicTrans2Service:
    """
    Service wrapper for ai4bharat/indictrans2-en-indic-dist-200M.
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        device: Optional[str] = None,
        num_beams: int = 4,
    ):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model_path = model_path
        self.num_beams = num_beams

        print(f"[IndicTrans2Service] Loading model from {model_path} on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=True,
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)
        self.model.eval()

        self.processor = IndicProcessor(inference=True)
        print(f"[IndicTrans2Service] IndicTrans2 loaded successfully on {self.device}.")

    def is_language_supported(self, lang_code: str) -> bool:
        return lang_code.lower() in SUPPORTED_LANGUAGES

    def split_paragraphs(self, text: str) -> List[str]:
        """Preserves paragraph boundaries."""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def split_sentences(self, text: str) -> List[str]:
        """Splits paragraph text into clean sentences."""
        raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9_])|\n+", text)
        clean = [s.strip() for s in raw_sents if s.strip()]
        return clean if clean else [text]

    def translate_sentences(
        self,
        sentences: List[str],
        target_lang: str,
        batch_size: int = 4,
    ) -> List[str]:
        if not sentences:
            return []

        lang_entry = SUPPORTED_LANGUAGES.get(target_lang.lower())
        if not lang_entry:
            raise ValueError(
                f"Unsupported language code '{target_lang}'. "
                f"Supported languages: {list(SUPPORTED_LANGUAGES.keys())}"
            )

        src_code = "eng_Latn"
        tgt_code = lang_entry["code"]

        translated = []
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i : i + batch_size]
            preprocessed = self.processor.preprocess_batch(
                batch, src_lang=src_code, tgt_lang=tgt_code
            )
            inputs = self.tokenizer(
                preprocessed,
                padding="longest",
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    use_cache=False,
                    min_length=0,
                    max_length=512,
                    num_beams=self.num_beams,
                    num_return_sequences=1,
                )

            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            postprocessed = self.processor.postprocess_batch(decoded, lang=tgt_code)
            translated.extend(postprocessed)

            if self.device == "cuda":
                torch.cuda.empty_cache()

        return translated

    def translate_text(self, text: str, target_lang: str) -> Dict[str, Any]:
        """
        Translates text paragraph-by-paragraph, preserving paragraph boundaries.
        """
        t0 = time.time()
        paragraphs = self.split_paragraphs(text)
        if not paragraphs:
            return {
                "translated_text": "",
                "sentence_count": 0,
                "paragraph_count": 0,
                "latency_seconds": 0.0,
                "output_hash": hashlib.sha256(b"").hexdigest(),
            }

        translated_paragraphs = []
        total_sentences = 0

        for para in paragraphs:
            sentences = self.split_sentences(para)
            total_sentences += len(sentences)
            trans_sents = self.translate_sentences(sentences, target_lang)
            translated_paragraphs.append(" ".join(trans_sents))

        full_translation = "\n\n".join(translated_paragraphs)
        latency = round(time.time() - t0, 3)

        return {
            "translated_text": full_translation,
            "sentence_count": total_sentences,
            "paragraph_count": len(paragraphs),
            "latency_seconds": latency,
            "output_hash": hashlib.sha256(full_translation.encode("utf-8")).hexdigest(),
        }
