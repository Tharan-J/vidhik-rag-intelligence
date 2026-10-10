"""
Claim-to-Evidence Provenance Resolution Subsystem
=================================================
Maps each generated legal claim and its cited evidence IDs (E1, E2, ...)
back to the authoritative source document, court, case, and paragraph landmarks.
Preserves the complete verification chain: Claim -> Evidence -> Case -> Document.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .evidence import EvidenceItem


def _find_source_pdf(document_id: str) -> Optional[Path]:
    """Locate authentic physical court judgment PDF across known corpus roots."""
    prototype_root = Path(__file__).resolve().parent.parent
    workspace_root = prototype_root.parent
    search_dirs = [
        workspace_root / "research" / "legal_data",
        workspace_root / "frontend" / "public" / "documents",
        workspace_root / "frontend" / "storage" / "documents" / "matters",
        workspace_root / "test",
    ]
    clean = document_id.replace(".pdf", "").strip()
    tokens = [t for t in clean.split("_") if t and not t.startswith("SC") and not t.startswith("HC") and not t.startswith("DC")]
    target_token = "_".join(tokens) if tokens else clean

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for p in s_dir.rglob("*.pdf"):
            if p.name == document_id or p.name == f"{clean}.pdf":
                return p
            if p.name in document_id or clean in p.name:
                return p
            if target_token and len(target_token) >= 5 and target_token in p.name:
                return p
    return None


@dataclass
class CitationAuthority:
    """Detailed provenance metadata for an individual citation reference."""
    evidence_id: str
    document_id: str
    chunk_id: str
    qdrant_point_id: str
    court: str
    court_level: str
    case_title: str
    case_number: str
    decision_date: str
    page_number: str
    paragraph_id: str
    sentence_id: str
    text_snippet: str
    year: Optional[int] = None
    verification_status: str = "UNVERIFIED"
    verified_page: Optional[int] = None
    verified_paragraph: Optional[str] = None
    is_source_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "qdrant_point_id": self.qdrant_point_id,
            "court": self.court,
            "court_level": self.court_level,
            "case_title": self.case_title,
            "case_number": self.case_number,
            "decision_date": self.decision_date,
            "year": self.year,
            "page_number": self.page_number,
            "paragraph_id": self.paragraph_id,
            "sentence_id": self.sentence_id,
            "text_snippet": self.text_snippet,
            "verification_status": self.verification_status,
            "verified_page": self.verified_page,
            "verified_paragraph": self.verified_paragraph,
            "is_source_verified": self.is_source_verified,
        }


@dataclass
class ClaimWithProvenance:
    """A single factual/legal claim with resolved supporting authorities."""
    claim: str
    evidence_ids: List[str]
    authorities: List[CitationAuthority] = field(default_factory=list)
    is_grounded: bool = False
    claim_type: str = "judicial_finding"
    support_level: str = "directly_supports"
    qualification: Optional[str] = None
    citation_verified: bool = False
    verification_status: str = "UNVERIFIED"
    verification_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence_ids": self.evidence_ids,
            "is_grounded": self.is_grounded,
            "authorities": [a.to_dict() for a in self.authorities],
            "claim_type": self.claim_type,
            "support_level": self.support_level,
            "qualification": self.qualification,
            "citation_verified": self.citation_verified,
            "verification_status": self.verification_status,
            "verification_details": self.verification_details,
        }


class ProvenanceResolver:
    """
    Resolves evidence identifiers in generated claims to full provenance records
    and verifies citations against authentic court documents.
    """

    @staticmethod
    def resolve(
        raw_claims: List[Dict[str, Any]],
        evidence_items: List[EvidenceItem],
        verify_citations: bool = True,
    ) -> List[ClaimWithProvenance]:
        """
        Map claim evidence_ids (E1, E2, ...) to source CitationAuthority objects
        and verify against physical PDF manifests.
        """
        from .source_verifier import (
            LegalEvidenceVerifier,
            STATUS_VERIFIED_EXACT,
            STATUS_VERIFIED_NORMALIZED,
            STATUS_COORDINATE_MISMATCH,
            STATUS_PASSAGE_NOT_FOUND,
        )

        verifier = LegalEvidenceVerifier() if verify_citations else None

        # Build quick lookup map by evidence_id
        ev_map: Dict[str, EvidenceItem] = {
            item.evidence_id.upper(): item for item in evidence_items
        }

        resolved_claims: List[ClaimWithProvenance] = []

        for raw_c in raw_claims:
            claim_text = str(raw_c.get("claim", "")).strip()
            ev_ids = [str(eid).strip().upper() for eid in raw_c.get("evidence_ids", [])]
            raw_claim_type = str(raw_c.get("claim_type", "judicial_finding")).strip().lower()
            raw_support_level = str(raw_c.get("support_level", "directly_supports")).strip().lower()
            qualification = str(raw_c.get("qualification", "")).strip() or None

            if raw_claim_type not in {"judicial_finding", "statutory_provision", "party_submission", "procedural_history", "legal_interpretation"}:
                raw_claim_type = "judicial_finding"

            if raw_support_level not in {"directly_supports", "relevant_context", "contradicts_or_qualifies", "unrelated", "unverified"}:
                raw_support_level = "directly_supports"

            authorities: List[CitationAuthority] = []
            claim_citation_verified = False
            best_verification_status = "UNVERIFIED"
            verification_meta: Dict[str, Any] = {}

            for eid in ev_ids:
                if eid in ev_map:
                    ev = ev_map[eid]
                    snippet = ev.text.strip().replace("\r", "")
                    if len(snippet) > 250:
                        snippet = snippet[:250] + "..."

                    # Run source verification on the citation passage
                    auth_verified = False
                    auth_status = "UNVERIFIED"
                    v_page = None
                    v_para = None

                    if verifier is not None:
                        pdf_path = _find_source_pdf(ev.document_id)
                        if pdf_path and pdf_path.exists():
                            # Parse reported page number
                            rep_page = None
                            page_m = re.search(r"\b(\d+)\b", str(ev.page_number or ""))
                            if page_m:
                                rep_page = int(page_m.group(1))

                            v_res = verifier.verify_passage(
                                passage_text=ev.text[:300],
                                reported_page=rep_page,
                                reported_paragraph=ev.paragraph_id,
                                pdf_path=pdf_path,
                            )
                            auth_status = v_res.verification_status
                            v_page = v_res.verified_page
                            v_para = v_res.verified_paragraph
                            auth_verified = v_res.verification_status in (STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED)

                            if auth_verified:
                                claim_citation_verified = True
                                best_verification_status = v_res.verification_status
                                verification_meta = {
                                    "document_id": ev.document_id,
                                    "pdf_path": str(pdf_path),
                                    "verified_page": v_res.verified_page,
                                    "verified_paragraph": v_res.verified_paragraph,
                                    "sha256": v_res.document_sha256,
                                    "similarity_score": v_res.similarity_score,
                                }
                            elif best_verification_status == "UNVERIFIED":
                                best_verification_status = v_res.verification_status
                                verification_meta = {
                                    "document_id": ev.document_id,
                                    "notes": v_res.notes,
                                }

                    auth = CitationAuthority(
                        evidence_id=ev.evidence_id,
                        document_id=ev.document_id,
                        chunk_id=ev.chunk_id,
                        qdrant_point_id=ev.qdrant_point_id,
                        court=ev.court,
                        court_level=ev.court_level,
                        case_title=ev.case_title,
                        case_number=ev.case_number,
                        decision_date=ev.decision_date,
                        year=ev.year,
                        page_number=str(ev.page_number or "1"),
                        paragraph_id=str(ev.paragraph_id or "Holding"),
                        sentence_id=str(ev.sentence_id or ""),
                        text_snippet=snippet,
                        verification_status=auth_status,
                        verified_page=v_page,
                        verified_paragraph=v_para,
                        is_source_verified=auth_verified,
                    )
                    authorities.append(auth)

            is_grounded = len(authorities) > 0
            if not is_grounded:
                raw_support_level = "unverified"

            resolved_claims.append(ClaimWithProvenance(
                claim=claim_text,
                evidence_ids=ev_ids,
                authorities=authorities,
                is_grounded=is_grounded,
                claim_type=raw_claim_type,
                support_level=raw_support_level,
                qualification=qualification,
                citation_verified=claim_citation_verified,
                verification_status=best_verification_status,
                verification_details=verification_meta if verification_meta else None,
            ))

        return resolved_claims
