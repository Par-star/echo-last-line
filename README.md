# 🌌 ECHO://THE_LAST_LINE

> **Speak, and the world will listen.**

A **voice-driven visual novel / AI Dungeon Master** where your spoken words literally rewrite reality. You are the last **Echo Architect** in a collapsing universe called *the Weave* — whisper, shout, or chant, and the story bends around your voice. Every scene is narrated by an AI and painted with free AI-generated artwork.

🔗 **Live demo:** [https://echo-last-line-gby4utrgyinkhu32rflsns.streamlit.app/](https://echo-last-line-gby4utrgyinkhu32rflsns.streamlit.app/)

🎬 **Video demo:** [Watch on YouTube](https://youtu.be/ukDFCUqDz_Q)

---

## ✨ Features

- 🎙️ **Speak your actions** — free-form voice input transcribed by Groq Whisper (`whisper-large-v3-turbo`)
- 🧠 **AI Dungeon Master** — Llama 3.3 70B ("The Weaver") writes a living, branching noir-sci-fi story
- 🪄 **Echoes (power words)** — learn magic words as you play; speak a learned echo aloud to trigger a cinematic **Voice Surge**
- 💠 **Wordseed** — pick a signature word at birth (ASH / TIDE / STATIC); invoking it resonates deeper than any other
- 📊 **Living world state** — Stability (world health), Resonance (willpower), Static (corruption), Layer depth, Echo library
- 🎨 **AI scene art** — every scene is illustrated free by [Pollinations.ai](https://pollinations.ai) (no API key needed)
- 🌈 **Dynamic mood lighting** — the whole page re-tints to match each scene's `ambient_color`
- ⌨️ **Terminal Override** — no mic? Type your actions instead
- 📜 **Story export** — download your whole adventure as Markdown
- 🔁 **Multiple endings** — unravel, collapse the Weave, or be consumed by Static

## 🛠 Tech Stack

| Layer | Tech |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) + custom CSS (glitch art, typewriter effect) |
| Speech-to-text | [Groq](https://groq.com) — `whisper-large-v3-turbo` |
| Story / DM | [Groq](https://groq.com) — `llama-3.3-70b-versatile` |
| Scene art | [Pollinations.ai](https://pollinations.ai) — free, keyless |

## 🚀 Local Setup

```bash
git clone https://github.com/<your-username>/echo-last-line.git
cd echo-last-line

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
