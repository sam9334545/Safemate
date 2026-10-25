"""
Refine screenshot 13 to show expanded chat stream without split modules taking up vertical room.
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
    temp_raw = os.path.join(OUTPUT_DIR, "temp_raw_refine13.png")

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

        # 13. Legal Chatbot AI Consultation Output
        print("Refining 13_legal_chatbot_zero_fir_consult...")
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-chatbot');")
        time.sleep(0.8)
        driver.execute_script("""
            const splitModules = document.querySelector('.legal-modules-split');
            if (splitModules) splitModules.style.display = 'none';
            
            const chatLog = document.getElementById('simple-chat-log');
            if (chatLog) {
                chatLog.style.minHeight = '380px';
                chatLog.style.maxHeight = '420px';
                chatLog.innerHTML = `
                  <div class="chat-bubble-user" style="background:#0f172a; color:#ffffff; padding:12px 16px; border-radius:10px 10px 0 10px; margin-bottom:14px; max-width:82%; margin-left:auto; font-size:0.86rem; line-height:1.45;">
                    Someone is threatening to leak private and morphed photos of me unless I pay them. How can I file a Zero FIR and what are my legal protections under Indian law?
                  </div>
                  <div class="chat-bubble-ai" style="background:#ffffff; border:1.5px solid #cbd5e1; color:#0f172a; padding:16px 18px; border-radius:10px 10px 10px 0; margin-bottom:14px; max-width:92%; font-size:0.84rem; line-height:1.6; box-shadow:0 3px 10px rgba(0,0,0,0.05);">
                    <div style="font-weight:900; color:#881337; margin-bottom:6px; font-size:0.92rem; display:flex; align-items:center; gap:6px;">
                      <span>🛡️</span> <span>STATUTORY LEGAL SANCTUARY & ZERO FIR DIRECTIVE</span>
                    </div>
                    <p style="margin:0 0 8px 0; color:#334155;">You are protected by statutory safeguards under national law. You do not have to give in to coercion:</p>
                    <ul style="margin:0 0 10px 18px; padding:0; color:#0f172a;">
                      <li style="margin-bottom:5px;"><strong>Mandatory Zero FIR (Section 173 BNSS 2023):</strong> You can walk into <em>any</em> police station in India to file your FIR. Police officers cannot cite territorial jurisdiction to refuse registration.</li>
                      <li style="margin-bottom:5px;"><strong>Violation of Bodily Privacy (Section 66E IT Act):</strong> Capturing, publishing, or blackmailing with intimate or morphed media carries up to 3 years imprisonment and statutory fines.</li>
                      <li style="margin-bottom:5px;"><strong>Extortion & Criminal Intimidation:</strong> Punishable under Sections 308(2) and 351(2) of the Bharatiya Nyaya Sanhita (BNS).</li>
                      <li><strong>National Cybercrime Portal:</strong> Dial <a href="tel:1930" style="color:#0284c7; font-weight:800;">1930</a> immediately or report at <em>cybercrime.gov.in</em> to freeze perpetrator communication and banking channels.</li>
                    </ul>
                    <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:10px 14px; font-size:0.8rem; color:#15803d; font-weight:700; display:flex; align-items:center; gap:8px;">
                      <span>✨</span> <span>SafeMate Action: Click "Draft Zero FIR" in the top bar to auto-generate a court-ready, signed complaint letter ready for police submission.</span>
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

        print("[SUCCESS] Chatbot refinement complete!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
