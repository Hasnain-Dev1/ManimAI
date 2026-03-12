# ⚡ ManimAI — Powered by Groq (100% Free!)

Turn plain English into Manim animations using **Groq's free API** (Llama 3.3 70B).  
No credit card. No paid API. Just fast, free animations.

---

## 🚀 Setup in 4 Steps

### 1. Get your FREE Groq API key
1. Go to **https://console.groq.com**
2. Sign up (free, no credit card)
3. Create an API key → copy it

### 2. Install system dependencies

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y ffmpeg texlive-full python3-pip
```

**macOS:**
```bash
brew install ffmpeg
brew install --cask mactex   # for LaTeX/math equations
```

**Windows (WSL2 recommended):**
```bash
# Use Ubuntu in WSL2, then follow Ubuntu instructions above
```

### 3. Install Python packages
```bash
pip install -r requirements.txt
```

### 4. Run!
```bash
streamlit run app.py
```

Open **http://localhost:8501** → paste your Groq key in the sidebar → generate! ⚡

---

## 🆓 Groq Free Tier Limits

| Limit | Value |
|-------|-------|
| Requests/minute | 30 |
| Requests/day | 14,400 |
| Tokens/minute | 6,000 |
| Cost | **$0** |

More than enough for tons of animations!

---

## 🎨 Example Prompts

```
A bouncing orange ball that leaves a glowing trail
Pythagorean theorem proof with colored squares
Solar system with 3 orbiting planets
Sine wave drawing itself left to right
Text "Hello World" writing itself in neon green
Fibonacci spiral growing outward
DNA double helix rotating slowly
Bar chart animating from 0 to final values
```

---

## 🗂 File Structure

```
manim-groq/
├── app.py              ← Main Streamlit app (Groq-powered)
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🌐 Deploy Free on Streamlit Cloud

1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect repo → select `app.py`
4. Users enter their own Groq key in the sidebar

---

## ⚙️ Tech Stack

| Layer | Tool | Cost |
|-------|------|------|
| UI | Streamlit | Free |
| AI | Groq (Llama 3.3 70B) | **Free** |
| Animation | Manim CE | Free |
| Video | ffmpeg | Free |

**Total cost: $0** 🎉