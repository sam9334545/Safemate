"""Safemate Safety-First RAG (Retrieval-Augmented Generation) package.

Provides modular, lightweight lexical retrieval over audited legal and safety knowledge
to complement existing deterministic safety checks and structured flows.
"""

from .schemas import (
    KnowledgeDocument,
    RetrievedChunk,
    RetrievalResult,
    ChatbotSourceCitation,
)

__all__ = [
    "KnowledgeDocument",
    "RetrievedChunk",
    "RetrievalResult",
    "ChatbotSourceCitation",
]
