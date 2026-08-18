import os
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = os.path.join("docs", "payer_clinical_intelligence_demo.mp4")
WIDTH, HEIGHT = 1920, 1080
FPS = 30

# Colors (Dark Cyberpunk / Glassmorphism Theme)
BG_DARK = (15, 23, 42)        # Slate 900
CARD_BG = (30, 41, 59)        # Slate 800
CARD_BORDER = (51, 65, 85)    # Slate 700
CYAN_ACCENT = (56, 189, 248)  # Sky 400
PURPLE_ACCENT = (192, 132, 252) # Purple 400
GREEN_SUCCESS = (74, 222, 128) # Green 400
RED_ALERT = (248, 113, 113)   # Red 400
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)


def create_base_canvas():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    # Subtle background gradient glow
    for r in range(500, 0, -10):
        alpha = int((1 - r / 500) * 40)
        draw.ellipse([WIDTH // 2 - r, HEIGHT // 2 - r, WIDTH // 2 + r, HEIGHT // 2 + r],
                     fill=(30, 58, 138, alpha))
    return img, draw


def draw_header(draw, title, subtitle):
    # Top banner card
    draw.rectangle([60, 40, WIDTH - 60, 140], fill=CARD_BG, outline=CARD_BORDER, width=2)
    # Title & Subtitle
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_sub = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((90, 55), title, fill=CYAN_ACCENT, font=font_title)
    draw.text((90, 100), subtitle, fill=TEXT_MUTED, font=font_sub)
    
    # Status badges
    draw.rectangle([WIDTH - 420, 60, WIDTH - 260, 120], fill=(16, 185, 129), outline=(52, 211, 153), width=1)
    draw.text((WIDTH - 400, 80), "LIVE APP: ONLINE", fill=(255, 255, 255), font=font_sub)
    
    draw.rectangle([WIDTH - 240, 60, WIDTH - 90, 120], fill=(99, 102, 241), outline=(129, 140, 248), width=1)
    draw.text((WIDTH - 225, 80), "EVAL: 100%", fill=(255, 255, 255), font=font_sub)


def draw_subtitle_caption(draw, caption_text):
    # Bottom subtitle overlay bar
    draw.rectangle([100, HEIGHT - 120, WIDTH - 100, HEIGHT - 40], fill=(15, 23, 42, 230), outline=CYAN_ACCENT, width=2)
    try:
        font_cap = ImageFont.truetype("arial.ttf", 26)
    except IOError:
        font_cap = ImageFont.load_default()
    draw.text((140, HEIGHT - 95), f"🎙️ {caption_text}", fill=TEXT_WHITE, font=font_cap)


def generate_scene_1(frame_num):
    # Scene 1: Introduction & Inverted Philosophy
    img, draw = create_base_canvas()
    draw_header(draw, "Governed Payer Clinical Intelligence Fleet", "Demo-scale, Production-shaped Multi-Agent System on Gemini 3.5 + ADK")
    
    # Main hero card
    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    try:
        f_hero = ImageFont.truetype("arial.ttf", 44)
        f_sub = ImageFont.truetype("arial.ttf", 28)
        f_code = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        f_hero = f_sub = f_code = ImageFont.load_default()

    draw.text((140, 220), "💡 Inverted AI Governance Philosophy", fill=PURPLE_ACCENT, font=f_hero)
    draw.text((140, 290), "Every AI demo asks: 'How much can the agent do on its own?'", fill=TEXT_MUTED, font=f_sub)
    draw.text((140, 335), "We inverted the question: 'What is the agent structurally unable to do?'", fill=CYAN_ACCENT, font=f_sub)
    
    # Code contract card
    draw.rectangle([140, 400, WIDTH - 140, 680], fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.text((170, 430), "# Structural Security Contract (Enforced in Code, Not Prompt)", fill=GREEN_SUCCESS, font=f_code)
    draw.text((170, 475), "1. Roles are Server-Derived via X-Fleet-Token (0 model identity escalation)", fill=TEXT_WHITE, font=f_code)
    draw.text((170, 520), "2. SQL Predicate Filtering runs FIRST (unauthorized docs never enter memory)", fill=TEXT_WHITE, font=f_code)
    draw.text((170, 565), "3. Autonomy Grade = drafts_only (0 send tools exist in agent catalogs)", fill=TEXT_WHITE, font=f_code)
    draw.text((170, 610), "4. Premature Dispatch Attempt -> Returns HTTP 409 Conflict Refusal", fill=RED_ALERT, font=f_code)

    draw_subtitle_caption(draw, "This project is not interesting because agents are autonomous. It is interesting because of what they are structurally unable to do.")
    return np.array(img)


def generate_scene_2(frame_num):
    # Scene 2: Agent Registry & Autonomy Grades
    img, draw = create_base_canvas()
    draw_header(draw, "Clinical Command Ledger & Agent Registry", "Central Scope, Domain Isolation, and Autonomy Grade Registry")

    # Table Card
    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    try:
        f_head = ImageFont.truetype("arial.ttf", 30)
        f_row = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        f_head = f_row = ImageFont.load_default()

    draw.text((140, 210), "🏷️ Agent Autonomy Grade Catalogue (`app/registry.py`)", fill=CYAN_ACCENT, font=f_head)

    # Table Header
    draw.rectangle([140, 270, WIDTH - 140, 330], fill=(51, 65, 85))
    draw.text((170, 285), "Agent ID", fill=TEXT_WHITE, font=f_row)
    draw.text((450, 285), "Domain", fill=TEXT_WHITE, font=f_row)
    draw.text((700, 285), "Autonomy Grade", fill=TEXT_WHITE, font=f_row)
    draw.text((1050, 285), "Tool Capabilities & Structural Boundary", fill=TEXT_WHITE, font=f_row)

    # Row 1
    draw.rectangle([140, 340, WIDTH - 140, 430], fill=(15, 23, 42))
    draw.text((170, 370), "payer_intelligence", fill=CYAN_ACCENT, font=f_row)
    draw.text((450, 370), "payer", fill=TEXT_WHITE, font=f_row)
    draw.text((700, 370), "drafts_only", fill=RED_ALERT, font=f_row)
    draw.text((1050, 370), "Policy RAG, Denial Analysis, FHIR Drafts (0 Send Tools)", fill=TEXT_MUTED, font=f_row)

    # Row 2
    draw.rectangle([140, 440, WIDTH - 140, 530], fill=(15, 23, 42))
    draw.text((170, 470), "clinical_growth", fill=PURPLE_ACCENT, font=f_row)
    draw.text((450, 470), "clinical", fill=TEXT_WHITE, font=f_row)
    draw.text((700, 470), "drafts_only", fill=RED_ALERT, font=f_row)
    draw.text((1050, 470), "ACC/AHA Guidelines, HEDIS Care Gaps (0 Send Tools)", fill=TEXT_MUTED, font=f_row)

    # Row 3
    draw.rectangle([140, 540, WIDTH - 140, 630], fill=(15, 23, 42))
    draw.text((170, 570), "coordinator", fill=GREEN_SUCCESS, font=f_row)
    draw.text((450, 570), "cross_domain", fill=TEXT_WHITE, font=f_row)
    draw.text((700, 570), "read_only", fill=CYAN_ACCENT, font=f_row)
    draw.text((1050, 570), "Intent Routing & Identity Propagation Only", fill=TEXT_MUTED, font=f_row)

    draw_subtitle_caption(draw, "Every agent advertises its scope and explicit autonomy grade. Zero tools in their catalog contain 'send' or 'dispatch' in their names.")
    return np.array(img)


def generate_scene_3(frame_num):
    # Scene 3: Two-Stage RAG & Gemini 3.5 Grounding
    img, draw = create_base_canvas()
    draw_header(draw, "Two-Stage Retrieval & Gemini 3.5 Flash Grounding", "SQL Security Filter (Stage 1) -> Vector Cosine Similarity Ranking (Stage 2)")

    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CARD_BORDER, width=2)
    try:
        f_head = ImageFont.truetype("arial.ttf", 30)
        f_body = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        f_head = f_body = ImageFont.load_default()

    draw.text((140, 210), "🔍 Two-Stage Security-First RAG Pipeline (`app/retrieval.py`)", fill=CYAN_ACCENT, font=f_head)

    # Stage 1 Card
    draw.rectangle([140, 270, 930, 680], fill=(15, 23, 42), outline=RED_ALERT, width=2)
    draw.text((170, 300), "Stage 1: SQL Security Predicate Filter", fill=RED_ALERT, font=f_head)
    draw.text((170, 355), "• SELECT * FROM docs WHERE allowed_roles LIKE %role%", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 400), "• Security runs FIRST as a SQL database query", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 445), "• Clinicians querying Payer rate sheets get empty set", fill=TEXT_MUTED, font=f_body)
    draw.text((170, 490), "• Model NEVER sees unauthorized document rows", fill=GREEN_SUCCESS, font=f_body)

    # Stage 2 Card
    draw.rectangle([990, 270, 1780, 680], fill=(15, 23, 42), outline=CYAN_ACCENT, width=2)
    draw.text((1020, 300), "Stage 2: Gemini 3.5 Flash Grounding", fill=CYAN_ACCENT, font=f_head)
    draw.text((1020, 355), "• Ranks permitted candidates via cosine similarity", fill=TEXT_WHITE, font=f_body)
    draw.text((1020, 400), "• Vertex AI `google-genai` SDK invocation", fill=TEXT_WHITE, font=f_body)
    draw.text((1020, 445), "• Mandatory Document Citation Tagging: [PAY-POL-101]", fill=PURPLE_ACCENT, font=f_body)
    draw.text((1020, 490), "• Grounded Synthesis Precision: 100.0%", fill=GREEN_SUCCESS, font=f_body)

    draw_subtitle_caption(draw, "Stage 1 SQL filter isolates unauthorized documents before rows enter memory. Stage 2 ranks permitted candidates for Gemini 3.5 synthesis.")
    return np.array(img)


def generate_scene_4(frame_num):
    # Scene 4: Human Approval Gate & HTTP 409 Interception
    img, draw = create_base_canvas()
    draw_header(draw, "Isolated Human Approval Gate & HTTP 409 Interception", "Strict Separation of Draft Queueing from Send/Dispatch Endpoints")

    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CARD_BORDER, width=2)
    try:
        f_head = ImageFont.truetype("arial.ttf", 30)
        f_body = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        f_head = f_body = ImageFont.load_default()

    draw.text((140, 210), "🚦 Human-in-the-Loop Approval Lifecycle (`app/approvals.py`)", fill=CYAN_ACCENT, font=f_head)

    # Step 1: Draft Queue
    draw.rectangle([140, 270, 930, 460], fill=(15, 23, 42), outline=PURPLE_ACCENT, width=2)
    draw.text((170, 295), "1. Agent Queues HL7 FHIR v4 Draft", fill=PURPLE_ACCENT, font=f_head)
    draw.text((170, 345), "• Action: PRIOR_AUTH_SUBMISSION (CPT 75561)", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 385), "• Status: PENDING in isolated database queue", fill=TEXT_MUTED, font=f_body)

    # Step 2: HTTP 409 Refusal Banner
    draw.rectangle([140, 490, WIDTH - 140, 680], fill=(127, 29, 29), outline=RED_ALERT, width=3)
    draw.text((170, 520), "🚫 HTTP 409 CONFLICT: Premature Dispatch Interception", fill=TEXT_WHITE, font=f_head)
    draw.text((170, 570), "Conflict: Approval ID 'appr-8f3a12' is in 'pending' state. Human supervisor sign-off required.", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 615), "Enforced by HTTP endpoint boundary — Zero agent tool access to send endpoint.", fill=CYAN_ACCENT, font=f_body)

    draw_subtitle_caption(draw, "Watch what happens when an unapproved premature dispatch is attempted: The system refuses with an HTTP 409 Conflict error.")
    return np.array(img)


def generate_scene_5(frame_num):
    # Scene 5: Supervisor Approval & Bulk Dry-Run Engine
    img, draw = create_base_canvas()
    draw_header(draw, "Human Supervisor Sign-Off & Bulk Dry-Run Engine", "Medical Director Approval, Audit Logging, and Batch Denial Simulation")

    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CARD_BORDER, width=2)
    try:
        f_head = ImageFont.truetype("arial.ttf", 30)
        f_body = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        f_head = f_body = ImageFont.load_default()

    draw.text((140, 210), "✅ Human Approval & Bulk Dry-Run Simulation (`/fleet/simulation/dry-run`)", fill=GREEN_SUCCESS, font=f_head)

    # Left: Approval Card
    draw.rectangle([140, 270, 930, 680], fill=(15, 23, 42), outline=GREEN_SUCCESS, width=2)
    draw.text((170, 300), "Medical Director Approval", fill=GREEN_SUCCESS, font=f_head)
    draw.text((170, 355), "• Actor: Dr. Arthur Pendelton (tok-medical-director)", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 400), "• HTTP POST /fleet/approvals/{id}/approve -> 200 OK", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 445), "• HTTP POST /fleet/approvals/{id}/send -> 200 OK", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 490), "• HL7 FHIR v4 Bundle Dispatched to Payer Network", fill=CYAN_ACCENT, font=f_body)

    # Right: Bulk Simulation Engine Card
    draw.rectangle([990, 270, 1780, 680], fill=(15, 23, 42), outline=PURPLE_ACCENT, width=2)
    draw.text((1020, 300), "Bulk Dry-Run Simulation Engine", fill=PURPLE_ACCENT, font=f_head)
    draw.text((1020, 355), "• Batch input: 3 Claim Denial Events", fill=TEXT_WHITE, font=f_body)
    draw.text((1020, 400), "• Dry-Run Result: 3/3 PASSED_DRY_RUN", fill=GREEN_SUCCESS, font=f_body)
    draw.text((1020, 445), "• Unapproved Dispatches: 0 (100% Gate Security)", fill=GREEN_SUCCESS, font=f_body)
    draw.text((1020, 490), "• Audit Trail Log: Append-Only Recorded", fill=TEXT_MUTED, font=f_body)

    draw_subtitle_caption(draw, "Chief Medical Officer Dr. Pendelton approves and dispatches via HTTP 200. Bulk dry-run engine verifies batch safety.")
    return np.array(img)


def generate_scene_6(frame_num):
    # Scene 6: Prometheus Metrics & Conclusion
    img, draw = create_base_canvas()
    draw_header(draw, "Prometheus Live Metrics & Operational Summary", "Prometheus Stream Health (/metrics), OpenTelemetry Spans, and Live Dashboard")

    draw.rectangle([100, 180, WIDTH - 100, 720], fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    try:
        f_head = ImageFont.truetype("arial.ttf", 32)
        f_body = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        f_head = f_body = ImageFont.load_default()

    draw.text((140, 220), "📊 Prometheus Live Metrics Exporter (`/metrics`)", fill=CYAN_ACCENT, font=f_head)

    # Code / Metrics Block
    draw.rectangle([140, 280, 1000, 680], fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.text((170, 310), "# Prometheus Stream Health Metrics", fill=GREEN_SUCCESS, font=f_body)
    draw.text((170, 360), "fleet_active_agents 3", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 410), "fleet_total_audit_events 15", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 460), "fleet_security_denials_total 4", fill=RED_ALERT, font=f_body)
    draw.text((170, 510), "fleet_pending_approvals_count 0", fill=TEXT_WHITE, font=f_body)
    draw.text((170, 560), "fleet_stream_health_ratio 1.0000", fill=CYAN_ACCENT, font=f_body)

    # Right Live Links Block
    draw.rectangle([1040, 280, 1780, 680], fill=(15, 23, 42), outline=PURPLE_ACCENT, width=2)
    draw.text((1070, 310), "🌐 Live Application & Repositories", fill=PURPLE_ACCENT, font=f_head)
    draw.text((1070, 380), "Streamlit App:", fill=TEXT_MUTED, font=f_body)
    draw.text((1070, 420), "payer-clinical-intelligence.streamlit.app", fill=CYAN_ACCENT, font=f_body)
    draw.text((1070, 480), "GitHub Repositories:", fill=TEXT_MUTED, font=f_body)
    draw.text((1070, 520), "github.com/sechan9999/payer-clinical-intelligence", fill=TEXT_WHITE, font=f_body)
    draw.text((1070, 560), "github.com/sechan9999/gemini-ops-fleet", fill=TEXT_WHITE, font=f_body)

    draw_subtitle_caption(draw, "Try the live app at payer-clinical-intelligence.streamlit.app. Zero-trust multi-agent security enforced in code. Thank you!")
    return np.array(img)


def render_mp4_video():
    print(f"[VIDEO GENERATOR] Generating 1080p HD MP4 Demo Video: {OUTPUT_PATH}...")
    start_time = time.time()
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, FPS, (WIDTH, HEIGHT))

    scenes = [
        (generate_scene_1, 300),
        (generate_scene_2, 300),
        (generate_scene_3, 300),
        (generate_scene_4, 300),
        (generate_scene_5, 300),
        (generate_scene_6, 300),
    ]

    total_frames = sum(s[1] for s in scenes)
    frame_idx = 0

    for scene_fn, duration_frames in scenes:
        for i in range(duration_frames):
            rgb_frame = scene_fn(i)
            bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            out.write(bgr_frame)
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"  Rendering Progress: {frame_idx}/{total_frames} frames ({frame_idx/total_frames*100:.1f}%)...")

    out.release()
    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"[SUCCESS] MP4 Demo Video generated successfully!")
    print(f"  File Path : {os.path.abspath(OUTPUT_PATH)}")
    print(f"  Duration  : 60 Seconds (1800 Frames @ 30 FPS)")
    print(f"  Resolution: 1920x1080 Full HD")
    print(f"  File Size : {file_size_mb:.2f} MB")
    print(f"  Time Taken: {elapsed:.2f}s")


if __name__ == "__main__":
    render_mp4_video()
