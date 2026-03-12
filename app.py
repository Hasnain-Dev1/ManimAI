# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
import subprocess
import tempfile
import os
import re
import shutil
import unicodedata

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ManimAI - Prompt to Animation",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #0d0d14 !important;
    color: #ffffff !important;
    font-family: 'Syne', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 70% 45% at 15% 0%, #0d1f3c 0%, transparent 55%),
        radial-gradient(ellipse 55% 40% at 85% 5%, #1a0d2e 0%, transparent 50%),
        #0d0d14 !important;
}

/* Hide chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

[data-testid="stMainBlockContainer"] {
    padding: 2rem 3rem !important;
    max-width: 1100px !important;
    margin: 0 auto !important;
}

/* ══════════════════════════════
   SIDEBAR
══════════════════════════════ */
[data-testid="stSidebar"] {
    background: #0a0a12 !important;
    border-right: 1px solid rgba(251,191,36,0.15) !important;
}
/* All text in sidebar white by default */
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] div {
    color: #ffffff !important;
}
/* Sidebar headings gold */
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h1 {
    color: #fbbf24 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
}
/* Muted sidebar text */
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #6b7a99 !important;
}
/* Sidebar code/monospace (model name) */
[data-testid="stSidebar"] code,
[data-testid="stSidebar"] pre {
    background: rgba(251,191,36,0.1) !important;
    border: 1px solid rgba(251,191,36,0.25) !important;
    border-radius: 6px !important;
    color: #fbbf24 !important;
    font-family: 'JetBrains Mono', monospace !important;
    padding: 2px 8px !important;
    font-size: 0.85rem !important;
}
/* Sidebar password input */
[data-testid="stSidebar"] input[type="password"] {
    background: #1c1c2e !important;
    border: 1.5px solid rgba(251,191,36,0.3) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    caret-color: #fbbf24 !important;
}
[data-testid="stSidebar"] input[type="password"]:focus {
    border-color: #fbbf24 !important;
    box-shadow: 0 0 0 3px rgba(251,191,36,0.15) !important;
    outline: none !important;
}
[data-testid="stSidebar"] input::placeholder {
    color: #3a4260 !important;
}
/* Sidebar label */
[data-testid="stSidebar"] label {
    color: #8892aa !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
/* Sidebar alerts */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.82rem !important;
}
/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1rem 0 !important;
}
/* Sidebar bullet list */
[data-testid="stSidebar"] ul {
    padding-left: 1.1rem !important;
}
[data-testid="stSidebar"] ul li {
    color: #9aa3b8 !important;
    font-size: 0.84rem !important;
    margin-bottom: 0.4rem !important;
    font-style: italic;
}

/* ══════════════════════════════
   HERO
══════════════════════════════ */
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(251,191,36,0.12);
    border: 1px solid rgba(251,191,36,0.35);
    border-radius: 999px;
    padding: 5px 16px;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.12em; color: #fbbf24;
    text-transform: uppercase; margin-bottom: 1.2rem;
}
.hero-title {
    font-size: clamp(3rem, 7vw, 5.5rem);
    font-weight: 800; letter-spacing: -0.04em;
    line-height: 0.95; color: #ffffff; margin-bottom: 0.6rem;
}
.hero-title span {
    background: linear-gradient(90deg, #fbbf24 0%, #f97316 50%, #ef4444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 1.05rem; color: #8892aa;
    font-weight: 400; line-height: 1.6; margin-bottom: 2rem;
}

/* ══════════════════════════════
   MAIN INPUTS  (bright white text)
══════════════════════════════ */
.stTextArea > div > div > textarea,
.stTextInput > div > div > input {
    background: #1c1c2e !important;
    border: 1.5px solid rgba(255,255,255,0.18) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    caret-color: #fbbf24 !important;
    line-height: 1.6 !important;
}
.stTextArea > div > div > textarea:focus,
.stTextInput > div > div > input:focus {
    border-color: #fbbf24 !important;
    box-shadow: 0 0 0 3px rgba(251,191,36,0.15) !important;
    outline: none !important;
}
.stTextArea > div > div > textarea::placeholder,
.stTextInput > div > div > input::placeholder {
    color: #4a5270 !important;
}
.stTextArea label, .stTextInput label {
    color: #8892aa !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* ── Example tags ── */
.tag {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 0.25rem 0.9rem;
    font-size: 0.78rem; color: #9aa3b8;
    margin: 0.2rem 0.25rem 0.2rem 0;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Generate button ── */
.stButton > button {
    background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%) !important;
    border: none !important; border-radius: 12px !important;
    color: #0a0a0a !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.05rem !important; font-weight: 800 !important;
    padding: 0.75rem 2rem !important; width: 100% !important;
    box-shadow: 0 4px 24px rgba(251,191,36,0.3) !important;
    transition: transform 0.15s, box-shadow 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(251,191,36,0.45) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    font-size: 0.9rem !important; font-weight: 600 !important;
    box-shadow: none !important; border-radius: 10px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255,255,255,0.1) !important;
}

/* ── Code blocks ── */
.stCode, [data-testid="stCode"] {
    background: #10101c !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
}
pre, pre code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important; line-height: 1.65 !important;
}

/* ── Video ── */
video {
    border-radius: 16px !important;
    box-shadow: 0 0 0 1px rgba(251,191,36,0.2),
                0 16px 60px rgba(0,0,0,0.8) !important;
    width: 100% !important;
}

hr { border-color: rgba(255,255,255,0.07) !important; margin: 2rem 0 !important; }
.stSpinner > div { border-top-color: #fbbf24 !important; }
.stAlert { border-radius: 12px !important; }
.sec-title {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #4a5568; margin-bottom: 0.6rem;
}

/* ── Mobile API key card ── */
.mobile-api-card {
    background: rgba(251,191,36,0.06);
    border: 1.5px solid rgba(251,191,36,0.3);
    border-radius: 16px;
    padding: 1.2rem 1.3rem;
    margin-bottom: 1.5rem;
}
.mobile-api-title {
    font-size: 0.75rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #fbbf24; margin-bottom: 0.4rem;
}
.mobile-api-sub {
    font-size: 0.83rem; color: #8892aa; margin-bottom: 0.75rem;
    line-height: 1.5;
}
.mobile-api-sub a { color: #fbbf24; text-decoration: underline; }
.key-saved {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 8px; padding: 5px 12px;
    font-size: 0.8rem; color: #22c55e;
    font-family: 'JetBrains Mono', monospace;
}
.dot-g { width:7px;height:7px;border-radius:50%;background:#22c55e;
         box-shadow:0 0 6px #22c55e;display:inline-block; }

/* ── Hide mobile card on desktop, show on mobile ── */
.mobile-only { display: none !important; }
.desktop-only { display: block !important; }

@media (max-width: 768px) {
    .mobile-only  { display: block !important; }
    .desktop-only { display: none  !important; }
    [data-testid="stMainBlockContainer"] {
        padding: 1rem 1rem !important;
    }
    .hero-title { font-size: 3rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are ManimAI - a world-class expert in Manim Community Edition v0.19 animations.

Given a natural-language description, output ONLY valid Python code using Manim CE.

STRICT RULES:
1. Start with: from manim import *
2. Define exactly ONE class named GeneratedScene(Scene)
3. All animation logic goes inside def construct(self)
4. Use self.play(...) and self.wait(...) - never bare function calls
5. Keep total runtime between 6-12 seconds - enough to show the full animation
6. Use vivid colors, smooth transitions, visually rich designs
7. Output RAW Python only - no markdown, no backticks, no explanation
8. Code must be 100% runnable with: manim render -ql scene.py GeneratedScene

ANIMATION QUALITY RULES:
- For math/wave animations: use ValueTracker + always_redraw for smooth continuous motion
- For Fourier/wave: use ParametricFunction or FunctionGraph, update with ValueTracker
- For sorting algorithms: use simple Rectangle bars with fixed positions, animate one swap at a time
- For complex scenes: build objects first, then animate - never animate while building
- Keep loops short: max 4-5 iterations to avoid timeout
- Each self.play() should have run_time between 0.5 and 2.0 seconds
- Total self.play() run_times should add up to 6-10 seconds

SMOOTH ANIMATION PATTERNS (use these for glitch-free results):

For continuous motion (waves, drawing):
  tracker = ValueTracker(0)
  wave = always_redraw(lambda: FunctionGraph(
      lambda x: np.sin(x), x_range=[-5, max(-4.99, tracker.get_value())],
      color=BLUE))
  self.add(wave)
  self.play(tracker.animate.set_value(5), run_time=4, rate_func=linear)

For Fourier series (add harmonics one by one):
  axes = Axes(x_range=[-PI, PI], y_range=[-2, 2])
  self.add(axes)
  # Draw each harmonic as a separate FunctionGraph, use Create() to draw them
  for n in [1, 3, 5]:
      graph = axes.plot(lambda x, n=n: sum(
          4/(k*PI)*np.sin(k*x) for k in range(1, n+1, 2)), color=BLUE)
      self.play(Create(graph), run_time=1.5, rate_func=smooth)
      self.wait(0.5)

ALWAYS USE always_redraw() for anything that moves continuously.
NEVER use loops with many iterations - max 4 iterations.

VALID rate_func VALUES - ONLY these, never invent:
  linear, smooth, rush_into, rush_from, slow_into, double_smooth,
  there_and_back, there_and_back_with_pause, running_start, wiggle,
  ease_in_quad, ease_out_quad, ease_in_out_quad,
  ease_in_cubic, ease_out_cubic, ease_in_out_cubic,
  ease_in_sine, ease_out_sine, ease_in_out_sine
Default: rate_func=smooth

VALID COLORS:
  RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, WHITE, BLACK,
  GRAY, GREY, PINK, TEAL, GOLD, MAROON, DARK_BLUE, LIGHT_GRAY
  or hex like "#ff6600"

AVOID:
- NEVER invent rate_func names
- NEVER use np.sin inside always_redraw without importing numpy (use import numpy as np at top)
- NEVER create more than 50 objects in a loop
- NEVER use Tex or MathTex (requires LaTeX - use Text() instead)
- NEVER use 3D scenes (ThreeDScene) - stick to regular Scene
- NEVER skip self.wait() between major animation steps"""

RETRY_PROMPT = """The following Manim code produced this error:

CODE:
{code}

ERROR:
{error}

Fix the code. Replace any invalid rate_func names with: smooth
Keep the class name as GeneratedScene.
Output ONLY the fixed raw Python code, no explanation, no backticks."""

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "generated_code": "",
    "video_path": "",
    "render_error": "",
    "history": [],
    "groq_api_key": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def sanitize(text: str) -> str:
    """Strip non-ASCII so Windows httpx header encoding never crashes."""
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", errors="ignore").decode("ascii").strip()

GROQ_CLIENT = None

def get_groq_client():
    global GROQ_CLIENT
    key = st.session_state.get("groq_api_key", "").strip()
    if not key:
        return None
    if GROQ_CLIENT is None:
        GROQ_CLIENT = Groq(api_key=key)
    return GROQ_CLIENT

def clean_code(raw: str) -> str:
    raw = re.sub(r"^```python\s*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^```\s*\n?",       "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```\s*$",       "", raw, flags=re.MULTILINE)
    return raw.strip()

def fix_manim_code(bad_code: str, error: str) -> str:
    """Ask Groq to auto-fix broken Manim code given the error message."""
    client = get_groq_client()
    if client is None:
        return ""
    fix_prompt = RETRY_PROMPT.format(code=bad_code, error=sanitize(error[:1500]))
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": fix_prompt}],
        temperature=0.2,
        max_tokens=2048,
    )
    return clean_code(resp.choices[0].message.content.strip())

def generate_manim_code(prompt: str) -> str:
    client = get_groq_client()
    if client is None:
        st.error("Please enter your Groq API key in the sidebar first.")
        return ""
    safe = sanitize(prompt)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Create a Manim animation for: {safe}"},
        ],
        temperature=0.4,
        max_tokens=2048,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```python\s*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^```\s*\n?",       "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```\s*$",       "", raw, flags=re.MULTILINE)
    return raw.strip()

def render_manim(code: str) -> tuple[bool, str, str]:
    """
    Cross-platform Manim renderer (Windows + Linux/Streamlit Cloud).
    Renders PNG frames then encodes with ffmpeg for glitch-free output.
    """
    import threading, time, platform

    IS_WINDOWS = platform.system() == "Windows"

    if IS_WINDOWS:
        work_dir = "C:\\manim_tmp"
    else:
        work_dir = os.path.join(os.path.expanduser("~"), "manim_tmp")

    out_dir    = os.path.join(work_dir, "output")
    stable     = os.path.join(work_dir, "latest.mp4")
    scene_file = os.path.join(work_dir, "scene.py")

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(out_dir,  exist_ok=True)

    with open(scene_file, "w", encoding="utf-8") as f:
        f.write(code)

    # Clean old output
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)

    # ── Attempt 1: Normal -qm render (medium quality = 30fps, smoother) ──────
    partial_root = os.path.join(out_dir, "videos", "scene", "854p30",
                                "partial_movie_files", "GeneratedScene")
    concat_path  = os.path.join(partial_root, "partial_movie_file_list.txt")

    stop_evt = threading.Event()
    def patcher():
        while not stop_evt.is_set():
            if os.path.exists(concat_path):
                try:
                    txt = open(concat_path, encoding="utf-8").read()
                    if "\\" in txt:
                        open(concat_path, "w", encoding="utf-8").write(
                            txt.replace("\\", "/"))
                except: pass
            time.sleep(0.01)
    threading.Thread(target=patcher, daemon=True).start()

    r1 = subprocess.run(
        ["manim", "render", "-qm", "--disable_caching",
         "--media_dir", out_dir, scene_file, "GeneratedScene"],
        capture_output=True, text=True, cwd=work_dir,
        timeout=240, encoding="utf-8", errors="replace",
    )
    stop_evt.set()
    log1 = (r1.stderr + "\n" + r1.stdout).strip()

    # Check for final MP4 in any quality subfolder
    final_mp4 = None
    for root, dirs, files in os.walk(out_dir):
        # Skip partial_movie_files folders
        if "partial_movie_files" in root:
            continue
        for f in files:
            if f.endswith(".mp4"):
                final_mp4 = os.path.join(root, f)
                break
        if final_mp4:
            break

    if final_mp4 and os.path.exists(final_mp4):
        shutil.copy2(final_mp4, stable)
        return True, stable, ""

    # ── Attempt 2: PNG frame export → ffmpeg encode ───────────────────────────
    # Clean output and re-render as PNG frames (avoids PyAV entirely)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)

    r2 = subprocess.run(
        ["manim", "render", "-ql", "--disable_caching",
         "--media_dir", out_dir,
         "--format", "png",
         scene_file, "GeneratedScene"],
        capture_output=True, text=True, cwd=work_dir,
        timeout=240, encoding="utf-8", errors="replace",
    )
    log2 = (r2.stderr + "\n" + r2.stdout).strip()

    # Find folder with most PNG frames
    frames_src = None
    best_count = 0
    for root, dirs, files in os.walk(out_dir):
        pngs = [f for f in files if f.endswith(".png")]
        if len(pngs) > best_count:
            best_count = len(pngs)
            frames_src = root

    if frames_src and best_count > 0:
        fps = 15  # -ql = 15fps

        # Sort frames numerically
        pngs_sorted = sorted(
            [os.path.join(frames_src, f)
             for f in os.listdir(frames_src) if f.endswith(".png")],
            key=lambda x: int(''.join(filter(str.isdigit,
                              os.path.splitext(os.path.basename(x))[0])) or '0')
        )

        # Write concat with duration per frame
        concat_txt = os.path.join(work_dir, "frames.txt")
        frame_dur  = round(1.0 / fps, 6)
        with open(concat_txt, "w", encoding="utf-8") as cf:
            for i, p in enumerate(pngs_sorted):
                safe = p.replace("\\", "/")
                cf.write(f"file '{safe}'\n")
                cf.write(f"duration {frame_dur}\n")
            # ffmpeg needs last frame repeated to flush
            if pngs_sorted:
                cf.write(f"file '{pngs_sorted[-1].replace(chr(92), '/')}'\n")

        concat_fwd = concat_txt.replace("\\", "/")
        ff = subprocess.run(
            ["ffmpeg", "-y",
             "-f", "concat", "-safe", "0",
             "-i", concat_fwd,
             "-vf", "fps=30",           # smooth up to 30fps output
             "-c:v", "libx264",
             "-preset", "fast",
             "-crf", "18",              # high quality
             "-pix_fmt", "yuv420p",
             "-movflags", "+faststart",
             stable],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        if ff.returncode == 0 and os.path.exists(stable):
            return True, stable, ""

        return False, "", (
            f"PNG encode failed:\n{ff.stderr[:500]}\n\n"
            f"Attempt 1:\n{log1[:400]}\n\n"
            f"Attempt 2:\n{log2[:400]}"
        )

    return False, "", f"Render failed.\n\nAttempt 1:\n{log1[:600]}\n\nAttempt 2:\n{log2[:600]}"


# ══════════════════════════════════════════════════════════════
# SIDEBAR (desktop)
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Groq API Key")
    st.markdown(
        "Get your **free** key at "
        "[console.groq.com](https://console.groq.com) "
        "— no credit card needed."
    )
    key_input = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        label_visibility="collapsed",
        key="key_field",
    )
    if key_input:
        st.session_state["groq_api_key"] = key_input.strip()
        GROQ_CLIENT = None

    if st.session_state["groq_api_key"]:
        st.success("Key saved!")
    else:
        st.warning("No key yet")

    st.markdown("---")
    st.markdown("### Model")
    st.code(GROQ_MODEL)
    st.caption("Llama 3.3 70B — fast, free, great at code")

    st.markdown("---")
    st.markdown("### Prompt Tips")
    st.markdown("""
- *"bouncing ball with shadow trail"*
- *"Pythagorean theorem step by step"*
- *"letter A morphing to B"*
- *"spiral galaxy forming from dots"*
- *"sine and cosine waves together"*
    """)
    st.markdown("---")
    st.caption("ManimAI — Groq + Manim CE")

# ══════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="hero-badge">Powered by Groq - 100% Free</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Manim<span>AI</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Describe any animation in plain English — get a rendered video in seconds.</div>',
    unsafe_allow_html=True,
)

# ── Mobile API key card (visible only on small screens) ──────────────────────
st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
st.markdown("""
<div class="mobile-api-card">
  <div class="mobile-api-title">Groq API Key (Free)</div>
  <div class="mobile-api-sub">
    Get your free key at <a href="https://console.groq.com" target="_blank">console.groq.com</a>
    — no credit card needed.
  </div>
</div>
""", unsafe_allow_html=True)

mob_key = st.text_input(
    "Mobile API Key",
    type="password",
    placeholder="gsk_...",
    label_visibility="collapsed",
    key="mob_key_field",
)
if mob_key:
    st.session_state["groq_api_key"] = mob_key.strip()
    GROQ_CLIENT = None

if st.session_state["groq_api_key"]:
    st.markdown(
        '<div class="key-saved"><span class="dot-g"></span> Key saved</div>',
        unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

EXAMPLES = [
    "Bouncing neon ball", "Pythagorean theorem", "Fourier wave series",
    "Solar system orbits", "Fibonacci spiral", "Atom with electrons",
    "Sine wave drawing",  "Text morphing A to Z",
]
st.markdown(
    "".join(f'<span class="tag">{e}</span>' for e in EXAMPLES),
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

prompt = st.text_area(
    "Your animation prompt",
    placeholder="e.g. A glowing blue sine wave draws itself left to right, then a red cosine wave appears below it",
    height=130,
    key="prompt_box",
)

st.markdown("<br>", unsafe_allow_html=True)
btn_col, _ = st.columns([2, 3])
with btn_col:
    go = st.button("Generate Animation", use_container_width=True)

st.markdown("---")

# ── Generation pipeline ───────────────────────────────────────────────────────
if go:
    if not st.session_state["groq_api_key"]:
        st.error("Please paste your free Groq API key — on desktop use the sidebar, on mobile enter it above.")
    elif not prompt.strip():
        st.warning("Please type an animation description above.")
    else:
        st.session_state.update({"video_path": "", "render_error": "", "generated_code": ""})

        # Step 1 — generate code
        with st.spinner("Groq is writing Manim code..."):
            code = generate_manim_code(prompt.strip())

        if code:
            st.session_state["generated_code"] = code

            # Step 2 — first render attempt
            with st.spinner("Manim is rendering your animation... (~15-40s on first run)"):
                try:
                    success, video_path, err = render_manim(code)
                except subprocess.TimeoutExpired:
                    success, video_path, err = False, "", "Render timed out after 120s."

            # Step 3 — auto-retry: ask Groq to fix the error and try once more
            if not success and err:
                st.info("First attempt failed — asking Groq to auto-fix the code...")
                with st.spinner("Groq is fixing the error..."):
                    fixed_code = fix_manim_code(code, err)
                if fixed_code:
                    st.session_state["generated_code"] = fixed_code
                    with st.spinner("Re-rendering with fixed code..."):
                        try:
                            success, video_path, err = render_manim(fixed_code)
                        except subprocess.TimeoutExpired:
                            success, video_path, err = False, "", "Render timed out after 120s."

            if success:
                st.session_state["video_path"] = video_path
                st.session_state["history"].append({
                    "prompt": prompt.strip(),
                    "code": st.session_state["generated_code"],
                    "video": video_path,
                })
                st.success("Animation ready!")
            else:
                st.session_state["render_error"] = err
                st.error("Manim render failed — see error details below.")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state["video_path"]:
    col_v, col_c = st.columns([3, 2])
    with col_v:
        st.markdown('<div class="sec-title">Your Animation</div>', unsafe_allow_html=True)
        st.video(st.session_state["video_path"])
        with open(st.session_state["video_path"], "rb") as f:
            st.download_button(
                "Download MP4", f,
                file_name="manim_animation.mp4",
                mime="video/mp4",
            )
    with col_c:
        st.markdown('<div class="sec-title">Generated Code</div>', unsafe_allow_html=True)
        st.code(st.session_state["generated_code"], language="python")

elif st.session_state["generated_code"]:
    st.markdown('<div class="sec-title">Generated Code</div>', unsafe_allow_html=True)
    st.code(st.session_state["generated_code"], language="python")

if st.session_state["render_error"]:
    with st.expander("Render Error Details"):
        st.code(st.session_state["render_error"], language="bash")

# ── History ───────────────────────────────────────────────────────────────────
if st.session_state["history"]:
    st.markdown("---")
    st.markdown('<div class="sec-title">Session History</div>', unsafe_allow_html=True)
    for i, item in enumerate(reversed(st.session_state["history"])):
        label = f"#{len(st.session_state['history'])-i}  -  {item['prompt'][:60]}{'...' if len(item['prompt'])>60 else ''}"
        with st.expander(label):
            hc1, hc2 = st.columns([3, 2])
            with hc1:
                if os.path.exists(item["video"]):
                    st.video(item["video"])
            with hc2:
                st.code(item["code"], language="python")