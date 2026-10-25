/**
 * SafeMate - Centralized Demo Data Module
 * 
 * Provides consistent, realistic, fictional sample data for judges, evaluators,
 * and visitors exploring SafeMate without credentials or when backend is offline.
 * 
 * ALL DATA IN THIS MODULE IS STRICTLY FICTIONAL AND CLEARLY MARKED AS DEMO/SIMULATED.
 * Never connects to real emergency contacts or external APIs.
 */

export const DEMO_USER = {
  id: 'demo_judge_999',
  email: 'judge.evaluator@safemate.demo',
  full_name: 'Judge Evaluator',
  access_mode: 'demo',
  is_guest: false,
  is_active: true,
  role: 'demo_judge',
  created_at: '2026-10-25T10:00:00Z',
  badge: 'DEMO EVALUATOR'
};

export const DEMO_METRICS = {
  safetyScore: 96,
  vaultFiles: 4,
  activeTrips: 1,
  safetyCircleCount: 3,
  recentAlerts: 0,
  verifiedSignatures: 4,
  systemStatus: 'Operating in Demo Simulation Mode'
};

export const DEMO_SAFEWALK_TRIPS = [
  {
    id: 901,
    trip_id: 'sw_demo_8801',
    user_id: 'demo_judge_999',
    destination: 'North Campus Residence Hall, Block C',
    eta_minutes: 15,
    status: 'in_progress',
    tracking_token: 'sw_token_demo_eval_8801',
    created_at: new Date(Date.now() - 6 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    start_latitude: 28.5456,
    start_longitude: 77.1926,
    current_latitude: 28.5482,
    current_longitude: 77.1951,
    target_latitude: 28.5520,
    target_longitude: 77.1990,
    breadcrumbs: JSON.stringify([
      { lat: 28.5456, lng: 77.1926, time: '6m ago', note: 'Trip departed from Central Library' },
      { lat: 28.5469, lng: 77.1938, time: '3m ago', note: 'Passed Main Academic Gate' },
      { lat: 28.5482, lng: 77.1951, time: 'Just now', note: 'Current position on North Walkway' }
    ]),
    is_demo: true,
    badge: 'SIMULATED TRIP'
  },
  {
    id: 902,
    trip_id: 'sw_demo_8802',
    user_id: 'demo_judge_999',
    destination: 'Metro Transit Hub, Gate 2',
    eta_minutes: 20,
    status: 'completed',
    tracking_token: 'sw_token_demo_eval_8802',
    created_at: new Date(Date.now() - 48 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    start_latitude: 28.5390,
    start_longitude: 77.1850,
    current_latitude: 28.5510,
    current_longitude: 77.2010,
    target_latitude: 28.5510,
    target_longitude: 77.2010,
    is_demo: true,
    badge: 'COMPLETED TRIP'
  }
];

export const DEMO_EVIDENCE_RECORDS = [
  {
    id: 801,
    user_id: 'demo_judge_999',
    file_name: 'Threat_Voicemail_Call_Oct23.m4a',
    file_type: 'audio/m4a',
    file_size_bytes: 1845200,
    sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    category: 'Audio Harassment Evidence',
    incident_date: '2026-10-23T21:14:00Z',
    created_at: '2026-10-24T09:30:00Z',
    integrity_status: 'VERIFIED_UNALTERED',
    chain_of_custody_notes: 'Tamper-evident client-side SHA-256 seal verified against local vault ledger.',
    is_demo: true
  },
  {
    id: 802,
    user_id: 'demo_judge_999',
    file_name: 'Extortion_Message_Chat_Thread.png',
    file_type: 'image/png',
    file_size_bytes: 842100,
    sha256_hash: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
    category: 'Digital Cyberstalking Screenshot',
    incident_date: '2026-10-24T02:45:00Z',
    created_at: '2026-10-24T10:15:00Z',
    integrity_status: 'VERIFIED_UNALTERED',
    chain_of_custody_notes: 'Cryptographic EXIF metadata preserved. Hash matches original client capture.',
    is_demo: true
  },
  {
    id: 803,
    user_id: 'demo_judge_999',
    file_name: 'Stalker_Vehicle_Surveillance_Photo.jpg',
    file_type: 'image/jpeg',
    file_size_bytes: 2314500,
    sha256_hash: 'c897f1059530f6e19c004820ecd1d61132dfcd9f5ac99f75d5218a5ce55b4b7f',
    category: 'Physical Stalking Surveillance',
    incident_date: '2026-10-24T17:20:00Z',
    created_at: '2026-10-24T18:00:00Z',
    integrity_status: 'VERIFIED_UNALTERED',
    chain_of_custody_notes: 'Original geotag: 28.5482°N, 77.1951°E. Camera timestamp confirmed.',
    is_demo: true
  },
  {
    id: 804,
    user_id: 'demo_judge_999',
    file_name: 'Chronological_Incident_Dossier.pdf',
    file_type: 'application/pdf',
    file_size_bytes: 512400,
    sha256_hash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    category: 'Tell-Once Intake Brief',
    incident_date: '2026-10-25T08:00:00Z',
    created_at: '2026-10-25T08:15:00Z',
    integrity_status: 'VERIFIED_UNALTERED',
    chain_of_custody_notes: '3-in-1 Zero FIR, Cyber 1930 & Legal Advocate Manifest.',
    is_demo: true
  }
];

export const DEMO_TRUSTED_CONTACTS = [
  {
    id: 701,
    user_id: 'demo_judge_999',
    name: 'Priya Sharma (Sister & Primary Guardian)',
    phone: '+91 98765 43210',
    email: 'priya.demo@safemate.test',
    relationship: 'Family Member',
    notify_sms: true,
    notify_call: true,
    notify_whatsapp: true,
    is_demo: true
  },
  {
    id: 702,
    user_id: 'demo_judge_999',
    name: 'Advocate Rajesh Nair (Legal Counsel)',
    phone: '+91 98111 22334',
    email: 'advocate.nair@safemate.test',
    relationship: 'Legal Counselor / Advocate',
    notify_sms: true,
    notify_call: false,
    notify_whatsapp: true,
    is_demo: true
  },
  {
    id: 703,
    user_id: 'demo_judge_999',
    name: "Campus Women's Emergency Cell",
    phone: '+91 11 2659 1000',
    email: 'campus.safety@safemate.test',
    relationship: 'Campus Security & Support',
    notify_sms: true,
    notify_call: true,
    notify_whatsapp: false,
    is_demo: true
  }
];

export const DEMO_DETECTION_RESULTS = {
  imageScan: {
    is_deepfake: true,
    confidence: 0.942,
    verdict: 'HIGH PROBABILITY SYNTHETIC MANIPULATION',
    model_name: 'ResNet50-DualForensics (Local Neural Classifier)',
    execution_time_ms: 184,
    anomalies: [
      'Asymmetric corneal light reflection highlights in left pupil',
      'High-frequency boundary artifacts detected along facial perimeter',
      'GAN blending gradients detected around nose bridge'
    ],
    metadata: {
      resolution: '1024x1024',
      color_depth: '24-bit sRGB',
      compression_level: 'Low'
    },
    simulated: true,
    badge: 'DEMO FORENSIC RESULT'
  },
  videoScan: {
    is_deepfake: true,
    confidence: 0.918,
    verdict: 'TEMPORAL MORPHING & LIP-SYNC SYNTHESIS DETECTED',
    model_name: 'MesoNet4-TemporalForensics',
    execution_time_ms: 420,
    frames_analyzed: 142,
    manipulated_frames: 118,
    anomalies: [
      'Inconsistent phoneme-to-viseme lip transitions across frames 34-88',
      'Temporal eye-blink interval outside natural human physiological limits (0 blinks in 12s)'
    ],
    simulated: true,
    badge: 'DEMO FORENSIC RESULT'
  }
};

export const DEMO_SIMULATED_SOS_EVENT = {
  alert_id: 'emg_demo_sim_9912',
  status: 'SIMULATED_DISPATCH',
  created_at: new Date().toISOString(),
  resolved_at: null,
  latitude: 28.5456,
  longitude: 77.1926,
  location_name: 'Demo Location: Main University Avenue, New Delhi, India',
  safety_circle_notified: [
    'Priya Sharma (Sister & Primary Guardian)',
    'Advocate Rajesh Nair (Legal Counsel)',
    "Campus Women's Emergency Cell"
  ],
  dispatch_summary: 'Demo mode: This action is simulated. No emergency alert, SMS, or telephone call has been sent to real contacts or emergency services (112).',
  battery_level: '84%',
  network_type: '5G High-Precision GPS Fix',
  is_demo: true
};

export const DEMO_TELL_ONCE_DOSSIER = {
  fir: `FORMAL POLICE COMPLAINT (ZERO FIR)
UNDER SECTION 173 BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS) 2023 / SEC 154 CrPC
---------------------------------------------------------------------------------
[DEMO / SAMPLE DOCUMENT FOR JUDGE EVALUATION]

TO: The Station House Officer / Cyber Crime Police Station
DATE: ${new Date().toLocaleDateString()}
SUBJECT: Complaint regarding non-consensual deepfake generation, cyberstalking, and criminal intimidation

1. COMPLAINANT PARTICULARS:
   Name: [Confidential Survivor Persona - Demo Mode]
   Location of Incident: Online Platforms / Digital Messaging Service
   
2. NATURE OF OFFENCE:
   - Creation and transmission of sexually explicit morphed imagery (Sec 66E, 67, 67A IT Act 2000)
   - Cyberstalking & criminal intimidation (Sec 78, 351(2) BNS 2023)
   - Extortion via digital blackmail (Sec 308 BNS 2023)

3. EVIDENCE SECURED:
   - Audio recording stamped with SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
   - Digital message screenshots with verified EXIF timestamps
   - AI Deepfake Forensic Analysis Report (SafeMate ResNet50 Classifier: 94.2% Synthetic Confidence)

4. PRAYER:
   Requesting immediate registration of Zero FIR and preservation of IP logs from service providers.

VERIFIED EVIDENCE CHAIN OF CUSTODY ATTACHED.`,

  cyber1930: `NATIONAL CYBER CRIME REPORTING PORTAL (1930 HELPLINE BRIEF)
INCIDENT CATEGORY: Women/Children Related Crime - Intimate Image / Cyber Harassment
---------------------------------------------------------------------------------
[DEMO / SAMPLE DOCUMENT FOR JUDGE EVALUATION]

INCIDENT DETAILS:
- Platform: Messaging & Social Media Platform
- Nature of Morphed Media: Synthetic face-swap video and altered photographs
- Suspect Contact / Handle: Identified in sealed digital evidence record #802
- Financial Demand / Extortion: Yes - Digital payment demanded to suppress fabricated media

PRESERVED TECHNICAL EVIDENCE:
- Primary Media Hash: c897f1059530f6e19c004820ecd1d61132dfcd9f5ac99f75d5218a5ce55b4b7f
- Geolocation Coordinates: 28.5482°N, 77.1951°E
- Timestamp Range: 2026-10-23 to 2026-10-25`,

  lawyer: `CONFIDENTIAL SURVIVOR LEGAL INTAKE & ACTION BRIEF
PREPARED FOR: Designated Legal Counsel / Legal Aid Advocate
---------------------------------------------------------------------------------
[DEMO / SAMPLE DOCUMENT FOR JUDGE EVALUATION]

CASE BRIEF & STRATEGY NOTES:
1. Legal Provisions Applicable:
   - Bharatiya Nyaya Sanhita (BNS) 2023: Sections 78 (Stalking), 79 (Outraging Modesty), 308 (Extortion), 351 (Criminal Intimidation).
   - Information Technology Act 2000: Sections 66E (Violation of privacy), 67A (Sexually explicit content).

2. Immediate Remedies Sought:
   - Urgent ex-parte interim injunction directing global platforms to takedown media within 24 hours under Rule 3(2)(b) of IT Rules 2021.
   - Restraining order against identified respondent.
   - Protection order under Domestic Violence Act / Sec 18 if relational.

3. Chain of Custody Readiness:
   - All files certified under Section 63 Bharatiya Sakshya Adhiniyam (BSA) 2023 (formerly Sec 65B Indian Evidence Act).`,

  evidenceChecklist: `EVIDENCE CHECKLIST & CHAIN OF CUSTODY MANIFEST
SAFEGUARDED DIGITAL ARTIFACTS
---------------------------------------------------------------------------------
[DEMO / SAMPLE DOCUMENT FOR JUDGE EVALUATION]

1. [VERIFIED] Threat_Voicemail_Call_Oct23.m4a (1.8 MB)
   SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
2. [VERIFIED] Extortion_Message_Chat_Thread.png (842 KB)
   SHA-256: a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
3. [VERIFIED] Stalker_Vehicle_Surveillance_Photo.jpg (2.3 MB)
   SHA-256: c897f1059530f6e19c004820ecd1d61132dfcd9f5ac99f75d5218a5ce55b4b7f
4. [VERIFIED] AI Forensic Model Classification Log (SafeMate Deepfake Engine)`
};

// Export to window object for vanilla JavaScript compatibility
if (typeof window !== 'undefined') {
  window.SafeMateDemoData = {
    DEMO_USER,
    DEMO_METRICS,
    DEMO_SAFEWALK_TRIPS,
    DEMO_EVIDENCE_RECORDS,
    DEMO_TRUSTED_CONTACTS,
    DEMO_DETECTION_RESULTS,
    DEMO_SIMULATED_SOS_EVENT,
    DEMO_TELL_ONCE_DOSSIER
  };
}
