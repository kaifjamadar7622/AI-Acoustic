import os

import gradio as gr
from app import STYLE_PRESETS, create_genai_result
from storage import authenticate_user, history_gallery_items, history_table_rows, register_user

# ── Cinematic dark glassmorphism theme ────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Outfit:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
    --bg-deep:        #04050d;
    --bg-mid:         #080c1a;
    --accent-gold:    #c9a84c;
    --accent-amber:   #e8b65a;
    --accent-teal:    #3ecfcf;
    --accent-violet:  #8b5cf6;
    --glass-bg:       rgba(255,255,255,0.04);
    --glass-border:   rgba(255,255,255,0.10);
    --glass-hover:    rgba(255,255,255,0.07);
    --text-primary:   #f0ead8;
    --text-muted:     #8a8078;
    --text-dim:       #504848;
    --glow-gold:      0 0 24px rgba(201,168,76,0.35);
    --glow-teal:      0 0 24px rgba(62,207,207,0.35);
    --radius-lg:      16px;
    --radius-md:      10px;
    --radius-sm:      6px;
}

/* ── Full-page background ── */
body, .gradio-container {
    background: radial-gradient(ellipse at 20% 10%,  #0e1628 0%, transparent 55%),
                radial-gradient(ellipse at 80% 85%,  #130d22 0%, transparent 55%),
                radial-gradient(ellipse at 50% 50%,  #060a14 0%, transparent 80%),
                linear-gradient(160deg, #04050d 0%, #07091a 50%, #05060e 100%) !important;
    min-height: 100vh;
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Animated noise grain overlay */
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.6;
}

/* ── App title banner ── */
#app-header {
    text-align: center;
    padding: 40px 20px 24px;
    position: relative;
}
#app-header h1 {
    font-family: 'Cinzel', serif !important;
    font-size: clamp(1.8rem, 4vw, 3rem) !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-amber) 40%, var(--accent-teal) 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: 0.08em;
    text-shadow: none;
    margin: 0 0 8px;
}
#app-header p {
    color: var(--text-muted) !important;
    font-size: 0.95rem;
    font-weight: 300;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0;
}
/* Decorative rule */
#app-header::after {
    content: '';
    display: block;
    width: 220px;
    height: 1px;
    margin: 20px auto 0;
    background: linear-gradient(90deg, transparent, var(--accent-gold), var(--accent-teal), transparent);
}

/* ── Glass panel (columns) ── */
.glass-panel {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    backdrop-filter: blur(18px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(140%) !important;
    padding: 28px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.glass-panel::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
    pointer-events: none;
    border-radius: inherit;
}
.glass-panel:hover {
    transform: translateY(-2px);
    border-color: rgba(201,168,76,0.35) !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.35);
}

/* ── Section headings inside panels ── */
.section-label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: var(--accent-gold) !important;
    margin-bottom: 14px !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid rgba(201,168,76,0.2) !important;
}

/* ── Inputs, textareas, dropdowns ── */
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container .gr-box,
input[type="text"], input[type="number"], textarea {
    background: rgba(10,12,25,0.7) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
.gradio-container input:focus,
.gradio-container textarea:focus {
    border-color: var(--accent-gold) !important;
    box-shadow: var(--glow-gold) !important;
    outline: none !important;
}

/* ── Labels ── */
.gradio-container label span,
.gradio-container .gr-form label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    font-family: 'Outfit', sans-serif !important;
}

/* ── Sliders ── */
.gradio-container input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    height: 3px !important;
    background: linear-gradient(90deg, var(--accent-gold), var(--accent-teal)) !important;
    border-radius: 99px !important;
    border: none !important;
    cursor: pointer;
}
.gradio-container input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--accent-gold);
    box-shadow: 0 0 8px rgba(201,168,76,0.6);
    cursor: pointer;
}

/* ── Dropdown ── */
.gradio-container .gr-dropdown,
.gradio-container select {
    background: rgba(10,12,25,0.8) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    padding: 8px 12px !important;
}

/* ── Generate button ── */
#generate-btn {
    background: linear-gradient(135deg, #b8882a 0%, #c9a84c 40%, #3ecfcf 100%) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    color: #04050d !important;
    font-family: 'Cinzel', serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 14px 28px !important;
    cursor: pointer !important;
    transition: transform 0.2s, box-shadow 0.2s, filter 0.2s !important;
    width: 100% !important;
    margin-top: 8px !important;
    position: relative;
    overflow: hidden;
}
#generate-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 60%);
}
#generate-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(201,168,76,0.5), 0 2px 8px rgba(62,207,207,0.3) !important;
    filter: brightness(1.08) !important;
}
#generate-btn:active {
    transform: translateY(0) !important;
}

/* ── Status box ── */
#status-box textarea {
    font-size: 0.82rem !important;
    color: var(--accent-teal) !important;
    font-family: 'Outfit', monospace !important;
    background: rgba(5,8,18,0.9) !important;
    border-color: rgba(62,207,207,0.2) !important;
}

/* ── Gallery ── */
.gradio-container .gr-gallery {
    background: rgba(5,8,18,0.6) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 12px !important;
}
.gradio-container .gr-gallery img {
    border-radius: var(--radius-sm) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
.gradio-container .gr-gallery img:hover {
    transform: scale(1.03) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.6) !important;
}

/* ── Audio component ── */
.gradio-container .gr-audio {
    background: rgba(8,12,26,0.7) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-md) !important;
}

/* ── Accordion (Advanced Controls) ── */
.gradio-container .gr-accordion {
    background: rgba(8,12,26,0.5) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: var(--radius-md) !important;
}
.gradio-container .gr-accordion .label-wrap {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.06em !important;
}

/* ── Divider ── */
.divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
    margin: 18px 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--accent-gold); border-radius: 99px; }

/* ── Responsive glow orbs (decorative) ── */
.gradio-container::before {
    content: '';
    position: fixed;
    top: -200px; left: -200px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(201,168,76,0.07) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: orb1 18s ease-in-out infinite alternate;
}
.gradio-container::after {
    content: '';
    position: fixed;
    bottom: -200px; right: -150px;
    width: 450px; height: 450px;
    background: radial-gradient(circle, rgba(62,207,207,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: orb2 22s ease-in-out infinite alternate;
}
@keyframes orb1 { from { transform: translate(0,0) scale(1); } to { transform: translate(80px,60px) scale(1.15); } }
@keyframes orb2 { from { transform: translate(0,0) scale(1); } to { transform: translate(-60px,-80px) scale(1.12); } }

.credit-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    padding: 6px 12px;
    border-radius: 999px;
    border: 1px solid rgba(201,168,76,0.35);
    background: rgba(201,168,76,0.10);
    color: #d7be76;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    text-transform: uppercase;
}

.creator-banner {
    display: block;
    width: fit-content;
    margin: 0 auto 16px;
    padding: 8px 16px;
    border-radius: 999px;
    border: 1px solid rgba(62,207,207,0.35);
    background: rgba(62,207,207,0.10);
    color: #b7f4f4;
    font-size: 0.78rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    box-shadow: 0 0 24px rgba(62,207,207,0.12);
}

.footer-credit {
    color: #72665a;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    margin-top: 6px;
}

.session-banner {
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid rgba(62,207,207,0.18);
    background: rgba(62,207,207,0.08);
    color: #d8ffff;
    letter-spacing: 0.06em;
    font-size: 0.82rem;
    margin-bottom: 12px;
}

.app-shell {
    max-width: 1260px;
    margin: 0 auto;
}

.hero-grid {
    margin-bottom: 18px;
}

.hero-panel {
    padding: 22px 24px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(135deg, rgba(12,16,30,0.95), rgba(18,24,42,0.82));
    box-shadow: 0 18px 50px rgba(0,0,0,0.28);
}

.hero-kicker {
    color: var(--accent-teal);
    text-transform: uppercase;
    letter-spacing: 0.22em;
    font-size: 0.72rem;
    margin-bottom: 10px;
}

.hero-title {
    font-family: 'Cinzel', serif !important;
    font-size: clamp(2rem, 4vw, 3.35rem) !important;
    margin: 0 0 10px;
    line-height: 1.05;
}

.hero-copy {
    color: var(--text-muted);
    max-width: 760px;
    line-height: 1.6;
    margin-bottom: 14px;
}

.stat-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.stat-pill {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid rgba(201,168,76,0.25);
    background: rgba(201,168,76,0.08);
    color: #ead9a2;
    font-size: 0.76rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
}

.panel-note {
    color: var(--text-muted);
    font-size: 0.82rem;
    margin-top: 10px;
}

.tab-note {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin: 6px 0 14px;
}

.app-tabs > div > button {
    border-radius: 999px !important;
}
"""

# ─────────────────────────────────────────────────────────────────────────────

def _normalize_username(username):
    return (username or "").strip().lower()


def _history_views(username):
    if not username:
        return "", []
    rows = history_table_rows(username, limit=10)
    if not rows:
        return "No saved generations yet.", []
    lines = ["Created | Style | Transcript | Status"]
    lines.extend(" | ".join(row) for row in rows)
    return "\n".join(lines), history_gallery_items(username, limit=6)


def _signed_in_label(username, display_name=None):
    if not username:
        return "**Not signed in**"
    name = display_name or username
    return f"**Signed in as:** {name}"


def create_account(username, display_name, password, confirm_password):
    username = _normalize_username(username)
    display_name = (display_name or username).strip() or username

    if password != confirm_password:
        return "Passwords do not match.", "", _signed_in_label("") , "", []

    ok, message = register_user(username, password, display_name)
    if not ok:
        return message, "", _signed_in_label(""), "", []

    history_rows, history_gallery = _history_views(username)
    return message, username, _signed_in_label(username, display_name), history_rows, history_gallery


def sign_in(username, password):
    username = _normalize_username(username)
    ok, message, account = authenticate_user(username, password)
    if not ok or not account:
        return message, "", _signed_in_label(""), "", []

    history_rows, history_gallery = _history_views(account["username"])
    return message, account["username"], _signed_in_label(account["username"], account["display_name"]), history_rows, history_gallery


def sign_out():
    return "Signed out.", "", _signed_in_label(""), "", []


def _resolve_audio_path(audio):
    """Normalize Gradio audio payloads to an existing local file path."""
    if audio is None:
        return None

    if isinstance(audio, str):
        path = audio.strip()
        return path if path and os.path.exists(path) else None

    if isinstance(audio, dict):
        candidate = (audio.get("path") or audio.get("name") or "").strip()
        return candidate if candidate and os.path.exists(candidate) else None

    if isinstance(audio, (list, tuple)) and audio:
        first = audio[0]
        if isinstance(first, str):
            path = first.strip()
            return path if path and os.path.exists(path) else None

    return None

def run_generation(audio, style, extra, variations, steps, guidance, width, height, seed, fast_mode, username):
    """Wrapper that maps UI inputs to backend function signature."""
    audio_path = _resolve_audio_path(audio)
    if not audio_path:
        yield (
            "",
            "",
            "",
            None,
            None,
            "⚠  No audio detected. Please record or upload a voice clip first.",
            "",
            [],
        )
        return
    status = "🎬  Initialising generation pipeline…"
    yield "", "", "", None, None, status, "", []

    try:
        username = _normalize_username(username) or "anonymous"

        if fast_mode:
            variations = 1
            steps = min(int(steps), 20)
            width = min(int(width), 512)
            height = min(int(height), 512)

        safe_seed = None if seed in (None, "") else int(seed)
        result = create_genai_result(
            audio_file_path=audio_path,
            style_name=style,
            extra_instructions=extra,
            steps=int(steps),
            guidance_scale=float(guidance),
            seed=safe_seed,
            image_count=int(variations),
            width=int(width),
            height=int(height),
            username=username,
        )
        # Unpack backend result and preserve backend status message when available.
        if isinstance(result, (list, tuple)) and len(result) >= 6:
            speech_text, refined_prompt, neg_prompt, images, audio_out, backend_status = result[:6]
        elif isinstance(result, (list, tuple)) and len(result) >= 5:
            speech_text, refined_prompt, neg_prompt, images, audio_out = result[:5]
            backend_status = "✅  Generation complete."
        else:
            speech_text, refined_prompt, neg_prompt, images, audio_out, backend_status = result, "", "", None, None, "✅  Generation complete."

        history_rows, history_gallery = _history_views(username)

        yield (
            speech_text,
            refined_prompt,
            neg_prompt,
            images,
            audio_out,
            backend_status,
            history_rows,
            history_gallery,
        )
    except Exception as e:
        yield "", "", "", None, None, f"❌  Error: {str(e)}", "", []


# ─────────────────────────────────────────────────────────────────────────────

with gr.Blocks(css=CUSTOM_CSS, title="Acoustic Artistry AI Studio | Kaif Jamadar") as demo:

    current_user_state = gr.State("")

    with gr.Column(elem_classes="app-shell"):
        gr.HTML("""
        <div class="creator-banner">Created by Kaif Jamadar</div>
        <div class="hero-panel">
            <div class="hero-kicker">Voice-to-Image Studio</div>
            <h1 class="hero-title">Acoustic Artistry AI Studio</h1>
            <div class="hero-copy">Speak an idea, refine it with GenAI, and generate polished image variations. Guest mode is available for quick use; sign in to save your work and revisit it later.</div>
            <div class="stat-row">
                <span class="stat-pill">Fast mode optimized</span>
                <span class="stat-pill">Guest generation supported</span>
                <span class="stat-pill">Free-tier deployment ready</span>
                <span class="stat-pill">History saved locally</span>
            </div>
        </div>
        """)

        with gr.Tabs(elem_classes="app-tabs"):
            with gr.Tab("Create"):
                gr.HTML('<div class="tab-note">Record audio, choose a style, and generate your image.</div>')
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">🎙 Voice Input</p>')
                        audio_input = gr.Audio(
                            sources=["microphone", "upload"],
                            type="filepath",
                            label="Record or Upload Audio",
                            show_label=False,
                        )

                        gr.HTML('<div class="divider"></div>')
                        gr.HTML('<p class="section-label">🎨 Creative Direction</p>')

                        style_dropdown = gr.Dropdown(
                            choices=list(STYLE_PRESETS.keys()),
                            value=list(STYLE_PRESETS.keys())[0],
                            label="Creative Style",
                            interactive=True,
                        )

                        extra_instructions = gr.Textbox(
                            label="Extra Instructions",
                            placeholder="e.g. dramatic lighting, cinematic fog, golden hour glow",
                            lines=3,
                        )

                        gr.HTML('<div class="divider"></div>')

                        with gr.Accordion("⚙  Advanced Controls", open=False):
                            with gr.Row():
                                variations = gr.Slider(minimum=1, maximum=8, step=1, value=1, label="Image Variations")
                                steps = gr.Slider(minimum=10, maximum=100, step=5, value=20, label="Inference Steps")
                            with gr.Row():
                                guidance = gr.Slider(minimum=1.0, maximum=20.0, step=0.5, value=7.5, label="Guidance Scale")
                                seed = gr.Number(value=42, label="Seed", precision=0)
                            with gr.Row():
                                width = gr.Slider(minimum=256, maximum=1024, step=64, value=512, label="Width (px)")
                                height = gr.Slider(minimum=256, maximum=1024, step=64, value=512, label="Height (px)")
                            fast_mode = gr.Checkbox(value=True, label="Fast Mode (faster generation)")

                        generate_btn = gr.Button("✦  Generate with AI  ✦", elem_id="generate-btn", variant="primary")

                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">📝 Recognised Speech</p>')
                        speech_out = gr.Textbox(label="", placeholder="Your spoken words will appear here…", lines=2, show_label=False, interactive=False)

                        gr.HTML('<div class="divider"></div>')
                        gr.HTML('<p class="section-label">✨ Refined GenAI Prompt</p>')
                        prompt_out = gr.Textbox(label="", placeholder="The AI-refined image prompt will appear here…", lines=3, show_label=False, interactive=False)

                        gr.HTML('<p class="section-label" style="margin-top:14px">🚫 Negative Prompt</p>')
                        neg_prompt_out = gr.Textbox(label="", placeholder="Negative prompt guidance will appear here…", lines=2, show_label=False, interactive=False)

                        gr.HTML('<div class="divider"></div>')
                        gr.HTML('<p class="section-label">🖼 Generated Gallery</p>')
                        gallery_out = gr.Gallery(label="", show_label=False, columns=2, rows=2, object_fit="cover", height=320)

                        gr.HTML('<div class="divider"></div>')
                        gr.HTML('<p class="section-label">🔊 Recorded Audio</p>')
                        audio_out = gr.Audio(label="", show_label=False, interactive=False)

                        gr.HTML('<div class="divider"></div>')
                        gr.HTML('<p class="section-label">📡 Status</p>')
                        status_out = gr.Textbox(label="", value="Ready. Record audio and press Generate.", lines=2, show_label=False, interactive=False, elem_id="status-box")

            with gr.Tab("Account"):
                gr.HTML('<div class="tab-note">Create an account to save generations and keep a private history.</div>')
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">🔐 Account Access</p>')
                        session_banner = gr.Markdown("<div class='session-banner'>Sign in to save history. Guest generation is available without an account.</div>")
                        username_input = gr.Textbox(label="Username", placeholder="kaif.jamadar")
                        display_name_input = gr.Textbox(label="Display name", placeholder="Kaif Jamadar")
                        password_input = gr.Textbox(label="Password", type="password", placeholder="Create a password")
                        confirm_password_input = gr.Textbox(label="Confirm password", type="password", placeholder="Repeat password for new accounts")

                        with gr.Row():
                            register_btn = gr.Button("Create Account", variant="secondary")
                            login_btn = gr.Button("Sign In", variant="primary")
                            logout_btn = gr.Button("Sign Out")

                        auth_status = gr.Textbox(label="", value="", placeholder="Auth status will appear here...", lines=2, show_label=False, interactive=False)
                        signed_in_view = gr.Markdown("**Not signed in**")
                        gr.Markdown("<div class='panel-note'>Account data stays local to the deployment. Use this tab when you want saved history.</div>")

                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">✨ Why sign in?</p>')
                        gr.Markdown(
                            "- Save transcripts, prompts, and images\n"
                            "- Re-open your recent generations\n"
                            "- Keep a workspace history for future iterations"
                        )

            with gr.Tab("History"):
                gr.HTML('<div class="tab-note">Review your previous generations and image outputs.</div>')
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">🕘 Your History</p>')
                        history_table = gr.Textbox(label="", show_label=False, lines=8, interactive=False, value="No saved generations yet.")
                        history_gallery = gr.Gallery(label="", show_label=False, columns=3, rows=2, object_fit="cover", height=260)
                        gr.Markdown("<div class='panel-note'>Tip: sign in before generating to store new results here.</div>")

                    with gr.Column(scale=1, elem_classes="glass-panel"):
                        gr.HTML('<p class="section-label">📂 Current Session</p>')
                        gr.Markdown("""
                        - Guest generations still work
                        - Logged-in generations are saved locally
                        - Use fast mode for free-tier deployments
                        """)

    # ── Footer ────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center; padding:24px 0 12px; color:#3a3530;
                font-size:0.78rem; letter-spacing:0.12em; font-family:'Outfit',sans-serif;">
        ACOUSTIC ARTISTRY AI STUDIO &nbsp;·&nbsp; POWERED BY GENERATIVE INTELLIGENCE
        <div class="footer-credit">Made by Kaif Jamadar</div>
    </div>
    """)

    # ── Event wiring ──────────────────────────────────────────────────────────
    generate_btn.click(
        fn=run_generation,
        inputs=[
            audio_input,
            style_dropdown,
            extra_instructions,
            variations,
            steps,
            guidance,
            width,
            height,
            seed,
            fast_mode,
            current_user_state,
        ],
        outputs=[
            speech_out,
            prompt_out,
            neg_prompt_out,
            gallery_out,
            audio_out,
            status_out,
            history_table,
            history_gallery,
        ],
    )

    register_btn.click(
        fn=create_account,
        inputs=[username_input, display_name_input, password_input, confirm_password_input],
        outputs=[auth_status, current_user_state, signed_in_view, history_table, history_gallery],
    )

    login_btn.click(
        fn=sign_in,
        inputs=[username_input, password_input],
        outputs=[auth_status, current_user_state, signed_in_view, history_table, history_gallery],
    )

    logout_btn.click(
        fn=sign_out,
        inputs=[],
        outputs=[auth_status, current_user_state, signed_in_view, history_table, history_gallery],
    )


def build_ui():
    return demo


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        share=False,
    )