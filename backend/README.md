# AI Image Screening Backend (Women's Safety Application)

A production-grade, privacy-first FastAPI backend providing AI-generated image screening for a women's safety application. Built with **FastAPI**, **Hugging Face Transformers**, **PyTorch (CPU)**, **Pillow**, and **Pydantic**.

This backend exposes high-performance REST APIs allowing clients (such as a React/Vite web or mobile app) to submit images for preliminary screening, check service and model readiness, and receive non-definitive, responsible interpretations—all without persisting user images to disk or database.

---

## 1. Features & Security Safeguards

- **In-Memory Image Processing**: Uploaded images are processed strictly in memory (`io.BytesIO`). No user images, filenames, EXIF tags, or base64 streams are written to disk, stored in a database, or sent to third-party tracking services.
- **Pretrained Hugging Face Model**: Integrates `umm-maybe/AI-image-detector` (Swin Transformer architecture) loaded once during application startup via FastAPI lifespan.
- **Decompression Bomb & Size Safeguards**: Enforces strict pixel limits (`Image.MAX_IMAGE_PIXELS = 16,000,000`), maximum dimensions (4096×4096), and upload size constraints (default 10 MB) to prevent denial-of-service and memory exhaustion.
- **Format & Type Validation**: Decodes and verifies image integrity with Pillow. Rejects corrupt files, disguised text/executable files, animated images (e.g. animated GIFs), and unsupported image formats.
- **Responsible Interpretation & Disclaimers**: Preserves raw model labels (`artificial`, `human`) and normalized confidence scores while pairing results with plain-language, non-definitive explanations and clear limitations.
- **Predictable Error Contracts**: Standardized error payloads with unique `request_id` correlation for safe diagnostics without leaking stack traces.
- **Configurable CORS**: Supports flexible frontend integration (e.g. `http://localhost:5173`) via `CORS_ORIGINS`.

---

## 2. API Contract Reference

Base prefix: `/api/v1`

### A. `GET /api/v1/health`
Liveness check to verify the web server process is running.
- **Status**: `200 OK`
- **Response**:
  ```json
  {
    "status": "ok",
    "service": "ai-image-screening-api"
  }
  ```

### B. `GET /api/v1/health/ready`
Model readiness check to verify the Hugging Face model and processor are initialized and ready for inference.
- **Status**: `200 OK` (when ready) or `503 Service Unavailable` (when unready/initializing)
- **Response (200 Ready)**:
  ```json
  {
    "status": "ready",
    "model_loaded": true,
    "model_id": "umm-maybe/AI-image-detector",
    "device": "cpu"
  }
  ```
- **Response (503 Unavailable)**:
  ```json
  {
    "status": "unavailable",
    "model_loaded": false,
    "model_id": "umm-maybe/AI-image-detector",
    "device": "cpu"
  }
  ```

### C. `GET /api/v1/model-info`
Public metadata, architecture, supported class taxonomy, and ethical notice.
- **Status**: `200 OK`
- **Response**:
  ```json
  {
    "model_id": "umm-maybe/AI-image-detector",
    "task": "image-classification",
    "description": "Pretrained Swin Transformer classifier for screening AI-generated artistic images vs. human-created images. Trained with AutoTrain on 2022 image data.",
    "model_loaded": true,
    "inference_available": true,
    "labels": ["artificial", "human"],
    "architecture": "SwinForImageClassification",
    "limitations_notice": "This model is an AI-generated-image screening tool developed in October 2022. It is not a definitive deepfake detector, does not prove manipulation or authenticity, and does not evaluate personal identity or consent. Newer diffusion models and general photos may yield false results."
  }
  ```

### D. `POST /api/v1/detect`
Primary screening endpoint.
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (single image file: JPEG, PNG, WEBP; max 10 MB)
- **Headers (Optional)**: `X-Request-ID` (client-provided correlation ID)
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "model_id": "umm-maybe/AI-image-detector",
    "prediction": {
      "label": "artificial",
      "score": 0.94215,
      "scores": [
        {
          "label": "artificial",
          "score": 0.94215
        },
        {
          "label": "human",
          "score": 0.05785
        }
      ]
    },
    "interpretation": {
      "category": "ai_image_screening",
      "summary": "The screening model identified visual characteristics frequently associated with AI-generated imagery (score: 94.2%). This is a probabilistic screening indicator, not definitive proof of synthetic origin.",
      "is_definitive": false,
      "limitations": [
        "This is an AI-generated-image screening result, not proof that an image is authentic, manipulated, or harmful.",
        "Model was trained on 2022 image distributions; newer generative models, edited photos, camera photos, or screenshots may yield inaccurate classifications.",
        "This screening does not establish personal identity, consent, intent, or whether content is intimate or abusive.",
        "Do not use this automated score as the sole basis for legal, protective, or moderation decisions."
      ]
    },
    "request_id": "req_a1b2c3d4e5f6"
  }
  ```

### E. `POST /api/v1/deepfake/detect`
Video deepfake and face-manipulation screening endpoint.
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (video file: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`; max 50 MB)
- **Query Param (Optional)**: `num_frames` (integer between 5 and 30, default 20 frames sampled uniformly)
- **Headers (Optional)**: `X-Request-ID` (client-provided correlation ID)
- **Response (200 OK — Face Detected & Screened)**:
  ```json
  {
    "success": true,
    "status": "success",
    "prediction": "potential_manipulation_detected",
    "score": 0.8842,
    "score_type": "confidence_score",
    "model_name": "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus",
    "frames_sampled": 20,
    "faces_detected": 18,
    "message": "Automated screening detected visual patterns frequently associated with digital face manipulation (confidence score: 88.4% across 18 analyzed face crops). This screening score is probabilistic and not definitive proof of manipulation.",
    "limitations": [
      "This is an automated video deepfake screening estimate, not definitive proof that a video is authentic, manipulated, or legally admissible evidence.",
      "Detection accuracy is dependent on visible facial clarity, lighting, compression, frame rate, and head movement.",
      "This screening tool does not verify individual identity, consent, intent, or whether video content is non-consensual or abusive.",
      "Do not use this automated screening score as the sole basis for moderation, legal, or protective actions."
    ],
    "request_id": "req_video_987654321"
  }
  ```
- **Response (200 OK — No Face Detected)**:
  ```json
  {
    "success": true,
    "status": "no_face_detected",
    "prediction": null,
    "score": null,
    "score_type": "confidence_score",
    "model_name": "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus",
    "frames_sampled": 20,
    "faces_detected": 0,
    "message": "No human face was detected in the sampled video frames. Video deepfake screening requires visible facial features.",
    "limitations": [ ... ],
    "request_id": "req_video_123456789"
  }
  ```

### Error Responses
All errors follow a unified structure:
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size (12.4MB) exceeds the maximum allowed upload limit of 10MB."
  },
  "request_id": "req_a1b2c3d4e5f6"
}
```
Standard error codes:
- `MISSING_FILE` (HTTP 400)
- `EMPTY_FILE` (HTTP 400)
- `INVALID_IMAGE` (HTTP 400)
- `EXCESSIVE_DIMENSIONS` (HTTP 400)
- `ANIMATED_IMAGE_NOT_SUPPORTED` (HTTP 400)
- `FILE_TOO_LARGE` (HTTP 413)
- `UNSUPPORTED_MEDIA_TYPE` (HTTP 415)
- `VALIDATION_ERROR` (HTTP 422)
- `MODEL_NOT_READY` (HTTP 503)
- `INFERENCE_FAILURE` (HTTP 500)
- `INTERNAL_SERVER_ERROR` (HTTP 500)

---

## 3. Frontend Integration Guide (React / Vite / Vanilla JS)

Connecting your frontend to this backend is straightforward.

### Environment Variable in Frontend
Define your API base URL in your frontend `.env` (e.g. `Vite`):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Complete Upload and Detection Function
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Check if the backend AI screening model is initialized and ready.
 * @returns {Promise<boolean>}
 */
export async function checkModelReadiness() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health/ready`);
    if (response.ok) {
      const data = await response.json();
      return data.status === "ready" && data.model_loaded === true;
    }
    return false;
  } catch (err) {
    console.error("Backend health check failed:", err);
    return false;
  }
}

/**
 * Screen an image file for AI-generated indicators.
 * @param {File} selectedFile - File object from <input type="file" />
 * @returns {Promise<object>}
 */
export async function screenImage(selectedFile) {
  if (!selectedFile) {
    throw new Error("Please select an image file.");
  }

  // Check readiness first to provide friendly feedback during cold starts
  const isReady = await checkModelReadiness();
  if (!isReady) {
    throw new Error("AI screening model is currently initializing. Please retry in a few moments.");
  }

  const formData = new FormData();
  // Field name MUST be 'file'
  formData.append("file", selectedFile);

  // CRITICAL: DO NOT manually set 'Content-Type': 'multipart/form-data'.
  // When you pass FormData, fetch automatically sets 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...'
  // Manually overriding it will break boundary parsing on the server.
  const response = await fetch(`${API_BASE_URL}/api/v1/detect`, {
    method: "POST",
    body: formData,
  });

  const result = await response.json();

  if (!response.ok || !result.success) {
    const errorMsg = result?.error?.message || "Failed to process image screening.";
    throw new Error(errorMsg);
  }

  // Successful prediction
  // result.prediction: { label: 'artificial', score: 0.942, scores: [...] }
  // result.interpretation: { summary: '...', limitations: [...], is_definitive: false }
  // result.request_id: 'req_...'
  return result;
}

/**
 * Screen a video file for deepfake facial manipulation artifacts.
 * @param {File} selectedFile - Video file object (.mp4, .mov, .webm, etc.)
 * @param {number} numFrames - Number of frames to sample (5 to 30, default 20)
 * @returns {Promise<object>}
 */
export async function screenVideo(selectedFile, numFrames = 20) {
  if (!selectedFile) {
    throw new Error("Please select a video file.");
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  const response = await fetch(`${API_BASE_URL}/api/v1/deepfake/detect?num_frames=${numFrames}`, {
    method: "POST",
    body: formData,
  });

  const result = await response.json();

  if (!response.ok || !result.success) {
    const errorMsg = result?.error?.message || "Failed to process video deepfake screening.";
    throw new Error(errorMsg);
  }

  // Result structure:
  // result.status: 'success' | 'no_face_detected' | 'inconclusive'
  // result.prediction: 'potential_manipulation_detected' | 'no_manipulation_detected_by_model' | null
  // result.score: 0.8842 | null
  // result.faces_detected: 18
  // result.frames_sampled: 20
  // result.message: '...'
  // result.limitations: [...]
  return result;
}
```

### Display Guidelines for Hackathon UI
1. **Never declare certainty**: Display the model's leading score as a probability indicator (e.g. "94% AI indicator"), never as an absolute judgment.
2. **Always render limitations**: Always display `result.interpretation.limitations` alongside the score.
3. **Handle Cold Starts**: During the first request on free cloud platforms, model weight initialization can take 15–30 seconds. Display a friendly loading indicator: *"Loading screening model into memory..."*.

---

## 4. Local Developer Setup (Windows PowerShell & Cross-Platform)

### Prerequisites
- Python 3.10+ (tested on Python 3.12.8)
- pip

### Step-by-Step Setup in PowerShell

```powershell
# 1. Navigate to the backend directory
cd c:\Users\win11\recHersion\backend

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Create local environment file from template
Copy-Item .env.example .env

# 6. Run the local development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Cross-Platform Setup (Linux / macOS)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verifying Service
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Liveness Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Readiness Endpoint**: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)
- **Model Info**: [http://localhost:8000/api/v1/model-info](http://localhost:8000/api/v1/model-info)

### Sending a Test Image via PowerShell

```powershell
$form = @{
    file = Get-Item "C:\path\to\sample_image.jpg"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/detect" -Method Post -Form $form
```

### Sending a Test Image via cURL

```bash
curl -X POST "http://localhost:8000/api/v1/detect" \
  -H "accept: application/json" \
  -F "file=@sample_image.jpg;type=image/jpeg"
```

### Sending a Test Video via PowerShell

```powershell
$form = @{
    file = Get-Item "C:\path\to\sample_video.mp4"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/deepfake/detect?num_frames=20" -Method Post -Form $form
```

### Sending a Test Video via cURL

```bash
curl -X POST "http://localhost:8000/api/v1/deepfake/detect?num_frames=20" \
  -H "accept: application/json" \
  -F "file=@sample_video.mp4;type=video/mp4"
```

---

## 5. Automated Tests

The test suite contains 45 fast, deterministic unit and integration tests that mock external model inference services so they run in ~1.3 seconds without requiring external network connectivity or downloading model weights during continuous integration.

### Run Fast Test Suite (Default)
```powershell
python -m pytest
```
Output:
```text
45 passed, 1 deselected in ~1.27s
```

The test suite verifies:
- Health, readiness, and metadata endpoints.
- Still-image screening with format validations, dimension constraints, corrupt-file handling, and header propagation.
- Video deepfake screening with multipart decoding, frame sampling constraints, face presence detection, corrupted streams, oversized files, 503 unready handling, 500 inference failure handling, and guaranteed temporary file cleanup in `finally` blocks.
- End-to-end backward compatibility of existing endpoints.

### Run Optional Live Hugging Face Integration Test
To run live end-to-end inference using the actual Hugging Face model weights (~350 MB download):
```powershell
python -m pytest -m integration -v
```

---

## 6. Render Cloud Deployment

A `render.yaml` blueprint is included in the project root and backend folder.

### Deployment Configuration
- **Environment**: Python 3.12
- **Root Directory**: `backend`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/api/v1/health`

### Hardware & Hosting Constraints
> [!IMPORTANT]
> **RAM Sizing**: 
> - Still-image model (`umm-maybe/AI-image-detector`): ~348 MB weights.
> - Video deepfake model (`KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus`): ~34.8 MB weights + YOLOv8n-Face (~6.1 MB).
> - Total memory footprint under dual model concurrency: ~900 MB – 1.2 GB RAM.
>
> On Render's **Free Tier (512 MB RAM)**, loading both models simultaneously can trigger an Out-Of-Memory (OOM) kill. For stable production hosting, select the **Render Starter plan (1 GB or 2 GB RAM)**.
>
> **CPU Inference Latency**: Models execute on CPU by default. Still-image inference latency is ~0.3s to 1.0s. Video deepfake screening (sampling 20 frames) executes in approximately 1.5s to 3.0s on multi-core cloud instances.

### Configuring CORS in Production
In the Render Dashboard Environment settings (or via `render.yaml`):
```env
CORS_ORIGINS=https://your-frontend-app.onrender.com,https://your-custom-domain.com
```

---

## 7. Model Attribution, License & Ethical Limitations

For complete license texts, copyright notices, and third-party dependency details, see [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and [../docs/DEEPFAKE_INTEGRATION_AUDIT.md](../docs/DEEPFAKE_INTEGRATION_AUDIT.md).

### 1. Still-Image AI Detection
- **Model Identifier**: [umm-maybe/AI-image-detector](https://huggingface.co/umm-maybe/AI-image-detector)
- **Author**: Matthew Maybe (`umm-maybe`)
- **Architecture**: Swin Transformer for Image Classification
- **License**: Creative Commons Attribution-NoDerivatives 4.0 International ([CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/))

### 2. Video Deepfake Detection
- **Model Checkpoint**: [KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus](https://huggingface.co/KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus)
- **Reference Project**: [HanMoonSub/DeepGuard](https://github.com/HanMoonSub/DeepGuard)
- **Architecture**: `MS-EffGCViT-B0` (Mobile-Scale Efficient Global Context Vision Transformer) + YOLOv8-Face
- **License**: MIT License (Copyright 2024 HanMoonSub)

### Critical Limitations for Women's Safety Use
1. **Automated Screening Indicator Only**: Neither detector produces cryptographically or legally admissible proof of manipulation. Confidence scores represent heuristic proximity to training distributions.
2. **Generative Distribution Drift**: Fast-evolving diffusion models and generative tools may create novel manipulation artifacts not present in benchmark datasets (e.g. FaceForensics++).
3. **No Context, Identity, or Intent Recognition**: The models analyze pixel textures and facial artifacts. They do not identify individuals, cannot verify legal age or identity, cannot evaluate personal consent, and cannot determine whether content constitutes harassment or non-consensual sexual material.
4. **Human Review Required**: High confidence scores should serve only as a preliminary triaging cue for human safety workers. Never base legal, punitive, or protective actions solely on automated model outputs.
