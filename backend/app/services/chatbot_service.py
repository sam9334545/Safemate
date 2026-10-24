"""Chatbot service providing structured safety, legal, and cybercrime guidance."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
    ChatExportResponse,
    ChatHistoryResponse,
    ChatbotFeedbackRequest,
    ChatbotFeedbackResponse,
    ChatbotHealthResponse,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatbotResourceListResponse,
    ChatbotSourceCitation,
    ChatbotStartRequest,
    ChatbotStartResponse,
    ChatMessageItem,
    ComplaintDraftRequest,
    ComplaintDraftResponse,
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

HINDI_TRIGGER_KEYWORDS = [
    "madad", "bachao", "dhamki", "shikayat",
    "pareshan", "picha kar raha", "fir darj",
    "cyber thana", "suraksha", "dar lag raha", "kya karu", "kaise report kare",
    "ganda photo", "morphed photo", "video viral", "thana", "shoshan",
    "chhedchhad", "help karo", "phas gaya", "phas gayi", "chori"
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
        self.session_histories: Dict[str, List[Dict[str, Any]]] = {}

    def is_hindi_query(self, text: str, language: Optional[str] = None) -> bool:
        """Detect if message is in Hindi (Devanagari script) or Hinglish safety query."""
        if language and language.lower().startswith("hi"):
            return True
        if not text:
            return False
        # Devanagari Unicode Block
        if re.search(r"[\u0900-\u097f]", text):
            return True
        lower = text.lower()
        return any(re.search(rf"\b{re.escape(k)}\b", lower) for k in HINDI_TRIGGER_KEYWORDS)

    def _build_hindi_safety_response(
        self, session_id: str, country: str, query: str
    ) -> ChatbotMessageResponse:
        """Generate structured, compassionate safety response in Hindi."""
        return ChatbotMessageResponse(
            session_id=session_id,
            title="सेफ़मेट सुरक्षा एवं कानूनी सहायता (Safemate Safety & Legal Assistance)",
            text=(
                f"आपकी सुरक्षा सर्वोपरि है। हम आपकी स्थिति को समझते हैं (प्रश्न: \"{query[:80]}\")。\n\n"
                "कृपया शांत रहें और घबराएं नहीं। सेफ़मेट आपको तत्काल सहायता और सही कानूनी कदम उठाने में मदद करेगा:\n\n"
                "1. यदि आप किसी तात्कालिक शारीरिक खतरे में हैं, तो सीधे 112 डायल करें।\n"
                "2. साइबर ब्लैकमेल, फ़ोटो लीक या ऑनलाइन उत्पीड़न के लिए 1930 साइबर हेल्पलाइन पर कॉल करें या cybercrime.gov.in पर रिपोर्ट करें।\n"
                "3. भारत में आप किसी भी नजदीकी पुलिस स्टेशन में 'Zero FIR' दर्ज करा सकते हैं, चाहे घटना कहीं भी हुई हो।"
            ),
            numbered_steps=[
                "तात्कालिक आपातकाल में तुरंत 112 डायल करें (ERSS - Police, Fire, Ambulance)।",
                "साइबर उत्पीड़न, ब्लैकमेल या मोर्फ़ फोटो के लिए 1930 पर कॉल करें या cybercrime.gov.in पर ऑनलाइन कंप्लेंट दर्ज करें।",
                "सभी चैट, कॉल रिकॉर्ड, प्रोफाइल लिंक और संदेशों के स्क्रीनशॉट सुरक्षित रखें (सबूत कभी डिलीट न करें)।",
                "ब्लैकमेलर को कोई पैसे न दें और तुरंत बातचीत बंद करें।",
                "भारतीय नागरिक सुरक्षा संहिता (BNSS) की धारा 173 (पूर्व CrPC 154) के तहत Zero FIR दर्ज कराने का आपका पूर्ण कानूनी अधिकार है।"
            ],
            disclaimer="यह जानकारी आधिकारिक सरकारी नियमों एवं कानूनी प्रावधानों पर आधारित है। आपातकाल में सीधे 112 डायल करें।",
            choices=[
                FlowChoiceResponse(
                    choice_id="choice_call_112",
                    label="🚨 112 आपातकालीन सहायता (Call 112)",
                    description="तुरंत पुलिस हेल्पलाइन से जुड़ें",
                    is_emergency=True,
                ),
                FlowChoiceResponse(
                    choice_id="choice_cyber_hindi",
                    label="💻 साइबर अपराध 1930 हेल्पलाइन",
                    description="साइबर फ्रॉड और ब्लैकमेल रिपोर्टिंग",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoiceResponse(
                    choice_id="choice_blackmail_hindi",
                    label="🛡️ ब्लैकमेल और धमकी से बचाव",
                    description="ब्लैकमेल से निपटने के सुरक्षित कदम",
                    target_flow_id="blackmail_threats",
                ),
                FlowChoiceResponse(
                    choice_id="choice_evidence_hindi",
                    label="📁 डिजिटल सबूत सुरक्षित रखें",
                    description="स्क्रीनशॉट और चैट बैकअप",
                    target_flow_id="preserve_evidence",
                ),
                FlowChoiceResponse(
                    choice_id="choice_options_hindi",
                    label="⚖️ अपने कानूनी अधिकार जानें (Zero FIR)",
                    description="कानूनी विकल्प और शिकायत पत्र",
                    target_flow_id="understand_options",
                ),
            ],
            resources=self._resolve_resources(
                ["erss_112_in", "women_helpline_181_in", "cybercrime_portal_in"],
                country,
            ),
            language="hi",
            audio_summary="आप सुरक्षित स्थान पर रहें। आपातकाल के लिए 112 और साइबर शिकायत के लिए 1930 पर कॉल करें। स्क्रीन पर दिए गए कदम फॉलो करें।",
        )

    def _record_turn(
        self,
        session_id: str,
        sender: str,
        text: str,
        title: Optional[str] = None,
        is_emergency: bool = False,
    ) -> None:
        """Append a message turn to the in-memory session history."""
        if not session_id:
            return
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []

        turn = {
            "sender": sender,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "is_emergency": is_emergency,
        }
        self.session_histories[session_id].append(turn)
        if len(self.session_histories[session_id]) > 50:
            self.session_histories[session_id] = self.session_histories[session_id][-50:]

    def _wrap_and_record(
        self,
        response: ChatbotMessageResponse,
        user_text: str = "",
        language: str = "en",
    ) -> ChatbotMessageResponse:
        """Enrich response with language, audio readout summary, and record session turn."""
        response.language = language or "en"

        if not response.audio_summary:
            if response.is_emergency_priority:
                response.audio_summary = (
                    "Emergency alert: Please get to a safe place immediately and call 112 for police or emergency dispatch."
                )
            elif response.language == "hi":
                response.audio_summary = (
                    "आप सुरक्षित स्थान पर रहें। आपातकाल के लिए 112 और साइबर शिकायत के लिए 1930 डायल करें।"
                )
            else:
                raw_text = response.text.replace("\n", " ").strip()
                sentences = re.split(r"(?<=[.!?])\s+", raw_text)
                first_part = " ".join(sentences[:2]) if sentences else raw_text
                if len(first_part) > 160:
                    first_part = first_part[:157] + "..."
                response.audio_summary = first_part

        if user_text:
            self._record_turn(
                session_id=response.session_id,
                sender="user",
                text=user_text,
                is_emergency=False,
            )
        self._record_turn(
            session_id=response.session_id,
            sender="assistant",
            text=response.text,
            title=response.title,
            is_emergency=response.is_emergency_priority,
        )
        return response

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

        start_response = ChatbotStartResponse(
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
        self._record_turn(
            session_id=session_id,
            sender="assistant",
            text=initial_step.guidance,
            title=initial_step.title,
            is_emergency=(flow.flow_id == "immediate_danger"),
        )
        return start_response

    async def process_message(self, request: ChatbotMessageRequest) -> ChatbotMessageResponse:
        """Process incoming user interaction (choice chip selection or free-text query)."""
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        country = request.country or "IN"
        user_text = (request.message or "").strip()
        language = (request.language or "en").strip().lower()

        # ---------------------------------------------------------------------
        # 1. IMMEDIATE DANGER INTERRUPT: Deterministic check overrides all
        # ---------------------------------------------------------------------
        if self.check_immediate_danger(user_text):
            resp = self._build_immediate_danger_response(session_id, country)
            return self._wrap_and_record(resp, user_text, language)

        # ---------------------------------------------------------------------
        # 2. SENSITIVE SECRETS & NCII DISCLOSURE SAFEGUARD
        # ---------------------------------------------------------------------
        if user_text:
            sensitive_guard = self._check_sensitive_secrets(user_text, session_id, country)
            if sensitive_guard:
                return self._wrap_and_record(sensitive_guard, user_text, language)

        # ---------------------------------------------------------------------
        # 3. HINDI / REGIONAL QUERY DETECTION & EMPATHETIC GUIDANCE
        # ---------------------------------------------------------------------
        if self.is_hindi_query(user_text, language):
            resp = self._build_hindi_safety_response(session_id, country, user_text)
            return self._wrap_and_record(resp, user_text, "hi")

        # ---------------------------------------------------------------------
        # 4. CHOICE CHIP SELECTION
        # ---------------------------------------------------------------------
        if request.choice_id:
            resp = self._handle_choice_selection(
                choice_id=request.choice_id,
                current_flow_id=request.flow_id,
                current_step_id=request.step_id,
                session_id=session_id,
                country=country,
            )
            return self._wrap_and_record(resp, user_text, language)

        # ---------------------------------------------------------------------
        # 5. FREE-TEXT INTENT MATCHING, RAG RETRIEVAL & LLM / FALLBACK LAYER
        # ---------------------------------------------------------------------
        if user_text:
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
                    llm_msg_resp = ChatbotMessageResponse(
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
                    return self._wrap_and_record(llm_msg_resp, user_text, language)

            # If LLM is unconfigured or failed, but RAG evidence is sufficient:
            # Curated safe fallback using retrieved verified knowledge
            if rag_result.is_sufficient and rag_result.chunks:
                top_chunk = rag_result.chunks[0]
                rag_msg_resp = ChatbotMessageResponse(
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
                return self._wrap_and_record(rag_msg_resp, user_text, language)

            # Fallback to curated guided flow matching when knowledge evidence is insufficient
            flow_resp = self._handle_free_text_query(user_text, session_id, country)
            return self._wrap_and_record(flow_resp, user_text, language)

        # ---------------------------------------------------------------------
        # 5. FALLBACK / EMPTY REQUEST
        # ---------------------------------------------------------------------
        menu_resp = self._build_menu_response(
            session_id=session_id,
            country=country,
            notice="Please choose a guided situation or type a question to receive safety options.",
        )
        return self._wrap_and_record(menu_resp, user_text, language)

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

    def generate_complaint_draft(
        self, request: ComplaintDraftRequest
    ) -> ComplaintDraftResponse:
        """Draft a formal, legally structured Zero FIR / Cyber Complaint letter."""
        itype = request.incident_type.lower().strip()
        complainant = request.complainant_name or "Concerned Citizen (Confidential)"
        inc_date = request.incident_date or "Recent date (as per recorded electronic timestamp)"
        platform = request.platform_or_location or "Online Platform / Electronic Communications"
        accused = request.accused_details or "Unknown suspect(s) / digital identifiers pending ISP disclosure"
        summary = request.incident_summary.strip()
        city_state = request.city_state or "New Delhi, India"
        today_str = datetime.now(timezone.utc).strftime("%d %B %Y")

        sections: List[str] = []
        if "blackmail" in itype or "extort" in itype:
            title = "Formal Complaint for Cyber Blackmail, Extortion, and Criminal Intimidation"
            sections.extend([
                "IT Act, 2000 - Section 66E: Violation of bodily privacy and transmitting non-consensual images",
                "IT Act, 2000 - Section 67: Publishing or transmitting obscene material in electronic form",
                "IT Act, 2000 - Section 67A: Publishing or transmitting sexually explicit material",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 308: Extortion and putting person in fear of injury",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 351: Criminal Intimidation",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 79: Acts/words intended to insult modesty of a woman",
                "BNSS Section 173 / CrPC Section 154: Mandatory registration of Zero FIR",
            ])
        elif "ncii" in itype or "morph" in itype or "image" in itype or "leak" in itype:
            title = "Formal Complaint for Non-Consensual Image Abuse, Morphing, and Privacy Violation"
            sections.extend([
                "IT Act, 2000 - Section 66E: Capture, publication or transmission of private images without consent",
                "IT Act, 2000 - Section 67A: Transmission of sexually explicit material via computer resources",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 79: Outraging and insulting modesty of a woman",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 336: Forgery and fabrication of electronic records",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 351: Criminal Intimidation",
                "BNSS Section 173 / CrPC Section 154: Mandatory registration of Zero FIR without jurisdictional denial",
            ])
        elif "stalk" in itype or "harass" in itype:
            title = "Formal Complaint for Cyberstalking, Harassment, and Criminal Intimidation"
            sections.extend([
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 78: Stalking (electronic monitoring or following)",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 79: Word, gesture or act intended to insult modesty",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 351: Criminal Intimidation",
                "IT Act, 2000 - Section 66E & Section 67: Harassment via electronic communications",
                "BNSS Section 173 / CrPC Section 154: Mandatory Zero FIR Registration",
            ])
        elif "fake" in itype or "impersonat" in itype or "profile" in itype:
            title = "Formal Complaint for Identity Theft, Impersonation, and Forgery"
            sections.extend([
                "IT Act, 2000 - Section 66C: Identity theft using electronic signature or password/attributes",
                "IT Act, 2000 - Section 66D: Cheating by personation using computer resource",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 336: Forgery of electronic profile and media",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 356: Defamation and damage to reputation",
                "BNSS Section 173 / CrPC Section 154: Zero FIR Registration",
            ])
        elif "physical" in itype or "domestic" in itype or "threat" in itype:
            title = "Formal Complaint for Physical Threats, Domestic Violence, and Safety Protection"
            sections.extend([
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 351: Criminal Intimidation",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 115: Voluntarily causing hurt",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 85: Cruelty by husband or relatives (where applicable)",
                "Protection of Women from Domestic Violence Act (PWDVA), 2005 - Sections 12 & 18",
                "BNSS Section 173 / CrPC Section 154: Mandatory FIR registration for cognizable offenses",
            ])
        else:
            title = "Formal Complaint and Request for Registration of Zero FIR"
            sections.extend([
                "IT Act, 2000 - Section 66E & Section 67: Offenses via digital platforms",
                "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 78, 79 & 351: Stalking and Criminal Intimidation",
                "BNSS Section 173 / CrPC Section 154: Mandatory Zero FIR Registration",
            ])

        if request.sections_requested:
            for s in request.sections_requested:
                if s not in sections:
                    sections.append(s)

        sections_formatted = "\n".join([f"   - {sec}" for sec in sections])

        complaint_letter = f"""To,
The Station House Officer (SHO) / Officer-in-Charge,
Cyber Crime Police Station / Local Police Station,
Jurisdiction: {city_state}

SUBJECT: FORMAL COMPLAINT AND REQUEST FOR IMMEDIATE REGISTRATION OF ZERO FIR UNDER SECTION 173 OF BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS), 2023 / SECTION 154 CrPC

Respected Sir/Madam,

I, {complainant}, resident of {city_state}, hereby submit this formal complaint regarding serious offenses committed against me, and respectfully request the registration of a Zero FIR and prompt investigation.

1. PARTICULARS OF THE INCIDENT:
   - Date & Time of Occurrence: {inc_date}
   - Platform / Medium / Location: {platform}
   - Accused / Suspect Information: {accused}

2. STATEMENT OF FACTS:
   {summary}

3. PERTINENT STATUTORY PROVISIONS APPLICABLE:
   The aforesaid acts constitute cognizable offenses under the Indian penal and cyber statutory framework, specifically:
{sections_formatted}

4. MANDATORY REGISTRATION OF ZERO FIR:
   In accordance with the binding ruling of the Hon'ble Supreme Court of India in Lalita Kumari v. Govt. of U.P. [(2014) 2 SCC 1] and Section 173(1) of the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (formerly Section 154 CrPC), registration of an FIR is mandatory upon receiving information disclosing a cognizable offense. In the event this Police Station does not hold territorial jurisdiction over the occurrence, this complaint must be registered forthwith as a "Zero FIR" and subsequently transferred to the appropriate jurisdiction without delay.

5. PRESERVATION OF DIGITAL EVIDENCE (SECTION 94 BNSS / SECTION 91 CrPC):
   It is respectfully prayed that law enforcement issue immediate preservation notices to the intermediaries ({platform}) to preserve IP logs, registration identifiers, MAC addresses, device metadata, and chat transcripts before they can be altered or erased.

6. PRAYER FOR RELIEF:
   In light of the facts stated above, it is earnestly prayed that:
   a) An FIR / Zero FIR be registered immediately against the suspect(s) under the cited provisions.
   b) Immediate steps be taken to safeguard the complainant from ongoing intimidation and extortion.
   c) Direct intermediaries to remove, block, or hash unauthorized media or fake accounts.
   d) Provide the undersigned with a duly signed and stamped acknowledgment copy with the General Diary (GD) / Daily Diary (DD) number.

Yours sincerely,

___________________________
Signature of Complainant
Name: {complainant}
Location: {city_state}
Date: {today_str}
"""

        instructions = [
            "Print two (2) physical copies of this complaint letter.",
            "Submit one copy to the duty officer / SHO and obtain an acknowledgment stamp with GD/DD number on the second copy for your records.",
            "Do not delete any original messages, call recordings, or social media links; export full chat backups and keep timestamped screenshots.",
            "Also file an online complaint at https://cybercrime.gov.in or call national helpline 1930 within 24 hours.",
            "If any police station hesitates due to territorial boundary, remind them of mandatory Zero FIR rights under BNSS Section 173 / CrPC Section 154.",
        ]

        helplines = [
            "National Emergency: 112 (Police, Fire, Ambulance - 24/7)",
            "National Cyber Crime Helpline: 1930 (MHA Portal - cybercrime.gov.in)",
            "National Commission for Women (NCW) WhatsApp Helpline: 7217735372",
            "Women in Distress Helpline: 181 / 1091",
        ]

        disclaimer = (
            "This complaint draft is structured in accordance with Indian procedural law (BNSS 2023 / CrPC 1973) "
            "and the Information Technology Act, 2000. It is an automated template and does not constitute formal attorney representation."
        )

        return ComplaintDraftResponse(
            status="success",
            incident_type=request.incident_type,
            title=title,
            applicable_sections=sections,
            complaint_letter=complaint_letter,
            instructions=instructions,
            helplines=helplines,
            disclaimer=disclaimer,
        )

    def get_history(self, session_id: str) -> ChatHistoryResponse:
        """Retrieve recorded multi-turn message history for a session."""
        turns = self.session_histories.get(session_id, [])
        items = [
            ChatMessageItem(
                sender=t["sender"],
                text=t["text"],
                timestamp=t["timestamp"],
                title=t.get("title"),
                is_emergency=t.get("is_emergency", False),
            )
            for t in turns
        ]
        return ChatHistoryResponse(
            session_id=session_id,
            total_messages=len(items),
            messages=items,
        )

    def clear_history(self, session_id: str) -> bool:
        """Clear conversation history for privacy / panic wipe."""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            return True
        return False

    def export_report(self, session_id: str) -> ChatExportResponse:
        """Export session dialogue and verified guidance as a formatted incident report."""
        turns = self.session_histories.get(session_id, [])
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        report_lines = [
            "=" * 60,
            "SAFEMATE SAFETY & LEGAL INCIDENT CONSULTATION REPORT",
            "=" * 60,
            f"Session ID: {session_id}",
            f"Generated At: {now_str}",
            f"Total Interaction Turns: {len(turns)}",
            "-" * 60,
            "CONVERSATION TRANSCRIPT & ADVICE LOG:",
        ]
        for idx, t in enumerate(turns, 1):
            sender_label = "USER" if t["sender"] == "user" else "SAFEMATE ASSISTANT"
            report_lines.append(f"\n[{idx}] {sender_label} ({t['timestamp']}):")
            if t.get("title"):
                report_lines.append(f"Subject: {t['title']}")
            report_lines.append(t["text"])

        report_lines.extend([
            "\n" + "-" * 60,
            "CRITICAL EMERGENCY CONTACTS & HELPLINES:",
            "- Pan-India Emergency: 112",
            "- National Cyber Crime Reporting Helpline: 1930 (cybercrime.gov.in)",
            "- Women in Distress Helpline: 181 / 1091",
            "- National Commission for Women (NCW): 7827170170",
            "=" * 60,
            "DISCLAIMER: This document records automated guidance and resource references",
            "provided by Safemate. It does not replace advice from a licensed advocate or legal officer.",
        ])

        return ChatExportResponse(
            session_id=session_id,
            generated_at=now_str,
            total_messages=len(turns),
            formatted_report="\n".join(report_lines),
            helplines_summary=[
                "National Emergency: 112",
                "Cybercrime Portal: 1930",
                "Women in Distress: 181 / 1091",
            ],
        )


# Global singleton instance
chatbot_service = ChatbotService()
