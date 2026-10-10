"""
Vidhik Multilingual Legal Representation Subsystem
"""

from .entity_protector import LegalEntityProtector, CONTROLLED_LEGAL_GLOSSARY
from .indictrans_service import IndicTrans2Service, SUPPORTED_LANGUAGES
from .verifier import DeterministicLegalVerifier
from .pipeline import LegalTranslationPipeline

__all__ = [
    "LegalEntityProtector",
    "CONTROLLED_LEGAL_GLOSSARY",
    "IndicTrans2Service",
    "SUPPORTED_LANGUAGES",
    "DeterministicLegalVerifier",
    "LegalTranslationPipeline",
]
