"""Automated test suite for Safemate Safety & Legal Chatbot (Feature 4)."""

import pytest
from fastapi.testclient import TestClient

from app.chatbot.knowledge.flows import SAFETY_FLOWS
from app.chatbot.knowledge.resources import VERIFIED_RESOURCES, get_resources_by_country
from app.services.chatbot_service import chatbot_service


# -----------------------------------------------------------------------------
# 1. Health and Discovery Endpoints
# -----------------------------------------------------------------------------
def test_chatbot_health_endpoint(client: TestClient):
    """Test that /api/v1/chatbot/health returns operational readiness."""
    res = client.get("/api/v1/chatbot/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["guided_flows_available"] == 9
    assert data["verified_resources_count"] >= 10
    assert "timestamp" in data
    assert "X-Request-ID" in res.headers


def test_root_lists_chatbot_endpoints(client: TestClient):
    """Ensure root discovery JSON includes chatbot routes."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "chatbot_ui" in data
    assert "chatbot_health" in data
    assert "chatbot_resources" in data
    assert "chatbot_flows" in data
    assert "chatbot_start" in data
    assert "chatbot_message" in data


def test_chatbot_ui_endpoint(client: TestClient):
    """Ensure chatbot web interface is served at /api/v1/chatbot/ui and /chatbot."""
    res_ui = client.get("/api/v1/chatbot/ui")
    assert res_ui.status_code == 200
    assert "Safemate Safety Assistant" in res_ui.text
    assert "text/html" in res_ui.headers.get("content-type", "")

    res_redir = client.get("/chatbot", follow_redirects=False)
    assert res_redir.status_code in (302, 307)
    assert res_redir.headers["location"] == "/api/v1/chatbot/ui"


# -----------------------------------------------------------------------------
# 2. Flows Listing and Starting
# -----------------------------------------------------------------------------
def test_list_all_safety_flows(client: TestClient):
    """Ensure all 9 required guided flows are registered and returned."""
    res = client.get("/api/v1/chatbot/flows")
    assert res.status_code == 200
    data = res.json()
    assert "flows" in data
    assert len(data["flows"]) == 9

    flow_ids = [f["flow_id"] for f in data["flows"]]
    expected_flows = [
        "immediate_danger",
        "online_harassment",
        "blackmail_threats",
        "intimate_image_abuse",
        "impersonation_fake_profile",
        "physical_harassment",
        "report_cybercrime_india",
        "preserve_evidence",
        "understand_options",
    ]
    for ef in expected_flows:
        assert ef in flow_ids


@pytest.mark.parametrize("flow_id", [
    "immediate_danger",
    "online_harassment",
    "blackmail_threats",
    "intimate_image_abuse",
    "impersonation_fake_profile",
    "physical_harassment",
    "report_cybercrime_india",
    "preserve_evidence",
    "understand_options",
])
def test_start_each_flow_successfully(client: TestClient, flow_id: str):
    """Test starting each of the 9 supported flows independently."""
    payload = {"flow_id": flow_id, "country": "IN"}
    res = client.post("/api/v1/chatbot/start", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["flow_id"] == flow_id
    assert "session_id" in data
    assert len(data["title"]) > 0
    assert len(data["guidance"]) > 0
    assert len(data["choices"]) > 0
    assert isinstance(data["resources"], list)


def test_start_unknown_flow_returns_404(client: TestClient):
    """Attempting to start an unregistered flow should return 404."""
    payload = {"flow_id": "non_existent_flow_xyz", "country": "IN"}
    res = client.post("/api/v1/chatbot/start", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 3. Step Transitions and Interactive Choice Traversal
# -----------------------------------------------------------------------------
def test_flow_step_transition(client: TestClient):
    """Test advancing within a flow from one step to the next via choice_id."""
    # Start online_harassment
    res_start = client.post("/api/v1/chatbot/start", json={"flow_id": "online_harassment"})
    data_start = res_start.json()
    assert data_start["step_id"] == "step_harassment_triage"

    # Select documentation choice
    choice_payload = {
        "session_id": data_start["session_id"],
        "flow_id": "online_harassment",
        "step_id": data_start["step_id"],
        "choice_id": "choice_harass_evidence",
    }
    res_step2 = client.post("/api/v1/chatbot/message", json=choice_payload)
    assert res_step2.status_code == 200
    data_step2 = res_step2.json()
    assert data_step2["step_id"] == "step_harassment_document"
    assert "Document Harassment Before Blocking" in data_step2["title"]
    assert any("screenshot" in s.lower() for s in data_step2["numbered_steps"])


def test_cross_flow_transition(client: TestClient):
    """Test transitioning from one flow (e.g., harassment) to another (e.g., immediate_danger)."""
    cross_payload = {
        "flow_id": "online_harassment",
        "step_id": "step_harassment_triage",
        "choice_id": "choice_harass_immed",
    }
    res = client.post("/api/v1/chatbot/message", json=cross_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency_priority"] is True
    assert data["flow_id"] == "immediate_danger"
    assert any(r["phone_number"] == "112" for r in data["resources"])


# -----------------------------------------------------------------------------
# 4. Immediate-Danger Deterministic Safety Logic
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("danger_phrase", [
    "I am in immediate danger right now",
    "Someone is following me down the street",
    "There is an active assault",
    "Help me now, he has a weapon",
    "Urgent help, I'm under attack",
    "Call police someone is breaking in",
])
def test_immediate_danger_triggers_emergency_response(client: TestClient, danger_phrase: str):
    """Ensure any dangerous phrase triggers immediate emergency guidance regardless of current step."""
    payload = {
        "message": danger_phrase,
        "country": "IN",
        "flow_id": "understand_options",
        "step_id": "step_options_overview",
    }
    res = client.post("/api/v1/chatbot/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency_priority"] is True
    assert data["flow_id"] == "immediate_danger"
    assert "112" in data["text"]
    assert any(r["phone_number"] == "112" for r in data["resources"])
    assert any(c["choice_id"] == "choice_call_112" for c in data["choices"])


def test_emergency_accessible_without_auth(client: TestClient):
    """Emergency guidance must be returned with zero auth headers, cookies, or login tokens."""
    payload = {"message": "in danger, need help"}
    res = client.post("/api/v1/chatbot/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency_priority"] is True


# -----------------------------------------------------------------------------
# 5. Verified Resources by Country
# -----------------------------------------------------------------------------
def test_get_india_resources(client: TestClient):
    """Test retrieving verified resources for India."""
    res = client.get("/api/v1/chatbot/resources?country=IN")
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "IN"
    assert data["total_count"] >= 7

    names = [r["display_name"] for r in data["resources"]]
    assert any("112" in n for n in names)
    assert any("181" in n for n in names)
    assert any("cybercrime.gov.in" in n for n in names)
    assert any("1930" in n for n in names)


def test_unknown_country_fallback(client: TestClient):
    """Test retrieving resources for unsupported country returns global verified fallback."""
    res = client.get("/api/v1/chatbot/resources?country=XX")
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "XX"
    # Should still include global fallbacks (StopNCII, TakeItDown, Emergency fallback)
    assert data["total_count"] >= 3
    names = [r["display_name"] for r in data["resources"]]
    assert any("StopNCII" in n for n in names)


# -----------------------------------------------------------------------------
# 6. Safety, Privacy & Abuse Safeguards
# -----------------------------------------------------------------------------
def test_sensitive_passwords_interception(client: TestClient):
    """Assistant intercepts questions about passwords/OTPs with security safeguards."""
    payload = {"message": "Can I give my password and OTP to recover my profile?"}
    res = client.post("/api/v1/chatbot/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Privacy & Security Safeguard" in data["title"]
    assert "never ask you for passwords" in data["text"].lower()


def test_intimate_media_query_does_not_solicit_uploads(client: TestClient):
    """Assistant never asks user to upload explicit photos; routes to NCII guidance."""
    payload = {"message": "Someone has a private photo of me and is threatening to leak it"}
    res = client.post("/api/v1/chatbot/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Guidance should route to blackmail or intimate_image_abuse
    assert data["flow_id"] in ("blackmail_threats", "intimate_image_abuse")
    assert "StopNCII.org" in str(data) or "not at fault" in str(data)


def test_message_length_validation(client: TestClient):
    """Oversized messages (>1000 characters) should be rejected cleanly."""
    long_message = "a" * 1005
    payload = {"message": long_message}
    res = client.post("/api/v1/chatbot/message", json=payload)
    assert res.status_code == 422


def test_no_false_dispatch_claims():
    """Verify that flow guidance explicitly discloses that Safemate does not self-dispatch."""
    danger_flow = SAFETY_FLOWS["immediate_danger"]
    step = danger_flow.steps["step_immediate_action"]
    assert "cannot automatically dispatch" in step.disclaimer


def test_feedback_submission(client: TestClient):
    """Test submitting user feedback on guidance accuracy."""
    payload = {
        "flow_id": "report_cybercrime_india",
        "step_id": "step_cyber_overview",
        "rating": "helpful",
        "comment": "Clear steps for cybercrime.gov.in portal.",
    }
    res = client.post("/api/v1/chatbot/feedback", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "received"


# -----------------------------------------------------------------------------
# 7. Groq LLM Provider & Fallback Mechanics
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_groq_llm_provider_unconfigured():
    """When GROQ_API_KEY is unset, provider returns None and is_configured is False."""
    from app.services.llm_provider import GroqLLMProvider

    provider = GroqLLMProvider(api_key=None)
    assert provider.is_configured is False
    res = await provider.generate_response("How do I stay safe online?")
    assert res is None


@pytest.mark.anyio
async def test_groq_llm_provider_success(monkeypatch):
    """Mock successful Groq API chat completion."""
    from app.services.llm_provider import GroqLLMProvider

    provider = GroqLLMProvider(api_key="gsk_mock_test_key_123")
    assert provider.is_configured is True

    class MockResponse:
        status_code = 200

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Here are 3 practical safety steps: 1. Keep copies. 2. Block. 3. Call 181.",
                        }
                    }
                ]
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json, headers):
            return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    answer = await provider.generate_response("Someone is sending rude messages")
    assert answer is not None
    assert "Call 181" in answer


@pytest.mark.anyio
async def test_groq_llm_provider_timeout_fallback(monkeypatch):
    """When Groq API encounters a timeout, it logs and safely returns None without raising."""
    import httpx
    from app.services.llm_provider import GroqLLMProvider

    provider = GroqLLMProvider(api_key="gsk_mock_key")

    class TimeoutAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json, headers):
            raise httpx.TimeoutException("Mock connection timed out")

    monkeypatch.setattr("httpx.AsyncClient", TimeoutAsyncClient)
    res = await provider.generate_response("Question that times out")
    assert res is None


@pytest.mark.anyio
async def test_chatbot_service_with_mock_groq(monkeypatch):
    """Test ChatbotService integration with an active Groq LLM provider."""
    from app.schemas.chatbot import ChatbotMessageRequest
    from app.services.chatbot_service import ChatbotService
    from app.services.llm_provider import BaseLLMProvider

    class MockLLM(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str):
            return "Here is supportive advice from Groq AI: Document all messages safely."

    service = ChatbotService(llm_provider=MockLLM())
    req = ChatbotMessageRequest(message="What should I do about recurring spam?", country="IN")
    res = await service.process_message(req)

    assert "Here is supportive advice from Groq AI" in res.text
    assert len(res.resources) > 0
    assert any(c.choice_id == "choice_opt_emergency" for c in res.choices)


# -----------------------------------------------------------------------------
# 8. Gemini LLM Provider & Cascading Fallback Tests
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_gemini_llm_provider_unconfigured():
    """When GEMINI_API_KEY is unset, provider returns None and is_configured is False."""
    from app.services.llm_provider import GeminiLLMProvider

    provider = GeminiLLMProvider(api_key=None)
    assert provider.is_configured is False
    res = await provider.generate_response("How do I stay safe online?")
    assert res is None


@pytest.mark.anyio
async def test_gemini_llm_provider_success(monkeypatch):
    """Mock successful Gemini API content generation."""
    from app.services.llm_provider import GeminiLLMProvider

    provider = GeminiLLMProvider(api_key="mock_gemini_key_123")
    assert provider.is_configured is True

    class MockGeminiResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Gemini safety guidance: Save evidence, block profile, and report to 1930 if extortion.",
                                }
                            ]
                        }
                    }
                ]
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json, headers):
            return MockGeminiResponse()

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    answer = await provider.generate_response("Someone is threatening me")
    assert answer is not None
    assert "Gemini safety guidance" in answer


@pytest.mark.anyio
async def test_cascading_provider_fallback_to_gemini():
    """Verify that if Groq fails, CascadingLLMProvider automatically falls back to Gemini."""
    from app.services.llm_provider import BaseLLMProvider, CascadingLLMProvider

    class FailingGroq(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str):
            # Groq experiences timeout or outage
            return None

    class SuccessfulGemini(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str):
            return "Fallback answer from Google Gemini: Here are your safe options."

    cascading = CascadingLLMProvider(providers=[FailingGroq(), SuccessfulGemini()])
    assert cascading.is_configured is True
    answer = await cascading.generate_response("I need safety help")
    assert answer is not None
    assert "Fallback answer from Google Gemini" in answer


@pytest.mark.anyio
async def test_cascading_provider_all_fail_returns_none():
    """When all external AI providers fail, cascading provider returns None so local flows take over."""
    from app.services.llm_provider import BaseLLMProvider, CascadingLLMProvider

    class FailingProvider(BaseLLMProvider):
        @property
        def is_configured(self):
            return True

        async def generate_response(self, user_query: str):
            return None

    cascading = CascadingLLMProvider(providers=[FailingProvider(), FailingProvider()])
    res = await cascading.generate_response("Question")
    assert res is None


