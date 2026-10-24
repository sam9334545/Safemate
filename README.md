# Safemate — Women's Safety Platform

Safemate is a modern, privacy-first safety platform engineered to protect women from digital harassment, non-consensual media manipulation, and synthetic content threats. Safemate equips individuals and support communities with transparent automated screening tools to evaluate suspicious media safely and confidentially.

---

## Media Safety Screening Overview

Safemate provides two complementary, strictly isolated media screening pipelines:

```
                                  [ Uploaded Media ]
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          [ Still Image Upload ]                        [ Video File Upload ]
                    │                                             │
      POST /api/v1/detect                          POST /api/v1/deepfake/detect
                    │                                             │
      InMemory Processing (BytesIO)                Ephemeral Temp File (Purged in finally)
                    │                                             │
      Swin Transformer Classifier                  Frame Extraction (cv2) + YOLOv8n-Face
                    │                                             │
       umm-maybe/AI-image-detector                 MS-EffGCViT-B0 Classifier (34.8 MB)
                    │                                             │
                    ▼                                             ▼
       AI-Generation Probability                   Confidence-Aggregated Deepfake Score
       + Contextual Disclaimers                    + Neutral Classification & Disclaimers
```

### 1. Safemate Still-Image Screening (`POST /api/v1/detect`)
Screens still photographs and artwork for visual artifacts characteristic of AI diffusion models (such as DALL-E, Midjourney, or Stable Diffusion).
- **Core Technology:** Pretrained Swin Transformer classifier (`umm-maybe/AI-image-detector`).
- **Privacy Guarantee:** Processed strictly in memory via `io.BytesIO`. Images, metadata, and EXIF tags are never written to disk or stored in any database.
- **Classification Output:** Normalized probability scores for `artificial` vs. `human` accompanied by plain-language guidance and operational boundaries.

### 2. Safemate Video Safety Screening (`POST /api/v1/deepfake/detect`)
Safemate analyses sampled video frames and visible facial features to screen for visual patterns associated with digital face manipulation. It returns an automated screening estimate with relevant limitations.
- **Core Technology:** Mobile-Scale Efficient Global Context Vision Transformer (`MS-EffGCViT-B0`, 8.7M parameters, ~34.8 MB weights) paired with a lightweight YOLOv8 face detector (`yolov8n-face.pt`, ~6.1 MB).
- **Workflow:** Decodes video files, samples between 5 and 30 representative frames (default: 20), crops visible facial regions with a 20% margin, normalizes crops with ImageNet parameters, and calculates a confidence-weighted score across frames.
- **Privacy Guarantee:** Uploaded videos are decoded through ephemeral temporary files with randomized filenames and are unconditionally deleted in a `finally` block immediately after frame extraction. No video files or facial crops are ever retained.
- **Neutral Classifications:**
  - `potential_manipulation_detected` (Score $\ge 0.70$)
  - `no_manipulation_detected_by_model` (Score $\le 0.35$)
  - `inconclusive` ($0.35 < \text{Score} < 0.70$)
  - `no_face_detected` (No visible human face located across sampled frames)

---

## Repository Structure

```
Safemate/
├── backend/                  # FastAPI Screening Backend Service
│   ├── app/
│   │   ├── api/routes/       # Route handlers: health, model-info, detect, deepfake
│   │   ├── core/             # Configuration settings, CORS, and logging
│   │   ├── schemas/          # Pydantic schemas (detection, deepfake, errors)
│   │   ├── services/         # Image & video inference service engines
│   │   ├── utils/            # Request ID correlation helpers
│   │   └── main.py           # Application entry point & model lifespan
│   ├── tests/                # Automated pytest suite (51 unit & integration tests)
│   ├── .env.example          # Environment configuration template
│   ├── pytest.ini            # Pytest configuration
│   ├── requirements.txt       # Production Python dependencies
│   └── README.md             # In-depth backend API & frontend integration guide
├── docs/
│   └── DEEPFAKE_INTEGRATION_AUDIT.md # Architecture & compliance audit report
├── THIRD_PARTY_NOTICES.md    # Upstream open-source licenses & model attribution
├── render.yaml               # Cloud deployment blueprint
├── .gitignore                # Exclusions for caches, weights, and environment files
└── README.md                 # Project documentation
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+ (tested on Python 3.12.8)
- Windows PowerShell, macOS zsh, or Linux bash

### Setup & Launch
```powershell
# 1. Enter the backend directory
cd backend

# 2. Set up virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # On macOS/Linux: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
Copy-Item .env.example .env

# 5. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, interactive OpenAPI documentation is available at:
`http://localhost:8000/docs`

---

## Running the Automated Test Suite

```powershell
cd backend
python -m pytest
```

**Test Outcome:**
- **51 passed, 1 deselected in ~1.8s**
- Rigorous coverage across both screening features, file constraints, corrupt streams, face-less videos, model cold starts, inference failures, request ID propagation, and temporary file cleanup guarantees.

---

## Production Deployment & Sizing

A `render.yaml` deployment blueprint is provided for cloud hosting (e.g. Render, Railway, AWS ECS).

- **Recommended Instance Tier:** Starter tier with **1 GB or 2 GB RAM**.
- **Memory Footprint:** The still-image classifier (~348 MB) and video deepfake classifier (~41 MB total weights) together require ~900 MB to 1.2 GB of active system RAM under dual model concurrency.
- **CPU Inference Speed:** Running entirely on CPU, still-image screening finishes in ~0.3s–1.0s, and video screening (20 sampled frames) finishes in ~1.5s–3.0s on standard multi-core instances.

---

## Ethical Principles & Safety Boundaries

1. **Automated Screening, Not Proof:** Safemate produces heuristic confidence indicators. Results are never presented as definitive proof of digital manipulation or authenticity.
2. **Context Limitations:** Detection accuracy depends on facial clarity, lighting, compression, frame rate, and movement.
3. **No Intent or Identity Recognition:** Safemate does not identify individuals, evaluate personal consent, or determine whether content is non-consensual sexual material.
4. **Human Review Centered:** Automated scores are designed to assist human safety caseworkers and users with triaging, never as the sole basis for legal, punitive, or moderation actions.

---

## Attribution & Licenses

Safemate is committed to ethical open-source reuse. All third-party neural architectures, pretrained checkpoints, and libraries are fully credited with original licenses in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [docs/DEEPFAKE_INTEGRATION_AUDIT.md](docs/DEEPFAKE_INTEGRATION_AUDIT.md).
