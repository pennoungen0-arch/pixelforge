import streamlit as st
import requests
import json
import random
import io
import base64
import zipfile
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="PixelForge — Character Asset Creator",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load keys from secrets ────────────────────────────────────────────────────
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
HF_KEY   = st.secrets.get("HF_API_KEY", "")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Share+Tech+Mono&display=swap');
:root {
    --bg:      #0a0a0f;
    --surface: #12121a;
    --panel:   #1a1a28;
    --border:  #2a2a40;
    --accent:  #00ffcc;
    --accent2: #ff6b35;
    --accent3: #a855f7;
    --text:    #e2e8f0;
    --muted:   #64748b;
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stAppViewContainer"] {
    background-image:
        linear-gradient(rgba(0,255,204,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,204,0.03) 1px, transparent 1px);
    background-size: 32px 32px;
}
[data-testid="stHeader"] { background: transparent !important; }
section.main > div { padding-top: 0.5rem !important; }
.pf-header {
    display: flex; align-items: center; gap: 1.5rem;
    padding: 1.2rem 2rem;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.pf-title {
    font-family: 'Press Start 2P', monospace;
    font-size: clamp(0.9rem, 2vw, 1.4rem);
    color: var(--accent);
    text-shadow: 0 0 20px rgba(0,255,204,0.5);
}
.pf-sub { color: var(--muted); font-size: 0.8rem; margin-top: 4px; }
.pf-badge {
    font-size: 0.5rem; padding: 2px 8px;
    background: rgba(0,255,204,0.1); border: 1px solid var(--accent);
    color: var(--accent); border-radius: 2px; margin-left: 10px;
    font-family: 'Press Start 2P', monospace;
}
.pf-card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 4px; padding: 1rem; margin-bottom: 1rem;
}
.pf-card-title {
    font-family: 'Press Start 2P', monospace; font-size: 0.5rem;
    color: var(--accent); letter-spacing: 2px;
    margin-bottom: 0.8rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.result-name {
    font-family: 'Press Start 2P', monospace; font-size: 0.85rem;
    color: var(--accent); text-shadow: 0 0 12px rgba(0,255,204,0.4);
}
.result-tag {
    display: inline-block; padding: 2px 8px;
    background: rgba(168,85,247,0.15); border: 1px solid var(--accent3);
    border-radius: 2px; color: var(--accent3); font-size: 0.72rem; margin: 2px;
}
.result-tag.orange {
    background: rgba(255,107,53,0.15); border-color: var(--accent2); color: var(--accent2);
}
div[data-testid="stButton"] > button {
    background: transparent !important; border: 1px solid var(--accent) !important;
    color: var(--accent) !important; font-family: 'Press Start 2P', monospace !important;
    font-size: 0.5rem !important; border-radius: 2px !important; letter-spacing: 1px;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,255,204,0.1) !important;
    box-shadow: 0 0 12px rgba(0,255,204,0.3) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(0,255,204,0.12) !important;
    box-shadow: 0 0 14px rgba(0,255,204,0.2) !important;
}
div[data-testid="stDownloadButton"] > button {
    background: rgba(168,85,247,0.15) !important;
    border: 1px solid var(--accent3) !important;
    color: var(--accent3) !important;
    font-family: 'Press Start 2P', monospace !important;
    font-size: 0.45rem !important; border-radius: 2px !important;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stNumberInput"] label {
    color: var(--muted) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
}
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: 'Share Tech Mono', monospace !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Press Start 2P', monospace !important;
    font-size: 0.45rem !important; color: var(--muted) !important;
    background: transparent !important; border: none !important;
    padding: 0.6rem 1rem !important; letter-spacing: 1px;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}
div[data-testid="stAlert"] {
    background: rgba(0,255,204,0.04) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important; color: var(--text) !important;
}
div[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important; border-radius: 2px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pf-header">
    <div style="font-size:2.2rem;filter:drop-shadow(0 0 12px rgba(0,255,204,0.6))">⚔️</div>
    <div>
        <div class="pf-title">PIXELFORGE <span class="pf-badge">v1.0</span></div>
        <div class="pf-sub">AI pixel character asset creator → Godot-ready export</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
LIVING_TYPES = {
    "Human":  {"icon": "🧑", "desc": "Humans, warriors, mages, rogues, demi-humans"},
    "Animal": {"icon": "🐺", "desc": "Beast-folk, familiars, mounts, creatures"},
    "Other":  {"icon": "👾", "desc": "Monsters, aliens, plants, mystical beings"},
}

CHARACTER_CLASSES = {
    "Human": {
        "Fantasy":  ["⚔️ Warrior",  "🔮 Mage",     "🗡️ Rogue",    "🛡️ Paladin",
                     "🏹 Ranger",   "✨ Cleric",    "🔥 Warlock",  "📜 Scholar"],
        "Sci-Fi":   ["🤖 Cyborg",   "👨‍🚀 Pilot",    "🔬 Scientist","💻 Hacker",
                     "🪖 Soldier",  "🧬 Bio-Mech",  "⚡ Gunner",   "🕵️ Agent"],
        "Modern":   ["🥊 Fighter",  "🏃 Runner",    "🎭 Performer","🧑‍🍳 Crafter",
                     "🕵️ Detective","🧑‍⚕️ Medic",    "🧑‍🔧 Engineer","🎯 Sniper"],
    },
    "Animal": {
        "Fantasy":  ["🐺 Wolf-folk","🦊 Fox-folk",  "🐉 Dragonkin","🦁 Lion-folk",
                     "🐻 Bear-folk","🦅 Bird-folk",  "🐍 Snake-folk","🦋 Fae-beast"],
        "Sci-Fi":   ["🤖 Mech-beast","🧬 Mutant",   "👾 Alien-pet", "🦾 Cyborg-pet"],
        "Wild":     ["🐯 Hunter",   "🦌 Scout",     "🐗 Berserker", "🦜 Trickster"],
    },
    "Other": {
        "Fantasy":  ["👹 Demon",    "👼 Angel",     "🧟 Undead",   "🧚 Fae",
                     "🌿 Plant",    "🪨 Golem",     "💀 Lich",     "🌊 Elemental"],
        "Sci-Fi":   ["👽 Alien",    "🤖 Android",   "🌌 Cosmic",   "🦠 Parasite",
                     "☢️ Mutant",   "🔮 Psionic",   "🛸 Drone",    "💠 Crystal"],
        "Mystical": ["🐲 Dragon",   "🦄 Unicorn",   "🔱 Titan",    "🌑 Shadow",
                     "⭐ Celestial","🍄 Shroom",    "🌀 Void",     "🕯️ Wraith"],
    },
}

ANIMATIONS   = ["idle", "walk", "run", "jump", "attack", "hurt", "die"]
SPRITE_SIZES = [16, 32, 48, 64, 128]
MODULAR_PARTS = {
    "Human":  ["body", "head", "hair", "eyes", "outfit_top", "outfit_bottom", "boots", "weapon", "accessory"],
    "Animal": ["body", "head", "ears", "tail", "fur_pattern", "outfit", "accessory"],
    "Other":  ["body", "head", "special_feature", "limbs", "outfit", "weapon", "aura"],
}

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in {
    "living_type": None, "char_class": None, "char_genre": "Fantasy",
    "mode": "full", "character_data": None,
    "generated_images": {}, "final_sheet": None, "final_atlas": None,
    "gdscript": None, "selected_anims": [], "fps": 8,
    "seed": random.randint(10000, 99999),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────
def call_groq(system, user, temperature=0.95, max_tokens=2500):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
              "temperature": temperature, "max_tokens": max_tokens},
        timeout=45,
    )
    return r.json()["choices"][0]["message"]["content"]

def parse_json(raw):
    clean = raw.strip()
    if "```" in clean:
        for part in clean.split("```"):
            part = part.strip().lstrip("json").strip()
            try: return json.loads(part)
            except: continue
    return json.loads(clean)

def hex_to_rgba(hex_str, alpha=255):
    h = hex_str.lstrip("#")
    try: return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)
    except: return (100, 100, 200, alpha)

def make_placeholder(size, primary, secondary, living_type="Human"):
    """Draw a detailed RPG-style pixel art character — no blobs, proper anatomy."""
    # Work at 4x then downscale for crisp pixels
    scale  = 4
    w      = size * scale
    img    = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d      = ImageDraw.Draw(img)
    cx     = w // 2
    p      = primary
    s2     = secondary
    skin   = (255, 220, 177, 255)
    dark   = tuple(max(0, c - 60) for c in p[:3]) + (255,)
    dark2  = tuple(max(0, c - 40) for c in s2[:3]) + (255,)
    shadow = (20, 20, 30, 180)
    white  = (255, 255, 255, 255)
    black  = (0, 0, 0, 255)
    
    # ── proportions (all in 4x space) ──
    u      = w // 16   # base unit
    
    head_w = u * 4
    head_h = u * 4
    head_x = cx - head_w // 2
    head_y = u * 1
    
    body_w = u * 4
    body_h = u * 5
    body_x = cx - body_w // 2
    body_y = head_y + head_h + u // 2
    
    leg_w  = u * 2 - u // 4
    leg_h  = u * 5
    leg_y  = body_y + body_h
    
    arm_w  = u * 2
    arm_h  = u * 4
    arm_y  = body_y
    
    foot_w = u * 2
    foot_h = u
    
    if living_type == "Animal":
        # Beast character — stocky body, animal head
        # Body (furry, wider)
        d.rectangle([cx - body_w//2 - u, body_y, cx + body_w//2 + u, body_y + body_h], fill=p)
        d.rectangle([cx - body_w//2 - u + u//2, body_y + u//2,
                     cx + body_w//2 + u - u//2, body_y + body_h - u//2], fill=dark)
        # Head (round)
        d.ellipse([head_x - u//2, head_y, head_x + head_w + u//2, head_y + head_h + u//2], fill=p)
        # Snout
        d.ellipse([cx - u, head_y + head_h//2, cx + u, head_y + head_h + u//2], fill=s2)
        # Ears (pointed)
        d.polygon([(head_x, head_y + u//2), (head_x - u, head_y - u*2), (head_x + u, head_y)], fill=p)
        d.polygon([(head_x + head_w, head_y + u//2), (head_x + head_w + u, head_y - u*2), (head_x + head_w - u, head_y)], fill=p)
        # Eyes
        d.rectangle([cx - u*2, head_y + u, cx - u, head_y + u*2], fill=s2)
        d.rectangle([cx + u, head_y + u, cx + u*2, head_y + u*2], fill=s2)
        d.rectangle([cx - u*2 + u//2, head_y + u + u//4, cx - u - u//4, head_y + u*2 - u//4], fill=black)
        d.rectangle([cx + u + u//4, head_y + u + u//4, cx + u*2 - u//2, head_y + u*2 - u//4], fill=black)
        # Legs
        d.rectangle([cx - body_w//2 - u, leg_y, cx - u//2, leg_y + leg_h - u], fill=p)
        d.rectangle([cx + u//2, leg_y, cx + body_w//2 + u, leg_y + leg_h - u], fill=p)
        # Paws
        d.ellipse([cx - body_w//2 - u - u//2, leg_y + leg_h - u*2, cx, leg_y + leg_h], fill=dark)
        d.ellipse([cx, leg_y + leg_h - u*2, cx + body_w//2 + u + u//2, leg_y + leg_h], fill=dark)
        # Tail
        d.arc([cx + body_w//2, body_y - u, cx + body_w//2 + u*4, body_y + u*4], 0, 200, fill=s2, width=u)

    elif living_type == "Other":
        # Monster/Mystical — asymmetric, otherworldly
        # Wide body
        d.rectangle([cx - body_w - u, body_y, cx + body_w + u, body_y + body_h + u], fill=p)
        # Body shading
        d.rectangle([cx - body_w - u + u//2, body_y + u//2,
                     cx + body_w + u - u//2, body_y + body_h + u - u//2], fill=dark)
        # Big horned head
        d.rectangle([head_x - u//2, head_y, head_x + head_w + u//2, head_y + head_h], fill=p)
        # Horns
        d.polygon([(cx - u*2, head_y), (cx - u*3, head_y - u*3), (cx - u, head_y)], fill=s2)
        d.polygon([(cx + u*2, head_y), (cx + u*3, head_y - u*3), (cx + u, head_y)], fill=s2)
        # Glowing eyes
        d.rectangle([cx - u*2, head_y + u, cx - u//2, head_y + u*2], fill=s2)
        d.rectangle([cx + u//2, head_y + u, cx + u*2, head_y + u*2], fill=s2)
        d.rectangle([cx - u*2 + u//4, head_y + u + u//4, cx - u//2 - u//4, head_y + u*2 - u//4], fill=white)
        d.rectangle([cx + u//2 + u//4, head_y + u + u//4, cx + u*2 - u//4, head_y + u*2 - u//4], fill=white)
        # Fang mouth
        for fx in [cx - u, cx, cx + u//2]:
            d.rectangle([fx, head_y + head_h - u//2, fx + u//2, head_y + head_h + u//2], fill=white)
        # Clawed arms
        d.rectangle([cx - body_w - u - arm_w, arm_y, cx - body_w - u, arm_y + arm_h], fill=dark)
        d.rectangle([cx + body_w + u, arm_y, cx + body_w + u + arm_w, arm_y + arm_h], fill=dark)
        # Claws
        for ci2 in range(3):
            ox = (ci2 - 1) * (u // 2)
            d.rectangle([cx - body_w - u - arm_w//2 + ox - u//4, arm_y + arm_h,
                          cx - body_w - u - arm_w//2 + ox + u//4, arm_y + arm_h + u], fill=s2)
            d.rectangle([cx + body_w + u + arm_w//2 + ox - u//4, arm_y + arm_h,
                          cx + body_w + u + arm_w//2 + ox + u//4, arm_y + arm_h + u], fill=s2)
        # Stubby legs
        d.rectangle([cx - body_w, leg_y, cx - u//2, leg_y + leg_h//2], fill=p)
        d.rectangle([cx + u//2, leg_y, cx + body_w, leg_y + leg_h//2], fill=p)
        # Aura glow effect
        for r_off in range(3, 0, -1):
            alpha = 40 + r_off * 20
            glow = tuple(p[:3]) + (alpha,)
            d.ellipse([cx - body_w - u - r_off*u*2, head_y - r_off*u*2,
                       cx + body_w + u + r_off*u*2, leg_y + leg_h//2 + r_off*u*2], outline=glow, width=u//2)

    else:
        # Humanoid — proper RPG hero proportions
        # ── Shadow ──
        d.ellipse([cx - u*3, leg_y + leg_h, cx + u*3, leg_y + leg_h + u], fill=shadow)

        # ── Boots ──
        d.rectangle([cx - leg_w - u//4, leg_y + leg_h - foot_h, cx - u//4, leg_y + leg_h], fill=dark2)
        d.rectangle([cx + u//4, leg_y + leg_h - foot_h, cx + leg_w + u//4, leg_y + leg_h], fill=dark2)
        # Boot highlight
        d.rectangle([cx - leg_w, leg_y + leg_h - foot_h + u//4, cx - u//2, leg_y + leg_h - u//4], fill=s2)

        # ── Legs / Pants ──
        d.rectangle([cx - leg_w - u//4, leg_y, cx - u//4, leg_y + leg_h - foot_h], fill=dark2)
        d.rectangle([cx + u//4, leg_y, cx + leg_w + u//4, leg_y + leg_h - foot_h], fill=dark2)
        # Pants highlight stripe
        d.rectangle([cx - leg_w + u//4, leg_y + u//4, cx - u//2, leg_y + u], fill=s2)

        # ── Belt ──
        d.rectangle([body_x, body_y + body_h - u, body_x + body_w, body_y + body_h], fill=dark)
        d.rectangle([cx - u//2, body_y + body_h - u, cx + u//2, body_y + body_h], fill=s2)  # buckle

        # ── Body / Torso ──
        d.rectangle([body_x, body_y, body_x + body_w, body_y + body_h - u], fill=p)
        # Chest armor panel
        d.rectangle([body_x + u//2, body_y + u//2, body_x + body_w - u//2, body_y + body_h//2], fill=dark)
        # Collar
        d.rectangle([cx - u, body_y, cx + u, body_y + u], fill=skin)

        # ── Arms ──
        # Left arm
        d.rectangle([body_x - arm_w, arm_y, body_x, arm_y + arm_h], fill=p)
        d.rectangle([body_x - arm_w + u//4, arm_y + u//4, body_x - u//4, arm_y + u], fill=dark)
        # Right arm (weapon hand — slightly forward)
        d.rectangle([body_x + body_w, arm_y, body_x + body_w + arm_w, arm_y + arm_h], fill=p)
        d.rectangle([body_x + body_w + u//4, arm_y + u//4, body_x + body_w + arm_w - u//4, arm_y + u], fill=dark)
        # Gloves/hands
        d.rectangle([body_x - arm_w + u//4, arm_y + arm_h, body_x - u//4, arm_y + arm_h + u], fill=skin)
        d.rectangle([body_x + body_w + u//4, arm_y + arm_h, body_x + body_w + arm_w - u//4, arm_y + arm_h + u], fill=skin)

        # ── Weapon (sword) ──
        sword_x = body_x + body_w + arm_w + u//4
        sword_y = arm_y + arm_h
        d.rectangle([sword_x, sword_y - arm_h, sword_x + u//2, sword_y + u*2], fill=(200, 200, 220, 255))  # blade
        d.rectangle([sword_x - u//2, sword_y - u//2, sword_x + u, sword_y + u//4], fill=s2)  # crossguard
        d.rectangle([sword_x + u//8, sword_y, sword_x + u//2 - u//8, sword_y + u*2], fill=dark2)  # grip

        # ── Neck ──
        d.rectangle([cx - u, head_y + head_h - u//2, cx + u, head_y + head_h + u//2], fill=skin)

        # ── Head ──
        d.rectangle([head_x, head_y, head_x + head_w, head_y + head_h], fill=skin)
        # Helmet / hair
        d.rectangle([head_x - u//4, head_y, head_x + head_w + u//4, head_y + head_h//2], fill=s2)
        # Helmet visor line
        d.rectangle([head_x, head_y + head_h//2 - u//4, head_x + head_w, head_y + head_h//2], fill=dark)
        # Face — eyes
        d.rectangle([cx - u*2 + u//4, head_y + head_h//2 + u//4, cx - u + u//4, head_y + head_h//2 + u], fill=white)
        d.rectangle([cx + u - u//4, head_y + head_h//2 + u//4, cx + u*2 - u//4, head_y + head_h//2 + u], fill=white)
        d.rectangle([cx - u*2 + u//2, head_y + head_h//2 + u//2, cx - u, head_y + head_h//2 + u], fill=(80, 40, 20, 255))  # iris L
        d.rectangle([cx + u, head_y + head_h//2 + u//2, cx + u*2 - u//2, head_y + head_h//2 + u], fill=(80, 40, 20, 255))  # iris R
        # Mouth
        d.rectangle([cx - u//2, head_y + head_h - u, cx + u//2, head_y + head_h - u//2], fill=(180, 100, 80, 255))
        # Hair strands peeking out
        d.rectangle([head_x, head_y + head_h - u//2, head_x + u//2, head_y + head_h + u//4], fill=s2)
        d.rectangle([head_x + head_w - u//2, head_y + head_h - u//2, head_x + head_w, head_y + head_h + u//4], fill=s2)

    # ── Outline pass ──
    outline_img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    for ox2, oy2 in [(-u//4,0),(u//4,0),(0,-u//4),(0,u//4)]:
        shifted = Image.new("RGBA", (w, w), (0, 0, 0, 0))
        shifted.paste(img, (ox2, oy2))
        outline_img = Image.alpha_composite(outline_img, shifted)
    dark_layer = Image.new("RGBA", (w, w), (10, 10, 20, 255))
    mask = outline_img.split()[3]
    final = Image.composite(dark_layer, Image.new("RGBA", (w,w), (0,0,0,0)), mask)
    result = Image.alpha_composite(final, img)
    return result.resize((size, size), Image.NEAREST)
def remove_bg(img: Image.Image) -> Image.Image:
    """
    Remove background using rembg (best) with flood-fill fallback.
    rembg uses U2Net neural net trained specifically for subject extraction.
    """
    # Try rembg first — it handles complex backgrounds properly
    try:
        from rembg import remove as rembg_remove, new_session
        session = new_session("u2net")
        buf_in = io.BytesIO()
        img.convert("RGBA").save(buf_in, format="PNG")
        result = rembg_remove(buf_in.getvalue(), session=session,
                              alpha_matting=True,
                              alpha_matting_foreground_threshold=240,
                              alpha_matting_background_threshold=10)
        out = Image.open(io.BytesIO(result)).convert("RGBA")
        import numpy as np
        # Only accept if at least 3% pixels are visible (not over-removed)
        if (np.array(out)[:,:,3] > 10).sum() > (img.width * img.height * 0.03):
            return out
    except Exception:
        pass

    # Flood-fill fallback — only removes clearly uniform bg colors
    import numpy as np
    img  = img.convert("RGBA")
    arr  = np.array(img, dtype=np.int32)
    rv, gv, bv = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    h, w = rv.shape
    bg   = np.zeros((h, w), dtype=bool)
    vis  = np.zeros((h, w), dtype=bool)

    # Sample corner colors to detect the actual bg color
    corners = [(0,0),(0,w-1),(h-1,0),(h-1,w-1)]
    bg_samples = [(int(rv[y,x]),int(gv[y,x]),int(bv[y,x])) for y,x in corners]
    avg_bg = tuple(sum(c[i] for c in bg_samples)//4 for i in range(3))

    def is_bg(py, px):
        pr,pg,pb = int(rv[py,px]),int(gv[py,px]),int(bv[py,px])
        # Only remove pixels close to the detected bg color
        diff = abs(pr-avg_bg[0]) + abs(pg-avg_bg[1]) + abs(pb-avg_bg[2])
        return diff < 60  # tight threshold

    stack = ([(0,x) for x in range(w)]+[(h-1,x) for x in range(w)]+
             [(y,0) for y in range(h)]+[(y,w-1) for y in range(h)])
    while stack:
        py,px = stack.pop()
        if py<0 or py>=h or px<0 or px>=w or vis[py,px]: continue
        vis[py,px] = True
        if is_bg(py,px):
            bg[py,px] = True
            stack += [(py-1,px),(py+1,px),(py,px-1),(py,px+1)]
    res = np.array(img, dtype=np.uint8)
    res[bg, 3] = 0
    return Image.fromarray(res, "RGBA")


def fetch_frame(prompt: str, size: int, seed: int = 0) -> Image.Image | None:
    """
    Fetch one sprite frame from Pollinations with retry + seed for consistency.
    Seed keeps character appearance consistent across all animation frames.
    """
    import urllib.parse, time
    import numpy as np

    poll_prompt = (
        f"pixel art 16-bit RPG character sprite, {prompt}, "
        f"SNES Chrono Trigger Final Fantasy 6 style, "
        f"black pixel outlines, flat cel shading, limited color palette, "
        f"plain white background, character only, no scenery, no ground"
    )
    encoded = urllib.parse.quote(poll_prompt)

    for attempt in range(3):
        if attempt > 0:
            time.sleep(4)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=512&height=512&nologo=true&model=flux"
            f"&enhance=false&seed={seed}"
        )
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and "image" in r.headers.get("content-type",""):
                raw_bytes = r.content
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                cleaned = remove_bg(img)
                visible = (np.array(cleaned)[:,:,3] > 10).sum()
                if visible > (size * size * 0.04):
                    return cleaned.resize((size, size), Image.NEAREST)
                # rembg removed too much — return without bg removal
                # (better to have background than invisible character)
                return img.resize((size, size), Image.NEAREST)
        except Exception:
            continue
    return None

# Pose descriptions for each animation frame
POSE_DESCRIPTIONS = {
    "idle": [
        "standing upright, neutral relaxed pose, weight on both feet",
        "standing upright, slight inhale, chest slightly expanded",
        "standing upright, neutral relaxed pose, arms slightly lowered",
        "standing upright, slight exhale, shoulders slightly down",
    ],
    "walk": [
        "walking, left foot forward, right arm forward, mid-stride",
        "walking, transferring weight, both feet near ground",
        "walking, right foot forward, left arm forward, mid-stride",
        "walking, transferring weight, pushing off back foot",
    ],
    "run": [
        "running fast, left leg lunging forward, leaning forward, arms pumping",
        "running fast, airborne both feet off ground, body fully extended",
        "running fast, right leg lunging forward, leaning forward, arms pumping",
        "running fast, landing on left foot, knees bent, momentum forward",
    ],
    "jump": [
        "crouching down, knees bent deeply, preparing to jump",
        "launching upward, legs extending, arms raising above head",
        "peak of jump, fully airborne, arms wide, legs slightly tucked",
        "landing, knees absorbing impact, arms out for balance",
    ],
    "attack": [
        "winding up attack, weapon raised behind head, weight shifted back",
        "mid-swing attack, weapon slashing forward with full force",
        "follow-through after attack, weapon extended, body twisted",
        "recovering stance, weapon returning, guard position",
    ],
    "hurt": [
        "recoiling from hit, body jerking backward, face wincing",
        "stumbling from impact, off-balance, one arm guarding face",
        "recovering from hit, hunched slightly, defensive position",
        "regaining footing, still pained, guard raised",
    ],
    "die": [
        "staggering, badly wounded, knees beginning to buckle",
        "falling forward, losing balance completely, arms flailing",
        "hitting the ground, collapsed on knees and elbows",
        "lying collapsed on ground, motionless, face down",
    ],
}


def build_spritesheet_ai(base_prompt: str, char_data: dict, animations: list,
                          fps: int, sprite_size: int, status_callback=None) -> tuple:
    """
    Generate each animation frame as a separate AI image.
    This is the AutoSprite approach — one image per pose per frame.
    """
    import math
    sz      = sprite_size
    frames_per_anim = min(fps, 4)  # 4 unique AI frames per animation, then loop
    sheet   = Image.new("RGBA", (sz * frames_per_anim, sz * len(animations)), (0,0,0,0))
    atlas   = {"frames": {}, "meta": {"size": {"w": sz*frames_per_anim, "h": sz*len(animations)}}}

    char_name = char_data.get("character_name", "character")
    species   = char_data.get("species", "")
    outfit    = char_data.get("outfit", "")
    palette   = char_data.get("color_palette", "")
    art_style = char_data.get("art_style", "pixel art 16-bit RPG")

    # Core character description — stays consistent across all frames
    char_desc = (
        f"{art_style} sprite, {species} character, {outfit}, "
        f"{palette}, side view, full body, "
        f"SNES Chrono Trigger Final Fantasy 6 style, "
        f"clean black pixel outlines, flat cel shading, "
        f"pure white plain background, no scenery"
    )

    p1 = hex_to_rgba(char_data.get("color_primary", "#7c3aed"))
    p2 = hex_to_rgba(char_data.get("color_secondary", "#ff6b35"))

    import time
    # Use a fixed base seed so character looks consistent across frames
    base_seed = abs(hash(char_data.get("character_name", "char"))) % 100000

    for ri, anim in enumerate(animations):
        poses = POSE_DESCRIPTIONS.get(anim, POSE_DESCRIPTIONS["idle"])
        for ci in range(frames_per_anim):
            pose  = poses[ci % len(poses)]
            # Vary seed slightly per frame so poses differ but character stays same
            frame_seed = base_seed + (ri * 100) + ci
            prompt = f"{char_desc}, {pose}"

            if status_callback:
                status_callback(f"  🎨 {anim} frame {ci+1}/{frames_per_anim} (seed {frame_seed})...")

            frame = fetch_frame(prompt, sz, seed=frame_seed)
            if frame is None:
                if status_callback:
                    status_callback(f"  ⚠️ {anim} frame {ci+1} failed — using placeholder")
                frame = make_placeholder(sz, p1, p2, char_data.get("living_type","Human"))
            else:
                if status_callback:
                    status_callback(f"  ✅ {anim} frame {ci+1} — AI image received")

            # Ensure exact size before pasting
            if frame.size != (sz, sz):
                frame = frame.resize((sz, sz), Image.NEAREST)

            # Paste onto transparent background (in case frame has white bg remnants)
            frame_canvas = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            frame_canvas.paste(frame, (0, 0))
            sheet.paste(frame_canvas, (ci * sz, ri * sz))
            key = f"{anim}_{ci:02d}"
            atlas["frames"][key] = {
                "frame": {"x": ci*sz, "y": ri*sz, "w": sz, "h": sz},
                "animation": anim, "frame_index": ci,
            }
            # Small delay between frames to avoid rate limiting
            time.sleep(1)

    return sheet, atlas, frames_per_anim


def build_gdscript(char_name, char_data, animations, sprite_size, fps):
    cn = "".join(w.capitalize() for w in char_name.replace("-"," ").split())
    anim_consts  = "\n".join([f'const ANIM_{a.upper()} = "{a}"' for a in animations])
    anim_list    = ", ".join([f'"{a}"' for a in animations])
    return f'''extends CharacterBody2D
# ═══════════════════════════════════════════════════
#  {char_name}
#  Type: {char_data.get("living_type","?")} | Species: {char_data.get("species","?")}
#  {char_data.get("personality","?")} | {char_data.get("outfit","")}
#  Sprite: {sprite_size}px | FPS: {fps}
#  Generated by PixelForge
# ═══════════════════════════════════════════════════

const SPEED      = 180.0
const RUN_SPEED  = 320.0
const JUMP_FORCE = -420.0

{anim_consts}
const ALL_ANIMS  = [{anim_list}]

@onready var sprite : AnimatedSprite2D = $AnimatedSprite2D
@onready var hitbox : CollisionShape2D = $CollisionShape2D

var current_anim : String = ANIM_IDLE
var is_attacking : bool   = false
var is_hurt      : bool   = false

func _ready() -> void:
    play(ANIM_IDLE)

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity += get_gravity() * delta
    _handle_movement()
    _handle_jump()
    move_and_slide()

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_just_pressed("attack"):
        attack()

func _handle_movement() -> void:
    if is_attacking or is_hurt: return
    var dir     := Input.get_axis("ui_left", "ui_right")
    var running := Input.is_action_pressed("run")
    if dir != 0:
        velocity.x    = dir * (RUN_SPEED if running else SPEED)
        sprite.flip_h = dir < 0
        if is_on_floor():
            play(ANIM_RUN if running else ANIM_WALK)
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED * 2)
        if is_on_floor() and not is_attacking and not is_hurt:
            play(ANIM_IDLE)

func _handle_jump() -> void:
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_FORCE
        play(ANIM_JUMP)

func attack() -> void:
    if is_attacking: return
    is_attacking = true
    play(ANIM_ATTACK)
    await get_tree().create_timer(0.5).timeout
    is_attacking = false
    play(ANIM_IDLE)

func take_damage(amount: int) -> void:
    if is_hurt: return
    is_hurt = true
    play(ANIM_HURT)
    await get_tree().create_timer(0.3).timeout
    is_hurt = false
    play(ANIM_IDLE)

func die() -> void:
    play(ANIM_DIE)
    set_physics_process(false)
    await get_tree().create_timer(1.0).timeout
    queue_free()

func play(anim: String) -> void:
    if current_anim == anim: return
    current_anim = anim
    if sprite.sprite_frames and sprite.sprite_frames.has_animation(anim):
        sprite.play(anim)

# Project > Input Map: add "attack" and "run" actions
'''

def to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def to_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data.encode() if isinstance(data, str) else data)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT — Left (controls) | Right (output)
# ══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1, 1.7], gap="large")

# ── LEFT: Controls ────────────────────────────────────────────────────────────
with left:

    # 01 Living Type + Class + Genre
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 01 — LIVING TYPE</div>', unsafe_allow_html=True)
    tcols = st.columns(3)
    for i, (lt, info) in enumerate(LIVING_TYPES.items()):
        with tcols[i]:
            active = st.session_state.living_type == lt
            if st.button(f"{info['icon']} {lt}", key=f"lt_{lt}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.living_type = lt
                st.session_state.char_class  = None
                st.rerun()

    # Genre selector (Fantasy / Sci-Fi / etc) — shown after type selected
    if st.session_state.living_type:
        lt = st.session_state.living_type
        genres = list(CHARACTER_CLASSES[lt].keys())
        st.write("")
        gcols = st.columns(len(genres))
        for gi, genre in enumerate(genres):
            with gcols[gi]:
                active_g = st.session_state.char_genre == genre
                if st.button(genre, key=f"genre_{genre}", use_container_width=True,
                             type="primary" if active_g else "secondary"):
                    st.session_state.char_genre = genre
                    st.session_state.char_class = None
                    st.rerun()

        # Class buttons
        genre = st.session_state.char_genre
        if genre not in CHARACTER_CLASSES[lt]:
            genre = list(CHARACTER_CLASSES[lt].keys())[0]
            st.session_state.char_genre = genre

        classes = CHARACTER_CLASSES[lt][genre]
        st.write("")
        n_cols = 4
        for row_start in range(0, len(classes), n_cols):
            row_classes = classes[row_start:row_start+n_cols]
            ccols = st.columns(len(row_classes))
            for ci2, cls in enumerate(row_classes):
                with ccols[ci2]:
                    active_c = st.session_state.char_class == cls
                    if st.button(cls, key=f"cls_{cls}", use_container_width=True,
                                 type="primary" if active_c else "secondary"):
                        st.session_state.char_class = cls
                        st.rerun()
        if st.session_state.char_class:
            st.caption(f"▸ {st.session_state.char_genre} {lt} — {st.session_state.char_class}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 02 Gender
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 02 — GENDER</div>', unsafe_allow_html=True)
    gender = st.radio("Gender", ["Male", "Female", "Non-binary"], horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # 03 Mode
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 03 — MODE</div>', unsafe_allow_html=True)
    mc = st.columns(2)
    with mc[0]:
        if st.button("⚡ FULL CHARACTER", use_container_width=True,
                     type="primary" if st.session_state.mode == "full" else "secondary"):
            st.session_state.mode = "full"; st.rerun()
    with mc[1]:
        if st.button("🧩 MODULAR PARTS", use_container_width=True,
                     type="primary" if st.session_state.mode == "modular" else "secondary"):
            st.session_state.mode = "modular"; st.rerun()
    st.caption("▸ Full: one complete character | Modular: separate parts you can mix")
    st.markdown('</div>', unsafe_allow_html=True)

    # 04 Sprite Settings
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 04 — SPRITE SETTINGS</div>', unsafe_allow_html=True)
    sprite_size = st.select_slider("Sprite Size (px)", options=SPRITE_SIZES, value=64)
    fps         = st.slider("Animation FPS", 4, 24, 8)
    sel_anims   = st.multiselect("Animations", ANIMATIONS, default=["idle","walk","run","jump","attack"])
    st.markdown('</div>', unsafe_allow_html=True)

    # 05 Style hint
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 05 — STYLE HINT (OPTIONAL)</div>', unsafe_allow_html=True)
    hint = st.text_area("Style Hint", placeholder="e.g. dark fire mage with glowing eyes, carries a tome...",
                        height=70, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # Seed
    sc, rc = st.columns([4, 1])
    with sc:
        seed = st.number_input("Seed", value=st.session_state.seed, min_value=0, max_value=999999)
        st.session_state.seed = seed
    with rc:
        st.write(""); st.write("")
        if st.button("🎲", use_container_width=True):
            st.session_state.seed = random.randint(10000, 99999); st.rerun()

    st.write("")

    can_go = bool(st.session_state.living_type and sel_anims)

    if st.button("⚡ FORGE CHARACTER", use_container_width=True, type="primary", disabled=not can_go):
        if not GROQ_KEY:
            st.error("GROQ_API_KEY missing — add it in Streamlit Cloud → Settings → Secrets")
            st.stop()
        lt   = st.session_state.living_type
        mode = st.session_state.mode

        with st.status("⚡ Forging...", expanded=True) as status:

            # Step 1 — AI designs character
            st.write("🤖 AI designing character...")
            char_class = st.session_state.char_class or ""
            char_genre  = st.session_state.char_genre or "Fantasy"
            class_desc  = f"{char_genre} {lt} — {char_class}" if char_class else f"{char_genre} {lt}"
            sys_p = f"""You are an expert pixel art RPG character designer.
Design a unique {class_desc} character. Be specific and creative.
{"User hint: " + hint.strip() if hint.strip() else "Full randomization — be unexpected."}
Return ONLY valid JSON, no markdown:
{{
  "character_name": "string",
  "living_type": "{lt}",
  "gender": "{gender}",
  "species": "string (specific, e.g. 'shadow elf' not just 'elf')",
  "art_style": "string (e.g. 'retro 16-bit RPG', 'dark chibi pixel')",
  "body_type": "string",
  "outfit": "string (detailed)",
  "color_primary": "hex color string e.g. #3a7bd5",
  "color_secondary": "hex color string e.g. #ff6b35",
  "color_palette": "string description",
  "personality": "string",
  "weapon_or_item": "string",
  "special_ability": "string",
  "backstory": "string (2 vivid sentences)",
  "image_prompt": "string (5-6 sentence pixel art generation prompt with colors, outfit, pose, style)",
  "modular_parts": {{
    "body": "pixel art body description",
    "head": "pixel art head/face description",
    "hair_or_feature": "hair or special head feature",
    "outfit_top": "upper body detail",
    "outfit_bottom": "lower body detail",
    "weapon": "weapon/item description",
    "special": "wings, tail, aura, markings, etc"
  }}
}}"""
            usr_p = f"Living type: {lt}\nGenre: {char_genre}\nClass: {char_class or 'random'}\nGender: {gender}\nSeed: {st.session_state.seed}"

            try:
                raw  = call_groq(sys_p, usr_p, temperature=1.0, max_tokens=2500)
                data = parse_json(raw)
                st.session_state.character_data = data
                st.write(f"✅ Conceived: **{data.get('character_name','?')}**")
            except Exception as e:
                status.update(label="❌ AI failed", state="error")
                st.error(str(e)); st.stop()

            # Colors
            p1 = hex_to_rgba(data.get("color_primary",  "#7c3aed"))
            p2 = hex_to_rgba(data.get("color_secondary", "#ff6b35"))

            total_frames = len(sel_anims) * 4  # 4 AI frames per animation
            st.write(f"🎨 Generating {total_frames} animation frames via AI (this takes a few minutes)...")
            st.write("Each frame is a unique AI-generated pose — like AutoSprite.")

            # Generate full spritesheet with one AI image per frame
            def status_cb(msg):
                st.write(msg)

            sheet, atlas, frames_per_anim = build_spritesheet_ai(
                base_prompt    = data.get("image_prompt", ""),
                char_data      = data,
                animations     = sel_anims,
                fps            = fps,
                sprite_size    = sprite_size,
                status_callback= status_cb,
            )

            st.session_state.final_sheet    = sheet
            st.session_state.final_atlas    = atlas
            st.session_state.selected_anims = sel_anims
            st.session_state.fps            = frames_per_anim

            # Save a preview frame (first idle frame)
            preview = sheet.crop((0, 0, sprite_size, sprite_size))
            st.session_state.generated_images = {"full": preview}

            # GDScript
            st.write("🎮 Writing GDScript...")
            gd = build_gdscript(data["character_name"], data, sel_anims, sprite_size, frames_per_anim)
            st.session_state.gdscript = gd

            status.update(label="✅ Character forged!", state="complete", expanded=False)
            st.rerun()

# ── RIGHT: Output ──────────────────────────────────────────────────────────────
with right:
    if not st.session_state.character_data:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    height:520px;border:1px dashed #2a2a40;border-radius:4px;gap:1.5rem;">
            <div style="font-size:5rem;filter:drop-shadow(0 0 24px rgba(0,255,204,0.3))">⚔️</div>
            <div style="font-family:'Press Start 2P',monospace;font-size:0.55rem;color:#2a2a40;
                        text-align:center;line-height:2.5">
                01 · PICK LIVING TYPE<br>
                02 · CHOOSE GENDER<br>
                03 · SELECT MODE<br>
                04 · HIT FORGE
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        d  = st.session_state.character_data
        cn = d.get("character_name", "Unknown")

        st.markdown(f'<div class="result-name">{cn}</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin:8px 0 14px">
            <span class="result-tag">{d.get('species','?')}</span>
            <span class="result-tag">{d.get('living_type','?')}</span>
            <span class="result-tag">{d.get('gender','?')}</span>
            <span class="result-tag orange">{d.get('art_style','?')}</span>
            <span class="result-tag orange">{d.get('personality','?')}</span>
        </div>
        <div style="color:#94a3b8;font-style:italic;font-size:0.82rem;margin-bottom:1rem">
            {d.get('backstory','')}
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["🖼️ PREVIEW", "🧩 PARTS", "📋 SPRITESHEET", "🎮 GODOT"])

        # ── Preview ────────────────────────────────────────────────────────────
        with t1:
            if "full" in st.session_state.generated_images:
                img     = st.session_state.generated_images["full"]
                sz      = img.width
                anims   = st.session_state.get("selected_anims", ["idle"])
                fps_val = st.session_state.get("fps", 8)
                sheet   = st.session_state.final_sheet
                p1h     = d.get("color_primary", "#00ffcc")
                p2h     = d.get("color_secondary", "#ff6b35")

                prev_col, info_col = st.columns([1, 1])

                with prev_col:
                    # Build animated preview HTML from spritesheet frames
                    if sheet and anims:
                        # Extract all frames for all animations as base64
                        frames_b64 = {}
                        for ri, anim in enumerate(anims):
                            frames_b64[anim] = []
                            for ci2 in range(fps_val):
                                x = ci2 * sz
                                y = ri * sz
                                frame = sheet.crop((x, y, x + sz, y + sz))
                                # Scale up for display
                                disp_sz = min(sz * 6, 384)
                                frame_disp = frame.resize((disp_sz, disp_sz), Image.NEAREST)
                                # Add dark bg
                                bg_f = Image.new("RGBA", (disp_sz, disp_sz), (13, 13, 26, 255))
                                bg_f.paste(frame_disp, (0, 0), frame_disp)
                                buf = io.BytesIO()
                                bg_f.save(buf, format="PNG")
                                frames_b64[anim].append(base64.b64encode(buf.getvalue()).decode())

                        # Build frames JSON for JS
                        import json as _json
                        frames_json = _json.dumps(frames_b64)
                        anims_json  = _json.dumps(anims)
                        fps_json    = fps_val

                        preview_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a0f; font-family:'Courier New',monospace; color:#e2e8f0; }}
  #viewer {{
    display:flex; flex-direction:column; align-items:center;
    gap:12px; padding:16px;
  }}
  #canvas-wrap {{
    position:relative;
    background: repeating-conic-gradient(#1a1a28 0% 25%, #12121a 0% 50%) 0 0 / 16px 16px;
    border:2px solid #2a2a40; border-radius:4px;
    display:flex; align-items:center; justify-content:center;
    width:200px; height:200px;
  }}
  #sprite {{ image-rendering:pixelated; width:180px; height:180px; }}
  #controls {{
    display:flex; flex-direction:column; align-items:center; gap:8px; width:100%;
  }}
  #anim-btns {{
    display:flex; flex-wrap:wrap; gap:4px; justify-content:center;
  }}
  .anim-btn {{
    padding:3px 10px;
    background:#1a1a28; border:1px solid #2a2a40;
    color:#64748b; font-size:10px; font-family:'Courier New',monospace;
    cursor:pointer; border-radius:2px; letter-spacing:1px;
    text-transform:uppercase;
  }}
  .anim-btn.active {{
    border-color:#00ffcc; color:#00ffcc;
    background:rgba(0,255,204,0.08);
    box-shadow:0 0 6px rgba(0,255,204,0.2);
  }}
  #playbar {{
    display:flex; align-items:center; gap:8px;
  }}
  .ctrl-btn {{
    width:30px; height:30px;
    background:#1a1a28; border:1px solid #2a2a40;
    color:#00ffcc; font-size:14px; cursor:pointer;
    border-radius:2px; display:flex; align-items:center; justify-content:center;
  }}
  .ctrl-btn:hover {{ background:rgba(0,255,204,0.1); }}
  #fps-label {{ font-size:10px; color:#64748b; }}
  #frame-counter {{ font-size:10px; color:#2a2a40; }}
  input[type=range] {{
    -webkit-appearance:none; width:80px; height:3px;
    background:#2a2a40; border-radius:2px; outline:none;
  }}
  input[type=range]::-webkit-slider-thumb {{
    -webkit-appearance:none; width:12px; height:12px;
    background:#00ffcc; border-radius:0; cursor:pointer;
  }}
  #scale-btns {{ display:flex; gap:4px; }}
  .scale-btn {{
    padding:2px 6px; background:#1a1a28; border:1px solid #2a2a40;
    color:#64748b; font-size:9px; cursor:pointer; border-radius:2px;
  }}
  .scale-btn.active {{ border-color:#a855f7; color:#a855f7; }}
</style>
</head>
<body>
<div id="viewer">
  <div id="canvas-wrap">
    <img id="sprite" src="" alt="sprite"/>
  </div>
  <div id="controls">
    <div id="anim-btns"></div>
    <div id="playbar">
      <button class="ctrl-btn" id="prev-btn">&#9664;</button>
      <button class="ctrl-btn" id="play-btn">&#9646;&#9646;</button>
      <button class="ctrl-btn" id="next-btn">&#9654;</button>
      <span id="fps-label">FPS:</span>
      <input type="range" id="fps-slider" min="1" max="24" value="{fps_json}"/>
      <span id="fps-val">{fps_json}</span>
      <span id="frame-counter">0/0</span>
    </div>
    <div id="scale-btns">
      <button class="scale-btn" data-scale="1">1x</button>
      <button class="scale-btn active" data-scale="2">2x</button>
      <button class="scale-btn" data-scale="3">3x</button>
      <button class="scale-btn" data-scale="4">4x</button>
    </div>
  </div>
</div>
<script>
const ALL_FRAMES = {frames_json};
const ANIM_LIST  = {anims_json};

let currentAnim  = ANIM_LIST[0];
let currentFrame = 0;
let playing      = true;
let fps          = {fps_json};
let scale        = 2;
let timer        = null;

const spriteEl   = document.getElementById("sprite");
const playBtn    = document.getElementById("play-btn");
const counter    = document.getElementById("frame-counter");
const fpsSlider  = document.getElementById("fps-slider");
const fpsVal     = document.getElementById("fps-val");
const animBtns   = document.getElementById("anim-btns");
const canvasWrap = document.getElementById("canvas-wrap");

// Build animation buttons
ANIM_LIST.forEach(anim => {{
  const btn = document.createElement("button");
  btn.className = "anim-btn" + (anim === currentAnim ? " active" : "");
  btn.textContent = anim;
  btn.onclick = () => {{
    currentAnim = anim;
    currentFrame = 0;
    document.querySelectorAll(".anim-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    showFrame();
  }};
  animBtns.appendChild(btn);
}});

// Scale buttons
document.querySelectorAll(".scale-btn").forEach(btn => {{
  btn.onclick = () => {{
    scale = parseInt(btn.dataset.scale);
    document.querySelectorAll(".scale-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const s = Math.min(scale * 64, 180);
    spriteEl.style.width = s + "px";
    spriteEl.style.height = s + "px";
  }};
}});

function showFrame() {{
  const frames = ALL_FRAMES[currentAnim] || [];
  if (!frames.length) return;
  spriteEl.src = "data:image/png;base64," + frames[currentFrame % frames.length];
  counter.textContent = (currentFrame + 1) + "/" + frames.length;
}}

function nextFrame() {{
  const frames = ALL_FRAMES[currentAnim] || [];
  currentFrame = (currentFrame + 1) % Math.max(frames.length, 1);
  showFrame();
}}

function startPlay() {{
  if (timer) clearInterval(timer);
  timer = setInterval(nextFrame, 1000 / fps);
}}

function stopPlay() {{
  if (timer) {{ clearInterval(timer); timer = null; }}
}}

playBtn.onclick = () => {{
  playing = !playing;
  playBtn.innerHTML = playing ? "&#9646;&#9646;" : "&#9654;";
  playing ? startPlay() : stopPlay();
}};

document.getElementById("prev-btn").onclick = () => {{
  const frames = ALL_FRAMES[currentAnim] || [];
  currentFrame = (currentFrame - 1 + frames.length) % Math.max(frames.length, 1);
  showFrame();
}};

document.getElementById("next-btn").onclick = () => {{ nextFrame(); }};

fpsSlider.oninput = () => {{
  fps = parseInt(fpsSlider.value);
  fpsVal.textContent = fps;
  if (playing) startPlay();
}};

// Init
showFrame();
if (playing) startPlay();
</script>
</body>
</html>"""
                        st.components.v1.html(preview_html, height=380, scrolling=False)
                    else:
                        # Static fallback
                        disp_sz = min(sz * 6, 384)
                        display_img = img.resize((disp_sz, disp_sz), Image.NEAREST)
                        bg = Image.new("RGBA", (disp_sz, disp_sz), (13, 13, 26, 255))
                        bg.paste(display_img, (0,0), display_img)
                        st.image(bg, caption=f"{cn} — {sz}×{sz}px", width="stretch")

                with info_col:
                    st.markdown(f"""
                    <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
                        <div style="width:28px;height:28px;background:{p1h};border:1px solid #444;border-radius:2px"></div>
                        <div style="width:28px;height:28px;background:{p2h};border:1px solid #444;border-radius:2px"></div>
                        <span style="color:#64748b;font-size:0.72rem">{p1h} · {p2h}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    for label, key in [
                        ("Species",  "species"), ("Outfit",   "outfit"),
                        ("Weapon",   "weapon_or_item"), ("Ability",  "special_ability"),
                        ("Palette",  "color_palette"),
                    ]:
                        st.markdown(f"**{label}:** {d.get(key,'—')}")

                    st.write("")
                    st.caption("🎮 Animation controls: pick animation row, play/pause, step frame by frame, adjust FPS and scale")

                st.download_button("⬇️ DOWNLOAD SPRITE PNG", to_bytes(img),
                                   f"{cn.replace(' ','_')}_sprite.png", "image/png",
                                   use_container_width=True)

        # ── Parts ──────────────────────────────────────────────────────────────
        with t2:
            parts = {k: v for k, v in st.session_state.generated_images.items() if k != "full"}
            if not parts:
                st.info("Switch to **🧩 MODULAR PARTS** mode and forge again to generate individual parts.")
            else:
                sz   = list(parts.values())[0].width
                disp = min(sz * 5, 200)
                pl   = list(parts.items())
                for row in range(0, len(pl), 3):
                    cols = st.columns(3)
                    for ci, (pname, pimg) in enumerate(pl[row:row+3]):
                        with cols[ci]:
                            bg = Image.new("RGBA", (disp, disp), (13,13,26,255))
                            d_img = pimg.resize((disp, disp), Image.NEAREST)
                            bg.paste(d_img, (0,0), d_img)
                            st.image(bg, caption=pname, width="stretch")
                            st.download_button(f"⬇️ {pname}", to_bytes(pimg),
                                               f"{cn.replace(' ','_')}_{pname}.png", "image/png",
                                               key=f"dl_{pname}", use_container_width=True)

        # ── Spritesheet ────────────────────────────────────────────────────────
        with t3:
            if st.session_state.final_sheet:
                sheet   = st.session_state.final_sheet
                atlas   = st.session_state.final_atlas
                anims   = st.session_state.selected_anims
                fps_val = st.session_state.fps

                st.caption(f"{len(anims)} anims × {fps_val} frames = {len(anims)*fps_val} frames | {sheet.width}×{sheet.height}px")

                scale = max(1, min(4, 600 // sheet.width))
                ds    = sheet.resize((sheet.width*scale, sheet.height*scale), Image.NEAREST)
                bg    = Image.new("RGBA", ds.size, (13,13,26,255))
                bg.paste(ds, (0,0), ds)
                st.image(bg, caption="Full spritesheet", width="stretch")

                st.markdown("**Rows:** " + " ".join([
                    f'<span class="result-tag">{i}: {a}</span>' for i,a in enumerate(anims)
                ]), unsafe_allow_html=True)

                dc1, dc2 = st.columns(2)
                with dc1:
                    st.download_button("⬇️ SPRITESHEET PNG", to_bytes(sheet),
                                       f"{cn.replace(' ','_')}_sheet.png", "image/png",
                                       use_container_width=True)
                with dc2:
                    st.download_button("⬇️ ATLAS JSON", json.dumps(atlas, indent=2),
                                       f"{cn.replace(' ','_')}_atlas.json", "application/json",
                                       use_container_width=True)

        # ── Godot ──────────────────────────────────────────────────────────────
        with t4:
            if st.session_state.gdscript:
                gd   = st.session_state.gdscript
                anims = st.session_state.selected_anims
                sz    = sprite_size if 'sprite_size' in dir() else 64
                clsnm = "".join(w.capitalize() for w in cn.replace("-"," ").split())

                with st.expander("📄 View GDScript", expanded=False):
                    st.code(gd, language="gdscript")

                readme = f"""PixelForge Export — {cn}
{'='*40}
1. Copy this folder → res://characters/{clsnm}/
2. Godot: Create CharacterBody2D scene
3. Add child: AnimatedSprite2D
4. Add child: CollisionShape2D
5. Attach {clsnm}.gd as the script
6. SpriteFrames editor → import PNG sheet
7. Map animation rows:
{chr(10).join([f"   Row {i}: {a}" for i,a in enumerate(anims)])}
8. Set FPS: {st.session_state.fps}
9. Project > Input Map → add "attack" + "run"
{'='*40}
"""
                zip_files = {
                    f"{clsnm}.gd": gd,
                    f"{cn.replace(' ','_')}_sheet.png": to_bytes(st.session_state.final_sheet),
                    f"{cn.replace(' ','_')}_atlas.json": json.dumps(atlas, indent=2),
                    "README.txt": readme,
                }
                if parts := {k:v for k,v in st.session_state.generated_images.items() if k!="full"}:
                    for pn, pi in parts.items():
                        zip_files[f"parts/{cn.replace(' ','_')}_{pn}.png"] = to_bytes(pi)

                st.download_button(
                    "⬇️ DOWNLOAD FULL GODOT PACKAGE (.ZIP)",
                    to_zip(zip_files),
                    f"{clsnm}_PixelForge.zip", "application/zip",
                    use_container_width=True,
                )

                st.code(f"""res://characters/{clsnm}/
├── {clsnm}.gd
├── {cn.replace(' ','_')}_sheet.png
├── {cn.replace(' ','_')}_atlas.json
├── README.txt
└── parts/  ← individual part PNGs (modular mode)""", language="bash")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;
            color:#1e1e30;font-size:0.55rem;font-family:'Press Start 2P',monospace;letter-spacing:2px">
    PIXELFORGE · GROQ + HUGGING FACE · GODOT READY
</div>
""", unsafe_allow_html=True)
