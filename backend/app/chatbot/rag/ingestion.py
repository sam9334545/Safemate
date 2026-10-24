"""Corpus ingestion, validation, and chunking pipeline for Safemate RAG."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from pydantic import ValidationError

from app.chatbot.rag.bm25 import BM25Index
from app.chatbot.rag.schemas import KnowledgeDocument, RetrievedChunk

logger = logging.getLogger(__name__)


class IngestionReport:
    """Audit report of corpus validation and indexing outcome."""

    def __init__(self) -> None:
        self.accepted_docs: int = 0
        self.rejected_docs: int = 0
        self.skipped_unverified: int = 0
        self.total_chunks: int = 0
        self.errors: List[str] = []

    def summary(self) -> Dict[str, int]:
        return {
            "accepted_docs": self.accepted_docs,
            "rejected_docs": self.rejected_docs,
            "skipped_unverified": self.skipped_unverified,
            "total_chunks": self.total_chunks,
            "error_count": len(self.errors),
        }


class CorpusIngestionEngine:
    """Validates source corpus, splits passages safely, and builds local BM25 index."""

    def __init__(self, corpus_dir: Optional[Path] = None, max_chunk_chars: int = 700) -> None:
        self.corpus_dir = (
            corpus_dir or Path(__file__).resolve().parent / "corpus"
        )
        self.max_chunk_chars = max_chunk_chars
        self.index = BM25Index()
        self.chunks: List[RetrievedChunk] = []
        self.report = IngestionReport()

    def load_and_index(self, corpus_file: Optional[str] = "verified_corpus.json") -> Tuple[BM25Index, IngestionReport]:
        """Load, validate, chunk, and index the approved corpus."""
        self.report = IngestionReport()
        self.chunks = []
        file_path = self.corpus_dir / corpus_file if corpus_file else None

        if not file_path or not file_path.exists():
            msg = f"Corpus file not found: {file_path}"
            logger.error(msg)
            self.report.errors.append(msg)
            self.index.build_index([])
            return self.index, self.report

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_records = json.load(f)
        except Exception as e:
            msg = f"Failed to parse JSON corpus: {e}"
            logger.error(msg)
            self.report.errors.append(msg)
            self.index.build_index([])
            return self.index, self.report

        if not isinstance(raw_records, list):
            msg = f"Corpus JSON root must be a list of documents, got {type(raw_records).__name__}"
            self.report.errors.append(msg)
            self.index.build_index([])
            return self.index, self.report

        seen_doc_ids: Set[str] = set()

        for idx, item in enumerate(raw_records):
            # 1. Pydantic schema validation
            try:
                doc = KnowledgeDocument(**item)
            except ValidationError as ve:
                self.report.rejected_docs += 1
                self.report.errors.append(f"Record #{idx} validation error: {ve}")
                continue
            except Exception as ex:
                self.report.rejected_docs += 1
                self.report.errors.append(f"Record #{idx} malformed: {ex}")
                continue

            # 2. Strict verification status check: reject unverified/pending from production index
            if doc.verification_status != "verified":
                self.report.skipped_unverified += 1
                logger.info(
                    f"Excluding unverified document '{doc.document_id}' (status: {doc.verification_status})"
                )
                continue

            # 3. Duplicate document ID detection
            if doc.document_id in seen_doc_ids:
                self.report.rejected_docs += 1
                self.report.errors.append(f"Duplicate document ID detected: {doc.document_id}")
                continue
            seen_doc_ids.add(doc.document_id)

            # 4. Source URL validation
            if not doc.source_url.startswith(("https://", "http://")):
                self.report.rejected_docs += 1
                self.report.errors.append(f"Invalid URL for '{doc.document_id}': {doc.source_url}")
                continue

            # 5. Chunking passage while preserving metadata
            doc_chunks = self._chunk_document(doc)
            self.chunks.extend(doc_chunks)
            self.report.accepted_docs += 1

        self.report.total_chunks = len(self.chunks)
        # 6. Build lexical BM25 index
        self.index.build_index(self.chunks)
        logger.info(
            f"Corpus ingestion complete: {self.report.accepted_docs} docs accepted, "
            f"{self.report.skipped_unverified} unverified skipped, {len(self.chunks)} chunks indexed."
        )
        return self.index, self.report

    def _chunk_document(self, doc: KnowledgeDocument) -> List[RetrievedChunk]:
        """Split long passages along paragraphs or sentences while preserving metadata."""
        text = doc.text.strip()
        # If text is within comfortable size limit, keep as single atomic chunk
        if len(text) <= self.max_chunk_chars:
            return [
                RetrievedChunk(
                    chunk_id=f"{doc.document_id}_c0",
                    document_id=doc.document_id,
                    title=doc.title,
                    topic=doc.topic,
                    jurisdiction=doc.jurisdiction,
                    source_organization=doc.source_organization,
                    source_url=doc.source_url,
                    section=doc.section,
                    text=text,
                    last_verified=doc.last_verified,
                )
            ]

        # Split along paragraph breaks or sentence boundaries
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[RetrievedChunk] = []

        curr_text = ""
        chunk_idx = 0

        for p in paragraphs:
            if len(curr_text) + len(p) + 2 <= self.max_chunk_chars:
                curr_text = f"{curr_text}\n\n{p}" if curr_text else p
            else:
                if curr_text:
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=f"{doc.document_id}_c{chunk_idx}",
                            document_id=doc.document_id,
                            title=doc.title,
                            topic=doc.topic,
                            jurisdiction=doc.jurisdiction,
                            source_organization=doc.source_organization,
                            source_url=doc.source_url,
                            section=doc.section,
                            text=curr_text.strip(),
                            last_verified=doc.last_verified,
                        )
                    )
                    chunk_idx += 1
                curr_text = p

        if curr_text:
            chunks.append(
                RetrievedChunk(
                    chunk_id=f"{doc.document_id}_c{chunk_idx}",
                    document_id=doc.document_id,
                    title=doc.title,
                    topic=doc.topic,
                    jurisdiction=doc.jurisdiction,
                    source_organization=doc.source_organization,
                    source_url=doc.source_url,
                    section=doc.section,
                    text=curr_text.strip(),
                    last_verified=doc.last_verified,
                )
            )

        return chunks
