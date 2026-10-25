"""
Capture Video Deepfake feature screenshots (Staged Video & Neural Detection Result).
Ensures zero blue borders, bright, attractive images.
"""

import time
import os
from PIL import Image, ImageEnhance
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots")

def remove_blue_borders_and_polish(image_path: str, output_path: str):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    
    def is_blue_pixel(r, g, b):
        return (b > 120 and b > r * 1.2 and b > g * 1.1) or (b > 160 and r < 100)
    
    crop_left = 6
    crop_top = 6
    crop_right = width - 6
    crop_bottom = height - 6
    
    for x in range(min(25, width)):
        if any(is_blue_pixel(*pixels[x, y]) for y in range(0, height, 4)):
            crop_left = max(crop_left, x + 3)
            
    for x in range(width - 1, max(width - 25, 0), -1):
        if any(is_blue_pixel(*pixels[x, y]) for y in range(0, height, 4)):
            crop_right = min(crop_right, x - 3)
            
    for y in range(min(25, height)):
        if any(is_blue_pixel(*pixels[x, y]) for x in range(0, width, 4)):
            crop_top = max(crop_top, y + 3)
            
    for y in range(height - 1, max(height - 25, 0), -1):
        if any(is_blue_pixel(*pixels[x, y]) for x in range(0, width, 4)):
            crop_bottom = min(crop_bottom, y - 3)

    if crop_right > crop_left + 100 and crop_bottom > crop_top + 100:
        img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    bright_enhancer = ImageEnhance.Brightness(img)
    img = bright_enhancer.enhance(1.03)
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(1.05)
    
    img.save(output_path, "PNG", quality=95, optimize=True)
    print(f"[OK] Polished: {os.path.basename(output_path)} ({img.width}x{img.height})")


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1440,940")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(options=chrome_options)
    temp_raw = os.path.join(OUTPUT_DIR, "temp_video_deepfake.png")

    try:
        driver.get("http://localhost:3000")
        time.sleep(2)
        driver.execute_script("""
            const style = document.createElement('style');
            style.id = 'clean-screenshots-style';
            style.innerHTML = `
                *:focus { outline: none !important; box-shadow: none !important; }
                ::-webkit-scrollbar { display: none !important; }
                body { overflow-x: hidden !important; }
            `;
            document.head.appendChild(style);
        """)

        # 1. Open Deepfake Modal and switch to Video tab
        print("Staging Video Deepfake Media...")
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('deepfakeModal');")
        time.sleep(0.8)
        driver.execute_script("""
            const tabVideo = document.getElementById('tab-deepfake-video');
            const tabImage = document.getElementById('tab-deepfake-image');
            if (tabVideo) tabVideo.click();

            if (tabVideo) {
                tabVideo.style.backgroundColor = '#0B132B';
                tabVideo.style.color = '#ffffff';
                tabVideo.style.fontWeight = '700';
                tabVideo.style.boxShadow = '0 2px 8px rgba(11, 19, 43, 0.2)';
                tabVideo.setAttribute('aria-selected', 'true');
            }
            if (tabImage) {
                tabImage.style.backgroundColor = 'transparent';
                tabImage.style.color = '#475569';
                tabImage.style.fontWeight = '600';
                tabImage.style.boxShadow = 'none';
                tabImage.setAttribute('aria-selected', 'false');
            }
            const engineLabel = document.getElementById('deepfake-active-engine-label');
            if (engineLabel) {
                engineLabel.textContent = 'MS-EffGCViT-B0 + YOLOv8n-Face (KoreaPeter/ms-eff-gcvit)';
            }
            const scanLabel = document.getElementById('btn-scan-deepfake-label');
            if (scanLabel) {
                scanLabel.textContent = 'Execute Video Deepfake Scan';
            }

            const stagedCard = document.getElementById('deepfake-staged-file-card');
            const dropzonePrompt = document.getElementById('deepfake-dropzone-prompt');
            const hashBar = document.getElementById('deepfake-hash-bar');
            const hashCode = document.getElementById('deepfake-hash-code');
            const filenameEl = document.getElementById('deepfake-staged-filename');
            const metaEl = document.getElementById('deepfake-staged-meta');
            const iconEl = document.getElementById('deepfake-staged-icon');
            const downloadBtn = document.getElementById('btn-download-sample-video');

            if (dropzonePrompt) dropzonePrompt.style.display = 'none';
            if (stagedCard) stagedCard.style.display = 'flex';
            if (filenameEl) filenameEl.textContent = 'sample_deepfake_video.mp4';
            if (metaEl) metaEl.textContent = '120.8 KB • Video Stream (25 Frames, 10 fps)';
            if (iconEl) {
                iconEl.textContent = 'VIDEO';
                iconEl.style.background = '#881337';
            }
            if (hashBar) hashBar.style.display = 'flex';
            if (hashCode) hashCode.textContent = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
            if (downloadBtn) downloadBtn.style.display = 'inline-flex';
        """)
        time.sleep(1.2)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "15_video_deepfake_upload_staged.png"))

        # 2. Render Video Deepfake Detection Result
        print("Rendering Video Deepfake Detection Result...")
        driver.execute_script("""
            const stagedCard = document.getElementById('deepfake-staged-file-card');
            const dropzone = document.getElementById('dropzone-deepfake');
            const hashBar = document.getElementById('deepfake-hash-bar');
            const progressCard = document.getElementById('deepfake-progress-card');
            const verdictCard = document.getElementById('deepfake-verdict-card');
            const scanBtn = document.getElementById('btn-scan-deepfake');
            const tabVideo = document.getElementById('tab-deepfake-video');
            const tabImage = document.getElementById('tab-deepfake-image');

            if (tabVideo) {
                tabVideo.style.backgroundColor = '#0B132B';
                tabVideo.style.color = '#ffffff';
                tabVideo.style.fontWeight = '700';
                tabVideo.style.boxShadow = '0 2px 8px rgba(11, 19, 43, 0.2)';
                tabVideo.setAttribute('aria-selected', 'true');
            }
            if (tabImage) {
                tabImage.style.backgroundColor = 'transparent';
                tabImage.style.color = '#475569';
                tabImage.style.fontWeight = '600';
                tabImage.style.boxShadow = 'none';
                tabImage.setAttribute('aria-selected', 'false');
            }

            if (stagedCard) stagedCard.style.display = 'none';
            if (dropzone) dropzone.style.display = 'none';
            if (hashBar) hashBar.style.display = 'none';
            if (progressCard) progressCard.style.display = 'none';
            if (scanBtn) scanBtn.style.display = 'none';

            if (verdictCard) {
                verdictCard.style.display = 'block';
                verdictCard.style.border = '1.5px solid #be123c';
                verdictCard.innerHTML = `
                  <!-- Verdict Header Ribbon -->
                  <div style="background-color: #be123c; color: #ffffff; padding: 12px 18px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span style="font-weight: 800; font-size: 0.8rem; letter-spacing: 0.06em;">[ALERT]</span>
                      <span style="font-weight: 800; font-size: 0.88rem; letter-spacing: 0.04em;">POTENTIAL SYNTHETIC MANIPULATION DETECTED</span>
                    </div>
                    <span style="background-color: rgba(255, 255, 255, 0.22); padding: 3px 10px; border-radius: 4px; font-size: 0.76rem; font-weight: 700;">
                      91.8% Confidence
                    </span>
                  </div>

                  <!-- Verdict Details & Authenticity Meters -->
                  <div style="padding: 18px 20px; display: flex; flex-direction: column; gap: 14px;">
                    <div>
                      <div style="display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 6px;">
                        <span style="color: #047857; font-weight: 700;">Natural Camera Optical Pattern: 8.2%</span>
                        <span style="color: #b91c1c; font-weight: 700;">Synthetic Face-Swap Manipulation: 91.8%</span>
                      </div>
                      <div style="height: 10px; background-color: #e2e8f0; border-radius: 5px; overflow: hidden; display: flex;">
                        <div style="width: 8.2%; background-color: #10b981;"></div>
                        <div style="width: 91.8%; background-color: #f43f5e;"></div>
                      </div>
                    </div>

                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 14px; font-size: 0.8rem; line-height: 1.55; color: #334155;">
                      <strong style="color: #090d16; display: block; margin-bottom: 4px;">Forensic Neural Findings (MS-EffGCViT-B0):</strong>
                      Automated screening detected temporal boundary warping, facial lighting incoherence, and neural blending markers frequently associated with digital face-swapping across 20 sampled video frames.
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; font-size: 0.72rem; color: #475569; background-color: #fafaf9; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                      <div>
                        <span style="color: #64748b; display: block;">Video Neural Architecture:</span>
                        <strong style="color: #090d16;">MS-EffGCViT-B0 + YOLOv8n-Face</strong>
                      </div>
                      <div>
                        <span style="color: #64748b; display: block;">Inspection Scope:</span>
                        <strong style="color: #090d16;">20 frames sampled • 20 localized faces</strong>
                      </div>
                      <div>
                        <span style="color: #64748b; display: block;">Traceable Audit ID:</span>
                        <code style="color: #0284c7;">req_vid_effgcvit_9887ff77</code>
                      </div>
                      <div>
                        <span style="color: #64748b; display: block;">Evidentiary Standard:</span>
                        <strong style="color: #090d16;">Section 63 BSA / Sec 65B IEA Compliant</strong>
                      </div>
                    </div>
                  </div>
                `;
            }
        """)
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "16_video_deepfake_detection_verdict.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('deepfakeModal');")
        time.sleep(0.5)

        if os.path.exists(temp_raw):
            os.remove(temp_raw)

        print("[SUCCESS] Video Deepfake screenshots captured successfully!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
