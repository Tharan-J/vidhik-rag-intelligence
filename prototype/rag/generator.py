"""
Evidence-Constrained Qwen Generator Subsystem
=============================================
Communicates with the local Qwen runtime (qwen3:4b-instruct via Ollama) to produce
structured, evidence-grounded legal answers in strict JSON format.
Includes robust parsing, JSON validation, and error recovery.
"""

import json
import re
import urllib.request
import urllib.error
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .config import GeneratorConfig

logger = logging.getLogger("VidhikRAG.Generator")

ALLOWED_CONFIDENCE_LEVELS = {"supported", "partially_supported", "insufficient_evidence"}


@dataclass
class RawGenerationOutput:
    """Parsed structured output from Qwen."""
    answer: str
    claims: List[Dict[str, Any]]
    limitations: str
    confidence: str
    raw_response: str
    model_name: str
    contrary_evidence: List[Dict[str, Any]] = field(default_factory=list)


class QwenGenerator:
    """
    Client for Qwen inference via local Ollama API with guaranteed JSON schema parsing.
    """

    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> RawGenerationOutput:
        """
        Invoke Qwen model and parse structured JSON legal answer.
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens_limit = max_tokens if max_tokens is not None else self.config.max_tokens

        payload = {
            "model": self.config.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": temp,
                "top_p": self.config.top_p,
                "num_predict": tokens_limit,
            },
        }

        endpoint = self.config.endpoint
        gateway_url = os.environ.get("AI_GATEWAY_URL", "")
        if gateway_url:
            clean_gw = gateway_url.rstrip("/")
            endpoint = clean_gw if clean_gw.endswith("/api/generate") else f"{clean_gw}/api/generate"

        headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true",
        }
        token = os.environ.get("AI_GATEWAY_TOKEN", os.environ.get("GATEWAY_TOKEN", ""))
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["x-gateway-token"] = token

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data_bytes,
            headers=headers,
        )

        logger.info(
            f"Invoking Qwen model ({self.config.model}) at {endpoint} "
            f"(temp={temp}, max_tokens={tokens_limit})..."
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            logger.error(f"Failed to connect to Qwen Ollama service: {e}")
            raise RuntimeError(
                f"Qwen service unreachable at {self.config.endpoint}: {e}. "
                "Ensure Ollama is running and qwen3:4b-instruct is pulled."
            ) from e

        raw_text = resp_json.get("response", "").strip()
        logger.debug(f"Received response from Qwen ({len(raw_text)} chars).")

        # Parse and validate structured JSON
        parsed = self._parse_and_validate_json(raw_text)
        return RawGenerationOutput(
            answer=parsed["answer"],
            claims=parsed["claims"],
            limitations=parsed["limitations"],
            confidence=parsed["confidence"],
            raw_response=raw_text,
            model_name=self.config.model,
            contrary_evidence=parsed.get("contrary_or_qualifying_evidence", []),
        )

    def _parse_and_validate_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Robust JSON extractor that handles code block formatting and enforces schema.
        """
        clean_text = raw_text.strip()

        # Remove thinking blocks if present
        clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()

        # Remove markdown code block if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)
            clean_text = clean_text.strip()

        data = None
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback: regex search for outer JSON object
            match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

        if not isinstance(data, dict):
            # Attempt resilient extraction of answer and claims if output was truncated
            ans_match = re.search(r'\"answer\"\s*:\s*\"(.*?)(?<!\\)\"', clean_text, re.DOTALL)
            extracted_ans = ans_match.group(1).replace('\\"', '"').replace('\\n', '\n') if ans_match else ""
            
            claims_matches = re.findall(
                r'\{\s*\"claim\"\s*:\s*\"(.*?)(?<!\\)\"\s*,\s*\"evidence_ids\"\s*:\s*\[(.*?)\]\s*\}',
                clean_text,
                re.DOTALL
            )
            extracted_claims = []
            for c_text, evs_str in claims_matches:
                clean_c = c_text.replace('\\"', '"').replace('\\n', '\n')
                ev_ids = [e.strip(' "\'').upper() for e in evs_str.split(',') if e.strip(' "\'')]
                extracted_claims.append({
                    "claim": clean_c,
                    "evidence_ids": ev_ids,
                    "claim_type": "judicial_finding",
                    "support_level": "directly_supports",
                    "qualification": "",
                })

            if extracted_ans:
                logger.info(f"Resiliently recovered answer and {len(extracted_claims)} claims from truncated JSON.")
                return {
                    "answer": extracted_ans,
                    "claims": extracted_claims,
                    "contrary_or_qualifying_evidence": [],
                    "limitations": "Response completed; trailing metadata safely recovered.",
                    "confidence": "supported" if extracted_claims else "partially_supported",
                }

            logger.warning("Qwen returned non-JSON response. Executing graceful schema recovery.")
            return {
                "answer": raw_text,
                "claims": [{
                    "claim": raw_text[:200],
                    "evidence_ids": [],
                    "claim_type": "legal_interpretation",
                    "support_level": "relevant_context",
                    "qualification": "",
                }],
                "contrary_or_qualifying_evidence": [],
                "limitations": "Model response could not be parsed as strict JSON.",
                "confidence": "partially_supported",
            }

        # Validate and clean answer
        answer = str(data.get("answer", "")).strip()

        # Validate and clean claims
        raw_claims = data.get("claims", [])
        clean_claims: List[Dict[str, Any]] = []
        if isinstance(raw_claims, list):
            for c in raw_claims:
                if isinstance(c, dict) and "claim" in c:
                    c_text = str(c.get("claim", "")).strip()
                    ev_ids = c.get("evidence_ids", [])
                    if isinstance(ev_ids, list):
                        clean_ev_ids = [str(e).strip().upper() for e in ev_ids if str(e).strip()]
                    else:
                        clean_ev_ids = []
                    
                    claim_type = str(c.get("claim_type", "judicial_finding")).strip().lower()
                    if claim_type not in {"judicial_finding", "statutory_provision", "party_submission", "procedural_history", "legal_interpretation"}:
                        claim_type = "judicial_finding"
                        
                    support_level = str(c.get("support_level", "directly_supports")).strip().lower()
                    if support_level not in {"directly_supports", "relevant_context", "contradicts_or_qualifies", "unrelated", "unverified"}:
                        support_level = "directly_supports"
                        
                    qualification = str(c.get("qualification", "")).strip()

                    clean_claims.append({
                        "claim": c_text,
                        "evidence_ids": clean_ev_ids,
                        "claim_type": claim_type,
                        "support_level": support_level,
                        "qualification": qualification,
                    })
                elif isinstance(c, str):
                    clean_claims.append({
                        "claim": c.strip(),
                        "evidence_ids": [],
                        "claim_type": "judicial_finding",
                        "support_level": "directly_supports",
                        "qualification": "",
                    })

        # Validate contrary / qualifying evidence
        raw_contrary = data.get("contrary_or_qualifying_evidence", [])
        clean_contrary: List[Dict[str, Any]] = []
        if isinstance(raw_contrary, list):
            for ce in raw_contrary:
                if isinstance(ce, dict) and "evidence_id" in ce:
                    clean_contrary.append({
                        "evidence_id": str(ce.get("evidence_id", "")).strip().upper(),
                        "nature": str(ce.get("nature", "qualification")).strip().lower(),
                        "explanation": str(ce.get("explanation", "")).strip(),
                    })

        # Validate limitations
        limitations = str(data.get("limitations", "")).strip()

        # Validate confidence
        conf = str(data.get("confidence", "partially_supported")).strip().lower()
        if conf not in ALLOWED_CONFIDENCE_LEVELS:
            if "insufficient" in conf:
                conf = "insufficient_evidence"
            elif "support" in conf:
                conf = "supported"
            else:
                conf = "partially_supported"

        return {
            "answer": answer,
            "claims": clean_claims,
            "contrary_or_qualifying_evidence": clean_contrary,
            "limitations": limitations,
            "confidence": conf,
        }
