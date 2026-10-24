# Third-Party Notices & Open Source Attribution

Safemate incorporates, references, or builds upon open-source software and pretrained machine learning models. This document sets forth required third-party notices, license texts, and attribution for all external models, libraries, and reference repositories utilized within Safemate.

---

## 1. DeepGuard (Reference Architecture & Pretrained Model)

- **Project Name:** DeepGuard
- **Repository URL:** [https://github.com/HanMoonSub/DeepGuard](https://github.com/HanMoonSub/DeepGuard)
- **Author / Copyright:** Copyright (c) 2024 HanMoonSub
- **License:** MIT License
- **License Text:**
  ```text
  MIT License

  Copyright (c) 2024 HanMoonSub

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
  ```

### Components Utilized in Safemate:
- **Model Architecture:** `MS-EffGCViT-B0` (Mobile-Scale Efficient Global Context Vision Transformer), integrating depthwise separable convolutions and windowed self-attention.
- **Inference Pipeline:** Uniform video frame extraction, face bounding-box cropping, ImageNet normalization, and confidence-based frame score aggregation.
- **Pretrained Checkpoint:** `KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus` (hosted on Hugging Face Hub, MIT License, 34.8 MB weights in `safetensors` format).

### Components NOT Reused / Excluded:
- DeepGuard's React web frontend was **NOT** copied or reused. Safemate maintains its own branded, dedicated user interface.
- Celery, Redis, MySQL, and Docker-compose orchestration stacks were **NOT** reused. Safemate implements stateless, in-memory, ephemeral inference within FastAPI.
- Training datasets (FaceForensics++, Celeb-DF, WildDeepfake) were **NOT** downloaded, bundled, or distributed.

---

## 2. umm-maybe / AI Image Detector (Still-Image Screening)

- **Model Identifier:** `umm-maybe/AI-image-detector`
- **Model Hub URL:** [https://huggingface.co/umm-maybe/AI-image-detector](https://huggingface.co/umm-maybe/AI-image-detector)
- **Base Architecture:** Vision Transformer (`google/vit-base-patch16-224-in21k`) fine-tuned for artificial vs. human image classification.
- **License:** Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0).
- **Terms:** Model weights are loaded strictly for runtime screening inference. Weights are not redistributed in modified form.
- **Usage Disclaimer:** Still-image AI generation screening only. Not a face-swap detector, not a video deepfake detector, and not definitive legal evidence.

---

## 3. YOLOv8 Face Detection (Face Bounding Box Extractor)

- **Model Name:** YOLOv8n-Face (`yolov8n-face.pt`)
- **Repository / Framework:** Ultralytics YOLOv8 ([https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics))
- **License:** AGPL-3.0 / Ultralytics Open Source License
- **Role:** Lightweight (6.1 MB) single-pass face localization used strictly at inference time to crop facial regions from sampled video frames before classification.

---

## 4. Key Python Dependencies

| Package | Version | License | Purpose |
|---|---|---|---|
| `fastapi` | `>=0.115.0` | MIT | High-performance asynchronous API framework |
| `pydantic` | `>=2.10.0` | MIT | Data validation and schema enforcement |
| `torch` | `>=2.4.0` | BSD-3-Clause | Tensor computation and neural network evaluation |
| `torchvision` | `>=0.19.0` | BSD-3-Clause | Vision utilities and tensor transforms |
| `timm` | `>=1.0.0` | Apache-2.0 | Deep learning vision models |
| `opencv-python-headless` | `>=4.8.0` | Apache-2.0 | Video decoding and frame extraction without GUI dependencies |
| `ultralytics` | `>=8.0.0` | AGPL-3.0 | Face localization inference |
| `huggingface-hub` | `>=0.25.0` | Apache-2.0 | Checkpoint downloading and caching |
| `safetensors` | `>=0.4.0` | Apache-2.0 | Fast, secure tensor serialization format |

---

## 5. Ethical & Operational Disclaimers

1. **Automated Screening Only:** Outputs from both the still-image detector and video deepfake detector are heuristic confidence scores, not infallible proofs of authenticity or manipulation.
2. **No Legal Admissibility:** Neither endpoint produces legally binding forensics or chain-of-custody evidence.
3. **Contextual Limitations:** Video deepfake screening accuracy depends on resolution, lighting, compression, frame rate, and visible facial features. Videos without visible human faces will return a neutral `no_face_detected` status.
4. **Privacy First:** Safemate processes all video uploads ephemerally in volatile temporary storage, purging all temporary files immediately upon request completion in guaranteed `finally` execution blocks. No user videos are retained or stored.
