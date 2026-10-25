"""API routes for Safemate Safety & Legal Assistant (/api/v1/chatbot)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models import UserModel
from app.utils.auth import get_optional_current_user
from app.chatbot.knowledge.resources import get_emergency_resources
from app.schemas.chatbot import (
    ChatExportResponse,
    ChatHistoryResponse,
    ChatbotFeedbackRequest,
    ChatbotFeedbackResponse,
    ChatbotFlowListResponse,
    ChatbotHealthResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotResourceListResponse,
    ChatbotStartRequest,
    ChatbotStartResponse,
    ComplaintDraftRequest,
    ComplaintDraftResponse,
    SafetyResourceResponse,
    TellOnceDossierResponse,
    TellOnceTurnRequest,
    TellOnceTurnResponse,
)
from app.services.chatbot_service import chatbot_service
from app.services.tell_once_service import tell_once_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chatbot", tags=["Safety & Legal Chatbot"])


class EmergencyOverrideRequest(BaseModel):
    """Payload for triggering immediate emergency hotline override."""

    country: Optional[str] = Field(
        default="IN",
        description="ISO 3166-1 alpha-2 country code (e.g. IN, US, GB, CA, AU, GLOBAL)",
    )


SUPPORTED_COUNTRIES: List[Dict[str, str]] = [
    {
        "code": "IN",
        "name": "India",
        "emergency_number": "112",
        "women_helpline": "1091 / 181",
        "cybercrime_portal": "1930 (cybercrime.gov.in)",
    },
    {
        "code": "US",
        "name": "United States",
        "emergency_number": "911",
        "women_helpline": "1-800-799-7233 (NDVH)",
        "cybercrime_portal": "ic3.gov",
    },
    {
        "code": "GB",
        "name": "United Kingdom",
        "emergency_number": "999",
        "women_helpline": "0808 2000 247 (Refuge)",
        "cybercrime_portal": "actionfraud.police.uk",
    },
    {
        "code": "CA",
        "name": "Canada",
        "emergency_number": "911",
        "women_helpline": "1-866-863-0511 (Assaulted Women's Helpline)",
        "cybercrime_portal": "antifraudcentre-centreantifraude.ca",
    },
    {
        "code": "AU",
        "name": "Australia",
        "emergency_number": "000",
        "women_helpline": "1800 737 732 (1800RESPECT)",
        "cybercrime_portal": "cyber.gov.au",
    },
    {
        "code": "GLOBAL",
        "name": "International Fallback",
        "emergency_number": "112 / 911 / 999",
        "women_helpline": "StopNCII.org",
        "cybercrime_portal": "takeitdown.ncmec.org",
    },
]


@router.get(
    "/countries",
    summary="List Supported Countries for Localized Safety Hotlines",
    description="Returns list of supported countries with their national emergency, women helpline, and cybercrime reporting contacts.",
)
async def list_supported_countries() -> List[Dict[str, str]]:
    """Return list of countries supported by the safety knowledge engine."""
    return SUPPORTED_COUNTRIES


@router.post(
    "/emergency-override",
    summary="Direct Emergency Hotline Override",
    description="Immediate non-LLM safety circuit breaker returning official emergency hotlines and rapid actions.",
)
async def emergency_override(
    payload: Optional[EmergencyOverrideRequest] = None,
) -> Dict[str, Any]:
    """Provide instant deterministic emergency resources and guidelines."""
    country = (payload.country if payload and payload.country else "IN").strip().upper()
    resources = get_emergency_resources(country)
    return {
        "status": "EMERGENCY_OVERRIDE_ACTIVATED",
        "guidance": (
            "🚨 CRITICAL SAFETY INTERRUPT: If you are in immediate danger, please contact local emergency authorities "
            "immediately or activate your SafeMate Emergency SOS button."
        ),
        "country": country,
        "emergency_resources": [
            {
                "resource_id": r.resource_id,
                "display_name": r.display_name,
                "phone_number": r.phone_number,
                "action_url": r.action_url,
                "description": r.description,
                "intended_use": r.intended_use,
            }
            for r in resources
        ],
    }


@router.get("/health", response_model=ChatbotHealthResponse, summary="Chatbot readiness health check")
async def get_chatbot_health() -> ChatbotHealthResponse:
    """Verify service readiness and availability of the guided knowledge base."""
    return chatbot_service.get_health()


@router.get(
    "/resources",
    response_model=ChatbotResourceListResponse,
    summary="List verified safety resources by country",
)
async def get_safety_resources(
    country: str = Query("IN", description="ISO 3166-1 alpha-2 country code (default: IN)")
) -> ChatbotResourceListResponse:
    """Return curated, verified emergency, cybercrime, and women helpline resources."""
    return chatbot_service.get_resources_for_country(country)


@router.get(
    "/flows",
    response_model=ChatbotFlowListResponse,
    summary="List available guided safety flows",
)
async def list_safety_flows() -> ChatbotFlowListResponse:
    """List available structured guidance situations and starting metadata."""
    flows = chatbot_service.list_flow_metadata()
    return ChatbotFlowListResponse(flows=flows)


@router.post(
    "/start",
    response_model=ChatbotStartResponse,
    summary="Start a specific guided safety flow",
)
async def start_safety_flow(
    request: ChatbotStartRequest,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> ChatbotStartResponse:
    """Initialize a structured flow by flow_id and return its entry step."""
    if current_user and not request.session_id:
        request.session_id = f"user_{current_user.id}"
    try:
        return chatbot_service.start_flow(request)
    except ValueError as e:
        logger.warning(f"Failed to start flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requested flow '{request.flow_id}' not found.",
        )


@router.post(
    "/message",
    response_model=ChatbotMessageResponse,
    summary="Send message or select structured option chip",
)
async def send_chatbot_message(
    request: ChatbotMessageRequest,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> ChatbotMessageResponse:
    """Submit a structured choice or text question to the safety assistant.
    
    Safety Guarantee: Immediate physical danger triggers deterministic emergency
    guidance regardless of ongoing flow, authentication state, or model state.
    """
    if current_user and not request.session_id:
        request.session_id = f"user_{current_user.id}"
    return await chatbot_service.process_message(request)


@router.post(
    "/feedback",
    response_model=ChatbotFeedbackResponse,
    summary="Submit feedback on safety guidance",
)
async def submit_feedback(
    request: ChatbotFeedbackRequest,
) -> ChatbotFeedbackResponse:
    """Submit optional feedback regarding outdated or confusing safety guidance."""
    return chatbot_service.record_feedback(request)


@router.post(
    "/draft-complaint",
    response_model=ComplaintDraftResponse,
    summary="Draft Structured Legal Complaint / Zero FIR",
    description="Generate a formal, ready-to-file police complaint / Zero FIR letter citing exact penal provisions (IT Act 66E/67/67A, BNS 78/79/351, CrPC 154 / BNSS 173).",
)
async def draft_complaint(
    request: ComplaintDraftRequest,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> ComplaintDraftResponse:
    """Generate a formal statutory Zero FIR / cyber crime complaint draft."""
    if current_user and (not request.complainant_name or request.complainant_name.startswith("Concerned Citizen")):
        request.complainant_name = current_user.full_name or current_user.email
    return chatbot_service.generate_complaint_draft(request)


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Retrieve Chat Session Message History",
    description="Fetch sequential interaction history recorded for a given session ID.",
)
async def get_chat_history(
    session_id: str,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> ChatHistoryResponse:
    """Return past message turns for multi-turn assistant context."""
    if session_id.startswith("user_"):
        if not current_user or session_id != f"user_{current_user.id}":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access another user's chat session history.",
            )
    return chatbot_service.get_history(session_id)


@router.delete(
    "/history/{session_id}",
    summary="Clear Chat Session History (Privacy Wipe)",
    description="Instantly delete session message history for emergency privacy protection.",
)
async def clear_chat_history(
    session_id: str,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Wipe session history immediately upon user request or panic trigger."""
    if session_id.startswith("user_"):
        if not current_user or session_id != f"user_{current_user.id}":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to clear another user's chat session history.",
            )
    cleared = chatbot_service.clear_history(session_id)
    return {
        "status": "cleared" if cleared else "not_found",
        "session_id": session_id,
        "message": "Chat session history wiped successfully." if cleared else "Session history was already empty.",
    }


@router.get(
    "/export/{session_id}",
    response_model=ChatExportResponse,
    summary="Export Safety Consultation Incident Report",
    description="Generate a structured, printable report of the session advice, evidence preservation tips, and emergency helplines.",
)
async def export_chat_report(
    session_id: str,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
) -> ChatExportResponse:
    """Export formatted consultation summary for police, legal counsel, or personal records."""
    if session_id.startswith("user_"):
        if not current_user or session_id != f"user_{current_user.id}":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to export another user's chat session report.",
            )
    return chatbot_service.export_report(session_id)


@router.get("/ui", response_class=HTMLResponse, summary="Safemate Chatbot Web Interface")
async def get_chatbot_ui():
    """Serve the standalone interactive web interface for the Safety Assistant."""
    static_file = Path(__file__).resolve().parent.parent.parent / "static" / "chatbot" / "index.html"
    if static_file.exists():
        return HTMLResponse(content=static_file.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="""<!DOCTYPE html><html><body><h1>Safemate Safety Assistant</h1>
        <p>Chatbot API is operational. Visit <a href="/docs">/docs</a> for API specifications.</p>
        </body></html>"""
    )


# -----------------------------------------------------------------------------
# Tell-Once Trauma-Informed Intake Endpoints
# -----------------------------------------------------------------------------
@router.post(
    "/tell-once/start",
    response_model=TellOnceTurnResponse,
    summary="Start Trauma-Informed Tell-Once Intake",
    description="Initializes a gentle, trauma-informed intake session where the survivor only tells their story once in Hindi or English.",
)
async def start_tell_once(
    language: str = Query("en", description="Preferred language: 'en' or 'hi'"),
) -> TellOnceTurnResponse:
    """Initialize single intake flow with gentle safety check."""
    return tell_once_service.start_intake(language=language)


@router.post(
    "/tell-once/turn",
    response_model=TellOnceTurnResponse,
    summary="Advance Tell-Once Intake Turn",
    description="Submits the survivor's response or breather request for the current intake question and advances to the next gentle prompt.",
)
async def advance_tell_once_turn(
    payload: TellOnceTurnRequest,
) -> TellOnceTurnResponse:
    """Process current turn answers or breathe pause request."""
    return await tell_once_service.process_turn(payload)


@router.get(
    "/tell-once/{intake_id}/dossier",
    response_model=TellOnceDossierResponse,
    summary="Compile Multi-Agency Tell-Once Dossier",
    description="Generates the 3-in-1 dossier: Police Zero FIR (BNSS 173), Cyber 1930 Helpline brief, and Lawyer case brief from the single intake session.",
)
async def get_tell_once_dossier(
    intake_id: str,
) -> TellOnceDossierResponse:
    """Synthesize multi-agency legal & crisis response dossier."""
    return tell_once_service.compile_dossier(intake_id)
