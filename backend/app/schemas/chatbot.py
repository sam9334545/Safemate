"""Pydantic schemas for the Safemate Safety & Legal Chatbot service."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


from app.chatbot.rag.schemas import ChatbotSourceCitation


class ChatbotHealthResponse(BaseModel):
    """Health and readiness response for the Safety Assistant."""

    status: str = Field("ready", description="Service readiness status")
    guided_flows_available: int = Field(..., description="Number of loaded guided flows")
    verified_resources_count: int = Field(..., description="Number of verified safety resources")
    llm_provider_configured: bool = Field(False, description="Whether an external LLM is configured")
    timestamp: str = Field(..., description="Timestamp of health check")


class SafetyResourceResponse(BaseModel):
    """Public representation of a verified emergency or legal resource."""

    resource_id: str
    country: str
    category: str
    display_name: str
    phone_number: Optional[str] = None
    action_url: Optional[str] = None
    description: str
    intended_use: str
    verification_source: str
    last_verified: str
    availability_caveat: str
    is_emergency: bool = False


class ChatbotResourceListResponse(BaseModel):
    """List of verified resources for a requested country/locale."""

    country: str
    total_count: int
    resources: List[SafetyResourceResponse]


class FlowChoiceResponse(BaseModel):
    """Interactive choice or suggested response chip."""

    choice_id: str
    label: str
    description: Optional[str] = None
    next_step_id: Optional[str] = None
    target_flow_id: Optional[str] = None
    is_emergency: bool = False
    is_terminal: bool = False


class FlowMetadataResponse(BaseModel):
    """Summary metadata of an available guidance flow."""

    flow_id: str
    title: str
    subtitle: str
    category: str
    icon: str
    initial_step_id: str


class ChatbotFlowListResponse(BaseModel):
    """List of available structured safety flows."""

    flows: List[FlowMetadataResponse]


class ChatbotStartRequest(BaseModel):
    """Request to initiate a structured guidance flow."""

    flow_id: str = Field(..., min_length=1, max_length=100, description="ID of the flow to start")
    country: Optional[str] = Field("IN", max_length=10, description="Country code (ISO 3166-1 alpha-2)")
    session_id: Optional[str] = Field(None, max_length=100, description="Optional client session ID")


class ChatbotStartResponse(BaseModel):
    """Initial step returned when launching a flow."""

    session_id: str
    flow_id: str
    step_id: str
    title: str
    guidance: str
    numbered_steps: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    choices: List[FlowChoiceResponse] = Field(default_factory=list)
    resources: List[SafetyResourceResponse] = Field(default_factory=list)
    safemate_feature_link: Optional[str] = None
    safemate_feature_name: Optional[str] = None
    safemate_feature_note: Optional[str] = None
    is_emergency_priority: bool = False
    sources: List[ChatbotSourceCitation] = Field(default_factory=list)


class ChatbotMessageRequest(BaseModel):
    """Message or option selection sent to the Safety Assistant."""

    session_id: Optional[str] = Field(None, max_length=100, description="Session identifier")
    flow_id: Optional[str] = Field(None, max_length=100, description="Current flow identifier")
    step_id: Optional[str] = Field(None, max_length=100, description="Current step identifier")
    choice_id: Optional[str] = Field(None, max_length=100, description="Selected option chip ID")
    message: Optional[str] = Field(None, max_length=1000, description="Optional free-text query")
    country: Optional[str] = Field("IN", max_length=10, description="Country code")


class ChatbotMessageResponse(BaseModel):
    """Assistant response to user selection or message."""

    session_id: str
    flow_id: Optional[str] = None
    step_id: Optional[str] = None
    title: str
    text: str
    numbered_steps: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    choices: List[FlowChoiceResponse] = Field(default_factory=list)
    resources: List[SafetyResourceResponse] = Field(default_factory=list)
    is_complete: bool = False
    is_emergency_priority: bool = False
    safemate_feature_link: Optional[str] = None
    safemate_feature_name: Optional[str] = None
    safemate_feature_note: Optional[str] = None
    sources: List[ChatbotSourceCitation] = Field(
        default_factory=list, description="Verified knowledge sources retrieved for this response"
    )
    answer_mode: Optional[str] = Field(
        "guided", description="Answer generation mode: guided, rag, emergency, or safe_fallback"
    )
    fallback_used: Optional[bool] = Field(
        False, description="Whether fallback mechanism was used"
    )


class ChatbotFeedbackRequest(BaseModel):
    """User feedback on safety guidance accuracy."""

    flow_id: Optional[str] = Field(None, max_length=100)
    step_id: Optional[str] = Field(None, max_length=100)
    rating: Optional[str] = Field(None, max_length=50, description="helpful, confusing, outdated, incorrect")
    comment: Optional[str] = Field(None, max_length=500, description="Feedback comment")


class ChatbotFeedbackResponse(BaseModel):
    """Feedback receipt acknowledgement."""

    status: str = "received"
    message: str = "Thank you for your feedback. We review safety guidance to ensure accuracy."
