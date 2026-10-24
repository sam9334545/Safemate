"""Jurisdiction-aware lexical retriever with relevance thresholds and context budgeting."""

from __future__ import annotations

import logging
from typing import List, Optional, Set

from app.chatbot.rag.bm25 import BM25Index
from app.chatbot.rag.schemas import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves authoritative knowledge passages using BM25 ranking and strict safety thresholds."""

    def __init__(
        self,
        index: BM25Index,
        min_score: float = 2.0,
        default_top_k: int = 3,
        max_context_chars: int = 1800,
    ) -> None:
        self.index = index
        self.min_score = min_score
        self.default_top_k = default_top_k
        self.max_context_chars = max_context_chars

    def retrieve(
        self,
        query: str,
        jurisdiction: str = "IN",
        topic: Optional[str] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> RetrievalResult:
        """Retrieve relevant knowledge chunks matching query, jurisdiction, and topic."""
        k = top_k or self.default_top_k
        cutoff = min_score if min_score is not None else self.min_score
        clean_jurisdiction = (jurisdiction or "IN").strip().upper()

        clean_query = query.strip()
        if not clean_query:
            return RetrievalResult(
                query=query,
                jurisdiction=clean_jurisdiction,
                chunks=[],
                is_sufficient=False,
                top_score=0.0,
                total_chunks_matched=0,
            )

        # BM25 search
        matches = self.index.search(
            query=clean_query,
            jurisdiction=clean_jurisdiction,
            topic=topic,
            top_k=k * 2,  # Fetch slightly more to allow deduplication
            min_score=cutoff,
        )

        if not matches:
            return RetrievalResult(
                query=query,
                jurisdiction=clean_jurisdiction,
                chunks=[],
                is_sufficient=False,
                top_score=0.0,
                total_chunks_matched=0,
            )

        top_score = matches[0][1]

        # Deduplicate by document_id and enforce context budget (max chunks & character budget)
        selected_chunks: List[RetrievedChunk] = []
        seen_docs: Set[str] = set()
        accumulated_chars = 0

        for chunk, score in matches:
            if chunk.document_id in seen_docs:
                continue

            chunk_len = len(chunk.text)
            if accumulated_chars + chunk_len > self.max_context_chars and selected_chunks:
                # Stop if adding this chunk exceeds max context budget
                break

            chunk_copy = chunk.model_copy()
            chunk_copy.relevance_score = round(score, 3)
            selected_chunks.append(chunk_copy)
            seen_docs.add(chunk.document_id)
            accumulated_chars += chunk_len

            if len(selected_chunks) >= k:
                break

        is_sufficient = len(selected_chunks) > 0 and top_score >= cutoff

        return RetrievalResult(
            query=query,
            jurisdiction=clean_jurisdiction,
            chunks=selected_chunks,
            is_sufficient=is_sufficient,
            top_score=round(top_score, 3),
            total_chunks_matched=len(matches),
        )
