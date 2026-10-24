# Safemate Backend API Documentation

The Safemate backend is an asynchronous, privacy-focused FastAPI microservice powering the **Safemate Women's Safety Platform**. It provides automated media safety screening capabilities for detecting AI-generated still imagery and deepfake facial manipulation in video files.

---

## 1. Feature Architecture & Safeguards

Safemate provides two isolated screening features under the `/api/v1` namespace:

### A. Still-Image AI Generation Screening
- **Endpoint:** `POST /api/v1/detect`
- **Model:** `umm-maybe/AI-image-detector` (Swin Transformer for Image Classification)
- **Input Formats:** JPEG, PNG, WEBP (up to 10 MB, max dimension 4096×4096, max 16MP)
- **Memory Safety:** Processed 100% in memory via `io.BytesIO`. Images and metadata are never saved to disk or persistent storage.
- **Output:** Categorized probabilities (`artificial` vs. `human`) with plain-language limitations.

### B. Safemate Video Safety Screening
- **Endpoint:** `POST /api/v1/deepfake/detect`
- **Model:** `KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus` (`MS-EffGCViT-B0`, 8.7M parameters, ~34.8 MB weights)
- **Face Localization:** `YOLOv8n-Face` (`yolov8n-face.pt`, ~6.1 MB weights)
- **Input Formats:** `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv` (up to 50 MB, max duration 180s, max resolution 3840px)
- **Sampling:** 5 to 30 frames sampled uniformly across the video (default: 20 frames).
- **Processing Engine:**
  1. Decodes video via OpenCV into an ephemeral temporary file with a randomized name.
  2. Extracts uniformly spaced frames; downscales frames exceeding 1080p to conserve memory.
  3. Detects and crops primary face regions with a 20% margin.
  4. Resizes crops to $224 \times 224$ and applies ImageNet channel normalization.
  5. Runs batched CPU forward passes through the MS-EffGCViT network.
  6. Aggregates frame scores using a confidence-weighted heuristic (`conf` mode).
  7. **Guaranteed Cleanup:** Automatically removes the temporary video file in a `finally` block immediately after extraction. No user videos or facial crops are ever retained.
- **Output:** Structured outcome (`potential_manipulation_detected`, `no_manipulation_detected_by_model`, `inconclusive`, or `no_face_detected`).

### C. Interactive Safety & Legal Chatbot (Feature 4)
- **Web UI:** `/chatbot` (or `/api/v1/chatbot/ui`)
- **API Prefix:** `/api/v1/chatbot`
- **Core Technology:** Deterministic safety guidance engine with 9 structured flows, emergency priority interrupts, verified helplines, intent mapping, and an optional multi-tier cascading LLM layer (Groq `llama-3.1-8b-instant` primary → Google Gemini `gemini-1.5-flash` fallback → local curated safety engine).
- **Privacy Guarantee:** Privacy-first, stateless design. No login or identity required. No conversation transcripts or sensitive personal narratives are logged or permanently stored.
- **Immediate-Danger Priority:** Any message indicating active physical danger, assault, or being followed interrupts the dialogue and presents emergency contacts (112, 181, 1091) immediately without demanding logins, coordinates, or explanations.
- **No False Claims:** Safemate explicitly discloses that it does not automatically dispatch police or submit cybercrime complaints on its own; it provides official direct links and verified phone numbers for user action.

---

## 2. API Contract Reference

Base URL prefix: `/api/v1`

### Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service root and discovery directory |
| `GET` | `/chatbot` | Interactive Safety Assistant web interface |
| `GET` | `/api/v1/health` | Liveness check (verifies process is running) |
| `GET` | `/api/v1/health/ready` | Still-image model readiness check |
| `GET` | `/api/v1/model-info` | Still-image model metadata and limitations |
| `POST` | `/api/v1/detect` | Screen still image for AI generation |
| `GET` | `/api/v1/deepfake/ready` | Video deepfake model readiness check |
| `GET` | `/api/v1/deepfake/model-info` | Video deepfake model metadata and limitations |
| `POST` | `/api/v1/deepfake/detect` | Screen video for facial manipulation / deepfakes |
| `POST` | `/api/v1/emergency/sos` | Safemate Emergency SOS panic button |
| `POST` | `/api/v1/safewalk/create-trip` | Create active SafeWalk monitoring trip |
| `GET` | `/api/v1/safewalk/trip/{token}` | Retrieve SafeWalk trip session details |
| `POST` | `/api/v1/safewalk/update-location` | Update SafeWalk location ping |
| `POST` | `/api/v1/evidence/upload` | Upload and catalog incident evidence |
| `GET` | `/api/v1/chatbot/health` | Chatbot service readiness & catalog check |
| `GET` | `/api/v1/chatbot/resources` | List verified resources filtered by country |
| `GET` | `/api/v1/chatbot/flows` | List available structured safety flows |
| `POST` | `/api/v1/chatbot/start` | Launch a guided safety flow by ID |
| `POST` | `/api/v1/chatbot/message` | Submit choice chip or text query to assistant |
| `POST` | `/api/v1/chatbot/feedback` | Submit guidance review / outdated report |

---

### Detailed Endpoint Specifications

#### 1. `GET /api/v1/health`
- **Status:** `200 OK`
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "ai-image-screening-api"
  }
  ```

#### 2. `GET /api/v1/health/ready`
- **Status:** `200 OK` (when ready) or `503 Service Unavailable` (when unready/initializing)
- **Response (200 OK):**
  ```json
  {
    "status": "ready",
    "model_loaded": true,
    "model_id": "umm-maybe/AI-image-detector",
    "device": "cpu"
  }
  ```

#### 3. `GET /api/v1/model-info`
- **Status:** `200 OK`
- **Response:**
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

#### 4. `POST /api/v1/detect`
- **Content-Type:** `multipart/form-data`
- **Field:** `file` (Image: JPEG, PNG, WEBP, max 10 MB)
- **Header (Optional):** `X-Request-ID`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "model_id": "umm-maybe/AI-image-detector",
    "prediction": {
      "label": "artificial",
      "score": 0.94215,
      "scores": [
        { "label": "artificial", "score": 0.94215 },
        { "label": "human", "score": 0.05785 }
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

#### 5. `GET /api/v1/deepfake/ready`
- **Status:** `200 OK` (when ready) or `503 Service Unavailable` (when unready/initializing)
- **Response (200 OK):**
  ```json
  {
    "status": "ready",
    "model_loaded": true,
    "detector_loaded": true,
    "model_id": "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus",
    "device": "cpu"
  }
  ```

#### 6. `GET /api/v1/deepfake/model-info`
- **Status:** `200 OK`
- **Response:**
  ```json
  {
    "model_id": "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus",
    "task": "video-deepfake-screening",
    "architecture": "MS-EffGCViT-B0",
    "face_detector": "YOLOv8n-Face",
    "description": "Mobile-Scale Efficient Global Context Vision Transformer (MS-EffGCViT-B0) paired with YOLOv8-Face. Analyzes face bounding boxes extracted from video frames to screen for digital facial manipulation artifacts.",
    "model_loaded": true,
    "inference_available": true,
    "labels": [
      "potential_manipulation_detected",
      "no_manipulation_detected_by_model",
      "inconclusive",
      "no_face_detected"
    ],
    "limitations_notice": "This is an automated video deepfake screening estimate, not definitive proof that a video is authentic, manipulated, or legally admissible evidence. It requires visible facial clarity and does not evaluate personal identity or consent."
  }
  ```

#### 7. `POST /api/v1/deepfake/detect`
- **Content-Type:** `multipart/form-data`
- **Field:** `file` (Video: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`, max 50 MB)
- **Query Parameter (Optional):** `num_frames` (integer 5–30, default: 20)
- **Header (Optional):** `X-Request-ID`

**Response (200 OK — Faces Detected & Analyzed):**
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
  "request_id": "req_8ffc60bdcb"
}
```

**Response (200 OK — No Visible Face Detected):**
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
  "limitations": [
    "This is an automated video deepfake screening estimate, not definitive proof that a video is authentic, manipulated, or legally admissible evidence.",
    "Detection accuracy is dependent on visible facial clarity, lighting, compression, frame rate, and head movement.",
    "This screening tool does not verify individual identity, consent, intent, or whether video content is non-consensual or abusive.",
    "Do not use this automated screening score as the sole basis for moderation, legal, or protective actions."
  ],
  "request_id": "req_video_12345"
}
```

---

### Standardized Error Format

All error responses return a uniform contract:
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Video size (54.2MB) exceeds the maximum allowed limit of 50MB."
  },
  "request_id": "req_a1b2c3d4e5f6"
}
```

#### Error Code Reference:
- `MISSING_FILE` (HTTP 400) — No file provided in the `file` multipart field.
- `EMPTY_FILE` (HTTP 400) — The uploaded payload is 0 bytes.
- `INVALID_IMAGE` / `INVALID_VIDEO` (HTTP 400) — Corrupted file or decoding failure.
- `EXCESSIVE_DIMENSIONS` (HTTP 400) — Image exceeds 4096px or video exceeds 3840px.
- `VIDEO_TOO_LONG` (HTTP 400) — Video duration exceeds 180 seconds.
- `ANIMATED_IMAGE_NOT_SUPPORTED` (HTTP 400) — Animated GIF/APNG uploaded to still image endpoint.
- `FILE_TOO_LARGE` (HTTP 413) — Upload exceeds 10 MB (image) or 50 MB (video).
- `UNSUPPORTED_MEDIA_TYPE` (HTTP 415) — File extension or MIME type not in allowed list.
- `MODEL_NOT_READY` (HTTP 503) — Classifier or face detector is still initializing or unready.
- `INFERENCE_FAILURE` (HTTP 500) — Controlled internal inference failure without fabricated responses.

---

## 3. Frontend Integration Guide (JavaScript / TypeScript)

The Safemate frontend connects to the backend using standard browser `fetch` calls.

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * 1. Screen a Still Image for AI Generation
 * @param {File} imageFile - File object from <input type="file" />
 * @returns {Promise<object>}
 */
export async function screenImage(imageFile) {
  if (!imageFile) throw new Error("Please select an image file.");

  // Check image model readiness
  const readyRes = await fetch(`${API_BASE_URL}/api/v1/health/ready`);
  if (!readyRes.ok) {
    throw new Error("Still-image screening service is initializing. Please retry in a few moments.");
  }

  const formData = new FormData();
  formData.append("file", imageFile);

  const res = await fetch(`${API_BASE_URL}/api/v1/detect`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok || !data.success) {
    throw new Error(data?.error?.message || "Failed to screen image.");
  }
  return data;
}

/**
 * 2. Safemate Video Safety Screening
 * @param {File} videoFile - Video file object (.mp4, .mov, .webm, etc.)
 * @param {number} numFrames - Sampled frame count (5 to 30, default 20)
 * @returns {Promise<object>}
 */
export async function screenVideo(videoFile, numFrames = 20) {
  if (!videoFile) throw new Error("Please select a video file.");

  // Check video model readiness
  const readyRes = await fetch(`${API_BASE_URL}/api/v1/deepfake/ready`);
  if (!readyRes.ok) {
    throw new Error("Video safety screening service is initializing. Please retry in a few moments.");
  }

  const formData = new FormData();
  formData.append("file", videoFile);

  const res = await fetch(`${API_BASE_URL}/api/v1/deepfake/detect?num_frames=${numFrames}`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok || !data.success) {
    throw new Error(data?.error?.message || "Failed to screen video.");
  }
  return data;
}
```

---

## 4. Testing Endpoints via CLI

### Test Image Screening (PowerShell)
```powershell
$form = @{
    file = Get-Item "C:\path\to\sample_photo.jpg"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/detect" -Method Post -Form $form
```

### Test Video Safety Screening (PowerShell)
```powershell
$form = @{
    file = Get-Item "C:\path\to\sample_video.mp4"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/deepfake/detect?num_frames=20" -Method Post -Form $form
```

### Test Video Safety Screening (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/deepfake/detect?num_frames=20" \
  -H "accept: application/json" \
  -F "file=@sample_video.mp4;type=video/mp4"
```

### Test Chatbot Guidance (PowerShell)
```powershell
# 1. Start a guided flow (e.g., immediate_danger or report_cybercrime_india)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chatbot/start" -Method Post `
  -ContentType "application/json" `
  -Body '{"flow_id": "report_cybercrime_india", "country": "IN"}'

# 2. Submit interaction or query
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chatbot/message" -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "I need help with someone sharing my private photos", "country": "IN"}'
```

### Test Chatbot Guidance (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Someone is blackmailing me online", "country": "IN"}'
```

---

## 5. Automated Tests

The backend includes a comprehensive pytest suite with 111 deterministic unit and integration tests executing in under 5 seconds.

```powershell
cd backend
python -m pytest
```

Output:
```text
===================== 111 passed, 1 deselected, 7 warnings in 4.38s =====================
```

The test suite validates:
- **Image & Video AI Screening:** Liveness, readiness, and model-info contracts for both image and video services.
- **Multipart Uploading & Limits:** Boundary parsing, dimension/duration limits, and oversized media rejection.
- **Privacy Guarantees:** Ephemeral in-memory image screening and guaranteed temporary video file cleanup.
- **Feature 4 Safety Assistant:**
  - Health and flow metadata discovery.
  - Starting all 9 supported flows independently (`immediate_danger`, `online_harassment`, `blackmail_threats`, `intimate_image_abuse`, `impersonation_fake_profile`, `physical_harassment`, `report_cybercrime_india`, `preserve_evidence`, `understand_options`).
  - Next-step and cross-flow transitions.
  - Deterministic immediate danger interception overriding non-emergency conversation.
  - Verified emergency helplines delivered without authentication.
  - Security safeguards against asking for passwords, OTPs, or intimate photo uploads.
  - Error and bounds validation (>1000 characters rejected).
  - Feedback submission and standalone web interface rendering.
- **Emergency SOS & SafeWalk:** Panic button alert dispatch, tracking token validation, and overdue trip alerts.

---

## 6. Cloud Deployment (Render Blueprint)

A `render.yaml` blueprint is configured for automated container or Python environment deployment.

### Specifications:
- **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/v1/health`
- **Hardware Requirement:** **Render Starter (1 GB or 2 GB RAM)**. Loading both neural models simultaneously into memory requires approximately ~900 MB to 1.2 GB RAM under concurrent request processing. Free tier (512 MB) instances may experience memory pressure.

---

## 7. Responsible Safety Boundaries

1. **Screening Indicator Only:** Automated scores represent heuristic statistical proximity to training distributions, not legal proof of manipulation or authenticity.
2. **Environmental Variance:** Motion blur, heavy video compression, extreme camera angles, and low lighting may influence detection reliability.
3. **No Personal Identification:** Safemate does not identify people, verify identity, or detect consent.
4. **Caseworker Triaging:** High confidence scores should serve solely to assist human caseworkers with triaging potential non-consensual media.
