"""API routes for Safemate Safety & Legal Assistant (/api/v1/chatbot)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse

from app.models import UserModel
from app.utils.auth import get_optional_current_user
from app.schemas.chatbot import (
    ChatbotFeedbackRequest,
    ChatbotFeedbackResponse,
    ChatbotFlowListResponse,
    ChatbotHealthResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotResourceListResponse,
    ChatbotStartRequest,
    ChatbotStartResponse,
)
from app.services.chatbot_service import chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chatbot", tags=["Safety & Legal Chatbot"])


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
