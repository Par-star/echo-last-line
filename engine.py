
import os
import re
import json

from groq import Groq

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Tunables ----------------------------------------------------------------
STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
DM_MODEL = os.getenv("GROQ_DM_MODEL", "openai/gpt-oss-120b")

# The full vocabulary of power words the game understands.
POWER_WORDS = [
    "ASH", "TIDE", "STATIC", "SHATTER", "HUSH",
    "REKINDLE", "WEAVE", "SILENCE", "ECHO", "UNMAKE",
]

STORY_BIBLE = """
You are THE WEAVER — the omniscient narrator and Dungeon Master of ECHO://THE_LAST_LINE, a surreal sci-fi noir visual novel.

THE SETTING: The WEAVE is reality itself — a living tapestry of sound, light, and memory — and it is collapsing under a cosmic affliction called THE SILENCE. Sound dies first, then color, then memory, then people. The player is the last ECHO ARCHITECT: a person whose spoken words literally rewrite the world around them.

STYLE — write like the lovechild of a noir detective novel, a fever dream, and a poetry collection:
- SECOND PERSON, PRESENT TENSE: "You step into the corridor of frozen echoes…"
- Poetic, cinematic, eerie. Engage every sense: color, temperature, texture, taste, hum, pressure.
- Short, punchy paragraphs. Never recap mechanics. Show, don't tell.
- End most turns with a hook: an open question, an approaching sound, a decision framed as something the player could say aloud.
- Plain prose only — NEVER use markdown, asterisks, or bullet symbols in the narrative.

WORLD RULES:
1. The player's voice is the only tool that works. Spoken words become literal phenomena: "hush" quiets a shrieking Hollow, "ash" burns, "tide" washes barriers away, "static" scrambles and corrupts.
2. HOLLOWS are enemies: memories that forgot their own words. Defeat them by speaking the right word back to them. Always plant clues for the right word in the scene.
3. The player descends roughly one LAYER deeper into the collapse every 3-4 turns; each layer is stranger and more beautiful than the last. Every 3-4 layers, stage an ECHO STORM — a setpiece climax where the world screams.
4. THE GREAT SILENCE is the final antagonist. Build slowly toward it.
5. The player's WORDSEED is their signature word; invoking it resonates deeply with the world.

COMBAT is a contest of will. The player's spoken line is their attack. Reward poetic, clever, or echo-fueled lines with victories. Punish recklessness with consequences.

STATE (all 0-100 except layer):
- stability: health of the Weave. At 0, the world collapses.
- resonance: the player's willpower. At 0, the player unravels.
- static: corruption clinging to the player. At 100, they are consumed.
- layer: depth of the descent (starts at 1).
- echoes: power words the player has learned; invoking one triggers a VOICE SURGE (critical, cinematic payoff).

OUTPUT FORMAT — return ONLY a valid JSON object. No markdown fences, no commentary, no trailing text:
{
  "narrative": "2-4 short paragraphs ending with a hook",
  "image_prompt": "A concise visual description of this scene, max 30 words, surreal sci-fi noir style, comma-separated",
  "ambient_color": "hex color matching the scene mood, e.g. #1a0b2e",
  "state_deltas": {"stability": -5, "resonance": -3, "static": 2, "layer": 0},
  "echo_learned": null,
  "suggested_words": ["spoken line idea one", "spoken line idea two"],
  "scene_emotion": "one word, e.g. dread, wonder, grief",
  "game_over": false,
  "ending": null
}

RULES:
- state_deltas: small numbers, usually between -8 and +8. Clever, poetic, or echo-fueled actions reward; reckless actions punish.
- echo_learned: set to one of ASH, TIDE, STATIC, SHATTER, HUSH, REKINDLE, WEAVE, SILENCE, ECHO, UNMAKE only when the player genuinely earns a new power word. Otherwise null.
- image_prompt: always describe the current scene visually (place, light, mood, key objects/characters) — this becomes the illustration for this turn.
- game_over: true ONLY when the player is erased, the Weave collapses, or a major arc resolves. When true, name the ending.
- Keep continuity with the conversation log — reference earlier events, characters, and consequences.
"""


def get_client():
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Put it in a .env file "
            "(GROQ_API_KEY=gsk-...) or export it in your shell."
        )
    return Groq(api_key=key)


def transcribe(client, audio_bytes, mime="audio/wav", filename="voice.wav"):
    resp = client.audio.transcriptions.create(
        file=(filename, audio_bytes, mime),
        model=STT_MODEL,
        response_format="text",
        language="en",
    )
    return (resp if isinstance(resp, str) else str(resp)).strip()


def _extract_json(text):
    """Robustly pull a JSON object out of a model reply."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output")
    try:
        return json.loads(text)
    except Exception:
        pass
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("No JSON found in model output")


def detect_surge(text, state):
    """Look for power words & stealth phrasing in what the player said."""
    flags, invoked = [], []
    upper = (text or "").upper()
    for word in POWER_WORDS:
        if re.search(rf"\b{word}\b", upper):
            invoked.append(word)
            if word in state.get("echoes", []):
                flags.append(
                    f"VOICE SURGE: the player invoked the learned echo '{word}'. "
                    "This is a critical, cinematic moment — grant dramatic advantage."
                )
            elif word == (state.get("wordseed") or "").upper():
                flags.append(
                    f"WORDSEED RESONANCE: the player spoke their signature word "
                    f"'{word}'. The Weave shudders — make something special happen."
                )
    if re.search(r"\b(whisper|quietly|stealth|sneak|silently)\b", upper):
        flags.append(
            "SUBVOCAL MODE: the player described a quiet/stealthy action. "
            "Honor the subtlety — narrate the hush and reward a careful approach."
        )
    return flags, invoked


def _state_summary(s):
    echoes = ", ".join(s.get("echoes", [])) or "none yet"
    return (
        "CURRENT STATE:\n"
        f"- Player: {s.get('name') or 'the Nameless One'} (Wordseed: {s.get('wordseed') or '?'})\n"
        f"- Layer: {s.get('layer', 1)}  |  Turns: {s.get('turns', 0)}\n"
        f"- stability (Weave health): {s.get('stability', 70)}/100\n"
        f"- resonance (willpower):    {s.get('resonance', 60)}/100\n"
        f"- static (corruption):      {s.get('static', 5)}/100\n"
        f"- echoes learned: {echoes}"
    )


def _build_messages(state, history, user_text, flags, is_opening):
    system = STORY_BIBLE + "\n\n" + _state_summary(state)
    if flags:
        system += "\n\nLATEST EVENT:\n- " + "\n- ".join(flags)
    if is_opening:
        system += (
            "\n\nTHIS IS THE OPENING SCENE. The player just awoke in the THRESHOLD — "
            "a corridor of frozen echoes — and speaks their name and wordseed. "
            "Write the first scene: awaken them, show the unraveling world, "
            "and end with a hook they can answer aloud."
        )
    messages = [{"role": "system", "content": system}]
    messages += history[-14:]
    messages.append({"role": "user", "content": user_text})
    return messages


def _normalize(raw, invoked):
    try:
        data = _extract_json(raw)
        out = {
            "narrative": str(data.get("narrative", "")).strip(),
            "image_prompt": data.get("image_prompt") or None,
            "ambient_color": str(data.get("ambient_color", "#0b1026")),
            "state_deltas": data.get("state_deltas") or {},
            "echo_learned": data.get("echo_learned") or None,
            "suggested_words": list(data.get("suggested_words") or [])[:3],
            "scene_emotion": str(data.get("scene_emotion", "unknown")),
            "game_over": bool(data.get("game_over", False)),
            "ending": data.get("ending") or None,
        }
    except Exception:
        out = {
            "narrative": re.sub(r"```(?:json)?|```", "", raw or "").strip(),
            "image_prompt": None,
            "ambient_color": "#0b1026",
            "state_deltas": {},
            "echo_learned": None,
            "suggested_words": [],
            "scene_emotion": "unknown",
            "game_over": False,
            "ending": None,
        }
    out["invoked"] = invoked
    return out


def dm_turn(client, state, history, user_text, is_opening=False):
    """The Weaver hears the player's words and answers with the next scene."""
    flags, invoked = detect_surge(user_text, state)
    messages = _build_messages(state, history, user_text, flags, is_opening)
    resp = client.chat.completions.create(
        model=DM_MODEL,
        messages=messages,
        temperature=0.9,
        max_tokens=1300,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    return _normalize(raw, invoked)
