"""Pydantic data schemas for Safemate RAG (Retrieval-Augmented Generation) system."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class KnowledgeDocument(BaseModel):
    """Source authority document in the verified safety and legal corpus."""

    document_id: str = Field(..., min_length=3, description="Stable unique document identifier")
    title: str = Field(..., min_length=3, description="Document or section title")
    topic: str = Field(..., description="safety, cybercrime, blackmail, ncii, physical_safety, legal_aid, evidence")
    jurisdiction: str = Field(default="IN", description="ISO 3166-1 alpha-2 or GLOBAL")
    source_organization: str = Field(..., description="Authoritative publisher or government body")
    source_url: str = Field(..., description="Canonical reference URL")
    source_type: str = Field(..., description="official_portal, statutory_act, helpline_service, ngo_tool")
    section: Optional[str] = Field(None, description="Relevant statutory section or portal subsection")
    text: str = Field(..., min_length=20, description="Reviewed passage text")
    last_verified: str = Field(..., description="YYYY-MM-DD verification date")
    verification_status: str = Field(
        default="verified", description="'verified' or 'pending_review'"
    )
    effective_date: Optional[str] = Field(None, description="Enactment or policy effective date")
    review_notes: Optional[str] = Field(None, description="Reviewer audit comments")
    version: Optional[str] = Field("1.0", description="Corpus document version")


class RetrievedChunk(BaseModel):
    """Individual searchable knowledge chunk with preserved source metadata."""

    chunk_id: str
    document_id: str
    title: str
    topic: str
    jurisdiction: str
    source_organization: str
    source_url: str
    section: Optional[str] = None
    text: str
    last_verified: str
    relevance_score: float = 0.0


class RetrievalResult(BaseModel):
    """Output from the retrieval engine."""

    query: str
    jurisdiction: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    is_sufficient: bool = False
    top_score: float = 0.0
    total_chunks_matched: int = 0


class ChatbotSourceCitation(BaseModel):
    """Public citation metadata attached to chatbot responses."""

    document_id: str
    title: str
    source_organization: str
    source_url: str
    section: Optional[str] = None
    last_verified: str
