"""
SafeMate Automated Video Demonstration Generator
Compiles high-resolution feature screenshots, explanatory lower-third subtitles,
headers, and animated progress bars into a professional MP4 walkthrough video.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 24
SECONDS_PER_SCENE = 6

FONT_TITLE_PATH = "C:/Windows/Fonts/segoeuib.ttf" # Bold
FONT_BODY_PATH = "C:/Windows/Fonts/segoeui.ttf"   # Regular

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

font_h1 = get_font(FONT_TITLE_PATH, 42)
font_h2 = get_font(FONT_TITLE_PATH, 28)
font_body = get_font(FONT_BODY_PATH, 22)
font_small = get_font(FONT_BODY_PATH, 18)

SCENES = [
    {
        "type": "intro",
        "title": "SAFEMATE",
        "subtitle": "AI-Powered Personal Safety & Digital Forensic Sanctuary",
        "bullets": [
            "Trauma-Informed Single-Intake (Tell-Once Zero FIR Engine)",
            "Cryptographic Forensic Watermarking & Leak Tracer (LSB + HMAC)",
            "Neural AI Deepfake & Multi-Frame Video Manipulation Scanner",
            "Emergency SOS Dispatch, SafeWalk Escort & Disguised Evidence Vault"
        ]
    },
    {
        "type": "feature",
        "image": "docs/screenshots/01_survivor_sanctuary_hub.png",
        "badge": "FEATURE 01: SANCTUARY HUB & PRIVACY SHIELD",
        "headline": "Zero-Friction Access & Private Dashboard",
        "desc": "Supports 3 access modes: Registered Account, Ephemeral Guest Session, and Evaluator Demo Mode. Isolated state storage ensures zero local tracking footprints."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/02_instant_stealth_disguise.png",
        "badge": "FEATURE 02: PANIC STEALTH DISGUISE",
        "headline": "1-Tap Escape to Innocent Recipe Blog",
        "desc": "If an abuser or bystander walks into the room, pressing Escape instantly transforms the screen into a harmless cooking blog with zero traces of safety tools."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/06_tell_once_intake_flow.png",
        "badge": "FEATURE 03: VOICE ONE • TELL-ONCE INTAKE",
        "headline": "Trauma-Informed Voice Readout & Guided Questions",
        "desc": "SafeMate speaks gentle questions aloud via speech synthesis and listens to spoken replies in English or Hindi. Survivors never have to repeat their story multiple times."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/07_tell_once_zero_fir_dossier.png",
        "badge": "FEATURE 04: UNIFIED LEGAL DOSSIER (ZERO FIR)",
        "headline": "Automated Multi-Agency 3-in-1 Legal Complaint",
        "desc": "Automatically compiles a formal Police Zero FIR under Sec 173 BNSS, a 1930 Cyber Helpline takedown brief, and an attorney memorandum ready to copy or print."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/10_leak_tracer_watermark_generation.png",
        "badge": "FEATURE 05: FORENSIC WATERMARKING (LEAK TRACER)",
        "headline": "Dual-Layer Per-Recipient Signature Embedding",
        "desc": "Embeds visible forensic badges alongside invisible HMAC-SHA256 bitstreams scattered into blue-channel pixels and signed PNG metadata before sharing private media."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/11_leak_tracer_forensic_attribution.png",
        "badge": "FEATURE 06: LEAKER ATTRIBUTION AFFIDAVIT",
        "headline": "Cryptographic Proof & Source Identification",
        "desc": "If a photo leaks online, SafeMate inspects the steganographic payload and extracts verifiable attribution affidavits compliant with Section 65B Indian Evidence Act."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/09_deepfake_scan_result.png",
        "badge": "FEATURE 07: NEURAL DEEPFAKE & VIDEO SCANNER",
        "headline": "Multi-Frame Boundary & Frequency Domain Classification",
        "desc": "Detects synthetic face-swapping and morphed extortion media across temporal frames, outputting percentage confidence scores and immediate statutory legal guidance."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/04_emergency_sos_dispatch.png",
        "badge": "FEATURE 08: EMERGENCY SOS & 112 DISPATCH",
        "headline": "1-Tap Real Calling & Live GPS Coordinate Broadcasting",
        "desc": "Instant connection to national emergency services (112) or personal safety circle contacts with high-precision GPS geolocation broadcast."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/05_safewalk_active_escort.png",
        "badge": "FEATURE 09: SAFEWALK ESCORT & ROUTE TRACKING",
        "headline": "Automated Arrival Countdown & Overdue Alerts",
        "desc": "Provides virtual late-night escorting with shareable trip tokens and automated alerts if the user does not check in safely before the timer expires."
    },
    {
        "type": "feature",
        "image": "docs/screenshots/12_evidence_vault_chain_of_custody.png",
        "badge": "FEATURE 10: DISGUISED EVIDENCE VAULT",
        "headline": "Cryptographic SHA-256 Chain of Custody Locker",
        "desc": "Hidden behind a functioning calculator disguise, the vault covertly records microphone audio and seals evidence files with immutable cryptographic hashes."
    },
    {
        "type": "outro",
        "title": "SAFEMATE",
        "subtitle": "Putting Legal Certainty & Dignity Back Into the Survivor's Hands",
        "bullets": [
            "Verified Python FastAPI Backend with 200+ Automated Tests",
            "Privacy-First Client-Side Stego & Speech Engine Resilience",
            "Repository: https://github.com/sam9334545/Safemate.git",
            "Live Local Host: http://localhost:8000/app"
        ]
    }
]

def render_intro_slide(scene, progress):
    canvas = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), color="#090d16")
    draw = ImageDraw.Draw(canvas)

    # Accent top border
    draw.rectangle([0, 0, VIDEO_WIDTH, 8], fill="#D90429")

    # Center card
    card_w, card_h = 1300, 750
    card_x = (VIDEO_WIDTH - card_w) // 2
    card_y = (VIDEO_HEIGHT - card_h) // 2 - 20
    draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], fill="#0f172a", outline="#1e293b", width=2)
    draw.rectangle([card_x, card_y, card_x + card_w, card_y + 6], fill="#D90429")

    # Title & Subtitle
    draw.text((card_x + 60, card_y + 60), scene["title"], fill="#ffffff", font=font_h1)
    draw.text((card_x + 60, card_y + 130), scene["subtitle"], fill="#94a3b8", font=font_h2)
    draw.line([card_x + 60, card_y + 185, card_x + card_w - 60, card_y + 185], fill="#334155", width=2)

    # Bullets
    y_cursor = card_y + 220
    for bullet in scene["bullets"]:
        draw.ellipse([card_x + 60, y_cursor + 8, card_x + 72, y_cursor + 20], fill="#EF233C")
        draw.text((card_x + 90, y_cursor), bullet, fill="#f8fafc", font=font_body)
        y_cursor += 70

    # Tagline
    draw.text((card_x + 60, card_y + card_h - 65), "SafeMate • Digital Safety & Forensic Legal Sanctuary", fill="#64748b", font=font_small)

    return canvas

def render_feature_slide(scene, progress):
    canvas = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), color="#090d16")
    draw = ImageDraw.Draw(canvas)

    # Top accent bar
    draw.rectangle([0, 0, VIDEO_WIDTH, 6], fill="#D90429")

    # Load and scale screenshot
    img_path = scene["image"]
    if os.path.exists(img_path):
        raw_img = Image.open(img_path).convert("RGB")
        # Target viewport area for screenshot
        target_w, target_h = 1600, 720
        raw_img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Center horizontally
        img_x = (VIDEO_WIDTH - raw_img.width) // 2
        img_y = 75
        
        # Border framing
        draw.rectangle([img_x - 3, img_y - 3, img_x + raw_img.width + 3, img_y + raw_img.height + 3], fill="#1e293b")
        canvas.paste(raw_img, (img_x, img_y))

    # Top Header Badge
    draw.rectangle([img_x, 22, img_x + 500, 56], fill="#1e293b", outline="#334155", width=1)
    draw.text((img_x + 14, 28), scene["badge"], fill="#38bdf8", font=font_small)

    # Lower-third explanatory banner
    banner_y = 820
    banner_h = 210
    draw.rectangle([img_x, banner_y, img_x + raw_img.width, banner_y + banner_h], fill="#0f172a", outline="#334155", width=2)
    draw.rectangle([img_x, banner_y, img_x + 6, banner_y + banner_h], fill="#D90429")

    draw.text((img_x + 30, banner_y + 20), scene["headline"], fill="#ffffff", font=font_h2)
    draw.text((img_x + 30, banner_y + 70), scene["desc"], fill="#cbd5e1", font=font_body)

    # Bottom progress bar for current scene
    pb_w = int(raw_img.width * progress)
    draw.rectangle([img_x, banner_y + banner_h - 6, img_x + raw_img.width, banner_y + banner_h], fill="#1e293b")
    draw.rectangle([img_x, banner_y + banner_h - 6, img_x + pb_w, banner_y + banner_h], fill="#EF233C")

    return canvas

def main():
    output_path = "docs/safemate_walkthrough_demo.mp4"
    os.makedirs("docs", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))

    total_scenes = len(SCENES)
    frames_per_scene = FPS * SECONDS_PER_SCENE

    print(f"Generating Walkthrough Video: {total_scenes} scenes @ {FPS} FPS ({frames_per_scene} frames/scene)...")

    for s_idx, scene in enumerate(SCENES):
        print(f"Rendering scene {s_idx + 1}/{total_scenes}: {scene.get('badge') or scene.get('title')}...")
        for f in range(frames_per_scene):
            progress = f / frames_per_scene
            if scene["type"] in ["intro", "outro"]:
                pil_frame = render_intro_slide(scene, progress)
            else:
                pil_frame = render_feature_slide(scene, progress)

            # Convert PIL RGB to OpenCV BGR
            cv_frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
            writer.write(cv_frame)

    writer.release()
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"SUCCESS: Video exported to {output_path} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
