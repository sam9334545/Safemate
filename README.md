# Safemate — Women's Safety Platform

Safemate is a multi-faceted women's safety platform developed for the recHERsion 2026 hackathon. The platform provides automated, privacy-first media screening tools designed to help individuals inspect suspicious media for digital manipulation, non-consensual alterations, and synthetic content.

---

## Repository Overview

```
Safemate/
├── backend/                  # FastAPI Screening Backend
│   ├── app/                  # Application source code
│   │   ├── api/routes/       # Endpoints: detect (image), deepfake (video), health, model-info
│   │   ├── core/             # Configuration & structured logging
│   │   ├── schemas/          # Pydantic schemas (detection, deepfake, errors)
│   │   ├── services/         # Image & video inference services
│   │   ├── utils/            # Request ID tracking & correlation
│   │   └── main.py           # FastAPI entry point & lifespan
│   ├── tests/                # Automated test suite (45 unit & integration tests)
│   ├── .env.example          # Environment template
│   ├── pytest.ini            # Pytest configuration
│   ├── requirements.txt       # Python dependencies (Torch, OpenCV, Timm, Ultralytics, DeepGuard)
│   └── README.md             # Comprehensive backend & API documentation
├── docs/
│   └── DEEPFAKE_INTEGRATION_AUDIT.md # Full compliance & architecture audit report
├── THIRD_PARTY_NOTICES.md    # Open-source licenses and pretrained model attribution
├── render.yaml               # Cloud deployment blueprint
├── .gitignore                # Git exclusions
└── README.md                 # Project documentation
```

---

## Core Media Screening Capabilities

### 1. Still-Image AI Generation Screening (`POST /api/v1/detect`)
- **Model:** `umm-maybe/AI-image-detector` (Swin Transformer architecture, Hugging Face).
- **Function:** Analyzes still images (JPEG, PNG, WEBP) for visual patterns characteristic of generative diffusion models.
- **Privacy:** Processed 100% in-memory via `io.BytesIO`. No files or metadata are saved to disk or database.
- **Responsible Interpretation:** Returns raw confidence scores and neutral disclaimers emphasizing that still-image screening is not a video deepfake detector or proof of manipulation.

### 2. Video Deepfake Screening (`POST /api/v1/deepfake/detect`)
- **Model:** `KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus` (MS-EffGCViT-B0, 34.8 MB weights, MIT License).
- **Face Detection:** YOLOv8-Face (`yolov8n-face.pt`, 6.1 MB) for facial localization across sampled video frames.
- **Function:** Inspects uploaded video files (`.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`), extracts bounded frames (5–30 frames, default 20), crops facial regions, and evaluates subtle artifacting and boundary blending.
- **Privacy & Safety:** Videos are written to ephemeral temporary files using randomized filenames, decoded, and immediately purged in guaranteed `finally` execution blocks. No uploaded video or extracted frame is ever retained.
- **Neutral Classifications:** `potential_manipulation_detected`, `no_manipulation_detected_by_model`, `inconclusive`, or `no_face_detected`.

---

## Quick Start (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start local development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API documentation is available at `http://localhost:8000/docs`.

---

## Running the Automated Test Suite

```powershell
cd backend
python -m pytest
```

**Test Results:**
- **45 passed, 1 deselected in ~1.27s**
- Complete coverage across image detection, video deepfake screening, corrupted files, oversized uploads, missing files, unsupported formats, face-less videos, model unavailability (503), inference failures (500), request ID correlation, and temporary file cleanup guarantees.

---

## Legal & Competition Compliance

Safemate adheres strictly to open-source licensing and hackathon integrity rules:
- Pretrained video deepfake weights and architecture from `KoreaPeter` / DeepGuard are licensed under the **MIT License**.
- Detailed third-party notices, copyrights, and terms are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- The full audit report and architecture review are documented in [docs/DEEPFAKE_INTEGRATION_AUDIT.md](docs/DEEPFAKE_INTEGRATION_AUDIT.md).
