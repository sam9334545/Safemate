"""Structured safety, legal, and cybercrime conversation flows."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FlowChoice(BaseModel):
    """Suggested response chip or interactive button."""

    choice_id: str
    label: str
    description: Optional[str] = None
    next_step_id: Optional[str] = None
    target_flow_id: Optional[str] = None
    is_emergency: bool = False
    is_terminal: bool = False


class FlowStep(BaseModel):
    """Individual step within a guided safety flow."""

    step_id: str
    title: str
    guidance: str
    numbered_steps: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    choices: List[FlowChoice] = Field(default_factory=list)
    recommended_resource_ids: List[str] = Field(default_factory=list)
    safemate_feature_link: Optional[str] = None
    safemate_feature_name: Optional[str] = None
    safemate_feature_note: Optional[str] = None
    is_terminal: bool = False


class SafetyFlow(BaseModel):
    """Complete multi-step structured guidance flow."""

    flow_id: str
    title: str
    subtitle: str
    category: str
    icon: str
    initial_step_id: str
    steps: Dict[str, FlowStep]


# -----------------------------------------------------------------------------
# FLOW 1: Immediate Danger
# -----------------------------------------------------------------------------
FLOW_IMMEDIATE_DANGER = SafetyFlow(
    flow_id="immediate_danger",
    title="Immediate Danger",
    subtitle="Urgent steps for active physical threats, assault, or stalking",
    category="emergency",
    icon="shield-alert",
    initial_step_id="step_immediate_action",
    steps={
        "step_immediate_action": FlowStep(
            step_id="step_immediate_action",
            title="Prioritize Your Immediate Physical Safety",
            guidance=(
                "If you are in danger right now, your personal safety comes first above everything else. "
                "Move towards a safe, well-lit, or crowded place if you are able to do so safely."
            ),
            numbered_steps=[
                "Call 112 immediately for emergency police, medical, or fire response (pan-India).",
                "If you cannot speak, dial 112 and keep the call connected so the operator can register distress.",
                "Call 181 (Women Helpline) or 1091 (Women in Distress Police) for immediate crisis intervention.",
                "Alert someone nearby (shopkeeper, security guard, transit staff, or bystander).",
                "Contact a trusted friend or family member with your current location.",
            ],
            disclaimer=(
                "Safemate is a digital assistant and cannot automatically dispatch emergency services or track your live location "
                "unless an active emergency feature is confirmed by you. Please use direct emergency calling below."
            ),
            recommended_resource_ids=[
                "erss_112_in",
                "women_helpline_181_in",
                "police_women_1091_in",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_call_112",
                    label="Call 112 (Emergency)",
                    description="Immediate police, medical, and rescue assistance",
                    next_step_id="step_emergency_next",
                    is_emergency=True,
                ),
                FlowChoice(
                    choice_id="choice_sos_feature",
                    label="Use Safemate Emergency SOS",
                    description="View Safemate's Emergency SOS alert endpoint",
                    next_step_id="step_safemate_sos",
                ),
                FlowChoice(
                    choice_id="choice_safewalk",
                    label="Safemate SafeWalk Feature",
                    description="Share live trip monitoring with emergency contacts",
                    next_step_id="step_safewalk_info",
                ),
                FlowChoice(
                    choice_id="choice_return_options",
                    label="I am safe now — explore other options",
                    target_flow_id="understand_options",
                ),
            ],
        ),
        "step_emergency_next": FlowStep(
            step_id="step_emergency_next",
            title="While Help Is On The Way",
            guidance="Stay as calm as possible and focus on keeping yourself out of harm's reach.",
            numbered_steps=[
                "Stay on the call with the emergency dispatcher if safe to do so.",
                "Give clear landmarks (shop name, metro station, street junction).",
                "Keep phone volume adjusted so you can hear surroundings.",
                "If you are inside, lock doors and keep exit routes accessible.",
            ],
            disclaimer="Direct calling via device dialer (tel:112) is the fastest and most reliable emergency response.",
            recommended_resource_ids=["erss_112_in", "women_helpline_181_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_back_to_menu",
                    label="Explore Other Safety Guidance",
                    target_flow_id="understand_options",
                )
            ],
            is_terminal=True,
        ),
        "step_safemate_sos": FlowStep(
            step_id="step_safemate_sos",
            title="Safemate Emergency SOS",
            guidance=(
                "Safemate provides an Emergency SOS backend service (/api/v1/emergency/sos) to record distress alerts "
                "and notify configured emergency contacts."
            ),
            numbered_steps=[
                "Use the Emergency SOS button in the navigation header or the `/api/v1/emergency/sos` endpoint.",
                "Provide your active emergency contacts in your profile so they receive instant notification.",
                "Remember: Emergency SOS complements but does not replace dialing 112 directly.",
            ],
            safemate_feature_link="/api/v1/emergency/sos",
            safemate_feature_name="Emergency SOS Endpoint",
            safemate_feature_note="Requires configured contacts on backend; always prioritize calling 112 first.",
            choices=[
                FlowChoice(
                    choice_id="choice_back_immediate",
                    label="Back to Immediate Safety Steps",
                    next_step_id="step_immediate_action",
                ),
                FlowChoice(
                    choice_id="choice_to_options",
                    label="View Other Guidance Options",
                    target_flow_id="understand_options",
                ),
            ],
        ),
        "step_safewalk_info": FlowStep(
            step_id="step_safewalk_info",
            title="Safemate SafeWalk Active Monitoring",
            guidance=(
                "Safemate SafeWalk (/api/v1/safewalk/create-trip) allows you to generate a secure trip token and share "
                "periodic location pings with trusted contacts during night travel or unfamiliar routes."
            ),
            numbered_steps=[
                "Create a trip before beginning your commute to get a shareable tracking link.",
                "Designate expected arrival times so trusted contacts receive alerts if you fail to check in.",
                "If danger arises during a trip, use the instant SOS trigger or dial 112.",
            ],
            safemate_feature_link="/api/v1/safewalk/create-trip",
            safemate_feature_name="SafeWalk Trip Creator",
            safemate_feature_note="Shareable secure tracking token for trusted contacts.",
            choices=[
                FlowChoice(
                    choice_id="choice_back_immediate",
                    label="Back to Immediate Safety Steps",
                    next_step_id="step_immediate_action",
                )
            ],
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 2: Online Harassment
# -----------------------------------------------------------------------------
FLOW_ONLINE_HARASSMENT = SafetyFlow(
    flow_id="online_harassment",
    title="Online Harassment",
    subtitle="Guidance for persistent messaging, trolling, cyberstalking, or online threats",
    category="cyber_safety",
    icon="message-square-off",
    initial_step_id="step_harassment_triage",
    steps={
        "step_harassment_triage": FlowStep(
            step_id="step_harassment_triage",
            title="Determine Threat Level & Avoid Retaliation",
            guidance=(
                "Online harassment can feel overwhelming, but you are not alone. "
                "First, check whether the harasser has mentioned your physical location, workplace, or made threats of physical violence."
            ),
            numbered_steps=[
                "If there is any threat of physical harm or real-world stalking, treat this as an immediate emergency.",
                "Do not engage, debate, or retaliate against the harasser. Retaliation often escalates their behavior.",
                "Take a moment to step back. You do not need to read new messages immediately.",
            ],
            disclaimer="You do not have to decide immediately whether to file a formal police report. Preserving information first preserves your options.",
            recommended_resource_ids=["cybercrime_portal_in", "women_helpline_181_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_harass_immed",
                    label="There is a threat of physical harm",
                    target_flow_id="immediate_danger",
                    is_emergency=True,
                ),
                FlowChoice(
                    choice_id="choice_harass_evidence",
                    label="How do I safely document this?",
                    next_step_id="step_harassment_document",
                ),
                FlowChoice(
                    choice_id="choice_harass_platform",
                    label="How do I block or report on the platform?",
                    next_step_id="step_harassment_block",
                ),
                FlowChoice(
                    choice_id="choice_harass_police",
                    label="How do I report to Indian Cyber Police?",
                    target_flow_id="report_cybercrime_india",
                ),
            ],
        ),
        "step_harassment_document": FlowStep(
            step_id="step_harassment_document",
            title="Document Harassment Before Blocking",
            guidance=(
                "Before blocking the harasser or deleting messages, capture evidence. "
                "Once an account is deleted or blocked, certain message histories may disappear from your view."
            ),
            numbered_steps=[
                "Take full-screen screenshots showing the sender's username, profile handle, date, and exact timestamps.",
                "Copy the exact profile URL (e.g., https://instagram.com/username) rather than just the display name.",
                "Save original email headers if harassment occurs via email (these contain origin IP routing details).",
                "Store screenshots and notes in a secure private folder or Safemate Evidence Vault.",
            ],
            disclaimer="Do not alter, crop, or apply filters to screenshots. Preserving original unedited files maintains evidentiary value.",
            choices=[
                FlowChoice(
                    choice_id="choice_to_block",
                    label="Next: Block & restrict the harasser",
                    next_step_id="step_harassment_block",
                ),
                FlowChoice(
                    choice_id="choice_to_evidence_vault",
                    label="Learn about Safemate Evidence Vault",
                    target_flow_id="preserve_evidence",
                ),
            ],
        ),
        "step_harassment_block": FlowStep(
            step_id="step_harassment_block",
            title="Block, Restrict, and Secure Your Profile",
            guidance=(
                "Once you have documented the messages, take control of your digital space to protect your peace of mind."
            ),
            numbered_steps=[
                "Use the platform's in-app Report tool (select 'Harassment / Bullying / Hate Speech').",
                "Block the user across all connected platforms and email accounts.",
                "Switch personal profiles to 'Private' mode temporarily.",
                "Review your account privacy settings to restrict who can comment, tag you, or send direct messages.",
                "Turn on Two-Factor Authentication (2FA) with an authenticator app to protect your account.",
            ],
            disclaimer=(
                "Blocking an account stops direct messages but may not guarantee the individual will not create new accounts. "
                "If they create duplicate accounts, document each new handle as evidence of repeated stalking."
            ),
            recommended_resource_ids=["cybercrime_portal_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_to_cyber_report",
                    label="Official Cybercrime Reporting Guide",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_done_harassment",
                    label="Understand My Legal & Support Options",
                    target_flow_id="understand_options",
                ),
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 3: Blackmail or Threats
# -----------------------------------------------------------------------------
FLOW_BLACKMAIL_THREATS = SafetyFlow(
    flow_id="blackmail_threats",
    title="Blackmail or Threats",
    subtitle="Safe response to sextortion, monetary demands, coercion, or intimidation",
    category="cyber_safety",
    icon="alert-octagon",
    initial_step_id="step_blackmail_first",
    steps={
        "step_blackmail_first": FlowStep(
            step_id="step_blackmail_first",
            title="You Are Not at Fault — Do Not Pay or Panic",
            guidance=(
                "Receiving blackmail threats or extortion demands is terrifying, but please remember: "
                "You have done nothing wrong. Extortion is a serious criminal offense. "
                "Perpetrators rely on panic and shame to force compliance."
            ),
            numbered_steps=[
                "Do NOT pay any money or send additional images. Paying does not stop extortion; it usually leads to larger demands.",
                "Do not confront, plead, or negotiate with the blackmailer.",
                "Do not delete the conversation thread yet — the messages, payment handles, and phone numbers are crucial evidence.",
                "Confide in a trusted friend, family member, or specialized counselor.",
            ],
            disclaimer=(
                "Safemate will never judge you, blame you, or ask you to describe intimate details or upload explicit content."
            ),
            recommended_resource_ids=[
                "cybercrime_portal_in",
                "cyber_fraud_1930_in",
                "women_helpline_181_in",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_blackmail_evidence",
                    label="How to safely record extortion evidence",
                    next_step_id="step_blackmail_evidence",
                ),
                FlowChoice(
                    choice_id="choice_blackmail_financial",
                    label="They are demanding money / I paid money",
                    next_step_id="step_blackmail_financial",
                ),
                FlowChoice(
                    choice_id="choice_blackmail_ncii",
                    label="They are threatening to share private photos",
                    target_flow_id="intimate_image_abuse",
                ),
            ],
        ),
        "step_blackmail_evidence": FlowStep(
            step_id="step_blackmail_evidence",
            title="Safely Preserve Blackmail Evidence",
            guidance=(
                "Document everything systematically while keeping yourself emotionally and digitally protected."
            ),
            numbered_steps=[
                "Screenshot the entire chat, including the blackmailer's explicit threats and demands.",
                "Capture profile URLs, phone numbers, UPI IDs, cryptocurrency wallet addresses, or bank account numbers provided by the extortionist.",
                "Export chat history if the messaging app allows it.",
                "Store evidence in a password-protected location or Safemate Evidence Vault.",
            ],
            disclaimer="Never hack, retaliate, or attempt vigilante actions. This can jeopardize police investigation or compromise your security.",
            choices=[
                FlowChoice(
                    choice_id="choice_blackmail_report",
                    label="Next: How to report to Cyber Police",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_back_blackmail",
                    label="Back to Blackmail Safety Steps",
                    next_step_id="step_blackmail_first",
                ),
            ],
        ),
        "step_blackmail_financial": FlowStep(
            step_id="step_blackmail_financial",
            title="Financial Extortion & Fraud Response",
            guidance=(
                "If money was demanded or transferred under threat, immediate reporting can help freeze fraudulent accounts."
            ),
            numbered_steps=[
                "Dial 1930 immediately (National Cyber Financial Fraud Helpline in India).",
                "Have your transaction ID, bank account / UPI ID, and transfer timestamp ready.",
                "Contact your bank or payment app's fraud helpline to lodge an unauthorized/coerced transaction complaint.",
                "File a formal report on https://cybercrime.gov.in/ under Financial Fraud / Extortion.",
            ],
            recommended_resource_ids=["cyber_fraud_1930_in", "cybercrime_portal_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_blackmail_cyber_flow",
                    label="Guide: Reporting on cybercrime.gov.in",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_options_fin",
                    label="Understand My Legal & Support Options",
                    target_flow_id="understand_options",
                ),
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 4: Non-consensual Image or Video Sharing
# -----------------------------------------------------------------------------
FLOW_INTIMATE_IMAGE_ABUSE = SafetyFlow(
    flow_id="intimate_image_abuse",
    title="Non-consensual Image Sharing",
    subtitle="Actions for intimate image abuse, deepfake morphing, or unauthorized sharing",
    category="cyber_safety",
    icon="image-off",
    initial_step_id="step_ncii_triage",
    steps={
        "step_ncii_triage": FlowStep(
            step_id="step_ncii_triage",
            title="Supportive, Non-Judgemental Support",
            guidance=(
                "Having private images or synthetic media shared without your consent is a grave violation of your privacy and dignity. "
                "You are the victim of a crime, not the cause. You never have to share or upload explicit images with Safemate."
            ),
            numbered_steps=[
                "Take a deep breath — there are verified technologies and legal channels specifically designed to stop image spread.",
                "Do not blame yourself. Non-consensual sharing and AI morphing are criminal offenses under Indian IT Act (Sec 66E, 67, 67A) and BNS/IPC.",
                "Explore StopNCII.org (for adults) or Take It Down (for minors) to stop images from appearing on major platforms.",
            ],
            disclaimer=(
                "Safemate's AI detection tools (/api/v1/detect and /api/v1/deepfake/detect) are technical screening tools. "
                "They provide probabilistic indicators and do not establish legal proof, consent, or abuse."
            ),
            recommended_resource_ids=[
                "stopncii_global",
                "takeitdown_global",
                "cybercrime_portal_in",
                "ncw_helpline_in",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_stopncii_info",
                    label="How StopNCII.org Works (Adults 18+)",
                    next_step_id="step_ncii_stopncii",
                ),
                FlowChoice(
                    choice_id="choice_takeitdown_info",
                    label="Take It Down Tool (Under 18)",
                    next_step_id="step_ncii_takeitdown",
                ),
                FlowChoice(
                    choice_id="choice_ncii_legal_in",
                    label="Report to Cybercrime Against Women & Children",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_safemate_screening",
                    label="About Safemate Screening Tools",
                    next_step_id="step_ncii_screening_limits",
                ),
            ],
        ),
        "step_ncii_stopncii": FlowStep(
            step_id="step_ncii_stopncii",
            title="StopNCII.org: Prevent Image Sharing on Major Platforms",
            guidance=(
                "StopNCII.org is an internationally recognized, free platform operated by the UK Revenge Porn Helpline and SWGfL, "
                "supported by major tech platforms (Meta, Instagram, Facebook, Threads, TikTok, Bumble, Reddit, OnlyFans)."
            ),
            numbered_steps=[
                "Visit https://stopncii.org/ directly from your browser.",
                "Your image NEVER leaves your device. The website creates a unique digital fingerprint (cryptographic hash) in your browser.",
                "Only the numerical hash is shared with participating platforms.",
                "If someone attempts to upload matching media, participating platforms block the upload automatically.",
                "Keep your case reference PIN safe so you can manage your case.",
            ],
            disclaimer="StopNCII.org is for adults 18+. Images must still be in your possession on your device to generate the hash.",
            recommended_resource_ids=["stopncii_global"],
            choices=[
                FlowChoice(
                    choice_id="choice_to_cyber_report_ncii",
                    label="Official Police Reporting (cybercrime.gov.in)",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_back_ncii",
                    label="Back to NCII Options",
                    next_step_id="step_ncii_triage",
                ),
            ],
        ),
        "step_ncii_takeitdown": FlowStep(
            step_id="step_ncii_takeitdown",
            title="Take It Down (NCMEC): Content Involving Anyone Under 18",
            guidance=(
                "If the image or video depicts someone who was under 18 at the time, Take It Down by the National Center for Missing & Exploited Children (NCMEC) provides free anonymous protection."
            ),
            numbered_steps=[
                "Visit https://takeitdown.ncmec.org/.",
                "Generates an anonymous numerical hash locally on your device.",
                "Works with participating platforms to remove existing posts and prevent re-uploads.",
                "In India, any explicit content involving minors also falls under the stringent POCSO Act and Section 67B of the IT Act.",
            ],
            recommended_resource_ids=["takeitdown_global", "childline_1098_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_back_ncii",
                    label="Back to NCII Options",
                    next_step_id="step_ncii_triage",
                )
            ],
        ),
        "step_ncii_screening_limits": FlowStep(
            step_id="step_ncii_screening_limits",
            title="Safemate Screening Tools & Their Limitations",
            guidance=(
                "Safemate provides optional AI screening endpoints for research and risk screening:\n"
                "- Still-Image Screening: `/api/v1/detect`\n"
                "- Video Deepfake Screening: `/api/v1/deepfake/detect`"
            ),
            numbered_steps=[
                "These screening tools produce confidence scores, not definitive legal proof.",
                "Never rely solely on an AI score to decide legal authenticity in court.",
                "You are never required or pressured to upload intimate media to Safemate.",
                "If you need legal assistance, official forensic labs designated by law enforcement are the recognized evidentiary standard.",
            ],
            disclaimer="Safemate does not store or distribute uploaded screening files.",
            choices=[
                FlowChoice(
                    choice_id="choice_back_ncii",
                    label="Back to NCII Options",
                    next_step_id="step_ncii_triage",
                )
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 5: Fake Profile or Impersonation
# -----------------------------------------------------------------------------
FLOW_IMPERSONATION = SafetyFlow(
    flow_id="impersonation_fake_profile",
    title="Fake Profile or Impersonation",
    subtitle="Handling clone accounts, identity theft, or impersonation scams",
    category="cyber_safety",
    icon="user-x",
    initial_step_id="step_impersonation_action",
    steps={
        "step_impersonation_action": FlowStep(
            step_id="step_impersonation_action",
            title="Steps to Take Down Fake Profiles",
            guidance=(
                "If someone has created an account using your name, photos, or personal info, act promptly to document and take it down."
            ),
            numbered_steps=[
                "Document the account first: copy the exact profile link and take full-page screenshots showing username, bio, and photos.",
                "Use the platform's official Impersonation Reporting form (e.g., Instagram/Facebook 'Someone is pretending to be me').",
                "Alert close friends and contacts via an alternative channel to prevent them from falling for scams or requests for money.",
                "Review and secure your own original account — enable Two-Factor Authentication and check connected devices.",
            ],
            disclaimer=(
                "Never share passwords, 2FA codes, or SMS OTPs with anyone claiming to help you recover or remove accounts."
            ),
            recommended_resource_ids=["cybercrime_portal_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_imper_evidence",
                    label="How to preserve profile evidence safely",
                    target_flow_id="preserve_evidence",
                ),
                FlowChoice(
                    choice_id="choice_imper_cybercrime",
                    label="Report to Cyber Crime (if fraud/defamation involved)",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_imper_options",
                    label="Understand My Options",
                    target_flow_id="understand_options",
                ),
            ],
            is_terminal=True,
        )
    },
)

# -----------------------------------------------------------------------------
# FLOW 6: Physical Harassment
# -----------------------------------------------------------------------------
FLOW_PHYSICAL_HARASSMENT = SafetyFlow(
    flow_id="physical_harassment",
    title="Physical Harassment",
    subtitle="Safety and reporting for eve-teasing, workplace harassment, or street stalking",
    category="physical_safety",
    icon="shield",
    initial_step_id="step_physical_triage",
    steps={
        "step_physical_triage": FlowStep(
            step_id="step_physical_triage",
            title="Assess Current Safety & Available Help",
            guidance=(
                "If you are experiencing harassment in public, at work, or near your residence, your physical safety is the priority."
            ),
            numbered_steps=[
                "If in immediate danger or being actively followed, call 112 or 1091 (Women Police Helpline) immediately.",
                "Move to a public space with other people, security personnel, or open commercial establishments.",
                "If harassment occurs at work, you have the right to file a complaint before the Internal Complaints Committee (ICC) under the POSH Act, 2013.",
                "Keep a discrete record of dates, times, locations, and descriptions of recurring incidents.",
            ],
            disclaimer="Never confront an aggressive harasser alone if there is risk of physical violence.",
            recommended_resource_ids=[
                "erss_112_in",
                "police_women_1091_in",
                "women_helpline_181_in",
                "ncw_helpline_in",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_phys_urgent",
                    label="I am in danger right now",
                    target_flow_id="immediate_danger",
                    is_emergency=True,
                ),
                FlowChoice(
                    choice_id="choice_phys_safewalk",
                    label="Use SafeWalk Trip Monitoring",
                    next_step_id="step_physical_safewalk",
                ),
                FlowChoice(
                    choice_id="choice_phys_options",
                    label="Explore Legal & Support Services",
                    target_flow_id="understand_options",
                ),
            ],
        ),
        "step_physical_safewalk": FlowStep(
            step_id="step_physical_safewalk",
            title="Safemate SafeWalk Assistance",
            guidance=(
                "SafeWalk allows you to share live travel status with your trusted contacts during commutes."
            ),
            numbered_steps=[
                "Create a trip before departing via `/api/v1/safewalk/create-trip`.",
                "Share the trip link with a friend or family member.",
                "If you feel uneasy, you can trigger Emergency SOS immediately.",
            ],
            safemate_feature_link="/api/v1/safewalk/create-trip",
            safemate_feature_name="SafeWalk Feature",
            choices=[
                FlowChoice(
                    choice_id="choice_back_phys",
                    label="Back to Physical Harassment Guidance",
                    next_step_id="step_physical_triage",
                )
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 7: Reporting Cybercrime in India
# -----------------------------------------------------------------------------
FLOW_REPORT_CYBERCRIME_INDIA = SafetyFlow(
    flow_id="report_cybercrime_india",
    title="Report Cybercrime in India",
    subtitle="Official, step-by-step walkthrough for cybercrime.gov.in and helpline 1930",
    category="reporting",
    icon="file-text",
    initial_step_id="step_cyber_overview",
    steps={
        "step_cyber_overview": FlowStep(
            step_id="step_cyber_overview",
            title="Official National Cyber Crime Reporting Portal",
            guidance=(
                "In India, cybercrimes are officially reported through the Ministry of Home Affairs (MHA) portal: "
                "https://cybercrime.gov.in/ or the national helpline 1930."
            ),
            numbered_steps=[
                "Visit the official website: https://cybercrime.gov.in/.",
                "Choose the appropriate reporting track:\n"
                "  • 'Report Crime Related to Women / Child' (Provides options to Report Anonymously or Report & Track).\n"
                "  • 'Report Financial Fraud' (For monetary extortion or phishing).\n"
                "  • 'Report Other Cyber Crimes' (For stalking, hacking, defamation).",
                "Read the terms and verify you are on the official `.gov.in` domain.",
            ],
            disclaimer=(
                "Safemate is an independent safety assistant and cannot submit complaints on your behalf. "
                "Complaints must be submitted directly on the official government portal."
            ),
            recommended_resource_ids=["cybercrime_portal_in", "cyber_fraud_1930_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_prep_info",
                    label="What documents/info should I prepare?",
                    next_step_id="step_cyber_prepare",
                ),
                FlowChoice(
                    choice_id="choice_women_child_track",
                    label="Reporting Anonymously vs Report & Track",
                    next_step_id="step_cyber_anon_vs_track",
                ),
                FlowChoice(
                    choice_id="choice_evidence_tips",
                    label="Evidence Preservation Guidance",
                    target_flow_id="preserve_evidence",
                ),
            ],
        ),
        "step_cyber_prepare": FlowStep(
            step_id="step_cyber_prepare",
            title="Information to Prepare Before Lodging Complaint",
            guidance=(
                "Having the required information organized will make filing your report smoother and faster:"
            ),
            numbered_steps=[
                "Suspect Information: Suspect's profile username, profile URL, mobile number, email address, or bank details if known.",
                "Incident Details: Exact date, approximate time, and chronological description of the event.",
                "Evidence Files: Screenshots of messages/posts, URL links, original email files, or transaction receipts (PDF/JPEG/PNG).",
                "Valid Mobile Number: For receiving OTP and complaint acknowledgment SMS (if choosing Report & Track).",
            ],
            disclaimer="Never fabricate details. State only factual occurrences.",
            choices=[
                FlowChoice(
                    choice_id="choice_to_track_info",
                    label="Next: How to track after submitting",
                    next_step_id="step_cyber_after_submission",
                ),
                FlowChoice(
                    choice_id="choice_back_overview",
                    label="Back to Portal Overview",
                    next_step_id="step_cyber_overview",
                ),
            ],
        ),
        "step_cyber_anon_vs_track": FlowStep(
            step_id="step_cyber_anon_vs_track",
            title="Report Anonymously vs Report & Track",
            guidance=(
                "The portal offers two options for 'Women / Child' reporting:"
            ),
            numbered_steps=[
                "Report Anonymously: Does not require your personal details or OTP verification. Suitable if you fear reprisal and only want abusive content blocked. However, police cannot contact you for follow-up investigation or provide status updates.",
                "Report & Track: Requires mobile OTP and basic complainant details. Acknowledgment number is generated, allowing you to track investigation status and follow up with the assigned state cyber police cell.",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_to_after_sub",
                    label="Next: After Submitting Your Report",
                    next_step_id="step_cyber_after_submission",
                )
            ],
        ),
        "step_cyber_after_submission": FlowStep(
            step_id="step_cyber_after_submission",
            title="After Submitting: Acknowledgement & Follow-Up",
            guidance=(
                "Once you submit a report on cybercrime.gov.in, note down the following:"
            ),
            numbered_steps=[
                "Save your Complaint Acknowledgment Number and download a PDF copy of the complaint summary.",
                "Your complaint is assigned to the state/district cyber police station based on your jurisdiction.",
                "You may be contacted by an investigating officer (IO) to verify facts or provide original evidence files.",
                "If urgent action is delayed, you can escalate through the National Commission for Women (NCW) or your local District Police Superintendent.",
            ],
            recommended_resource_ids=["ncw_helpline_in", "cybercrime_portal_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_finish_cyber",
                    label="Explore Other Safety Options",
                    target_flow_id="understand_options",
                )
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 8: Preserve Evidence Safely
# -----------------------------------------------------------------------------
FLOW_PRESERVE_EVIDENCE = SafetyFlow(
    flow_id="preserve_evidence",
    title="Preserve Evidence Safely",
    subtitle="Best practices for screenshots, message exports, and Safemate Evidence Vault",
    category="evidence",
    icon="archive",
    initial_step_id="step_evidence_basics",
    steps={
        "step_evidence_basics": FlowStep(
            step_id="step_evidence_basics",
            title="General Evidence Preservation Standards",
            guidance=(
                "Digital evidence can be ephemeral. Preserving it safely ensures you have credible records if you choose to take formal action."
            ),
            numbered_steps=[
                "Keep original files: Never crop, edit, compress, or use drawing tools on screenshots.",
                "Capture context: Include device status bar, clock, date, and full username handles.",
                "Record URLs: Full web address (e.g. `https://instagram.com/p/xxx`) is more valuable than just a screenshot.",
                "Export complete chats: Use messaging app 'Export Chat' with media where available.",
                "Do NOT put yourself in physical danger or breach any laws/privacy to obtain evidence.",
            ],
            disclaimer=(
                "Evidence preservation is for your protection. Safemate does not certify legal admissibility in a court of law; "
                "formal admissibility in Indian courts is governed by Section 65B of the Indian Evidence Act / Section 63 of Bharatiya Sakshya Adhiniyam (BSA)."
            ),
            choices=[
                FlowChoice(
                    choice_id="choice_vault_details",
                    label="Using Safemate Evidence Vault",
                    next_step_id="step_evidence_safemate_vault",
                ),
                FlowChoice(
                    choice_id="choice_offline_backup",
                    label="Safe offline & cloud backup tips",
                    next_step_id="step_evidence_backup",
                ),
                FlowChoice(
                    choice_id="choice_back_to_reporting",
                    label="How to report using preserved evidence",
                    target_flow_id="report_cybercrime_india",
                ),
            ],
        ),
        "step_evidence_safemate_vault": FlowStep(
            step_id="step_evidence_safemate_vault",
            title="Safemate Evidence Vault Feature",
            guidance=(
                "Safemate includes a backend endpoint (`/api/v1/evidence/upload`) to upload and catalog incident metadata, "
                "notes, and media hashes."
            ),
            numbered_steps=[
                "Upload incident records and files through the Evidence Vault interface or API.",
                "Keep your own independent offline copy as well (e.g., password-protected USB drive or private drive).",
                "Safemate provides digital preservation assistance; it does NOT automatically dispatch police or transmit evidence to authorities without your action.",
            ],
            safemate_feature_link="/api/v1/evidence/upload",
            safemate_feature_name="Evidence Vault API",
            safemate_feature_note="Secure upload endpoint for incident documentation.",
            choices=[
                FlowChoice(
                    choice_id="choice_back_basics",
                    label="Back to Evidence Basics",
                    next_step_id="step_evidence_basics",
                ),
                FlowChoice(
                    choice_id="choice_to_options",
                    label="Explore Legal Options",
                    target_flow_id="understand_options",
                ),
            ],
            is_terminal=True,
        ),
        "step_evidence_backup": FlowStep(
            step_id="step_evidence_backup",
            title="Safe Storage & Redundancy",
            guidance=(
                "Ensure your evidence cannot be accidentally deleted, synced away, or accessed by the person harassing you."
            ),
            numbered_steps=[
                "Create a separate, secure email account or private cloud folder with a strong, unique password and 2FA.",
                "If sharing a device or computer with someone unsafe, use private/incognito browsing or store copies on an encrypted external drive.",
                "Share a backup copy with a trusted family member, close friend, or legal advisor.",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_back_basics",
                    label="Back to Evidence Basics",
                    next_step_id="step_evidence_basics",
                )
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW 9: Understand My Options
# -----------------------------------------------------------------------------
FLOW_UNDERSTAND_OPTIONS = SafetyFlow(
    flow_id="understand_options",
    title="Understand My Options",
    subtitle="Overview of safety pathways, legal protections, and choosing when to act",
    category="general_support",
    icon="compass",
    initial_step_id="step_options_overview",
    steps={
        "step_options_overview": FlowStep(
            step_id="step_options_overview",
            title="Navigating Your Choices with Dignity",
            guidance=(
                "Every situation is unique, and you have the power to decide what pace and approach feel right for you. "
                "Here are the primary pathways available:"
            ),
            numbered_steps=[
                "1. Immediate Protection: If you are at physical risk, focus on safety first (Call 112, reach trusted contacts, activate SafeWalk).",
                "2. Platform Remedies: Block, report, and remove content through platform tools, StopNCII.org, or Take It Down.",
                "3. Safe Preservation: Save records quietly in case you want to take formal action later.",
                "4. Formal Legal Reporting: File a complaint via cybercrime.gov.in, National Commission for Women (NCW), or your local police station.",
                "5. Confidential Support: Talk to a counselor or helpline (181) without committing to a police case.",
                "6. Choosing Not to Proceed Immediately: It is completely valid to pause, rest, and decide later.",
            ],
            disclaimer=(
                "Safemate provides general legal information and safety guidance, not formal legal advice. "
                "For legal representation, consult a qualified advocate or the Legal Services Authority (DLSA/SLSA)."
            ),
            recommended_resource_ids=[
                "women_helpline_181_in",
                "ncw_helpline_in",
                "cybercrime_portal_in",
            ],
            choices=[
                FlowChoice(
                    choice_id="choice_opt_legal_rights",
                    label="Key Protections Under Indian Law",
                    next_step_id="step_options_legal_in",
                ),
                FlowChoice(
                    choice_id="choice_opt_cyber_guide",
                    label="Step-by-step Cybercrime Reporting",
                    target_flow_id="report_cybercrime_india",
                ),
                FlowChoice(
                    choice_id="choice_opt_evidence",
                    label="Preserving Evidence Safely",
                    target_flow_id="preserve_evidence",
                ),
                FlowChoice(
                    choice_id="choice_opt_emergency",
                    label="Immediate Danger Resources",
                    target_flow_id="immediate_danger",
                    is_emergency=True,
                ),
            ],
        ),
        "step_options_legal_in": FlowStep(
            step_id="step_options_legal_in",
            title="Key Legal Protections Under Indian Law",
            guidance=(
                "Indian law provides several dedicated legal provisions to protect women and digital safety:"
            ),
            numbered_steps=[
                "Zero FIR: You can file an FIR at ANY police station in India, regardless of where the incident occurred. The station must register the Zero FIR and transfer it to the jurisdictional station.",
                "Information Technology Act, 2000:\n"
                "  • Sec 66E: Violation of privacy by capturing/publishing private area images without consent.\n"
                "  • Sec 67 & 67A: Publishing or transmitting obscene or sexually explicit material electronically.\n"
                "  • Sec 67B: Offenses related to child sexual abuse material (CSAM).",
                "Bharatiya Nyaya Sanhita (BNS) / IPC:\n"
                "  • Provisions against stalking, harassment, voyeurism, criminal intimidation, and word/gesture insulting the modesty of a woman.",
                "Free Legal Aid: Under the Legal Services Authorities Act (NALSA), women are entitled to free legal aid from District Legal Services Authorities (DLSA).",
            ],
            disclaimer=(
                "These provisions are summarized for awareness. Interpretation varies based on specific case facts. "
                "Consult a licensed legal professional for tailored legal advice."
            ),
            recommended_resource_ids=["ncw_helpline_in", "women_helpline_181_in"],
            choices=[
                FlowChoice(
                    choice_id="choice_back_options",
                    label="Back to Options Overview",
                    next_step_id="step_options_overview",
                )
            ],
            is_terminal=True,
        ),
    },
)

# -----------------------------------------------------------------------------
# FLOW REGISTRY
# -----------------------------------------------------------------------------
SAFETY_FLOWS: Dict[str, SafetyFlow] = {
    FLOW_IMMEDIATE_DANGER.flow_id: FLOW_IMMEDIATE_DANGER,
    FLOW_ONLINE_HARASSMENT.flow_id: FLOW_ONLINE_HARASSMENT,
    FLOW_BLACKMAIL_THREATS.flow_id: FLOW_BLACKMAIL_THREATS,
    FLOW_INTIMATE_IMAGE_ABUSE.flow_id: FLOW_INTIMATE_IMAGE_ABUSE,
    FLOW_IMPERSONATION.flow_id: FLOW_IMPERSONATION,
    FLOW_PHYSICAL_HARASSMENT.flow_id: FLOW_PHYSICAL_HARASSMENT,
    FLOW_REPORT_CYBERCRIME_INDIA.flow_id: FLOW_REPORT_CYBERCRIME_INDIA,
    FLOW_PRESERVE_EVIDENCE.flow_id: FLOW_PRESERVE_EVIDENCE,
    FLOW_UNDERSTAND_OPTIONS.flow_id: FLOW_UNDERSTAND_OPTIONS,
}


def get_flow(flow_id: str) -> Optional[SafetyFlow]:
    """Retrieve a safety flow by ID."""
    return SAFETY_FLOWS.get(flow_id)


def list_flows() -> List[SafetyFlow]:
    """List all registered safety guidance flows."""
    return list(SAFETY_FLOWS.values())
