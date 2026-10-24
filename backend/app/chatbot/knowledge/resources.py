"""Verified emergency, legal, and cybercrime reporting resources."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SafetyResource(BaseModel):
    """Schema for a verified safety or legal resource."""

    resource_id: str
    country: str = "IN"  # ISO 3166-1 alpha-2 code
    category: str  # emergency, women_helpline, cybercrime, ncii_removal, legal_aid, general
    display_name: str
    phone_number: Optional[str] = None
    action_url: Optional[str] = None
    description: str
    intended_use: str
    verification_source: str
    last_verified: str = "2026-10-24"
    availability_caveat: str
    is_emergency: bool = False


# -----------------------------------------------------------------------------
# Curated Verified Resources Database
# -----------------------------------------------------------------------------
VERIFIED_RESOURCES: Dict[str, SafetyResource] = {
    # 1. India - Emergency Services
    "erss_112_in": SafetyResource(
        resource_id="erss_112_in",
        country="IN",
        category="emergency",
        display_name="National Emergency Response Support System (ERSS 112)",
        phone_number="112",
        action_url="https://112.gov.in/",
        description="Unified 24x7 emergency helpline for police, fire, ambulance, and disaster assistance across all Indian states and union territories.",
        intended_use="Immediate physical danger, active assault, life-threatening emergency, or urgent police intervention.",
        verification_source="Ministry of Home Affairs (MHA), Government of India (https://112.gov.in/)",
        availability_caveat="Toll-free, 24x7, pan-India coverage.",
        is_emergency=True,
    ),
    # 2. India - Women Helpline
    "women_helpline_181_in": SafetyResource(
        resource_id="women_helpline_181_in",
        country="IN",
        category="women_helpline",
        display_name="Women Helpline (WHL 181)",
        phone_number="181",
        action_url="https://wcd.nic.in/",
        description="24x7 toll-free telephonic helpline providing integrated support, rescue, crisis counseling, and referral to women affected by violence.",
        intended_use="Domestic violence, harassment, stalking, emotional crisis, and referral to One Stop Centres (Sakhi).",
        verification_source="Ministry of Women and Child Development (MWCD), Government of India",
        availability_caveat="Toll-free, 24x7 in most states; operational availability may vary by telecom operator or regional hub.",
        is_emergency=True,
    ),
    # 3. India - Police Women Safety Helpline
    "police_women_1091_in": SafetyResource(
        resource_id="police_women_1091_in",
        country="IN",
        category="women_helpline",
        display_name="Women in Distress Police Helpline (1091)",
        phone_number="1091",
        action_url="https://police.gov.in/",
        description="Dedicated police helpline for women facing harassment, stalking, or domestic distress.",
        intended_use="Urgent police assistance and reporting of harassment or stalking.",
        verification_source="State Police Departments / National Crime Records Bureau (NCRB)",
        availability_caveat="24x7 toll-free in major cities and states across India.",
        is_emergency=True,
    ),
    # 4. India - National Cyber Crime Reporting Portal
    "cybercrime_portal_in": SafetyResource(
        resource_id="cybercrime_portal_in",
        country="IN",
        category="cybercrime",
        display_name="National Cyber Crime Reporting Portal (cybercrime.gov.in)",
        phone_number="1930",
        action_url="https://cybercrime.gov.in/",
        description="Official Government of India portal to report cybercrimes, with dedicated priority channels for 'Cyber Crime Against Women & Children'.",
        intended_use="Formal reporting of cyber harassment, cyber stalking, blackmail, morphing, and non-consensual intimate image sharing.",
        verification_source="Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs, Government of India",
        availability_caveat="Online portal is accessible 24x7; complaints are routed to the relevant state cyber police jurisdiction.",
        is_emergency=False,
    ),
    # 5. India - Cyber Financial Fraud Helpline
    "cyber_fraud_1930_in": SafetyResource(
        resource_id="cyber_fraud_1930_in",
        country="IN",
        category="cybercrime",
        display_name="National Cyber Financial Fraud Helpline (1930)",
        phone_number="1930",
        action_url="https://cybercrime.gov.in/",
        description="Dedicated government helpline to immediately freeze fraudulently siphoned funds or report cyber extortion involving money.",
        intended_use="Reporting financial extortion, urgent cyber fraud, and immediate bank freeze requests.",
        verification_source="Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs",
        availability_caveat="Operates with maximum effectiveness if called within the 'golden hour' following unauthorized financial transfers.",
        is_emergency=False,
    ),
    # 6. India - National Commission for Women (NCW)
    "ncw_helpline_in": SafetyResource(
        resource_id="ncw_helpline_in",
        country="IN",
        category="legal_aid",
        display_name="National Commission for Women 24x7 Helpline",
        phone_number="7827170170",
        action_url="http://ncw.nic.in/",
        description="Statutory body providing grievance redressal, legal guidance, and counseling support to women facing abuse, discrimination, or violence.",
        intended_use="Escalation of unresolved police complaints, legal aid referrals, and formal grievance submissions.",
        verification_source="National Commission for Women (NCW), Government of India (http://ncw.nic.in/)",
        availability_caveat="24x7 helpline operating nationwide.",
        is_emergency=False,
    ),
    # 7. India - Childline
    "childline_1098_in": SafetyResource(
        resource_id="childline_1098_in",
        country="IN",
        category="emergency",
        display_name="Childline India (1098)",
        phone_number="1098",
        action_url="https://wcd.nic.in/",
        description="24-hour, free, emergency phone service for children in need of aid, protection, and rescue.",
        intended_use="Minors facing abuse, exploitation, cyberbullying, or urgent distress.",
        verification_source="Ministry of Women and Child Development, Government of India",
        availability_caveat="Toll-free, 24x7 nationwide.",
        is_emergency=True,
    ),
    # 8. Global - StopNCII.org
    "stopncii_global": SafetyResource(
        resource_id="stopncii_global",
        country="GLOBAL",
        category="ncii_removal",
        display_name="StopNCII.org (Non-Consensual Intimate Image Prevention)",
        phone_number=None,
        action_url="https://stopncii.org/",
        description="Free, privacy-preserving tool operated by SWGfL that generates cryptographic perceptual hashes on your own device to prevent the sharing of intimate images on participating tech platforms.",
        intended_use="Preventing the spread of intimate images or videos on major tech platforms (Meta, TikTok, Bumble, Reddit, OnlyFans, etc.). Does not require uploading actual photos.",
        verification_source="Revenge Porn Helpline / South West Grid for Learning (SWGfL) (https://stopncii.org/)",
        availability_caveat="Works only on participating platforms for adults (18+). Uses client-side hashing so private media never leaves your device.",
        is_emergency=False,
    ),
    # 9. Global - Take It Down (NCMEC)
    "takeitdown_global": SafetyResource(
        resource_id="takeitdown_global",
        country="GLOBAL",
        category="ncii_removal",
        display_name="Take It Down by NCMEC (For Minors)",
        phone_number=None,
        action_url="https://takeitdown.ncmec.org/",
        description="Anonymous tool to help remove or prevent the posting of sexually explicit images and videos taken of anyone under 18.",
        intended_use="Assisting young people or parents to remove explicit content depicting anyone under 18 from public platforms.",
        verification_source="National Center for Missing & Exploited Children (NCMEC) (https://takeitdown.ncmec.org/)",
        availability_caveat="Dedicated to individuals under 18 years old or images taken when under 18.",
        is_emergency=False,
    ),
    # 10. Global - Emergency Fallback
    "emergency_global": SafetyResource(
        resource_id="emergency_global",
        country="GLOBAL",
        category="emergency",
        display_name="Local Emergency Police & Ambulance",
        phone_number="112",
        action_url="https://en.wikipedia.org/wiki/List_of_emergency_telephone_numbers",
        description="International standard emergency number (112 / 911 / 999) to connect with immediate emergency response services.",
        intended_use="Immediate life-threatening danger, ongoing assault, or urgent physical risk.",
        verification_source="International Telecommunication Union (ITU)",
        availability_caveat="Varies by country (112 in EU/India, 911 in US/Canada, 000 in Australia, 999 in UK).",
        is_emergency=True,
    ),
}


def get_resources_by_country(country_code: str = "IN") -> List[SafetyResource]:
    """Retrieve verified safety resources for a specific country with global fallbacks."""
    normalized_code = country_code.strip().upper()
    country_resources = [
        res for res in VERIFIED_RESOURCES.values() if res.country == normalized_code
    ]
    global_resources = [
        res for res in VERIFIED_RESOURCES.values() if res.country == "GLOBAL"
    ]
    return country_resources + global_resources


def get_emergency_resources(country_code: str = "IN") -> List[SafetyResource]:
    """Retrieve only the emergency-priority resources for immediate display."""
    all_res = get_resources_by_country(country_code)
    return [r for r in all_res if r.is_emergency]
