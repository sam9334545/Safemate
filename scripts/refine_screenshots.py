"""
Re-capture 07, 09, and 13 with full rendered outputs.
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
    print(f"[OK] Re-polished: {os.path.basename(output_path)} ({img.width}x{img.height})")


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
    temp_raw = os.path.join(OUTPUT_DIR, "temp_raw_refine.png")

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

        # 07. Tell-Once Zero FIR Dossier Output
        print("Refining 07_tell_once_zero_fir_dossier...")
        driver.execute_script("if (window.openTellOnceModal) window.openTellOnceModal('en');")
        time.sleep(0.8)
        driver.execute_script("""
            const convView = document.getElementById('tell-once-conversation-view');
            const dossierView = document.getElementById('tell-once-dossier-view');
            if (convView) convView.style.display = 'none';
            if (dossierView) dossierView.style.display = 'flex';
            
            const docTitle = document.getElementById('tell-once-doc-badge');
            if (docTitle) {
                docTitle.innerHTML = `
                  <span style="background:#be123c; color:#ffffff; font-weight:800; font-size:0.75rem; padding:3px 8px; text-transform:uppercase;">Statutory Complaint</span>
                  <span style="font-weight:700; font-size:0.85rem; color:#0f172a;" id="tellOnceDocBadgeTitle">MANDATORY ZERO FIR COMPLAINT • SECTION 173 BNSS / SEC 154 CrPC</span>
                `;
            }
            
            const docText = document.getElementById('tell-once-dossier-text');
            if (docText) {
                docText.style.display = 'block';
                docText.style.fontFamily = 'monospace';
                docText.style.fontSize = '0.82rem';
                docText.style.lineHeight = '1.55';
                docText.style.whiteSpace = 'pre-wrap';
                docText.textContent = `TO THE STATION HOUSE OFFICER (SHO),
ANY POLICE STATION UNDER MANDATORY ZERO FIR JURISDICTION (SEC 173 BNSS)

SUBJECT: MANDATORY ZERO FIR COMPLAINT FOR EXTORTION & NON-CONSENSUAL INTIMATE MEDIA

Respected Sir/Madam,

I am submitting this statutory complaint under Section 173 of the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 mandating registration of a Zero FIR regardless of territorial jurisdiction.

1. INCIDENT BRIEF: Blackmail threats demanding payment to suppress privately shared photographs on social media.
2. TRANSMISSION PLATFORM & TIMELINE: Instagram Direct & Telegram (First received 24 Oct 2026, 21:40 IST)
3. ACCUSED IDENTIFIERS: User handle @extort_anon_2026 (Digital forensics preserved)
4. NATURE OF THREATS: Demand for monetary transfer within 24 hours under threat of non-consensual distribution.

STATUTORY PROVISIONS APPLICABLE:
• Section 351(2) BNSS (Criminal Intimidation)
• Section 308(2) BNSS (Extortion)
• Information Technology Act Section 66E (Violation of Bodily Privacy)
• Information Technology Act Section 67A (Sexually Explicit Electronic Transmission)

PRAYER: Kindly register this Zero FIR immediately, forward to the competent territorial Special Cell Cyber Police Station, and issue urgent Preservation Notices under Section 79(3)(b) IT Act to intermediary platforms.

Respectfully submitted,
Aggrieved Survivor (Identity Protected Under Section 72 BNSS)`;
            }
        """)
        time.sleep(1.2)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "07_tell_once_zero_fir_dossier.png"))
        driver.execute_script("if (window.closeTellOnceModal) window.closeTellOnceModal();")
        time.sleep(0.8)

        # 09. Deepfake Scan Result Output
        print("Refining 09_deepfake_scan_result...")
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('deepfakeModal');")
        time.sleep(0.8)
        driver.execute_script("""
            const stagedCard = document.getElementById('deepfake-staged-card');
            const dropzone = document.getElementById('dropzone-deepfake');
            const progressCard = document.getElementById('deepfake-progress-card');
            const verdictCard = document.getElementById('deepfake-verdict-card');
            const scanBtn = document.getElementById('btn-scan-deepfake');
            
            if (stagedCard) stagedCard.style.display = 'none';
            if (dropzone) dropzone.style.display = 'none';
            if (progressCard) progressCard.style.display = 'none';
            if (scanBtn) scanBtn.style.display = 'none';
            
            if (verdictCard) {
                verdictCard.style.display = 'block';
                verdictCard.style.border = '1.5px solid #be123c';
                verdictCard.innerHTML = `
                  <div style="background-color: #be123c; color: #ffffff; padding: 12px 18px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span style="font-weight: 800; font-size: 0.8rem; letter-spacing: 0.06em;">[ALERT]</span>
                      <span style="font-weight: 800; font-size: 0.88rem; letter-spacing: 0.04em;">POTENTIAL SYNTHETIC MANIPULATION DETECTED</span>
                    </div>
                    <span style="background-color: rgba(255, 255, 255, 0.22); padding: 3px 10px; border-radius: 4px; font-size: 0.76rem; font-weight: 700;">
                      94.2% Confidence
                    </span>
                  </div>
                  <div style="padding: 18px 20px; display: flex; flex-direction: column; gap: 14px;">
                    <div>
                      <div style="display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 6px;">
                        <span style="color: #047857; font-weight: 700;">Natural Camera Sensor Pattern: 5.8%</span>
                        <span style="color: #b91c1c; font-weight: 700;">Synthetic / AI Diffusion Probability: 94.2%</span>
                      </div>
                      <div style="height: 10px; background-color: #e2e8f0; border-radius: 5px; overflow: hidden; display: flex;">
                        <div style="width: 5.8%; background-color: #10b981;"></div>
                        <div style="width: 94.2%; background-color: #f43f5e;"></div>
                      </div>
                    </div>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 14px; font-size: 0.8rem; line-height: 1.55; color: #334155;">
                      <strong style="color: #090d16; display: block; margin-bottom: 4px;">Forensic Neural Findings:</strong>
                      High-frequency boundary artifacts, generative diffusion noise patterns, and discrete cosine transform anomalies characteristic of generative diffusion morphing models were detected across pixel channels.
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; font-size: 0.72rem; color: #475569; background-color: #fafaf9; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                      <div><span style="color: #64748b; display: block;">Neural Architecture:</span><strong style="color: #090d16;">Swin-Transformer (umm-maybe/AI-image-detector)</strong></div>
                      <div><span style="color: #64748b; display: block;">Inspection Environment:</span><strong style="color: #090d16;">100% Volatile RAM (Zero Cloud Disk Retention)</strong></div>
                      <div><span style="color: #64748b; display: block;">Traceable Audit ID:</span><code style="color: #0284c7;">req_swin_8829140</code></div>
                      <div><span style="color: #64748b; display: block;">Evidentiary Standard:</span><strong style="color: #090d16;">Section 63 BSA / Sec 65B IEA Compliant</strong></div>
                    </div>
                  </div>
                `;
            }
        """)
        time.sleep(1.2)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "09_deepfake_scan_result.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('deepfakeModal');")
        time.sleep(0.8)

        # 13. Legal Chatbot AI Consultation Output
        print("Refining 13_legal_chatbot_zero_fir_consult...")
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-chatbot');")
        time.sleep(0.8)
        driver.execute_script("""
            const chatLog = document.getElementById('simple-chat-log');
            if (chatLog) {
                chatLog.innerHTML = `
                  <div class="chat-bubble-user" style="background:#0f172a; color:#ffffff; padding:10px 14px; border-radius:10px 10px 0 10px; margin-bottom:12px; max-width:80%; margin-left:auto; font-size:0.84rem;">
                    Someone is threatening to leak morphed photos of me unless I pay them. How can I file a Zero FIR and what are my legal rights?
                  </div>
                  <div class="chat-bubble-ai" style="background:#ffffff; border:1px solid #cbd5e1; color:#0f172a; padding:12px 14px; border-radius:10px 10px 10px 0; margin-bottom:12px; max-width:88%; font-size:0.83rem; line-height:1.55; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                    <div style="font-weight:800; color:#881337; margin-bottom:4px; font-size:0.88rem;">
                      🛡️ STATUTORY LEGAL SANCTUARY & ZERO FIR ADVICE
                    </div>
                    <p style="margin:0 0 6px 0;">You are protected under statutory safeguards. You do not have to face this alone:</p>
                    <ul style="margin:0 0 8px 16px; padding:0;">
                      <li><strong>Zero FIR (Section 173 BNSS 2023):</strong> You can walk into ANY police station in India to lodge an FIR. Officers cannot cite territorial jurisdiction to refuse registration.</li>
                      <li><strong>Bodily Privacy Violation (Section 66E IT Act):</strong> Capturing, publishing, or blackmailing with intimate/morphed images carries up to 3 years imprisonment.</li>
                      <li><strong>Extortion & Criminal Intimidation:</strong> Punishable under Sections 308 and 351 of Bharatiya Nyaya Sanhita (BNS).</li>
                      <li><strong>National Cybercrime Portal:</strong> Dial <strong style="color:#0284c7;">1930</strong> immediately or visit <em>cybercrime.gov.in</em> to freeze recipient accounts.</li>
                    </ul>
                    <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:4px; padding:6px 10px; font-size:0.78rem; color:#15803d; font-weight:700;">
                      ✨ SafeMate Action: Click "Draft Zero FIR" above to auto-generate your ready-to-sign complaint letter.
                    </div>
                  </div>
                `;
            }
        """)
        time.sleep(1.2)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "13_legal_chatbot_zero_fir_consult.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('modal-feature-chatbot');")
        time.sleep(0.5)

        if os.path.exists(temp_raw):
            os.remove(temp_raw)

        print("[SUCCESS] Refinement complete!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
