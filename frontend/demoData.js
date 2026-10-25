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
export const DEMO_LANDMARKS = [
{ name: 'Connaught Place', display_name: 'Connaught Place, Inner Circle, New Delhi, Delhi 110001', latitude: 28.6315, longitude: 77.2167 },
{ name: 'India Gate', display_name: 'India Gate, Rajpath, New Delhi, Delhi 110001', latitude: 28.6129, longitude: 77.2295 },
{ name: 'Hauz Khas Village', display_name: 'Hauz Khas Village, Sri Aurobindo Marg, New Delhi 110016', latitude: 28.5494, longitude: 77.1936 },
{ name: 'Select Citywalk Saket', display_name: 'Select Citywalk, Saket District Centre, New Delhi 110017', latitude: 28.5283, longitude: 77.2190 },
{ name: 'South Extension', display_name: 'South Extension Part II, Ring Road, New Delhi 110049', latitude: 28.5689, longitude: 77.2223 },
{ name: 'Lajpat Nagar Central Market', display_name: 'Lajpat Nagar Central Market, New Delhi 110024', latitude: 28.5700, longitude: 77.2373 },
{ name: 'Delhi University North Campus', display_name: 'DU North Campus, Chhatra Marg, Delhi 110007', latitude: 28.6903, longitude: 77.2066 },
{ name: 'DLF Cyber Hub', display_name: 'DLF Cyber Hub, DLF Phase 2, Gurugram, Haryana 122002', latitude: 28.4950, longitude: 77.0895 }
];
export function generateDemoRoutePlan(originName, originLat, originLon, destName, destLat, destLon, travelMode = 'walking') {
const oLat = parseFloat(originLat) || 28.6315;
const oLon = parseFloat(originLon) || 77.2167;
const dLat = parseFloat(destLat) || 28.6129;
const dLon = parseFloat(destLon) || 77.2295;
// Haversine straight-line distance
const R = 6371000;
const phi1 = (oLat * Math.PI) / 180;
const phi2 = (dLat * Math.PI) / 180;
const dPhi = ((dLat - oLat) * Math.PI) / 180;
const dLambda = ((dLon - oLon) * Math.PI) / 180;
const a = Math.sin(dPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) ** 2;
const straightM = 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
const isWalking = travelMode === 'walking';
const speedMps = isWalking ? 1.3 : 8.5; // ~4.7 km/h walking, ~30 km/h driving
// Curved corridor geometry helper
function makeCurvedCoords(offsetRatio, steps = 28) {
const coords = [];
const deltaLat = dLat - oLat;
const deltaLon = dLon - oLon;
const perpLat = -deltaLon;
const perpLon = deltaLat;
const mag = Math.sqrt(perpLat * perpLat + perpLon * perpLon) || 1;
const normLat = perpLat / mag;
const normLon = perpLon / mag;
const offsetMag = Math.max(0.0015, Math.abs(offsetRatio));
for (let i = 0; i <= steps; i++) {
const t = i / steps;
const sag = Math.sin(Math.PI * t);
const lat = oLat + t * deltaLat + (offsetRatio >= 0 ? 1 : -1) * sag * offsetMag * normLat;
const lon = oLon + t * deltaLon + (offsetRatio >= 0 ? 1 : -1) * sag * offsetMag * normLon;
coords.push([parseFloat(lon.toFixed(6)), parseFloat(lat.toFixed(6))]);
}
return coords;
}
const distA_m = straightM * 1.18;
const durA_s = distA_m / speedMps;
const geomA = makeCurvedCoords(0.0022, 28);
const distB_m = straightM * 1.32;
const durB_s = distB_m / speedMps;
const geomB = makeCurvedCoords(-0.0034, 32);
const midLat = (oLat + dLat) / 2;
const midLon = (oLon + dLon) / 2;
const placesA = [
{ id: 'demo_poi_1', name: 'Apollo 24/7 Pharmacy & First Aid', category: 'pharmacy', latitude: oLat + (dLat - oLat) * 0.25 + 0.0004, longitude: oLon + (dLon - oLon) * 0.25 + 0.0003, distance_to_route_meters: 22, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_2', name: 'SafeCity Metro Transit Hub', category: 'transit', latitude: midLat + 0.0006, longitude: midLon + 0.0005, distance_to_route_meters: 35, is_likely_open: true, hours_unknown: false, opening_hours_raw: '05:30-23:30' },
{ id: 'demo_poi_3', name: '24-Hour Express Market & Convenience', category: 'shop', latitude: oLat + (dLat - oLat) * 0.70 - 0.0003, longitude: oLon + (dLon - oLon) * 0.70 + 0.0004, distance_to_route_meters: 18, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_4', name: 'Public Fuel & EV Quick Assistance Hub', category: 'fuel', latitude: oLat + (dLat - oLat) * 0.85 + 0.0005, longitude: oLon + (dLon - oLon) * 0.85 - 0.0004, distance_to_route_meters: 42, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' }
];
const placesB = [
{ id: 'demo_poi_5', name: 'Women Police Assistance Post & PCR Booth', category: 'police', latitude: oLat + (dLat - oLat) * 0.20 - 0.0005, longitude: oLon + (dLon - oLon) * 0.20 - 0.0005, distance_to_route_meters: 15, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_6', name: 'MedPlus 24x7 Chemist & Diagnostic Store', category: 'pharmacy', latitude: oLat + (dLat - oLat) * 0.40 - 0.0006, longitude: oLon + (dLon - oLon) * 0.40 - 0.0007, distance_to_route_meters: 20, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_7', name: 'District Emergency Healthcare Care Centre', category: 'hospital', latitude: midLat - 0.0008, longitude: midLon - 0.0006, distance_to_route_meters: 30, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_8', name: 'Central Interchange Lighted Bus Bay', category: 'transit', latitude: oLat + (dLat - oLat) * 0.75 - 0.0004, longitude: oLon + (dLon - oLon) * 0.75 - 0.0005, distance_to_route_meters: 25, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' },
{ id: 'demo_poi_9', name: 'BrightMart 24h Convenience Cafe', category: 'shop', latitude: oLat + (dLat - oLat) * 0.88 - 0.0003, longitude: oLon + (dLon - oLon) * 0.88 - 0.0004, distance_to_route_meters: 16, is_likely_open: true, hours_unknown: false, opening_hours_raw: '24/7' }
];
const durA_min = Math.max(1, Math.round(durA_s / 60));
const durB_min = Math.max(1, Math.round(durB_s / 60));
return {
status: 'success',
origin_resolved: {
name: originName || 'Origin Point',
display_name: originName || 'Origin Point',
latitude: oLat,
longitude: oLon
},
destination_resolved: {
name: destName || 'Destination Point',
display_name: destName || 'Destination Point',
latitude: dLat,
longitude: dLon
},
travel_mode: travelMode,
departure_time_evaluated: new Date().toISOString(),
routes: [
{
route_id: 'sim_route_a',
id: 'sim_route_a',
name: 'Route A — Direct Arterial Boulevard',
is_fastest: true,
is_recommended_for_night: false,
is_highest_activity: false,
distance_meters: Math.round(distA_m),
distance_km: parseFloat((distA_m / 1000).toFixed(1)),
duration_seconds: Math.round(durA_s),
duration_minutes: durA_min,
travel_mode: travelMode,
geometry: geomA,
score: {
overall_night_activity_score: 72,
score_label: 'Moderate Night Activity',
is_score_available: true,
open_establishments_count: 14,
unknown_hours_count: 3,
assistance_points_count: 2,
transit_points_count: 3,
longest_low_activity_segment_meters: 280,
low_activity_segments_count: 1,
road_characteristics_summary: 'Primary arterial boulevard with continuous commercial storefronts',
disclaimer: 'Calculated using SafeMate explainable normalization model. Does not predict crime or guarantee personal safety.',
components: {
open_establishments: { name: 'Open Establishments Density', score: 74, weight: 0.35, available: true, description: '14 verified open establishments along corridor' },
lighting_transit: { name: 'Transit & Street Activity', score: 76, weight: 0.25, available: true, description: 'Active transit nodes and commercial frontage' },
assistance_nodes: { name: 'Assistance Nodes Proximity', score: 68, weight: 0.25, available: true, description: 'Nearby pharmacy and transit help points' },
distribution: { name: 'Corridor Activity Continuity', score: 70, weight: 0.15, available: true, description: 'Max low-activity gap 280m' }
}
},
nearby_places: placesA,
trade_off_statement: `Fastest option (${durA_min} min). However, Route B offers a higher night activity score (+16 pts) and dedicated police assistance presence.`
},
{
route_id: 'sim_route_b',
id: 'sim_route_b',
name: 'Route B — Well-Lit Commercial Transit Corridor',
is_fastest: false,
is_recommended_for_night: true,
is_highest_activity: true,
distance_meters: Math.round(distB_m),
distance_km: parseFloat((distB_m / 1000).toFixed(1)),
duration_seconds: Math.round(durB_s),
duration_minutes: durB_min,
travel_mode: travelMode,
geometry: geomB,
score: {
overall_night_activity_score: 88,
score_label: 'Higher Mapped Night Activity',
is_score_available: true,
open_establishments_count: 22,
unknown_hours_count: 2,
assistance_points_count: 4,
transit_points_count: 4,
longest_low_activity_segment_meters: 140,
low_activity_segments_count: 0,
road_characteristics_summary: 'Well-lit commercial transit corridor with high density of 24/7 pharmacies and police assistance nodes',
disclaimer: 'Calculated using SafeMate explainable normalization model. Does not predict crime or guarantee personal safety.',
components: {
open_establishments: { name: 'Open Establishments Density', score: 90, weight: 0.35, available: true, description: '22 verified open establishments along corridor' },
lighting_transit: { name: 'Transit & Street Activity', score: 88, weight: 0.25, available: true, description: 'Continuous street activity and lighted transit points' },
assistance_nodes: { name: 'Assistance Nodes Proximity', score: 92, weight: 0.25, available: true, description: 'Police post, hospital emergency, and 24/7 pharmacy' },
distribution: { name: 'Corridor Activity Continuity', score: 82, weight: 0.15, available: true, description: 'Continuous activity; longest gap ~140m' }
}
},
nearby_places: placesB,
trade_off_statement: `Higher mapped night activity score (+16 pts) and 8 more mapped open places with police assistance, taking approximately ${Math.max(1, durB_min - durA_min)} min longer than fastest route.`
}
],
data_attribution: 'Route geometries generated via SafeMate corridor geometry engine. POI indicators modeled from open verified safety points.',
is_simulated: true
};
}
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
DEMO_TELL_ONCE_DOSSIER,
DEMO_LANDMARKS,
generateDemoRoutePlan
};
}
