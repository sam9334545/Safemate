"""Automated test suite for Safemate Safety-First RAG (Retrieval-Augmented Generation).

Covers:
A. Corpus validation and ingestion engine.
B. Lexical BM25 retrieval, jurisdiction filtering, and context limits.
C. LLM provider integration with identical evidence to Groq and Gemini fallback.
D. Deterministic safety priorities, emergency overrides, and credential interception.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.chatbot.rag.bm25 import BM25Index, tokenize
from app.chatbot.rag.engine import RAGEngine
from app.chatbot.rag.ingestion import CorpusIngestionEngine
from app.chatbot.rag.retriever import RAGRetriever
from app.chatbot.rag.schemas import KnowledgeDocument, RetrievedChunk
from app.schemas.chatbot import ChatbotMessageRequest, ChatbotSourceCitation
from app.services.chatbot_service import ChatbotService
from app.services.llm_provider import (
    BaseLLMProvider,
    CascadingLLMProvider,
    GeminiLLMProvider,
    GroqLLMProvider,
    format_prompt_with_evidence,
)


# =============================================================================
# A. Corpus and Ingestion Tests
# =============================================================================

def test_valid_approved_corpus_loads_completely():
    """Verify that all 12 reviewed documents in verified_corpus.json load without errors."""
    engine = CorpusIngestionEngine()
    index, report = engine.load_and_index("verified_corpus.json")

    assert report.accepted_docs == 12
    assert report.rejected_docs == 0
    assert report.skipped_unverified == 0
    assert report.total_chunks >= 12
    assert len(report.errors) == 0
    assert index.corpus_size == report.total_chunks


def test_pending_review_documents_are_strictly_excluded(tmp_path: Path):
    """Ensure documents marked with 'pending_review' are NEVER indexed into production index."""
    test_docs = [
        {
            "document_id": "doc_approved_sample",
            "title": "Approved Guidance Document",
            "topic": "cybercrime",
            "jurisdiction": "IN",
            "source_organization": "Official Agency",
            "source_url": "https://cybercrime.gov.in/test",
            "source_type": "official_portal",
            "text": "This is reviewed and fully approved safety guidance for citizens.",
            "last_verified": "2026-10-24",
            "verification_status": "verified",
        },
        {
            "document_id": "doc_pending_sample",
            "title": "Unverified Draft Law",
            "topic": "safety",
            "jurisdiction": "IN",
            "source_organization": "Unverified Source",
            "source_url": "https://example.org/draft",
            "source_type": "statutory_act",
            "text": "This text is unverified and pending editorial audit.",
            "last_verified": "2026-10-24",
            "verification_status": "pending_review",
        },
    ]

    corpus_file = tmp_path / "mixed_corpus.json"
    with open(corpus_file, "w", encoding="utf-8") as f:
        json.dump(test_docs, f)

    engine = CorpusIngestionEngine(corpus_dir=tmp_path)
    index, report = engine.load_and_index("mixed_corpus.json")

    assert report.accepted_docs == 1
    assert report.skipped_unverified == 1
    assert report.total_chunks == 1
    doc_ids_in_index = [c.document_id for c in index.chunks]
    assert "doc_approved_sample" in doc_ids_in_index
    assert "doc_pending_sample" not in doc_ids_in_index


def test_invalid_metadata_rejected(tmp_path: Path):
    """Test that records missing required fields or having invalid URLs are rejected."""
    bad_docs = [
        {
            "document_id": "bad_no_url",
            "title": "Title with missing URL",
            "topic": "safety",
            "jurisdiction": "IN",
            "source_organization": "Test Org",
            "source_url": "not-a-valid-http-url",  # Invalid URL
            "source_type": "official_portal",
            "text": "Some text content here for testing invalid URL rejection.",
            "last_verified": "2026-10-24",
            "verification_status": "verified",
        },
        {
            "document_id": "bad_short_text",
            "title": "Short",
            "topic": "safety",
            "jurisdiction": "IN",
            "source_organization": "Test Org",
            "source_url": "https://example.org/short",
            "source_type": "official_portal",
            "text": "Too short",  # min_length is 20
            "last_verified": "2026-10-24",
            "verification_status": "verified",
        },
    ]

    corpus_file = tmp_path / "invalid_corpus.json"
    with open(corpus_file, "w", encoding="utf-8") as f:
        json.dump(bad_docs, f)

    engine = CorpusIngestionEngine(corpus_dir=tmp_path)
    index, report = engine.load_and_index("invalid_corpus.json")

    assert report.accepted_docs == 0
    assert report.rejected_docs == 2
    assert len(report.errors) == 2


def test_duplicate_document_ids_are_rejected(tmp_path: Path):
    """Verify duplicate document_id collisions are detected and rejected."""
    dup_docs = [
        {
            "document_id": "doc_duplicate_id",
            "title": "First Version",
            "topic": "cybercrime",
            "jurisdiction": "IN",
            "source_organization": "Test Org",
            "source_url": "https://example.org/doc1",
            "source_type": "official_portal",
            "text": "Valid text length for the first instance of duplicate ID.",
            "last_verified": "2026-10-24",
            "verification_status": "verified",
        },
        {
            "document_id": "doc_duplicate_id",
            "title": "Second Version with same ID",
            "topic": "cybercrime",
            "jurisdiction": "IN",
            "source_organization": "Test Org",
            "source_url": "https://example.org/doc2",
            "source_type": "official_portal",
            "text": "Valid text length for second instance with identical ID.",
            "last_verified": "2026-10-24",
            "verification_status": "verified",
        },
    ]

    corpus_file = tmp_path / "dup_corpus.json"
    with open(corpus_file, "w", encoding="utf-8") as f:
        json.dump(dup_docs, f)

    engine = CorpusIngestionEngine(corpus_dir=tmp_path)
    index, report = engine.load_and_index("dup_corpus.json")

    assert report.accepted_docs == 1
    assert report.rejected_docs == 1
    assert any("Duplicate document ID" in err for err in report.errors)


def test_empty_or_missing_corpus_fails_safely(tmp_path: Path):
    """Empty or missing corpus file should return safe empty index without crashing."""
    engine = CorpusIngestionEngine(corpus_dir=tmp_path)
    index, report = engine.load_and_index("non_existent_corpus.json")

    assert index.corpus_size == 0
    assert len(report.errors) > 0
    matches = index.search("cybercrime", min_score=0.1)
    assert matches == []


def test_source_metadata_preserved_through_chunking():
    """Verify chunk metadata preserves canonical URLs, verification dates, and authority names."""
    doc = KnowledgeDocument(
        document_id="doc_audit_metadata",
        title="Audit Metadata Preservation",
        topic="evidence",
        jurisdiction="IN",
        source_organization="Ministry of Home Affairs",
        source_url="https://cybercrime.gov.in/guidance",
        source_type="official_portal",
        section="Section 63 BSA",
        text=(
            "Paragraph 1: Preserve original metadata and hash values.\n\n"
            "Paragraph 2: Ensure timestamps and device records are maintained intact."
        ),
        last_verified="2026-10-24",
        verification_status="verified",
    )

    engine = CorpusIngestionEngine()
    chunks = engine._chunk_document(doc)

    for chunk in chunks:
        assert chunk.document_id == "doc_audit_metadata"
        assert chunk.source_organization == "Ministry of Home Affairs"
        assert chunk.source_url == "https://cybercrime.gov.in/guidance"
        assert chunk.section == "Section 63 BSA"
        assert chunk.last_verified == "2026-10-24"


# =============================================================================
# B. Retrieval and Ranking Tests
# =============================================================================

def test_cybercrime_questions_retrieve_cybercrime_portal():
    """Query about cybercrime reporting must retrieve National Cyber Crime portal."""
    rag = RAGEngine()
    res = rag.retrieve("How and where do I report cyber harassment online in India?")

    assert res.is_sufficient is True
    assert len(res.chunks) > 0
    doc_ids = [c.document_id for c in res.chunks]
    assert any("cybercrime" in doc_id for doc_id in doc_ids)
    assert res.chunks[0].relevance_score >= 2.0


def test_blackmail_and_morphed_images_retrieve_ncii_tools():
    """Layperson extortion / morphed image query must retrieve StopNCII / IT Act."""
    rag = RAGEngine()
    res = rag.retrieve("Someone is blackmailing me with morphed private nude photos")

    assert res.is_sufficient is True
    doc_ids = [c.document_id for c in res.chunks]
    assert any("stopncii" in doc_id or "it_act" in doc_id for doc_id in doc_ids)


def test_evidence_preservation_retrieves_bsa_guidance():
    """Evidence saving query must retrieve digital evidence preservation standards."""
    rag = RAGEngine()
    res = rag.retrieve("How to save screenshots and chat logs as proof for police complaint?")

    assert res.is_sufficient is True
    doc_ids = [c.document_id for c in res.chunks]
    assert "doc_evidence_preservation_digital" in doc_ids


def test_jurisdiction_filtering():
    """Verify that retrieval strictly respects requested jurisdiction and global tools."""
    rag = RAGEngine()
    # When querying for US/GLOBAL, India-specific police statutes shouldn't dominate
    res = rag.retrieve("Take down explicit intimate photos online", jurisdiction="US")
    for chunk in res.chunks:
        assert chunk.jurisdiction in ("GLOBAL", "US")


def test_unrelated_queries_return_insufficient_evidence():
    """Out-of-domain queries must return is_sufficient=False and empty/filtered chunks."""
    rag = RAGEngine()
    res = rag.retrieve("What is the recipe for baking chocolate cookies?")

    assert res.is_sufficient is False
    assert len(res.chunks) == 0


def test_context_limits_enforced():
    """Retriever must limit results to top_k and enforce character budget."""
    rag = RAGEngine()
    res = rag.retrieve("cybercrime police complaint online reporting", top_k=2)

    assert len(res.chunks) <= 2
    total_chars = sum(len(c.text) for c in res.chunks)
    assert total_chars <= 1800


# =============================================================================
# C. LLM Integration & Provider Cascade Tests
# =============================================================================

def test_prompt_formatter_includes_untrusted_evidence_boundaries():
    """format_prompt_with_evidence must clearly mark retrieved passages as untrusted data."""
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="doc_test",
            title="Evidence Title",
            topic="cybercrime",
            jurisdiction="IN",
            source_organization="MHA",
            source_url="https://cybercrime.gov.in",
            text="Call 1930 for financial cyber fraud.",
            last_verified="2026-10-24",
        )
    ]
    prompt = format_prompt_with_evidence("How do I report fraud?", chunks)

    assert "=== APPROVED KNOWLEDGE PASSAGES (UNTRUSTED CONTENT) ===" in prompt
    assert "Call 1930 for financial cyber fraud." in prompt
    assert "=== USER QUESTION ===" in prompt
    assert "How do I report fraud?" in prompt


@pytest.mark.anyio
async def test_groq_and_gemini_receive_identical_evidence(monkeypatch):
    """Verify Groq and Gemini fallback both receive the exact same user query and evidence."""
    groq_calls = []
    gemini_calls = []

    class MockGroq(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str, evidence=None):
            groq_calls.append({"query": user_query, "evidence": evidence})
            # Groq fails, triggering cascade
            return None

    class MockGemini(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str, evidence=None):
            gemini_calls.append({"query": user_query, "evidence": evidence})
            return "Gemini response with identical evidence."

    cascading = CascadingLLMProvider(providers=[MockGroq(), MockGemini()])
    evidence_text = "Retrieved Passage 1: Call 1930."
    res = await cascading.generate_response("Where do I report fraud?", evidence=evidence_text)

    assert res == "Gemini response with identical evidence."
    assert len(groq_calls) == 1
    assert len(gemini_calls) == 1
    assert groq_calls[0]["query"] == gemini_calls[0]["query"]
    assert groq_calls[0]["evidence"] == gemini_calls[0]["evidence"]


@pytest.mark.anyio
async def test_safe_fallback_when_all_llms_unavailable():
    """When external AI providers are unavailable, ChatbotService returns curated safe fallback."""
    class FailingProvider(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str, evidence=None):
            return None

    service = ChatbotService(llm_provider=FailingProvider())
    req = ChatbotMessageRequest(message="Where do I report cyber harassment in India?", country="IN")
    res = await service.process_message(req)

    assert res.answer_mode == "safe_fallback"
    assert res.fallback_used is True
    assert len(res.sources) > 0
    assert "National Cyber Crime Reporting Portal" in res.text or "cybercrime" in res.text.lower()


# =============================================================================
# D. Safety Priority & Regression Tests
# =============================================================================

@pytest.mark.anyio
async def test_immediate_danger_bypasses_rag_and_llm():
    """Life threats must trigger deterministic emergency guidance immediately, bypassing RAG/LLMs."""
    llm_invoked = False

    class TrackingLLM(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str, evidence=None):
            nonlocal llm_invoked
            llm_invoked = True
            return "Should never be called!"

    service = ChatbotService(llm_provider=TrackingLLM())
    req = ChatbotMessageRequest(message="Help me now, I am in immediate danger, someone is attacking me!")
    res = await service.process_message(req)

    assert llm_invoked is False
    assert res.is_emergency_priority is True
    assert res.answer_mode == "emergency"
    assert "112" in res.text
    assert any(c.choice_id == "choice_call_112" for c in res.choices)


@pytest.mark.anyio
async def test_sensitive_passwords_intercepted_before_transmission():
    """Sensitive passwords/OTPs must be intercepted by safety guard before external transmission."""
    llm_invoked = False

    class TrackingLLM(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str, evidence=None):
            nonlocal llm_invoked
            llm_invoked = True
            return "Should never receive passwords!"

    service = ChatbotService(llm_provider=TrackingLLM())
    req = ChatbotMessageRequest(message="My account was hacked, here is my password and OTP: 123456")
    res = await service.process_message(req)

    assert llm_invoked is False
    assert "Privacy & Security Safeguard" in res.title
    assert "Safemate will never ask you for passwords" in res.text


def test_api_message_endpoint_returns_sources(client: TestClient):
    """Test /api/v1/chatbot/message endpoint returns typed source citations for RAG questions."""
    payload = {"message": "Where can I report cyber harassment in India?", "country": "IN"}
    res = client.post("/api/v1/chatbot/message", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    first_source = data["sources"][0]
    assert "document_id" in first_source
    assert "title" in first_source
    assert "source_organization" in first_source
    assert "source_url" in first_source
    assert first_source["source_url"].startswith("http")
    assert "last_verified" in first_source


def test_chatbot_with_jwt_auth_integration(client: TestClient):
    """Verify chatbot RAG seamlessly integrates with JWT auth while keeping anonymous access open."""
    # 1. Register and login test user
    reg_payload = {"email": "rag_user_test@example.com", "password": "SecurePassword123!"}
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in (201, 400)

    login_res = client.post("/api/v1/auth/login", json=reg_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Authenticated user message with JWT token
    headers = {"Authorization": f"Bearer {token}"}
    auth_msg_res = client.post(
        "/api/v1/chatbot/message",
        json={"message": "How do I preserve screenshots as digital evidence?", "country": "IN"},
        headers=headers,
    )
    assert auth_msg_res.status_code == 200
    auth_data = auth_msg_res.json()
    assert auth_data["session_id"].startswith("user_")
    assert len(auth_data["sources"]) > 0

    # 3. Unauthenticated user message without JWT token (must still succeed for crisis victims)
    anon_msg_res = client.post(
        "/api/v1/chatbot/message",
        json={"message": "How do I preserve screenshots as digital evidence?", "country": "IN"},
    )
    assert anon_msg_res.status_code == 200
    anon_data = anon_msg_res.json()
    assert len(anon_data["sources"]) > 0

