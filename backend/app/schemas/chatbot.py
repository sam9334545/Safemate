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
    language: Optional[str] = Field("en", max_length=10, description="Language code ('en', 'hi', 'mr', 'ta', 'te', 'bn')")


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
    language: Optional[str] = Field("en", description="Language code of the response")
    audio_summary: Optional[str] = Field(None, description="Concise text suitable for audio voice readout")


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


# -----------------------------------------------------------------------------
# Legal Assistance & FIR Drafter Schemas
# -----------------------------------------------------------------------------
class ComplaintDraftRequest(BaseModel):
    """Payload to generate a customized legal Zero FIR / Cyber Crime Complaint letter."""

    incident_type: str = Field(
        ...,
        description="Type of incident: 'cyber_blackmail', 'stalking_harassment', 'ncii_morph_leak', 'fake_profile', 'physical_threat', 'domestic_violence'",
        examples=["cyber_blackmail"],
    )
    complainant_name: Optional[str] = Field(
        default="Concerned Citizen (Confidential)",
        description="Name of complainant (or 'Anonymous')",
        examples=["Priya Sharma"],
    )
    incident_date: Optional[str] = Field(
        default=None,
        description="Date and approximate time of the incident",
        examples=["24 October 2026, approx 8:30 PM"],
    )
    platform_or_location: Optional[str] = Field(
        default="Instagram & WhatsApp",
        description="Platform where cyber harassment occurred or physical address",
        examples=["Instagram & Telegram"],
    )
    accused_details: Optional[str] = Field(
        default="Unknown user handle @stalker_xyz / mobile +91-XXXXXXXXXX",
        description="Known information about the perpetrator",
        examples=["User handle @stalker_xyz / Phone +91-9876543210"],
    )
    incident_summary: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Factual summary of what occurred",
        examples=["Received threatening messages demanding monetary extortion to prevent circulating morphed photographs."],
    )
    sections_requested: Optional[List[str]] = Field(
        default_factory=list,
        description="Specific legal provisions to explicitly cite",
    )
    city_state: Optional[str] = Field(
        default="New Delhi, India",
        description="Jurisdiction city and state",
        examples=["Bengaluru, Karnataka"],
    )


class ComplaintDraftResponse(BaseModel):
    """Formal structured complaint / Zero FIR draft response."""

    status: str = "success"
    incident_type: str
    title: str
    applicable_sections: List[str]
    complaint_letter: str
    instructions: List[str]
    helplines: List[str]
    disclaimer: str


# -----------------------------------------------------------------------------
# Conversation History & Session Management Schemas
# -----------------------------------------------------------------------------
class ChatMessageItem(BaseModel):
    """Single turn message item in session history."""

    sender: str = Field(..., description="'user' or 'assistant'")
    text: str = Field(..., description="Message text")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    title: Optional[str] = None
    is_emergency: bool = False


class ChatHistoryResponse(BaseModel):
    """Thread history for a given conversation session."""

    session_id: str
    total_messages: int
    messages: List[ChatMessageItem]


class ChatExportResponse(BaseModel):
    """Structured export of conversation history for legal or support reference."""

    session_id: str
    generated_at: str
    total_messages: int
    formatted_report: str
    helplines_summary: List[str]

