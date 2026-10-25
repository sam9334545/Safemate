"""Tell-Once Intake Service: Trauma-informed single interview compiling multi-agency dossiers."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.chatbot import (
    TellOnceDossierResponse,
    TellOnceTurnRequest,
    TellOnceTurnResponse,
)
from app.services.llm_provider import BaseLLMProvider, get_llm_provider


INTAKE_STEPS = [
    "safety_check",
    "what_happened",
    "timeline_and_platform",
    "perpetrator_details",
    "demands_and_evidence",
    "resolution_and_name",
]

STEPS_CONTENT = {
    "safety_check": {
        "en": {
            "prompt": (
                "Welcome to Tell-Once Intake. You are in a safe, judgment-free space. "
                "You only have to tell your story once, and we will prepare everything for police, "
                "helplines, and lawyers so you never have to repeat it. "
                "First: Are you in a physically safe space right now?"
            ),
            "affirmation": "Take a breath. You are in full control of this conversation.",
            "audio": "Welcome to Tell-Once Intake. You are in a safe space. First, are you in a physically safe space right now?",
            "chips": [
                "Yes, I am in a safe place",
                "I am somewhat safe, but worried",
                "No, I am in immediate danger (Call 112)",
            ],
        },
        "hi": {
            "prompt": (
                "टेल-वन्स (Tell-Once) सहायता में आपका स्वागत है। आप एक सुरक्षित और गोपनीय स्थान पर हैं। "
                "आपको अपनी बात केवल एक बार बतानी होगी—हम इसे पुलिस, हेल्पलाइन और वकील तीनों के लिए तैयार करेंगे ताकि आपको बार-बार न दोहराना पड़े। "
                "सबसे पहले: क्या आप अभी किसी शारीरिक खतरे से सुरक्षित स्थान पर हैं?"
            ),
            "affirmation": "कृपया शांत रहें। आप सुरक्षित हैं और आपका पूरा नियंत्रण है।",
            "audio": "टेल-वन्स सहायता में आपका स्वागत है। क्या आप अभी किसी सुरक्षित स्थान पर हैं?",
            "chips": [
                "हाँ, मैं सुरक्षित स्थान पर हूँ",
                "मैं अभी सुरक्षित हूँ लेकिन चिंतित हूँ",
                "नहीं, मुझे तुरंत पुलिस सहायता चाहिए (112)",
            ],
        },
    },
    "what_happened": {
        "en": {
            "prompt": (
                "Thank you for letting me know. Take all the time you need. "
                "In your own words, could you gently describe what you have been experiencing or what occurred?"
            ),
            "affirmation": "We believe you, and we are listening without any judgment.",
            "audio": "Take all the time you need. In your own words, could you gently describe what happened?",
            "chips": [
                "Online Blackmail & Extortion",
                "Morphed / Fake Images Leaked",
                "Stalking & Threatening Messages",
                "Fake Account Impersonation",
                "Physical Harassment or Threats",
            ],
        },
        "hi": {
            "prompt": (
                "बताने के लिए धन्यवाद। कृपया आराम से, अपनी सुविधा के अनुसार बताएं कि आपके साथ क्या हुआ था "
                "या आप किस परेशानी का सामना कर रही हैं?"
            ),
            "affirmation": "हम आपकी बात को समझ रहे हैं और हर कदम पर आपके साथ हैं।",
            "audio": "कृपया आराम से बताएं कि आपके साथ क्या हुआ था या आप किस परेशानी का सामना कर रही हैं?",
            "chips": [
                "ऑनलाइन ब्लैकमेल और वसूली",
                "मोर्फ़ / नकली फोटो वायरल करने की धमकी",
                "पीछा करना और धमकी भरे संदेश",
                "नकली प्रोफाइल से बदनामी",
                "शारीरिक या घरेलू हिंसा का खतरा",
            ],
        },
    },
    "timeline_and_platform": {
        "en": {
            "prompt": (
                "Thank you for trusting me with that. Roughly when did this start, "
                "and on which platform or location did it take place (such as WhatsApp, Instagram, Telegram, phone calls, or in person)?"
            ),
            "affirmation": "Every detail you provide strengthens your legal protections.",
            "audio": "Roughly when did this start, and on which platform or location did it happen?",
            "chips": [
                "Started recently on Instagram & WhatsApp",
                "Ongoing for several weeks on Telegram",
                "Phone calls & SMS messages",
                "In-person / workplace / street",
            ],
        },
        "hi": {
            "prompt": (
                "यह साझा करने के लिए धन्यवाद। यह घटना लगभग कब शुरू हुई, "
                "और किस ऐप या जगह पर हुई (जैसे इंस्टाग्राम, व्हाट्सएप, टेलीग्राम या फोन पर)?"
            ),
            "affirmation": "हर जानकारी आपके कानूनी अधिकारों को मजबूत बनाती है।",
            "audio": "यह घटना कब शुरू हुई, और किस ऐप या जगह पर हुई?",
            "chips": [
                "हाल ही में इंस्टाग्राम व व्हाट्सएप पर",
                "पिछले कुछ हफ्तों से टेलीग्राम पर",
                "फोन कॉल्स और मैसेज पर",
                "व्यक्तिगत / कार्यस्थल पर",
            ],
        },
    },
    "perpetrator_details": {
        "en": {
            "prompt": (
                "Do you have any information about who might be doing this, such as usernames, "
                "phone numbers, email addresses, or profile links? If you don't know or aren't sure, "
                "that is completely fine—simply write 'Unknown'."
            ),
            "affirmation": "It is completely normal not to have all the details right now.",
            "audio": "Do you have any details about who is doing this, such as usernames or phone numbers?",
            "chips": [
                "Unknown / anonymous username",
                "Known acquaintance / ex-partner",
                "I have their phone number and handle",
                "Multiple fake accounts",
            ],
        },
        "hi": {
            "prompt": (
                "क्या आपके पास उत्पीड़क के बारे में कोई जानकारी है (जैसे यूज़रनेम, फोन नंबर, सोशल मीडिया लिंक या नाम)? "
                "यदि आपको नहीं पता, तो कोई चिंता नहीं—बस 'अज्ञात' लिख दें।"
            ),
            "affirmation": "अगर पूरी जानकारी नहीं है, तो भी चिंता की कोई बात नहीं है।",
            "audio": "क्या आपके पास उत्पीड़क का यूज़रनेम या फोन नंबर है? नहीं पता तो 'अज्ञात' लिखें।",
            "chips": [
                "अज्ञात यूज़रनेम / अकाउंट",
                "कोई परिचित व्यक्ति",
                "मेरे पास उनका फोन नंबर और हैंडल है",
                "मुझे ठीक से नहीं पता",
            ],
        },
    },
    "demands_and_evidence": {
        "en": {
            "prompt": (
                "Has this person made any specific demands or threats (such as asking for money, or threatening to share media)? "
                "Have you saved any screenshots, call logs, or messages?"
            ),
            "affirmation": "Preserving digital records is the strongest step toward holding them accountable.",
            "audio": "Has this person made any specific demands or threats? Have you saved any screenshots or messages?",
            "chips": [
                "Demanded money; screenshots saved",
                "Threatening to leak photos; chats preserved",
                "Threatened physical harm; call logs saved",
                "No demands yet, but persistent harassment",
            ],
        },
        "hi": {
            "prompt": (
                "क्या उस व्यक्ति ने कोई धमकी या मांग की है (जैसे पैसे मांगना या फोटो वायरल करना)? "
                "क्या आपने स्क्रीनशॉट, कॉल रिकॉर्डिंग या चैट सुरक्षित रखी हैं?"
            ),
            "affirmation": "डिजिटल सबूत सुरक्षित रखना आपकी सबसे बड़ी ताकत है।",
            "audio": "क्या उस व्यक्ति ने कोई धमकी या पैसे मांगे हैं? क्या स्क्रीनशॉट सुरक्षित हैं?",
            "chips": [
                "पैसे मांगे हैं; स्क्रीनशॉट सेव हैं",
                "फोटो लीक की धमकी; चैट सुरक्षित है",
                "शारीरिक नुकसान की धमकी दी है",
                "कोई मांग नहीं; बस लगातार परेशान कर रहा है",
            ],
        },
    },
    "resolution_and_name": {
        "en": {
            "prompt": (
                "Almost finished. What is your city & state, and would you prefer your name on the formal police complaint, "
                "or would you like to remain listed as 'Concerned Citizen (Confidential)'?"
            ),
            "affirmation": "You have taken a courageous step today by documenting this.",
            "audio": "Almost finished. What is your city and state, and would you prefer your name on the complaint or to remain confidential?",
            "chips": [
                "Keep my name Confidential (Concerned Citizen)",
                "Include my full name on the complaint",
                "New Delhi, India",
                "Bengaluru, Karnataka",
                "Mumbai, Maharashtra",
            ],
        },
        "hi": {
            "prompt": (
                "हमारा विवरण पूरा हो रहा है। आपका शहर और राज्य क्या है, और क्या आप शिकायत पर अपना नाम लिखना चाहती हैं "
                "या 'गोपनीय नागरिक' के रूप में दर्ज करना चाहती हैं?"
            ),
            "affirmation": "आपने आज अपनी सुरक्षा के लिए एक बहुत साहसी कदम उठाया है।",
            "audio": "आपका शहर और राज्य क्या है, और क्या आप अपना नाम गोपनीय रखना चाहती हैं?",
            "chips": [
                "नाम गोपनीय रखें (Concerned Citizen)",
                "मेरा नाम शिकायत पर दर्ज करें",
                "नई दिल्ली",
                "बेंगलुरु",
                "मुंबई",
            ],
        },
    },
}


class TellOnceService:
    """Trauma-informed intake engine implementing the 'Tell-Once' assistant."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()
        self.intake_sessions: Dict[str, Dict[str, Any]] = {}

    def start_intake(self, intake_id: Optional[str] = None, language: str = "en") -> TellOnceTurnResponse:
        """Initialize a new trauma-informed intake session starting at Step 1."""
        session_id = intake_id or f"intake_{uuid.uuid4().hex[:12]}"
        lang = "hi" if language and language.lower().startswith("hi") else "en"

        self.intake_sessions[session_id] = {
            "intake_id": session_id,
            "current_step_index": 1,
            "language": lang,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "answers": {},
            "history": [],
        }

        step_info = STEPS_CONTENT["safety_check"][lang]
        return TellOnceTurnResponse(
            intake_id=session_id,
            step_index=1,
            total_steps=len(INTAKE_STEPS),
            step_name="safety_check",
            gentle_prompt=step_info["prompt"],
            calm_affirmation=step_info["affirmation"],
            audio_summary=step_info["audio"],
            suggested_chips=step_info["chips"],
            is_completed=False,
            language=lang,
        )

    async def process_turn(self, request: TellOnceTurnRequest) -> TellOnceTurnResponse:
        """Process incoming user turn, save extracted details, and deliver next gentle question."""
        session_id = request.intake_id or f"intake_{uuid.uuid4().hex[:12]}"
        lang = "hi" if request.language and request.language.lower().startswith("hi") else "en"

        if session_id not in self.intake_sessions:
            self.intake_sessions[session_id] = {
                "intake_id": session_id,
                "current_step_index": 1,
                "language": lang,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "answers": {},
                "history": [],
            }

        session = self.intake_sessions[session_id]
        current_idx = session["current_step_index"]

        # 1. Handle user requesting a pause / breather
        if request.take_breather:
            breather_text = (
                "कृपया एक गहरी सांस लें। आप पूरी तरह सुरक्षित हैं। 4 सेकंड सांस अंदर लें, 4 सेकंड रोकें और धीरे-धीरे छोड़ें। "
                "कोई जल्दी नहीं है। जब भी आप तैयार महसूस करें, अगला जवाब दें।"
                if lang == "hi"
                else "Take all the time you need. Breathe in slowly for 4 seconds, hold for 4 seconds, and gently exhale. "
                "There is no rush at all. Whenever you feel ready to continue, we are right here with you."
            )
            breather_affirmation = (
                "सांस अंदर लें... धीरे से छोड़ें... आप सुरक्षित हैं।"
                if lang == "hi"
                else "Breathe in... Breathe out... You are safe."
            )
            step_key = INTAKE_STEPS[min(current_idx - 1, len(INTAKE_STEPS) - 1)]
            breather_chips = (
                ["मैं आगे बताने के लिए तैयार हूँ", "एक और गहरी सांस लें"]
                if lang == "hi"
                else ["I feel ready to continue", "Take another breath"]
            )
            return TellOnceTurnResponse(
                intake_id=session_id,
                step_index=current_idx,
                total_steps=len(INTAKE_STEPS),
                step_name=step_key,
                gentle_prompt=breather_text,
                calm_affirmation=breather_affirmation,
                audio_summary=breather_text,
                suggested_chips=breather_chips,
                is_completed=False,
                language=lang,
            )

        # 2. Record user's response to the current step
        step_name = INTAKE_STEPS[current_idx - 1]
        user_text = (request.user_response or "").strip()
        session["answers"][step_name] = user_text
        session["history"].append({"step": step_name, "response": user_text})

        # 3. Advance to the next step
        next_idx = current_idx + 1

        if next_idx > len(INTAKE_STEPS):
            # All steps completed!
            completion_prompt = (
                "आपका विवरण सुरक्षित रूप से दर्ज कर लिया गया है। "
                "अब आपका संपूर्ण 'Tell-Once Dossier' तैयार है—जिसमें पुलिस Zero FIR, साइबर हेल्पलाइन 1930 ब्रीफ, "
                "और कानूनी सहायता सारांश शामिल हैं। आपको यह बात दोबारा किसी को दोहराने की आवश्यकता नहीं है।"
                if lang == "hi"
                else "Thank you for trusting us with your story. Your Multi-Agency 'Tell-Once Dossier' has been generated. "
                "It contains your formal Police Zero FIR, Cyber Helpline 1930 Brief, and Legal Counsel Summary. "
                "You never have to repeat your story again."
            )
            return TellOnceTurnResponse(
                intake_id=session_id,
                step_index=len(INTAKE_STEPS),
                total_steps=len(INTAKE_STEPS),
                step_name="completed",
                gentle_prompt=completion_prompt,
                calm_affirmation=(
                    "शाबाश! आपने आज अपनी सुरक्षा के लिए बहुत बड़ा कदम उठाया है।"
                    if lang == "hi"
                    else "You have shown incredible strength today. We have prepared your complete documentation."
                ),
                audio_summary="Your Tell-Once Dossier has been compiled successfully.",
                suggested_chips=[
                    "View Multi-Agency Dossier",
                    "View Police Zero FIR",
                    "View 1930 Cyber Brief",
                    "View Lawyer Summary",
                    "Download All",
                ],
                is_completed=True,
                language=lang,
            )

        session["current_step_index"] = next_idx
        next_step_name = INTAKE_STEPS[next_idx - 1]
        step_info = STEPS_CONTENT[next_step_name][lang]

        return TellOnceTurnResponse(
            intake_id=session_id,
            step_index=next_idx,
            total_steps=len(INTAKE_STEPS),
            step_name=next_step_name,
            gentle_prompt=step_info["prompt"],
            calm_affirmation=step_info["affirmation"],
            audio_summary=step_info["audio"],
            suggested_chips=step_info["chips"],
            is_completed=False,
            language=lang,
        )

    def compile_dossier(self, intake_id: str) -> TellOnceDossierResponse:
        """Compile the answers from the intake session into a 3-in-1 Multi-Agency Dossier."""
        session = self.intake_sessions.get(intake_id)
        if not session:
            # Create a structured default container for empty / direct requests
            session = {
                "answers": {
                    "safety_check": "Safe place",
                    "what_happened": "Cyber harassment and extortion threats",
                    "timeline_and_platform": "Recent occurrence on social media",
                    "perpetrator_details": "Unknown suspect",
                    "demands_and_evidence": "Extortion demands; digital evidence preserved",
                    "resolution_and_name": "Concerned Citizen, New Delhi",
                },
                "language": "en",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        answers = session.get("answers", {})
        lang = session.get("language", "en")
        today_str = datetime.now(timezone.utc).strftime("%d %B %Y")

        what_happened = answers.get("what_happened", "Cyber harassment and blackmail")
        platform = answers.get("timeline_and_platform", "Online communications platform")
        perpetrator = answers.get("perpetrator_details", "Unknown suspect pending ISP log disclosure")
        demands = answers.get("demands_and_evidence", "Demands made; digital communications preserved")
        res_info = answers.get("resolution_and_name", "")

        # Extract name & city
        complainant_name = "Concerned Citizen (Confidential)"
        city_state = "New Delhi, India"

        city_match = re.search(
            r"\b(Delhi|New Delhi|Bengaluru|Bangalore|Mumbai|Hyderabad|Chennai|Kolkata|Pune|Jaipur|Lucknow|Chandigarh|Noida|Gurgaon|Gurugram)\b",
            res_info,
            re.IGNORECASE,
        )
        if city_match:
            matched_city = city_match.group(1).title()
            if matched_city in ("Delhi", "New Delhi"):
                city_state = "New Delhi, India"
            elif matched_city in ("Bengaluru", "Bangalore"):
                city_state = "Bengaluru, Karnataka"
            elif matched_city == "Mumbai":
                city_state = "Mumbai, Maharashtra"
            else:
                city_state = f"{matched_city}, India"

        name_match = re.search(
            r"(?:name\s+(?:is|:)|my\s+name\s+is|नाम\s+(?:है|:))\s*([A-Za-z\u0900-\u097F\s]{2,40})",
            res_info,
            re.IGNORECASE,
        )
        if name_match:
            candidate = name_match.group(1).split(",")[0].split(";")[0].strip()
            if candidate and len(candidate) > 2:
                complainant_name = candidate
        elif "Concerned Citizen" not in res_info and "Confidential" not in res_info and len(res_info) > 3:
            parts = [p.strip() for p in re.split(r"[,;]", res_info) if p.strip()]
            for p in parts:
                if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$", p):
                    complainant_name = p
                    break

        # Classify incident type
        lower_what = (what_happened + " " + demands).lower()
        if any(w in lower_what for w in ["blackmail", "extort", "money", "paise", "vassoli"]):
            incident_type = "Cyber Blackmail & Extortion"
        elif any(w in lower_what for w in ["morph", "nude", "photo", "image", "video", "leak"]):
            incident_type = "Non-Consensual Image Abuse (NCII) & Morphing"
        elif any(w in lower_what for w in ["stalk", "follow", "call", "picha"]):
            incident_type = "Cyberstalking & Intimidation"
        else:
            incident_type = "Online Harassment & Impersonation"

        # ---------------------------------------------------------------------
        # 1. Police Zero FIR Letter
        # ---------------------------------------------------------------------
        police_letter = f"""To,
The Station House Officer (SHO) / Cyber Crime Cell,
Police Department, Jurisdiction: {city_state}

SUBJECT: FORMAL COMPLAINT AND MANDATORY REGISTRATION OF ZERO FIR UNDER SECTION 173 OF BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS), 2023 / SECTION 154 CrPC

Respected Sir/Madam,

I, {complainant_name}, resident of {city_state}, hereby submit this formal complaint regarding serious cognizable offenses committed against me, and respectfully demand the prompt registration of a Zero FIR.

1. STATEMENT OF FACTS (RECORDED VIA TELL-ONCE INTAKE):
   - Incident Details: {what_happened}
   - Occurrence & Medium: {platform}
   - Perpetrator / Accused Information: {perpetrator}
   - Demands / Extortion / Proof: {demands}

2. STATUTORY LEGAL PROVISIONS APPLICABLE:
   - Information Technology Act, 2000:
     • Section 66E (Violation of privacy)
     • Section 67 & 67A (Transmitting sexually explicit / obscene material in electronic form)
   - Bharatiya Nyaya Sanhita (BNS), 2023:
     • Section 78 (Stalking - electronic or physical)
     • Section 79 (Acts/words intended to insult the modesty of a woman)
     • Section 308 (Extortion & putting person in fear of injury)
     • Section 351 (Criminal Intimidation)

3. MANDATORY ZERO FIR REGISTRATION JURISPRUDENCE:
   Pursuant to the landmark judgment of the Hon'ble Supreme Court of India in Lalita Kumari v. Govt. of U.P. [(2014) 2 SCC 1] and Section 173(1) of the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (formerly Section 154 CrPC), registration of an FIR is mandatory upon receipt of information disclosing a cognizable offense. If this police station lacks territorial jurisdiction, it is statutorily bound to register this as a "Zero FIR" and transfer the case to the appropriate jurisdiction forthwith.

4. PRESERVATION OF DIGITAL EVIDENCE (SECTION 94 BNSS / SECTION 91 CrPC):
   It is prayed that immediate preservation notices be served on intermediary platforms ({platform}) to freeze IP logs, session identifiers, SIM registration data, and communication transcripts before they can be deleted.

PRAYER:
Kindly register this complaint as a Zero FIR, initiate immediate investigation, and issue an official stamped acknowledgment copy with the GD/DD number to the complainant.

Yours faithfully,
{complainant_name}
Date: {today_str}
Location: {city_state}
"""

        # ---------------------------------------------------------------------
        # 2. Cyber Helpline 1930 / MHA Portal Quick Briefing Sheet
        # ---------------------------------------------------------------------
        cyber_brief = f"""================================================================================
NATIONAL CYBER CRIME REPORTING PORTAL (1930 / cybercrime.gov.in)
OPERATIONAL INTAKE BRIEFING SHEET (TELL-ONCE DOSSIER)
================================================================================
Generated Date: {today_str}
Jurisdiction: {city_state}
Complainant: {complainant_name}

INCIDENT SUMMARY:
• Category: {incident_type}
• Severity Level: HIGH / URGENT (Active Coercion)
• Platforms / Channels: {platform}
• Known Accused Handles / Identifiers: {perpetrator}

FACTUAL BRIEF FOR HELPLINE OPERATOR:
"{what_happened}. Perpetrator demands: {demands}."

IMMEDIATE OPERATIONAL ACTIONS REQUIRED:
1. Tag complaint under Cyber Financial / Extortion & Women Safety priority queue.
2. Issue intermediary preservation request to service providers ({platform}).
3. Prevent distribution of compromising or morphed media under IT Rules 2021 (24-hr takedown mandate).
4. Direct complainant to nearest cyber police station with Zero FIR reference.

OFFICIAL HELPLINE CONTACTS:
• National Cyber Crime Helpline: 1930 (MHA 24/7)
• Portal Reference: https://cybercrime.gov.in
================================================================================
"""

        # ---------------------------------------------------------------------
        # 3. Lawyer / Legal Counsel Case Summary
        # ---------------------------------------------------------------------
        lawyer_summary = f"""================================================================================
CONFIDENTIAL LEGAL BRIEF FOR ADVOCATE / LEGAL AID COUNSEL
================================================================================
Client / Complainant: {complainant_name}
Jurisdiction: {city_state}
Matter: Criminal Prosecution & Civil Protective Relief

1. CHRONOLOGY & CAUSE OF ACTION:
The client is experiencing targeted offenses: "{what_happened}". 
The communication originated on {platform} involving suspect {perpetrator}.
Extortion / Threats: "{demands}".

2. PENAL CHARGES TO DRAFT IN FORMAL PETITION:
• BNS 2023 Sec 78 (Stalking - non-bailable on second conviction)
• BNS 2023 Sec 79 (Outraging modesty of a woman)
• BNS 2023 Sec 308 (Extortion)
• BNS 2023 Sec 351 (Criminal Intimidation)
• IT Act Sec 66E, 67, 67A (Cognizable and non-bailable under Section 77B)

3. CIVIL & PROCEDURAL REMEDIES TO PURSUE:
• Mandatory Zero FIR Registration under Section 173(1) BNSS.
• Injunction / Intermediary Takedown: Rule 3(2)(b) of the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021 mandates takedown within 24 hours of receiving complaint of non-consensual sexual/intimate content.
• Digital Evidence Preservation Application under Section 94 BNSS.
• Protection Order under Protection of Women from Domestic Violence Act (PWDVA) Section 18 (if known domestic acquaintance).

4. ADVOCATE RECOMMENDATIONS:
Ensure that original metadata (EXIF tags, raw message headers, uncropped screenshots) are archived in the SafeMate Encrypted Vault.
================================================================================
"""

        evidence_checklist = [
            "Do NOT delete messages, voicemails, or threatening chats (they serve as primary proof).",
            "Take full screenshots including date, timestamp, and account handle/number.",
            "Copy full profile URLs (e.g., instagram.com/username) before accounts are changed.",
            "Export chat logs as .txt or .zip backup from messaging apps.",
            "Seal digital evidence in the SafeMate Evidence Vault with cryptographic SHA-256 stamp.",
        ]

        emergency_contacts = [
            {"service": "National Emergency Police", "number": "112", "action": "Immediate police dispatch"},
            {"service": "National Cyber Crime Helpline", "number": "1930", "action": "Financial freeze & cyber complaints"},
            {"service": "Women in Distress Helpline", "number": "1091 / 181", "action": "Crisis response & shelter"},
            {"service": "National Commission for Women (NCW)", "number": "7217735372", "action": "WhatsApp helpline"},
        ]

        support_msg = (
            "आपकी पूरी फाइल तैयार हो चुकी है। अब आपको अपनी कहानी किसी के सामने बार-बार दोहराने की आवश्यकता नहीं है। "
            "आप इस संपूर्ण डॉसियर (Dossier) को पुलिस, 1930 हेल्पलाइन या अपने वकील को एक क्लिक में दिखा सकती हैं।"
            if lang == "hi"
            else "Your Multi-Agency Dossier is ready. You never have to repeat your painful experience again. "
            "You can present this unified dossier directly to the police, helpline 1930, or your legal counsel."
        )

        return TellOnceDossierResponse(
            intake_id=intake_id,
            status="compiled",
            created_at=datetime.now(timezone.utc).isoformat(),
            language=lang,
            complainant_name=complainant_name,
            incident_type=incident_type,
            city_state=city_state,
            police_complaint_letter=police_letter,
            cyber_helpline_brief=cyber_brief,
            lawyer_case_summary=lawyer_summary,
            evidence_checklist=evidence_checklist,
            emergency_contacts=emergency_contacts,
            support_message=support_msg,
        )


# Global singleton instance
tell_once_service = TellOnceService()
