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

---

## 5. Automated Tests

The test suite contains 31 fast, deterministic unit and integration tests that mock the model inference service so they run instantly without requiring an internet connection or downloading large model weights.

### Run Fast Test Suite (Default)
```powershell
python -m pytest
```
Output:
```text
31 passed, 1 deselected in ~0.8s
```

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
> **RAM Sizing**: The `umm-maybe/AI-image-detector` model weighs ~348 MB on disk. When loaded into PyTorch memory alongside torchvision/transformers dependencies and Pillow buffers, runtime RAM usage is typically between **700 MB and 1.1 GB**.
>
> On Render's **Free Tier (512 MB RAM)**, loading the model into memory can trigger an Out-Of-Memory (OOM) process kill. For stable production hosting, select the **Render Starter plan (1 GB or 2 GB RAM)**.
>
> **CPU Inference Latency**: The model runs on CPU by default. Average inference time on modern multi-core cloud instances is approximately **0.3s to 1.2s** per image.

### Configuring CORS in Production
In the Render Dashboard Environment settings (or via `render.yaml`):
```env
CORS_ORIGINS=https://your-frontend-app.onrender.com,https://your-custom-domain.com
```

---

## 7. Model Attribution, License & Ethical Limitations

### Attribution
- **Model Name**: [umm-maybe/AI-image-detector](https://huggingface.co/umm-maybe/AI-image-detector)
- **Model Creator**: Matthew Maybe (`umm-maybe`)
- **Architecture**: Swin Transformer for Image Classification (`SwinForImageClassification`)
- **Training**: Trained in October 2022 using AutoTrain on artistic images (binary classification: `artificial` vs. `human`).

### License
- **License**: Creative Commons Attribution-NoDerivatives 4.0 International ([CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/)).
- **Permitted Use**: You may share, distribute, and make the model available as part of your application or service with proper attribution. It cannot be used within text-to-image systems to evade AI image detection.

### Critical Limitations for Women's Safety Use
1. **Not Proof of Manipulation**: This tool produces probabilistic classification scores based on 2022 image features. It is not cryptographic or legal proof that an image was AI-generated or manipulated.
2. **Generative Model Drift**: Training data does not include recent generators like Midjourney v5+, SDXL, or DALL-E 3. It may miss artifacts or misclassify modern generated photos.
3. **No Context, Identity, or Intent Recognition**: The model only analyzes pixel textures. It does not identify people, cannot verify age or identity, cannot evaluate consent, and cannot determine whether content constitutes harassment or non-consensual media.
4. **Human Review Required**: High confidence scores (e.g. >90%) should serve only as a triaging cue for human review. Never base legal, punitive, or protective actions solely on this automated output.
