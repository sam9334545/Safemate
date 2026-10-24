# Safemate - Women's Safety Application

A multi-faceted safety application developed for the Women's Safety Hackathon.

## Repository Overview

```
Safemate/
├── backend/            # FastAPI AI Image Screening Backend (Complete MVP)
│   ├── app/            # Application source code
│   │   ├── api/        # Versioned REST API routes (/api/v1)
│   │   ├── core/       # Configuration & structured logging
│   │   ├── schemas/    # Pydantic request/response/error schemas
│   │   ├── services/   # Image validation & Hugging Face model inference
│   │   ├── utils/      # Request ID tracking & correlation
│   │   └── main.py     # FastAPI entry point & lifespan
│   ├── tests/          # Automated test suite (31 fast unit tests + live integration test)
│   ├── .env.example    # Configuration template
│   ├── pytest.ini      # Test configuration
│   ├── requirements.txt # Python dependencies
│   ├── render.yaml     # Render cloud deployment blueprint
│   └── README.md       # Comprehensive backend documentation & frontend integration guide
├── render.yaml         # Root Render deployment blueprint
├── .gitignore          # Git exclusions for Python, caches, and frontend
└── README.md           # Repository documentation
```

## Backend: AI Image Screening Service

The AI image screening feature provides an automated, privacy-first screening tool for detecting characteristics of AI-generated imagery using a pretrained Swin Transformer model from Hugging Face (`umm-maybe/AI-image-detector`).

### Key Features
- **In-Memory Image Processing**: No user images, filenames, or metadata are ever saved to disk or persistent storage.
- **Pretrained ViT/Swin Classifier**: Uses `umm-maybe/AI-image-detector` loaded once at server startup.
- **Security Safeguards**: Protection against decompression bombs, oversized uploads, corrupt files, and animated media.
- **Ethical Interpretations**: Returns responsible, non-definitive explanations with explicit limitations.

For complete backend documentation, setup guides, API schemas, and frontend integration examples, please see [backend/README.md](backend/README.md).

### Quick Start (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```powershell
cd backend
python -m pytest
```
Result: 31 passed in ~0.8s.
