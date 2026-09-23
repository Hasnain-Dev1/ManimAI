# -*- coding: utf-8 -*-
import ast
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import time

import streamlit as st
from groq import BadRequestError, Groq

st.set_page_config(page_title="ManimAI - Prompt to Animation", page_icon="🎬",
                   layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background:#0d0d14 !important; color:#fff !important; font-family:'Syne',sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 70% 45% at 15% 0%, #0d1f3c 0%, transparent 55%),
                radial-gradient(ellipse 55% 40% at 85% 5%, #1a0d2e 0%, transparent 50%), #0d0d14 !important;
}
#MainMenu, footer, [data-testid="stDecoration"] { display:none !important; }
[data-testid="stHeader"] { background:transparent !important; }  /* keep sidebar toggle visible */
[data-testid="stMainBlockContainer"] { padding:2rem 3rem !important; max-width:1100px !important; margin:0 auto !important; }

[data-testid="stSidebar"] { background:#0a0a12 !important; border-right:1px solid rgba(251,191,36,.15) !important; }
[data-testid="stSidebar"] h3 { color:#fbbf24 !important; font-weight:700 !important; }
[data-testid="stSidebar"] li { color:#9aa3b8 !important; font-style:italic; font-size:.84rem !important; }

.hero-badge { display:inline-block; background:rgba(251,191,36,.12); border:1px solid rgba(251,191,36,.35);
    border-radius:999px; padding:5px 16px; font-size:.72rem; font-weight:700; letter-spacing:.12em;
    color:#fbbf24; text-transform:uppercase; margin-bottom:1.2rem; }
.hero-title { font-size:clamp(3rem,7vw,5.5rem); font-weight:800; letter-spacing:-.04em; line-height:.95; margin-bottom:.6rem; }
.hero-title span { background:linear-gradient(90deg,#fbbf24,#f97316 50%,#ef4444);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.hero-sub { font-size:1.05rem; color:#8892aa; line-height:1.6; margin-bottom:1.5rem; }
.sec-title { font-size:.7rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#6b7590; margin-bottom:.6rem; }

.stTextArea textarea, .stTextInput input {
    background:#1c1c2e !important; border:1.5px solid rgba(255,255,255,.18) !important; border-radius:12px !important;
    color:#fff !important; font-family:'JetBrains Mono',monospace !important; caret-color:#fbbf24 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus { border-color:#fbbf24 !important; box-shadow:0 0 0 3px rgba(251,191,36,.15) !important; }
.stTextArea label, .stTextInput label, .stRadio label { color:#8892aa !important; }

/* Secondary buttons (example chips) */
.stButton > button[kind="secondary"] {
    background:rgba(255,255,255,.05) !important; border:1px solid rgba(255,255,255,.12) !important;
    border-radius:999px !important; color:#9aa3b8 !important; font-size:.78rem !important; padding:.2rem .6rem !important;
}
.stButton > button[kind="secondary"]:hover { border-color:#fbbf24 !important; color:#fbbf24 !important; }
/* Primary = Generate */
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#f97316,#fbbf24) !important; border:none !important; border-radius:12px !important;
    color:#0a0a0a !important; font-weight:800 !important; font-size:1.05rem !important; padding:.75rem 2rem !important;
    box-shadow:0 4px 24px rgba(251,191,36,.3) !important; transition:transform .15s !important;
}
.stButton > button[kind="primary"]:hover { transform:translateY(-2px) !important; }

[data-testid="stDownloadButton"] button { background:rgba(255,255,255,.06) !important; border:1px solid rgba(255,255,255,.15) !important; color:#fff !important; border-radius:10px !important; }
[data-testid="stCode"] { background:#10101c !important; border:1px solid rgba(255,255,255,.08) !important; border-radius:14px !important; }
pre, pre code { font-family:'JetBrains Mono',monospace !important; font-size:.8rem !important; }
video { border-radius:16px !important; box-shadow:0 0 0 1px rgba(251,191,36,.2), 0 16px 60px rgba(0,0,0,.8) !important; width:100% !important; }
hr { border-color:rgba(255,255,255,.07) !important; margin:2rem 0 !important; }

@media (max-width:768px) {
    [data-testid="stMainBlockContainer"] { padding:1rem !important; }
    .hero-title { font-size:3rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
# Model IDs from console.groq.com/docs/models
GROQ_MODELS = {
    "openai/gpt-oss-120b": "GPT-OSS 120B — best quality",
    "openai/gpt-oss-20b": "GPT-OSS 20B — fastest",
    "llama-3.3-70b-versatile": "Llama 3.3 70B — reliable",
}

VALID_RATE_FUNCS = {
    "linear", "smooth", "rush_into", "rush_from", "slow_into", "double_smooth",
    "there_and_back", "there_and_back_with_pause", "running_start", "wiggle",
    "ease_in_quad", "ease_out_quad", "ease_in_out_quad",
    "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic",
    "ease_in_sine", "ease_out_sine", "ease_in_out_sine",
}
BANNED_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
                  "pathlib", "ctypes", "multiprocessing", "http", "builtins"}
BANNED_CALLS = {"exec", "eval", "open", "__import__", "compile", "input"}

QUALITY = {  # flag, folder, fps, timeout(s)
    "low":    ("-ql", "480p15", 15, 240),
    "medium": ("-qm", "720p30", 30, 300),
    "high":   ("-qh", "1080p60", 60, 480),
}
QUALITY_LABELS = {"low": "LOW · 480p", "medium": "MEDIUM · 720p", "high": "HIGH · 1080p"}

SYSTEM_PROMPT = """You are ManimAI - an expert in Manim Community Edition v0.19.
Given a description, output ONLY valid Python code.

STRICT RULES:
1. Start with: from manim import *  (and import numpy as np if you use np)
2. Define exactly ONE class named GeneratedScene(Scene); logic inside construct(self)
3. Use self.play(...) and self.wait(...); total runtime 6-12 seconds
4. Vivid colors, smooth transitions. RAW Python only - no markdown, no backticks, no explanation
5. Must run with: manim render -ql scene.py GeneratedScene
6. NEVER use Tex/MathTex/LaTeX - use Text() only. NEVER use ThreeDScene.
7. NEVER import os/sys/subprocess or read/write files.
8. Loops: max 4-5 iterations, max 50 objects. Each self.play run_time 0.5-2.0s.
9. Use ValueTracker + always_redraw for continuous motion (waves, drawing).
10. Put self.wait() between major steps.

VALID rate_func ONLY: linear, smooth, rush_into, rush_from, slow_into, double_smooth,
there_and_back, there_and_back_with_pause, running_start, wiggle, ease_in/out/in_out_(quad|cubic|sine).
VALID colors: RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, WHITE, BLACK, GRAY, PINK, TEAL, GOLD, MAROON,
DARK_BLUE, LIGHT_GRAY or hex like "#ff6600"."""

RETRY_PROMPT = """This Manim code failed.

CODE:
{code}

ERROR:
{error}

Fix it. Keep class name GeneratedScene. Replace invalid rate_func names with smooth.
Never use LaTeX. Output ONLY the fixed raw Python code."""

EXAMPLES = ["Bouncing neon ball", "Pythagorean theorem", "Fourier wave series", "Solar system orbits",
            "Fibonacci spiral", "Atom with electrons", "Sine wave drawing", "Text morphing A to Z"]

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"generated_code": "", "video_path": "", "render_error": "",
             "history": [], "groq_api_key": "", "model": "openai/gpt-oss-120b", "quality": "medium", "prompt_box": ""}.items():
    st.session_state.setdefault(k, v)

if not st.session_state["groq_api_key"]:  # env / secrets fallback
    env_key = os.environ.get("GROQ_API_KEY", "")
    if not env_key:
        try:
            env_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            env_key = ""
    st.session_state["groq_api_key"] = env_key.strip()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_client():
    key = st.session_state["groq_api_key"]
    if not key:
        return None
    if st.session_state.get("_client_key") != key:
        st.session_state["_client"] = Groq(api_key=key)
        st.session_state["_client_key"] = key
    return st.session_state["_client"]


def clean_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", raw, flags=re.DOTALL)
    if m:
        raw = m.group(1)
    raw = raw.strip()
    # replace invalid rate funcs
    raw = re.sub(r"rate_func\s*=\s*(\w+)",
                 lambda m: m.group(0) if m.group(1) in VALID_RATE_FUNCS else "rate_func=smooth", raw)
    if "from manim import" not in raw:
        raw = "from manim import *\n" + raw
    return raw


def validate_code(code: str) -> str:
    """Return an error string if the code is unsafe/invalid, else ''."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"
    if not any(isinstance(n, ast.ClassDef) and n.name == "GeneratedScene" for n in tree.body):
        return "Missing class GeneratedScene"
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods = {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods = {(n.module or "").split(".")[0]}
        else:
            mods = set()
        if mods & BANNED_IMPORTS:
            return f"Blocked import: {mods & BANNED_IMPORTS}"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in BANNED_CALLS:
            return f"Blocked call: {n.func.id}()"
    return ""


def ask_groq(messages, temperature) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("Please add your Groq API key first.")
    model = st.session_state.get("model", "openai/gpt-oss-120b")
    kwargs = dict(model=model, messages=messages, temperature=temperature,
                  max_completion_tokens=8192)
    if model.startswith("openai/gpt-oss"):
        kwargs["reasoning_effort"] = "low"  # keep thinking short so code isn't cut off
    try:
        resp = client.chat.completions.create(**kwargs)
    except BadRequestError:
        kwargs.pop("reasoning_effort", None)
        resp = client.chat.completions.create(**kwargs)
    return clean_code(resp.choices[0].message.content or "")


def _find_mp4(out_dir):
    for root, _, files in os.walk(out_dir):
        if "partial_movie_files" in root:
            continue
        for f in files:
            if f.endswith(".mp4"):
                return os.path.join(root, f)
    return None


def render_manim(code: str, quality: str = "medium"):
    """Returns (ok, video_path, error). Uses a unique temp dir per render."""
    q_flag, q_folder, q_fps, q_timeout = QUALITY.get(quality, QUALITY["medium"])
    work = tempfile.mkdtemp(prefix="manim_")
    out_dir = os.path.join(work, "output")
    scene = os.path.join(work, "scene.py")
    stable = os.path.join(work, "latest.mp4")
    os.makedirs(out_dir, exist_ok=True)
    with open(scene, "w", encoding="utf-8") as f:
        f.write(code)

    def run(extra=()):
        return subprocess.run(
            ["manim", "render", q_flag, "--disable_caching", "--media_dir", out_dir, *extra,
             scene, "GeneratedScene"],
            capture_output=True, text=True, cwd=work, timeout=q_timeout,
            encoding="utf-8", errors="replace")

    # Windows-only: fix backslashes in ffmpeg concat list while rendering
    stop = threading.Event()
    if platform.system() == "Windows":
        concat = os.path.join(out_dir, "videos", "scene", q_folder,
                              "partial_movie_files", "GeneratedScene", "partial_movie_file_list.txt")
        def patcher():
            while not stop.is_set():
                try:
                    if os.path.exists(concat):
                        txt = open(concat, encoding="utf-8").read()
                        if "\\" in txt:
                            open(concat, "w", encoding="utf-8").write(txt.replace("\\", "/"))
                except OSError:
                    pass
                time.sleep(0.05)
        threading.Thread(target=patcher, daemon=True).start()

    try:
        try:
            r1 = run()
        except subprocess.TimeoutExpired:
            return False, "", f"Render timed out after {q_timeout}s. Try LOW quality or a simpler prompt."
        finally:
            stop.set()
        log1 = (r1.stderr + "\n" + r1.stdout).strip()
        mp4 = _find_mp4(out_dir)
        if mp4:
            shutil.copy2(mp4, stable)
            return True, stable, ""

        # Fallback: PNG frames -> ffmpeg
        shutil.rmtree(out_dir, ignore_errors=True)
        os.makedirs(out_dir, exist_ok=True)
        try:
            r2 = run(("--format", "png"))
        except subprocess.TimeoutExpired:
            return False, "", f"Fallback render timed out.\n\n{log1[-700:]}"
        log2 = (r2.stderr + "\n" + r2.stdout).strip()

        best, src = 0, None
        for root, _, files in os.walk(out_dir):
            n = sum(f.endswith(".png") for f in files)
            if n > best:
                best, src = n, root
        if not src:
            return False, "", f"Render failed.\n\nAttempt 1:\n{log1[-700:]}\n\nAttempt 2:\n{log2[-700:]}"

        pngs = sorted((os.path.join(src, f) for f in os.listdir(src) if f.endswith(".png")),
                      key=lambda p: int("".join(filter(str.isdigit, os.path.basename(p))) or 0))
        list_file = os.path.join(work, "frames.txt")
        with open(list_file, "w", encoding="utf-8") as cf:
            for p in pngs:
                cf.write(f"file '{p.replace(chr(92), '/')}'\nduration {round(1 / q_fps, 6)}\n")
            cf.write(f"file '{pngs[-1].replace(chr(92), '/')}'\n")
        ff = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file.replace("\\", "/"),
             "-vf", "fps=30", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", stable],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if ff.returncode == 0 and os.path.exists(stable):
            return True, stable, ""
        return False, "", f"PNG encode failed:\n{ff.stderr[-500:]}\n\nAttempt 1:\n{log1[-400:]}"
    except FileNotFoundError as e:
        return False, "", f"Missing executable: {e}. Make sure manim and ffmpeg are installed and on PATH."


def use_example(text):
    st.session_state["prompt_box"] = text


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Model")
    st.selectbox("Groq model", list(GROQ_MODELS), key="model",
                 format_func=GROQ_MODELS.get, label_visibility="collapsed")
    st.caption("Served by GroqCloud")
    st.markdown("---")
    st.markdown("### Prompt Tips")
    st.markdown("""
- *"bouncing ball with shadow trail"*
- *"Pythagorean theorem step by step"*
- *"letter A morphing to B"*
- *"spiral galaxy forming from dots"*
- *"sine and cosine waves together"*
""")
    st.caption("ManimAI — Groq + Manim CE")

# ── Main page ─────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">Powered by Groq - 100% Free</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Manim<span>AI</span></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Describe any animation in plain English — get a rendered video in seconds.</div>',
            unsafe_allow_html=True)

# One API key input for all screen sizes
has_key = bool(st.session_state["groq_api_key"])
with st.expander("🔑 Groq API key" + (" ✓" if has_key else " (required)"), expanded=not has_key):
    st.markdown("Get a **free** key at [console.groq.com](https://console.groq.com) — no credit card needed.")
    key_in = st.text_input("Groq API key", type="password", placeholder="gsk_...",
                           label_visibility="collapsed", key="key_field")
    if key_in and key_in.strip() != st.session_state["groq_api_key"]:
        st.session_state["groq_api_key"] = key_in.strip()
        st.rerun()

# Clickable example chips
cols = st.columns(4)
for i, ex in enumerate(EXAMPLES):
    cols[i % 4].button(ex, key=f"ex_{i}", on_click=use_example, args=(ex,), use_container_width=True)

prompt = st.text_area("Your animation prompt", height=130, key="prompt_box",
                      placeholder="e.g. A glowing blue sine wave draws itself left to right, then a red cosine wave appears below it")

st.radio("Render quality", list(QUALITY_LABELS), format_func=QUALITY_LABELS.get,
         key="quality", horizontal=True)

btn_col, _ = st.columns([2, 3])
go = btn_col.button("Generate Animation", type="primary", use_container_width=True)
st.markdown("---")

# ── Pipeline ──────────────────────────────────────────────────────────────────
if go:
    if not st.session_state["groq_api_key"]:
        st.error("Please add your free Groq API key above.")
    elif not prompt.strip():
        st.warning("Please type an animation description.")
    else:
        st.session_state.update(video_path="", render_error="", generated_code="")
        quality = st.session_state["quality"]
        ok, video, err, code = False, "", "", ""
        with st.status("Working...", expanded=True) as status:
            try:
                st.write("✍️ Groq is writing Manim code...")
                code = ask_groq([{"role": "system", "content": SYSTEM_PROMPT},
                                 {"role": "user", "content": f"Create a Manim animation for: {prompt.strip()}"}], 0.4)
                st.session_state["generated_code"] = code

                for attempt in (1, 2):  # attempt 2 = auto-fix
                    bad = validate_code(code)
                    if bad:
                        ok, video, err = False, "", bad
                    else:
                        st.write(f"🎞️ Rendering at {QUALITY_LABELS[quality]}...")
                        ok, video, err = render_manim(code, quality)
                    if ok or attempt == 2:
                        break
                    st.write("🔧 First attempt failed — asking Groq to fix it...")
                    code = ask_groq([{"role": "user",
                                      "content": RETRY_PROMPT.format(code=code, error=err[:1500])}], 0.2)
                    st.session_state["generated_code"] = code
            except Exception as e:  # API/key/rate-limit errors
                ok, err = False, f"{type(e).__name__}: {e}"
            status.update(label="Animation ready!" if ok else "Failed",
                          state="complete" if ok else "error", expanded=False)

        if ok:
            st.session_state["video_path"] = video
            st.session_state["history"].append({"prompt": prompt.strip(), "code": code, "video": video})
        else:
            st.session_state["render_error"] = err
            st.error("Something went wrong — see error details below.")

# ── Results ───────────────────────────────────────────────────────────────────
vp = st.session_state["video_path"]
if vp and os.path.exists(vp):
    col_v, col_c = st.columns([3, 2])
    with col_v:
        st.markdown('<div class="sec-title">Your Animation</div>', unsafe_allow_html=True)
        st.video(vp)
        with open(vp, "rb") as f:
            st.download_button("Download MP4", f.read(), file_name="manim_animation.mp4", mime="video/mp4")
    with col_c:
        st.markdown('<div class="sec-title">Generated Code</div>', unsafe_allow_html=True)
        st.code(st.session_state["generated_code"], language="python")
elif st.session_state["generated_code"]:
    st.markdown('<div class="sec-title">Generated Code</div>', unsafe_allow_html=True)
    st.code(st.session_state["generated_code"], language="python")

if st.session_state["render_error"]:
    with st.expander("Error details"):
        st.code(st.session_state["render_error"], language="bash")

# ── History ───────────────────────────────────────────────────────────────────
if st.session_state["history"]:
    st.markdown("---")
    st.markdown('<div class="sec-title">Session History</div>', unsafe_allow_html=True)
    n = len(st.session_state["history"])
    for i, item in enumerate(reversed(st.session_state["history"])):
        p = item["prompt"]
        with st.expander(f"#{n - i} - {p[:60]}{'...' if len(p) > 60 else ''}"):
            h1, h2 = st.columns([3, 2])
            if os.path.exists(item["video"]):
                h1.video(item["video"])
            h2.code(item["code"], language="python")