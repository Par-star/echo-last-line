
import hashlib
import html
import os
import time
import urllib.parse

import requests
import streamlit as st

import engine

st.set_page_config(page_title="ECHO://THE_LAST_LINE", page_icon="🌌", layout="wide")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Space+Mono:wght@400;700&family=VT323&display=swap');

.stApp { background: radial-gradient(ellipse at 25% 0%, #0b1026 0%, #04050a 55%) !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #07080f !important; border-right: 1px solid #1c2033; }
.block-container { padding-top: 1.5rem; max-width: 1000px; }

h1, h2, h3 { font-family: 'VT323', monospace; letter-spacing: 2px; color: #e8e4d8; }

.title-wrap { text-align: center; margin: 2rem 0 2.5rem; }
.glitch { font-family: 'VT323', monospace; font-size: 4.2rem; color: #e8e4d8; position: relative; letter-spacing: 6px; margin: 0; }
.glitch::before, .glitch::after { content: attr(data-text); position: absolute; inset: 0; overflow: hidden; }
.glitch::before { color: #7fd4ff; transform: translate(-2px, -1px); clip-path: inset(0 0 60% 0); animation: glitch-a 3.2s infinite linear alternate-reverse; }
.glitch::after { color: #ff5d8f; transform: translate(2px, 1px); clip-path: inset(60% 0 0 0); animation: glitch-b 2.7s infinite linear alternate-reverse; }
@keyframes glitch-a { 0% { clip-path: inset(0 0 60% 0); } 20% { clip-path: inset(10% 0 40% 0); } 40% { clip-path: inset(30% 0 20% 0); } 60% { clip-path: inset(0 0 80% 0); } 80% { clip-path: inset(50% 0 5% 0); } 100% { clip-path: inset(20% 0 45% 0); } }
@keyframes glitch-b { 0% { clip-path: inset(60% 0 0 0); } 25% { clip-path: inset(70% 0 5% 0); } 50% { clip-path: inset(40% 0 30% 0); } 75% { clip-path: inset(80% 0 0 0); } 100% { clip-path: inset(55% 0 15% 0); } }

.tagline { font-family: 'Space Mono', monospace; color: #8f93a8; letter-spacing: 3px; text-transform: uppercase; font-size: .78rem; margin-top: .4rem; }

.novel { font-family: 'Cormorant Garamond', serif; font-size: 1.28rem; line-height: 1.75; color: #d8d3c8; padding: .4rem 0 .9rem; border-bottom: 1px dashed #232741; }
.novel .dropcap::first-letter { font-size: 3.4rem; font-weight: 600; float: left; line-height: .85; padding-right: .35rem; color: #c9a2ff; }
.turn-user { font-family: 'Space Mono', monospace; font-size: .95rem; color: #7fd4ff; border-left: 3px solid #7fd4ff; padding: .25rem .8rem; margin: .6rem 0 .1rem; background: rgba(127, 212, 255, .05); }
.badge { display: inline-block; font-family: 'VT323', monospace; font-size: 1.05rem; letter-spacing: 2px; color: #04050a; background: #c9a2ff; padding: .15rem .8rem; border-radius: 2px; margin: .3rem .3rem .3rem 0; }
.chip { display: inline-block; font-family: 'Space Mono', monospace; font-size: .8rem; color: #e8e4d8; border: 1px solid #c9a2ff; padding: .1rem .6rem; margin: .15rem .2rem; border-radius: 3px; }
.chip.gold { border-color: #ffd36e; color: #ffd36e; }
.quote { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #9aa0b8; font-size: 1.05rem; margin: .1rem .5rem .1rem 0; }
.stat { margin: .4rem 0 .9rem; }
.stat-label { font-family: 'Space Mono', monospace; font-size: .78rem; color: #8f93a8; display: flex; justify-content: space-between; }
.bar { height: 7px; background: #14182a; border-radius: 4px; overflow: hidden; margin-top: 3px; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .8s ease; }
.muted { color: #5d627a; font-family: 'Space Mono', monospace; font-size: .8rem; }
.sys { font-family: 'Space Mono', monospace; color: #ffd36e; font-size: .8rem; margin: .15rem 0; }
.ending-card { font-family: 'Cormorant Garamond', serif; font-size: 1.25rem; line-height: 1.7; color: #e8e4d8; border: 1px solid #ff5d8f; padding: 1.2rem 1.4rem; background: rgba(255, 93, 143, .07); margin-top: 1rem; }
.flash { font-family: 'VT323', monospace; font-size: 1.6rem; letter-spacing: 2px; color: #ffd36e; text-align: center; padding: .5rem; border: 1px dashed #ffd36e; margin-bottom: .8rem; animation: fade 1.2s ease; }
@keyframes fade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; } }
"""

# FIXED: wrap CSS in <style> so it's applied, not displayed
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

DEFAULT_STATE = {
    "name": "", "wordseed": "TIDE", "layer": 1,
    "stability": 70, "resonance": 60, "static": 5,
    "echoes": [], "turns": 0, "endings": [],
}

def init():
    st.session_state.setdefault("phase", "title")
    st.session_state.setdefault("game_state", dict(DEFAULT_STATE))
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("log", [])
    st.session_state.setdefault("ambient", "#0b1026")
    st.session_state.setdefault("last_fp", None)
    st.session_state.setdefault("name_fp", None)
    st.session_state.setdefault("stream_buf", None)
    st.session_state.setdefault("just_streamed", False)
    st.session_state.setdefault("error", None)
    st.session_state.setdefault("flash", None)
    st.session_state.setdefault("picked_name", "")
    st.session_state.setdefault("show_art", True)

init()
gs = st.session_state.game_state

# The scene's mood re-tints the whole page
st.markdown(
    f"<style>.stApp{{background: radial-gradient(ellipse at 25% 0%, "
    f"{st.session_state.ambient} 0%, #04050a 60%) !important;}}</style>",
    unsafe_allow_html=True,
)

def bar(label, value, color, mx=100):
    pct = max(0.0, min(100.0, value / mx * 100.0))
    return (
        f'<div class="stat"><div class="stat-label">{label}<span>{int(value)}</span></div>'
        f'<div class="bar"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div></div>'
    )

def typewriter(text, speed=0.008):
    for ch in text:
        yield ch
        time.sleep(speed)

def fetch_scene_art(prompt, seed=0):
    """Free scene art from Pollinations.ai. Returns image bytes or None."""
    if not prompt:
        return None
    full = f"{prompt}, dark atmospheric surreal sci-fi noir, highly detailed, cinematic digital painting"
    url = ("https://image.pollinations.ai/prompt/"
           f"{urllib.parse.quote(full)}?width=1024&height=576&nologo=true&seed={seed}")
    try:
        r = requests.get(url, timeout=20)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None

def render_turn(t):
    if t["role"] == "user":
        st.markdown(
            f'<div class="turn-user">🎙️&nbsp; {html.escape(t["content"])}</div>',
            unsafe_allow_html=True,
        )
        return
    invoked = t.get("invoked") or []
    if invoked:
        chips = " ".join(f'<span class="chip gold">{html.escape(w)}</span>' for w in invoked)
        st.markdown(f'<div class="sys">✦ VOICE SURGE — you spoke: {chips}</div>', unsafe_allow_html=True)
    if st.session_state.get("show_art", True) and t.get("art_bytes"):
        st.image(t["art_bytes"], use_container_width=True)
    narrative = html.escape(t["narrative"])
    st.markdown(f'<div class="novel"><span class="dropcap">{narrative}</span></div>', unsafe_allow_html=True)
    emo = f'<span class="badge">{html.escape(t.get("emotion", ""))}</span>' if t.get("emotion") else ""
    sugg = " ".join(f'<span class="quote">“{html.escape(q)}”</span>' for q in (t.get("suggested") or []))
    st.markdown(emo + sugg, unsafe_allow_html=True)

def render_story():
    log = st.session_state.log
    skip = 1 if st.session_state.just_streamed else 0
    for t in log[:-skip] if skip else log:
        render_turn(t)
    if st.session_state.just_streamed and st.session_state.stream_buf:
        ph = st.empty()
        ph.write_stream(typewriter(st.session_state.stream_buf))
        st.session_state.stream_buf = None
        st.session_state.just_streamed = False

def apply_turn(user_text, out):
    gs = st.session_state.game_state
    for k, v in (out.get("state_deltas") or {}).items():
        if k in ("stability", "resonance", "static") and isinstance(v, (int, float)):
            gs[k] = max(0, min(100, gs[k] + int(v)))
        elif k == "layer" and isinstance(v, (int, float)):
            gs["layer"] = max(1, gs["layer"] + int(v))
    learned = (out.get("echo_learned") or "").upper()
    if learned and learned in engine.POWER_WORDS and learned not in gs["echoes"]:
        gs["echoes"].append(learned)
        st.session_state.flash = f"✦ NEW ECHO LEARNED — {learned}"
    gs["turns"] += 1

    # Fetch the scene's artwork (runs while the spinner is showing)
    art_bytes = None
    if st.session_state.get("show_art", True):
        art_bytes = fetch_scene_art(out.get("image_prompt"), seed=gs["turns"])

    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": out["narrative"]})
    if len(st.session_state.history) > 28:
        st.session_state.history = st.session_state.history[-28:]

    st.session_state.log.append({"role": "user", "content": user_text})
    st.session_state.log.append({
        "role": "assistant",
        "narrative": out["narrative"],
        "emotion": out.get("scene_emotion", ""),
        "color": out.get("ambient_color", "#0b1026"),
        "suggested": out.get("suggested_words", []),
        "invoked": out.get("invoked", []),
        "art_bytes": art_bytes,
    })
    st.session_state.ambient = out.get("ambient_color", "#0b1026")
    st.session_state.stream_buf = out["narrative"]
    st.session_state.just_streamed = True

    game_over, ending = out.get("game_over", False), out.get("ending")
    if not game_over:
        if gs["stability"] <= 0:
            game_over, ending = True, "THE WEAVE FALLS SILENT"
        elif gs["resonance"] <= 0:
            game_over, ending = True, "THE ARCHITECT UNRAVELS"
        elif gs["static"] >= 100:
            game_over, ending = True, "SWALLOWED BY STATIC"
    if game_over:
        gs["endings"].append(ending or "AN UNFINISHED ECHO")
        st.session_state.final_ending = ending or "AN UNFINISHED ECHO"
        st.session_state.phase = "ended"

def run_turn(user_text, is_opening=False):
    user_text = (user_text or "").strip()
    if not user_text:
        return
    st.session_state.error = None
    try:
        client = engine.get_client()
        with st.spinner("The Weave listens…"):
            out = engine.dm_turn(client, gs, st.session_state.history, user_text, is_opening=is_opening)
        apply_turn(user_text, out)
    except Exception as exc:
        st.session_state.error = f"{type(exc).__name__}: {exc}"

def reset():
    keys = [k for k in st.session_state.keys()
            if k in ("phase", "game_state", "history", "log", "ambient",
                     "last_fp", "name_fp", "stream_buf", "just_streamed",
                     "error", "flash", "picked_name", "final_ending", "show_art")]
    for k in keys:
        del st.session_state[k]
    st.rerun()

def story_markdown():
    lines = [f"# ECHO://THE_LAST_LINE — {gs['name'] or 'the Nameless One'}", ""]
    for t in st.session_state.log:
        if t["role"] == "user":
            lines.append(f"> 🎙️ {t['content']}")
        else:
            lines.append(t["narrative"])
            lines.append("")
    return "\n".join(lines)

# ---------------------------------------------------------------- sidebar --
with st.sidebar:
    st.markdown("### 🌌 THE WEAVE")
    st.session_state.show_art = st.checkbox("🌌 Scene art", value=st.session_state.get("show_art", True))
    if st.session_state.phase in ("play", "ended"):
        st.markdown(bar("Stability — world health", gs["stability"], "#7fd4ff"), unsafe_allow_html=True)
        st.markdown(bar("Resonance — willpower", gs["resonance"], "#c9a2ff"), unsafe_allow_html=True)
        st.markdown(bar("Static — corruption", gs["static"], "#ff5d8f"), unsafe_allow_html=True)
        st.markdown(
            f'<div class="stat-label">Layer<span>{"▰" * min(gs["layer"], 10)} {gs["layer"]}</span></div>',
            unsafe_allow_html=True,
        )
        echoes = " ".join(f'<span class="chip">{html.escape(w)}</span>' for w in gs["echoes"]) or '<span class="muted">none yet</span>'
        st.markdown(f'<div class="stat-label">Echoes</div><div>{echoes}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">Wordseed<span>{html.escape(gs["wordseed"])}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">Turns<span>{gs["turns"]}</span></div>', unsafe_allow_html=True)
        if gs["endings"]:
            st.markdown("**Endings found:** " + ", ".join(gs["endings"]))
        if st.button("⟲ Reset the Weave", use_container_width=True):
            reset()
        if st.session_state.log:
            st.download_button("📜 Export story", story_markdown(), file_name="echo_last_line.md", use_container_width=True)
    st.markdown("---")
    st.markdown(
        '<div class="muted">ECHO://THE_LAST_LINE<br/>a voice-driven visual novel<br/>Groq Whisper + Llama 3.3 70B + Pollinations</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ phases --
if st.session_state.phase == "title":
    st.markdown(
        '<div class="title-wrap"><h1 class="glitch" data-text="ECHO://THE_LAST_LINE">'
        'ECHO://THE_LAST_LINE</h1><div class="tagline">Speak, and the world will listen</div></div>',
        unsafe_allow_html=True,
    )
    if not os.environ.get("GROQ_API_KEY"):
        st.error("**GROQ_API_KEY not found.** Create a key at console.groq.com and add `GROQ_API_KEY=gsk-...` to a `.env` file in this folder, then restart the app.")
    st.markdown(
        "Reality is a **Weave** — a tapestry of sound and memory. Something is unraveling it: "
        "**the Silence**. You are the last **Echo Architect**, a soul who can rewrite the world "
        "by speaking. Your voice is a weapon. Your words are spells. Every whisper leaves a scar."
    )
    with st.expander("🎮 How to play"):
        st.markdown(
            "- **Speak your actions** into the microphone — free form, like talking to a GM. "
            "“I follow the sound of the bells,” “I whisper past the Hollow,” “I shatter the mirror.”\n"
            "- Learn **Echoes** (power words) and speak them to trigger **Voice Surges** — critical, cinematic moments.\n"
            "- Keep an eye on **Stability** (the world’s health), **Resonance** (your willpower), and **Static** (corruption).\n"
            "- Watch your **Wordseed** — your signature word resonates deeper than any other.\n"
            "- No mic? Use the **Terminal Override** to type your actions.\n"
            "- **Scene art** is drawn free by Pollinations — toggle it off in the sidebar anytime."
        )
    if st.button("▶ Initiate new echo", type="primary", use_container_width=True):
        st.session_state.phase = "intro"
        st.rerun()

elif st.session_state.phase == "intro":
    st.markdown("## I. The Threshold")
    st.markdown(
        "You wake on cold stone, in a corridor of **frozen echoes**. Every footstep you can "
        "remember hangs in the air like a photograph of sound. A voice — yours, but older — "
        "tells you the only thing you kept: a **Wordseed**, one word burned into your soul. "
        "Choose it. Speak your name. Then step forward."
    )
    wordseed = st.radio(
        "Your Wordseed — the word engraved on your soul:",
        ["ASH", "TIDE", "STATIC"], horizontal=True,
        help="ASH burns away decay · TIDE carries and reshapes · STATIC scrambles and corrupts",
    )
    name_audio = st.audio_input("🎙️ Speak your name (optional)")
    if name_audio is not None:
        fp = hashlib.md5(name_audio.getvalue()).hexdigest()
        if fp != st.session_state.name_fp:
            st.session_state.name_fp = fp
            with st.spinner("Listening…"):
                try:
                    client = engine.get_client()
                    t = engine.transcribe(client, name_audio.getvalue(), mime=name_audio.type, filename=name_audio.name)
                    if t:
                        st.session_state.picked_name = t
                        st.toast(f"Heard: {t}")
                except Exception as exc:
                    st.session_state.error = f"Name decode failed: {exc}"
    name = st.text_input("Or type your name (press Enter to confirm)", value=st.session_state.picked_name, placeholder="e.g. June, Kai, the Nameless One")
    if st.button("Descend into the Threshold", type="primary", use_container_width=True):
        gs["name"] = (name or "the Nameless One").strip()
        gs["wordseed"] = wordseed
        run_turn(
            f"My name is {gs['name']}. My wordseed is {wordseed}. I speak it now, and step into the Threshold.",
            is_opening=True,
        )
        if not st.session_state.error:
            st.session_state.phase = "play"
            st.rerun()

elif st.session_state.phase == "play":
    if st.session_state.flash:
        st.markdown(f'<div class="flash">{html.escape(st.session_state.flash)}</div>', unsafe_allow_html=True)
        st.session_state.flash = None
    render_story()

    st.markdown("---")
    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        audio = st.audio_input("🎙️ Speak your action — the Weave is listening", key="mic")
    with col_b:
        st.markdown("**⌨️ Terminal Override**")
        typed = st.text_input(
            "Type your action if you can't speak", label_visibility="collapsed",
            placeholder="e.g. I shatter the mirror of the past…", key="term",
        )
        if st.button("Send words", type="primary", use_container_width=True):
            if typed.strip():
                run_turn(typed)
                st.rerun()
            else:
                st.toast("The Weave heard nothing. Say or type something.")
    if audio is not None:
        fp = hashlib.md5(audio.getvalue()).hexdigest()
        if fp != st.session_state.last_fp:
            st.session_state.last_fp = fp
            with st.spinner("Decoding your voice…"):
                try:
                    client = engine.get_client()
                    text = engine.transcribe(client, audio.getvalue(), mime=audio.type, filename=audio.name)
                except Exception as exc:
                    st.session_state.error = f"Voice decode failed: {exc}"
                    text = None
            if text:
                run_turn(text)
                st.rerun()

elif st.session_state.phase == "ended":
    if st.session_state.flash:
        st.markdown(f'<div class="flash">{html.escape(st.session_state.flash)}</div>', unsafe_allow_html=True)
        st.session_state.flash = None
    render_story()
    ending = st.session_state.get("final_ending", "AN UNFINISHED ECHO")
    st.markdown(
        f'<div class="ending-card"><h2 style="margin-top:0">◼ {html.escape(ending)}</h2>'
        f"The tale of {html.escape(gs['name'] or 'the Nameless One')} ends here — "
        f"after {gs['turns']} turns, {len(gs['endings'])} ending(s) woven.</div>",
        unsafe_allow_html=True,
    )
    if st.button("⟲ Reweave the story (new game)", type="primary", use_container_width=True):
        reset()

if st.session_state.error:
    st.error(st.session_state.error)
    if st.button("Dismiss"):
        st.session_state.error = None
        st.rerun()
