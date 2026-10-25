"""
Automated feature demonstration and clean screenshot capture script for SafeMate.
Ensures bright, attractive screenshots with zero blue borders or focus outlines.
"""

import time
import os
from PIL import Image, ImageEnhance
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def remove_blue_borders_and_polish(image_path: str, output_path: str):
    """
    Analyzes borders, removes any blue lines or artifacts, trims 4-8px margins,
    and applies subtle brightness/contrast enhancement.
    """
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    # Analyze and trim edges if blue or dark frame is found
    # We inspect outer 15 pixels on all four edges
    pixels = img.load()
    
    def is_blue_pixel(r, g, b):
        return (b > 120 and b > r * 1.2 and b > g * 1.1) or (b > 160 and r < 100)
    
    crop_left = 4
    crop_top = 4
    crop_right = width - 4
    crop_bottom = height - 4
    
    # Check left edge for blue
    for x in range(min(20, width)):
        has_blue = any(is_blue_pixel(*pixels[x, y]) for y in range(0, height, 5))
        if has_blue:
            crop_left = max(crop_left, x + 3)
            
    # Check right edge for blue
    for x in range(width - 1, max(width - 20, 0), -1):
        has_blue = any(is_blue_pixel(*pixels[x, y]) for y in range(0, height, 5))
        if has_blue:
            crop_right = min(crop_right, x - 3)
            
    # Check top edge for blue
    for y in range(min(20, height)):
        has_blue = any(is_blue_pixel(*pixels[x, y]) for x in range(0, width, 5))
        if has_blue:
            crop_top = max(crop_top, y + 3)
            
    # Check bottom edge for blue
    for y in range(height - 1, max(height - 20, 0), -1):
        has_blue = any(is_blue_pixel(*pixels[x, y]) for x in range(0, width, 5))
        if has_bottom := any(is_blue_pixel(*pixels[x, y]) for x in range(0, width, 5)):
            crop_bottom = min(crop_bottom, y - 3)

    # Ensure valid bounding box
    if crop_right > crop_left + 100 and crop_bottom > crop_top + 100:
        img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    # Polish: Boost brightness slightly (+3%) and contrast (+5%) for crisp, attractive presentation
    bright_enhancer = ImageEnhance.Brightness(img)
    img = bright_enhancer.enhance(1.03)
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(1.05)
    
    img.save(output_path, "PNG", quality=95, optimize=True)
    print(f"[OK] Saved polished screenshot: {os.path.basename(output_path)} ({img.width}x{img.height})")


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1440,920")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(options=chrome_options)
    temp_raw = os.path.join(OUTPUT_DIR, "temp_raw.png")

    try:
        base_url = "http://localhost:3000"
        print(f"Connecting to {base_url}...")
        driver.get(base_url)
        time.sleep(2)

        # Remove all focus outlines, borders, and dev outlines
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
        time.sleep(0.5)

        # 1. Homepage & Hero Display
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "01_hero_homepage.png"))

        # 2. 3-Mode Authentication Modal
        driver.execute_script("if (window.openAuthModal) window.openAuthModal('login');")
        time.sleep(1.2)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "02_auth_3mode_modal.png"))
        driver.execute_script("if (window.closeAuthModal) window.closeAuthModal();")
        time.sleep(0.8)

        # 3. Judge Demo Mode Active View
        driver.execute_script("if (window.SafeMateAuth) window.SafeMateAuth.enterDemoMode();")
        time.sleep(1.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "03_demo_mode_active.png"))

        # 4. Emergency SOS Simulated Dispatch
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('sosModal');")
        time.sleep(1.5)
        # Trigger simulated SOS
        driver.execute_script("""
            const sendBtn = document.getElementById('btn-send-sos');
            if (sendBtn) sendBtn.click();
        """)
        time.sleep(1.8)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "04_emergency_sos.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('sosModal');")
        time.sleep(0.8)

        # 5. SafeWalk Live Escort & Dead Man's Timer
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-safewalk');")
        time.sleep(1.5)
        # Start simulated safewalk trip
        driver.execute_script("""
            const swBtn = document.getElementById('btn-toggle-safewalk');
            if (swBtn && swBtn.innerText.includes('Start')) swBtn.click();
        """)
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "05_safewalk_journey.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('modal-feature-safewalk');")
        time.sleep(0.8)

        # 6. Tell-Once Trauma-Informed Incident Intake
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('tellOnceModal');")
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "06_tell_once_intake.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('tellOnceModal');")
        time.sleep(0.8)

        # 7. Secure Evidence Vault & Cryptographic Chain-of-Custody
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-vault');")
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "07_evidence_vault.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('modal-feature-vault');")
        time.sleep(0.8)

        # 8. Leak-Tracer Invisible Watermarking
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-leak');")
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "08_leak_tracer.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('modal-feature-leak');")
        time.sleep(0.8)

        # 9. Deepfake & AI Media Screening
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('deepfakeModal');")
        time.sleep(1.5)
        # Click sample test in deepfake modal if available
        driver.execute_script("""
            const sampleBtn = document.getElementById('btn-deepfake-demo-sample');
            if (sampleBtn) sampleBtn.click();
        """)
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "09_deepfake_scanner.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('deepfakeModal');")
        time.sleep(0.8)

        # 10. Interactive Safety & Legal Chatbot Assistant
        driver.execute_script("if (window.openWorkspaceModal) window.openWorkspaceModal('modal-feature-chatbot');")
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "10_legal_chatbot.png"))
        driver.execute_script("if (window.closeWorkspaceModal) window.closeWorkspaceModal('modal-feature-chatbot');")
        time.sleep(0.8)

        # 11. Stealth Panic Switch (Recipe Disguise)
        driver.execute_script("if (window.toggleRecipeDisguise) window.toggleRecipeDisguise();")
        time.sleep(1.5)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "11_stealth_recipe_disguise.png"))
        driver.execute_script("if (window.toggleRecipeDisguise) window.toggleRecipeDisguise();")
        time.sleep(0.8)

        # 12. Feature Cards & Urban Safety Grid
        driver.execute_script("window.scrollTo(0, 780);")
        time.sleep(1)
        driver.save_screenshot(temp_raw)
        remove_blue_borders_and_polish(temp_raw, os.path.join(OUTPUT_DIR, "12_feature_matrix_cards.png"))

        # Clean up temporary raw file
        if os.path.exists(temp_raw):
            os.remove(temp_raw)

        print("[SUCCESS] All 12 feature screenshots captured and polished successfully!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
