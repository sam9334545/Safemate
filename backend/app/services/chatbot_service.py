"""Chatbot service providing structured safety, legal, and cybercrime guidance."""

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.chatbot.knowledge.flows import (
    FlowChoice,
    FlowStep,
    SafetyFlow,
    get_flow,
    list_flows,
)
from app.chatbot.knowledge.resources import (
    SafetyResource,
    VERIFIED_RESOURCES,
    get_emergency_resources,
    get_resources_by_country,
)
from app.schemas.chatbot import (
    ChatbotFeedbackRequest,
    ChatbotFeedbackResponse,
    ChatbotHealthResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotResourceListResponse,
    ChatbotSourceCitation,
    ChatbotStartRequest,
    ChatbotStartResponse,
    FlowChoiceResponse,
    FlowMetadataResponse,
    SafetyResourceResponse,
)
from app.chatbot.rag.engine import RAGEngine, get_rag_engine
from app.services.llm_provider import BaseLLMProvider, get_llm_provider

# -----------------------------------------------------------------------------
# Emergency & Risk Detection Keywords (Deterministic Safety Engine)
# -----------------------------------------------------------------------------
EMERGENCY_TRIGGER_PATTERNS = [
    r"\bimmediate danger\b",
    r"\bin danger\b",
    r"\blife threat\b",
    r"\bthreat to life\b",
    r"\bbeing followed\b",
    r"\bsomeone is following me\b",
    r"\bhelp me now\b",
    r"\burgent help\b",
    r"\bactive assault\b",
    r"\battacked\b",
    r"\bunder attack\b",
    r"\bphysical danger\b",
    r"\bkill me\b",
    r"\bgoing to hurt me\b",
    r"\bhe has a knife\b",
    r"\bweapon\b",
    r"\bemergency\b",
    r"\bcall police\b",
    r"\bdial 112\b",
    r"\bbeing abused physically\b",
    r"\bbreaking in\b",
    r"\bstalker outside\b",
]

SENSITIVE_SECRET_PATTERNS = [
    r"\bpasswords?\b",
    r"\botps?\b",
    r"\bpin codes?\b",
    r"\bpins?\b",
    r"\bcvvs?\b",
    r"\bprivate photos?\b",
    r"\bnudes?\b",
    r"\bexplicit videos?\b",
]


class ChatbotService:
    """Service orchestrating safety guidance, emergency interventions, and flow transitions."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        rag_engine: Optional[RAGEngine] = None,
    ):
        self._emergency_regex = re.compile(
            "|".join(EMERGENCY_TRIGGER_PATTERNS), re.IGNORECASE
        )
        self.llm_provider = llm_provider or get_llm_provider()
        self.rag_engine = rag_engine or get_rag_engine()

    def check_immediate_danger(self, message: str) -> bool:
        """Deterministically check if message contains immediate physical threat keywords."""
        if not message:
            return False
        return bool(self._emergency_regex.search(message))

    def get_health(self) -> ChatbotHealthResponse:
        """Return operational readiness and knowledge catalog count."""
        flows = list_flows()
        resources = VERIFIED_RESOURCES
        return ChatbotHealthResponse(
            status="ready",
            guided_flows_available=len(flows),
            verified_resources_count=len(resources),
            llm_provider_configured=self.llm_provider.is_configured,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_resources_for_country(
        self, country_code: str = "IN"
    ) -> ChatbotResourceListResponse:
        """Retrieve verified resources filtered by country with global fallback."""
        resources = get_resources_by_country(country_code)
        response_items = [
            SafetyResourceResponse(**res.model_dump()) for res in resources
        ]
        return ChatbotResourceListResponse(
            country=country_code.strip().upper(),
            total_count=len(response_items),
            resources=response_items,
        )

    def list_flow_metadata(self) -> List[FlowMetadataResponse]:
        """List metadata for all supported safety guidance flows."""
        flows = list_flows()
        return [
            FlowMetadataResponse(
                flow_id=f.flow_id,
                title=f.title,
                subtitle=f.subtitle,
                category=f.category,
                icon=f.icon,
                initial_step_id=f.initial_step_id,
            )
            for f in flows
        ]

    def start_flow(self, request: ChatbotStartRequest) -> ChatbotStartResponse:
        """Initialize a structured safety flow from its entry step."""
        flow = get_flow(request.flow_id)
        if not flow:
            raise ValueError(f"Unknown safety flow ID: {request.flow_id}")

        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        initial_step = flow.steps.get(flow.initial_step_id)
        if not initial_step:
            raise ValueError(f"Flow {request.flow_id} has invalid initial step: {flow.initial_step_id}")

        # Resolve recommended resources
        resolved_resources = self._resolve_resources(
            initial_step.recommended_resource_ids, request.country or "IN"
        )

        # Convert choices to response schemas
        choices_response = [
            FlowChoiceResponse(**choice.model_dump())
            for choice in initial_step.choices
        ]

        return ChatbotStartResponse(
            session_id=session_id,
            flow_id=flow.flow_id,
            step_id=initial_step.step_id,
            title=initial_step.title,
            guidance=initial_step.guidance,
            numbered_steps=initial_step.numbered_steps,
            disclaimer=initial_step.disclaimer,
            choices=choices_response,
            resources=resolved_resources,
            safemate_feature_link=initial_step.safemate_feature_link,
            safemate_feature_name=initial_step.safemate_feature_name,
            safemate_feature_note=initial_step.safemate_feature_note,
            is_emergency_priority=(flow.flow_id == "immediate_danger"),
        )

    async def process_message(self, request: ChatbotMessageRequest) -> ChatbotMessageResponse:
        """Process incoming user interaction (choice chip selection or free-text query)."""
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        country = request.country or "IN"
        user_text = (request.message or "").strip()

        # ---------------------------------------------------------------------
        # 1. IMMEDIATE DANGER INTERRUPT: Deterministic check overrides all
        # ---------------------------------------------------------------------
        if self.check_immediate_danger(user_text):
            return self._build_immediate_danger_response(session_id, country)

        # ---------------------------------------------------------------------
        # 2. CHOICE CHIP SELECTION
        # ---------------------------------------------------------------------
        if request.choice_id:
            return self._handle_choice_selection(
                choice_id=request.choice_id,
                current_flow_id=request.flow_id,
                current_step_id=request.step_id,
                session_id=session_id,
                country=country,
            )

        # ---------------------------------------------------------------------
        # 3. FREE-TEXT INTENT MATCHING, RAG RETRIEVAL & LLM / FALLBACK LAYER
        # ---------------------------------------------------------------------
        if user_text:
            # Sensitive disclosures (passwords/OTPs) are intercepted deterministically
            sensitive_guard = self._check_sensitive_secrets(user_text, session_id, country)
            if sensitive_guard:
                return sensitive_guard

            # RAG Retrieval: Check knowledge base for verified evidence
            rag_result = self.rag_engine.retrieve(user_text, jurisdiction=country)
            evidence_block = (
                self.rag_engine.format_evidence_block(rag_result.chunks)
                if rag_result.is_sufficient
                else None
            )
            citations = (
                self.rag_engine.extract_citations(rag_result.chunks)
                if rag_result.is_sufficient
                else []
            )

            # If LLM is configured, request assistive answer (grounded in RAG evidence when sufficient)
            if self.llm_provider and self.llm_provider.is_configured:
                try:
                    llm_response = await self.llm_provider.generate_response(
                        user_text, evidence=evidence_block
                    )
                except TypeError:
                    # Backward compatibility for mocks or providers taking only (user_query)
                    try:
                        llm_response = await self.llm_provider.generate_response(user_text)
                    except Exception as e:
                        logger.warning(f"LLM provider failed: {e}")
                        llm_response = None
                except Exception as e:
                    logger.warning(f"LLM provider failed: {e}")
                    llm_response = None

                if llm_response:
                    return ChatbotMessageResponse(
                        session_id=session_id,
                        title="Safemate Safety Guidance",
                        text=llm_response,
                        choices=[
                            FlowChoiceResponse(
                                choice_id="choice_to_options",
                                label="Explore Safety Options",
                                target_flow_id="understand_options",
                            ),
                            FlowChoiceResponse(
                                choice_id="choice_opt_emergency",
                                label="Emergency Help (112)",
                                target_flow_id="immediate_danger",
                                is_emergency=True,
                            ),
                        ],
                        resources=self._resolve_resources(
                            ["erss_112_in", "women_helpline_181_in", "cybercrime_portal_in"],
                            country,
                        ),
                        sources=citations,
                        answer_mode="rag" if rag_result.is_sufficient else "safe_fallback",
                        fallback_used=False,
                        disclaimer=(
                            "AI-assisted guidance grounded in verified legal and safety resources. Not formal legal counsel."
                            if rag_result.is_sufficient
                            else "AI-assisted guidance is for general information. For emergency safety, call 112 directly."
                        ),
                    )

            # If LLM is unconfigured or failed, but RAG evidence is sufficient:
            # Curated safe fallback using retrieved verified knowledge
            if rag_result.is_sufficient and rag_result.chunks:
                top_chunk = rag_result.chunks[0]
                return ChatbotMessageResponse(
                    session_id=session_id,
                    title=f"Verified Guidance: {top_chunk.title}",
                    text=(
                        f"Based on verified official guidance from {top_chunk.source_organization}:\n\n"
                        f"{top_chunk.text}"
                    ),
                    choices=[
                        FlowChoiceResponse(
                            choice_id="choice_to_options",
                            label="Explore Safety Options",
                            target_flow_id="understand_options",
                        ),
                        FlowChoiceResponse(
                            choice_id="choice_opt_emergency",
                            label="Emergency Help (112)",
                            target_flow_id="immediate_danger",
                            is_emergency=True,
                        ),
                    ],
                    resources=self._resolve_resources(
                        ["erss_112_in", "women_helpline_181_in", "cybercrime_portal_in"],
                        country,
                    ),
                    sources=citations,
                    answer_mode="safe_fallback",
                    fallback_used=True,
                    disclaimer="Information retrieved directly from verified official sources. Not formal legal counsel.",
                )

            # Fallback to curated guided flow matching when knowledge evidence is insufficient
            return self._handle_free_text_query(user_text, session_id, country)

        # ---------------------------------------------------------------------
        # 4. FALLBACK / EMPTY REQUEST
        # ---------------------------------------------------------------------
        return self._build_menu_response(
            session_id=session_id,
            country=country,
            notice="Please choose a guided situation or type a question to receive safety options.",
        )

    def _check_sensitive_secrets(
        self, query: str, session_id: str, country: str
    ) -> Optional[ChatbotMessageResponse]:
        """Intercept queries containing sensitive secrets before external transmission."""
        q_lower = query.lower()
        if any(re.search(pat, q_lower) for pat in SENSITIVE_SECRET_PATTERNS):
            if "password" in q_lower or "otp" in q_lower or "pin" in q_lower:
                return ChatbotMessageResponse(
                    session_id=session_id,
                    title="Privacy & Security Safeguard",
                    text=(
                        "Safemate will never ask you for passwords, verification codes, or bank PINs. "
                        "Never share authentication credentials with anyone online, even someone claiming to help recover your account."
                    ),
                    numbered_steps=[
                        "Enable Two-Factor Authentication (2FA) using an authenticator app.",
                        "Review active device sessions in your account settings.",
                        "If someone is demanding login codes or money under threat, view our Blackmail guidance below.",
                    ],
                    disclaimer="Legitimate platforms and police officers will never demand your account passwords or OTPs.",
                    choices=[
                        FlowChoiceResponse(
                            choice_id="choice_blackmail_flow",
                            label="Blackmail or Threats Guidance",
                            target_flow_id="blackmail_threats",
                        ),
                        FlowChoiceResponse(
                            choice_id="choice_fake_profile",
                            label="Fake Profile / Impersonation",
                            target_flow_id="impersonation_fake_profile",
                        ),
                    ],
                    resources=self._resolve_resources(["cybercrime_portal_in"], country),
                )
            if "nude" in q_lower or "photo" in q_lower or "video" in q_lower or "intimate" in q_lower:
                return self._start_flow_as_response("intimate_image_abuse", session_id, country)
        return None

    def record_feedback(
        self, request: ChatbotFeedbackRequest
    ) -> ChatbotFeedbackResponse:
        """Acknowledge user feedback without persisting sensitive identifiers."""
        # Non-invasive acknowledgement; safe for compliance and privacy audits
        return ChatbotFeedbackResponse(
            status="received",
            message="Thank you for your feedback. We continuously review safety resources for accuracy.",
        )

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _resolve_resources(
        self, resource_ids: List[str], country: str
    ) -> List[SafetyResourceResponse]:
        """Convert a list of resource IDs into rich SafetyResourceResponse items."""
        resolved = []
        for rid in resource_ids:
            if rid in VERIFIED_RESOURCES:
                res = VERIFIED_RESOURCES[rid]
                resolved.append(SafetyResourceResponse(**res.model_dump()))
        # If no specific resource attached, include emergency contacts for country
        if not resolved:
            emergencies = get_emergency_resources(country)
            for res in emergencies[:2]:
                resolved.append(SafetyResourceResponse(**res.model_dump()))
        return resolved

    def _build_immediate_danger_response(
        self, session_id: str, country: str
    ) -> ChatbotMessageResponse:
        """Construct the high-priority immediate danger intervention."""
        emergencies = get_emergency_resources(country)
        resources_resp = [
            SafetyResourceResponse(**res.model_dump()) for res in emergencies
        ]

        choices = [
            FlowChoiceResponse(
                choice_id="choice_call_112",
                label="Call 112 Immediately",
                description="Dial pan-India emergency number",
                is_emergency=True,
                is_terminal=True,
            ),
            FlowChoiceResponse(
                choice_id="choice_sos_panic",
                label="Safemate Emergency SOS Feature",
                description="Trigger SOS alert on Safemate",
                next_step_id="step_safemate_sos",
                target_flow_id="immediate_danger",
            ),
            FlowChoiceResponse(
                choice_id="choice_safewalk_now",
                label="Safemate SafeWalk Trip Monitoring",
                description="Share live tracking token with trusted contacts",
                next_step_id="step_safewalk_info",
                target_flow_id="immediate_danger",
            ),
            FlowChoiceResponse(
                choice_id="choice_once_safe",
                label="I am safe now — explore options",
                target_flow_id="understand_options",
            ),
        ]

        return ChatbotMessageResponse(
            session_id=session_id,
            flow_id="immediate_danger",
            step_id="step_immediate_action",
            title="Immediate Physical Danger Detected",
            text=(
                "Please get to a safe place immediately. "
                "Call 112 (or 181 / 1091) from your device dialer for urgent police or crisis intervention. "
                "Safemate is a digital assistant and cannot automatically dispatch emergency services or track your live location "
                "without your explicit activation."
            ),
            numbered_steps=[
                "Dial 112 right now for immediate police, fire, or medical dispatch.",
                "If in public, alert security personnel, station managers, or shopkeepers.",
                "Share your live location with a trusted friend or family member.",
                "Avoid confronting the threatening person.",
            ],
            disclaimer=(
                "Emergency calling via your device dialer is the fastest and most reliable response. "
                "Safemate does not fabricate calls or dispatch police on its own."
            ),
            choices=choices,
            resources=resources_resp,
            is_complete=False,
            is_emergency_priority=True,
            safemate_feature_link="/api/v1/emergency/sos",
            safemate_feature_name="Emergency SOS Endpoint",
            safemate_feature_note="Requires configured contacts on backend; always prioritize calling 112 first.",
            answer_mode="emergency",
        )

    def _handle_choice_selection(
        self,
        choice_id: str,
        current_flow_id: Optional[str],
        current_step_id: Optional[str],
        session_id: str,
        country: str,
    ) -> ChatbotMessageResponse:
        """Handle selection of a choice chip across or within flows."""
        # 1. Check if user selected direct emergency action
        if choice_id in ("choice_call_112", "choice_opt_emergency", "choice_harass_immed", "choice_phys_urgent"):
            return self._build_immediate_danger_response(session_id, country)

        # 2. Check if choice switches to a new flow
        flow = get_flow(current_flow_id) if current_flow_id else None
        current_step = flow.steps.get(current_step_id) if flow and current_step_id else None

        target_flow_id = None
        next_step_id = None

        if current_step:
            for ch in current_step.choices:
                if ch.choice_id == choice_id:
                    target_flow_id = ch.target_flow_id
                    next_step_id = ch.next_step_id
                    break

        # Check top-level flow triggers by choice_id pattern
        if not target_flow_id and not next_step_id:
            if "blackmail" in choice_id:
                target_flow_id = "blackmail_threats"
            elif "harass" in choice_id:
                target_flow_id = "online_harassment"
            elif "ncii" in choice_id or "image" in choice_id:
                target_flow_id = "intimate_image_abuse"
            elif "cyber" in choice_id:
                target_flow_id = "report_cybercrime_india"
            elif "evidence" in choice_id:
                target_flow_id = "preserve_evidence"
            elif "option" in choice_id or "menu" in choice_id:
                target_flow_id = "understand_options"

        # If switching flows
        if target_flow_id:
            next_flow = get_flow(target_flow_id)
            if next_flow:
                step = next_flow.steps[next_flow.initial_step_id]
                resolved_resources = self._resolve_resources(
                    step.recommended_resource_ids, country
                )
                choices_resp = [
                    FlowChoiceResponse(**c.model_dump()) for c in step.choices
                ]
                return ChatbotMessageResponse(
                    session_id=session_id,
                    flow_id=next_flow.flow_id,
                    step_id=step.step_id,
                    title=step.title,
                    text=step.guidance,
                    numbered_steps=step.numbered_steps,
                    disclaimer=step.disclaimer,
                    choices=choices_resp,
                    resources=resolved_resources,
                    is_complete=step.is_terminal,
                    is_emergency_priority=(next_flow.flow_id == "immediate_danger"),
                    safemate_feature_link=step.safemate_feature_link,
                    safemate_feature_name=step.safemate_feature_name,
                    safemate_feature_note=step.safemate_feature_note,
                )

        # If advancing step within current flow
        if flow and next_step_id and next_step_id in flow.steps:
            step = flow.steps[next_step_id]
            resolved_resources = self._resolve_resources(
                step.recommended_resource_ids, country
            )
            choices_resp = [
                FlowChoiceResponse(**c.model_dump()) for c in step.choices
            ]
            return ChatbotMessageResponse(
                session_id=session_id,
                flow_id=flow.flow_id,
                step_id=step.step_id,
                title=step.title,
                text=step.guidance,
                numbered_steps=step.numbered_steps,
                disclaimer=step.disclaimer,
                choices=choices_resp,
                resources=resolved_resources,
                is_complete=step.is_terminal,
                is_emergency_priority=(flow.flow_id == "immediate_danger"),
                safemate_feature_link=step.safemate_feature_link,
                safemate_feature_name=step.safemate_feature_name,
                safemate_feature_note=step.safemate_feature_note,
            )

        # Fallback to menu if unknown option
        return self._build_menu_response(
            session_id=session_id,
            country=country,
            notice="Here are the available safety guidance areas you can explore:",
        )

    def _handle_free_text_query(
        self, query: str, session_id: str, country: str
    ) -> ChatbotMessageResponse:
        """Analyze free-text question and map to the most relevant guided safety flow."""
        q_lower = query.lower()

        # Sensitive disclosure / password / OTP prevention
        if any(re.search(pat, q_lower) for pat in SENSITIVE_SECRET_PATTERNS):
            if "password" in q_lower or "otp" in q_lower or "pin" in q_lower:
                return ChatbotMessageResponse(
                    session_id=session_id,
                    title="Privacy & Security Safeguard",
                    text=(
                        "Safemate will never ask you for passwords, verification codes, or bank PINs. "
                        "Never share authentication credentials with anyone online, even someone claiming to help recover your account."
                    ),
                    numbered_steps=[
                        "Enable Two-Factor Authentication (2FA) using an authenticator app.",
                        "Review active device sessions in your account settings.",
                        "If someone is demanding login codes or money under threat, view our Blackmail guidance below.",
                    ],
                    disclaimer="Legitimate platforms and police officers will never demand your account passwords or OTPs.",
                    choices=[
                        FlowChoiceResponse(
                            choice_id="choice_blackmail_flow",
                            label="Blackmail or Threats Guidance",
                            target_flow_id="blackmail_threats",
                        ),
                        FlowChoiceResponse(
                            choice_id="choice_fake_profile",
                            label="Fake Profile / Impersonation",
                            target_flow_id="impersonation_fake_profile",
                        ),
                    ],
                    resources=self._resolve_resources(["cybercrime_portal_in"], country),
                )
            if "nude" in q_lower or "photo" in q_lower or "video" in q_lower or "intimate" in q_lower:
                return self._start_flow_as_response("intimate_image_abuse", session_id, country)

        # Topic matching
        if any(k in q_lower for k in ["blackmail", "extort", "money demand", "sextortion", "pay"]):
            return self._start_flow_as_response("blackmail_threats", session_id, country)
        elif any(k in q_lower for k in ["ncii", "leak", "intimate image", "private video", "morph", "deepfake", "consent"]):
            return self._start_flow_as_response("intimate_image_abuse", session_id, country)
        elif any(k in q_lower for k in ["fake profile", "fake account", "impersonat", "cloned", "stolen photos"]):
            return self._start_flow_as_response("impersonation_fake_profile", session_id, country)
        elif any(k in q_lower for k in ["harass", "troll", "bully", "threat", "cyberstalk"]):
            return self._start_flow_as_response("online_harassment", session_id, country)
        elif any(k in q_lower for k in ["follow", "eve teas", "posh", "workplace", "street", "stalking"]):
            return self._start_flow_as_response("physical_harassment", session_id, country)
        elif any(k in q_lower for k in ["report", "cybercrime", "cyber crime", "1930", "portal", "fir", "police"]):
            return self._start_flow_as_response("report_cybercrime_india", session_id, country)
        elif any(k in q_lower for k in ["evidence", "proof", "screenshot", "save", "vault", "preserve"]):
            return self._start_flow_as_response("preserve_evidence", session_id, country)
        elif any(k in q_lower for k in ["option", "right", "legal", "law", "lawyer", "advice", "help"]):
            return self._start_flow_as_response("understand_options", session_id, country)

        # General empathetic default
        return ChatbotMessageResponse(
            session_id=session_id,
            title="Safemate Safety Guidance",
            text=(
                f"I understand you are asking about: \"{query[:100]}\". "
                "To give you the most accurate and safe assistance without assumptions, "
                "please choose the category below that best describes your situation:"
            ),
            choices=[
                FlowChoiceResponse(
                    choice_id="choice_to_harass",
                    label="Online Harassment",
                    target_flow_id="online_harassment",
                ),
                FlowChoiceResponse(
                    choice_id="choice_to_blackmail",
                    label="Blackmail or Threats",
                    target_flow_id="blackmail_threats",
                ),
                FlowChoiceResponse(
                    choice_id="choice_to_ncii",
                    label="Non-consensual Images",
                    target_flow_id="intimate_image_abuse",
                ),
                FlowChoiceResponse(
                    choice_id="choice_to_cyber",
                    label="Report Cybercrime in India",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoiceResponse(
                    choice_id="choice_to_options",
                    label="Understand My Options",
                    target_flow_id="understand_options",
                ),
            ],
            resources=self._resolve_resources(
                ["erss_112_in", "women_helpline_181_in", "cybercrime_portal_in"],
                country,
            ),
            disclaimer="Safemate provides structured guidance and verified official resources, not formal legal counsel.",
        )

    def _start_flow_as_response(
        self, flow_id: str, session_id: str, country: str
    ) -> ChatbotMessageResponse:
        """Launch a specific flow and format the output as ChatbotMessageResponse."""
        flow = get_flow(flow_id)
        if not flow:
            return self._build_menu_response(session_id, country)
        step = flow.steps[flow.initial_step_id]
        resolved_resources = self._resolve_resources(
            step.recommended_resource_ids, country
        )
        choices_resp = [
            FlowChoiceResponse(**c.model_dump()) for c in step.choices
        ]
        return ChatbotMessageResponse(
            session_id=session_id,
            flow_id=flow.flow_id,
            step_id=step.step_id,
            title=step.title,
            text=step.guidance,
            numbered_steps=step.numbered_steps,
            disclaimer=step.disclaimer,
            choices=choices_resp,
            resources=resolved_resources,
            is_complete=step.is_terminal,
            is_emergency_priority=(flow.flow_id == "immediate_danger"),
            safemate_feature_link=step.safemate_feature_link,
            safemate_feature_name=step.safemate_feature_name,
            safemate_feature_note=step.safemate_feature_note,
        )

    def _build_menu_response(
        self, session_id: str, country: str, notice: Optional[str] = None
    ) -> ChatbotMessageResponse:
        """Build initial top-level menu response."""
        flows = list_flows()
        choices = [
            FlowChoiceResponse(
                choice_id=f"start_{f.flow_id}",
                label=f.title,
                description=f.subtitle,
                target_flow_id=f.flow_id,
                is_emergency=(f.flow_id == "immediate_danger"),
            )
            for f in flows
        ]
        return ChatbotMessageResponse(
            session_id=session_id,
            title="Safemate Safety Assistant",
            text=notice
            or (
                "You're in a safe place to explore your options. "
                "Choose a situation below to receive practical, step-by-step guidance."
            ),
            choices=choices,
            resources=self._resolve_resources(
                ["erss_112_in", "women_helpline_181_in", "cybercrime_portal_in"],
                country,
            ),
            disclaimer="Safemate provides verified resources and digital safety guidance. In an emergency, always call 112 directly.",
        )


# Global singleton instance
chatbot_service = ChatbotService()
