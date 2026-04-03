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
ANIMATIONS   = ["idle", "walk", "run", "jump", "attack", "hurt", "die"]
SPRITE_SIZES = [16, 32, 48, 64, 128]
MODULAR_PARTS = {
    "Human":  ["body", "head", "hair", "eyes", "outfit_top", "outfit_bottom", "boots", "weapon", "accessory"],
    "Animal": ["body", "head", "ears", "tail", "fur_pattern", "outfit", "accessory"],
    "Other":  ["body", "head", "special_feature", "limbs", "outfit", "weapon", "aura"],
}

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in {
    "living_type": None, "mode": "full", "character_data": None,
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
    """Draw a pixel art placeholder matching the character's colors and type."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    s   = size
    cx  = s // 2

    if living_type == "Animal":
        # Round body beast
        bw = max(4, s // 3)
        bh = max(4, s // 4)
        by = s // 3
        d.ellipse([cx - bw, by, cx + bw, by + bh * 2], fill=primary)
        # Head
        hw = max(3, s // 5)
        d.ellipse([cx - hw, by - hw, cx + hw, by + hw], fill=primary)
        # Ears
        d.rectangle([cx - hw, by - hw - max(2, s//8), cx - hw//2, by - hw], fill=secondary)
        d.rectangle([cx + hw//2, by - hw - max(2, s//8), cx + hw, by - hw], fill=secondary)
        # Eyes
        ey = by - hw//3
        d.rectangle([cx - hw//2, ey, cx - hw//4, ey + max(1,s//16)], fill=(0,0,0,255))
        d.rectangle([cx + hw//4, ey, cx + hw//2, ey + max(1,s//16)], fill=(0,0,0,255))
        # Tail
        d.rectangle([cx + bw - max(1,s//8), by + bh, cx + bw + max(2,s//6), by + bh * 2], fill=secondary)
        # Legs
        lh = max(3, s // 5)
        d.rectangle([cx - bw//2 - max(1,s//8), by + bh * 2, cx - max(1,s//8), by + bh * 2 + lh], fill=primary)
        d.rectangle([cx + max(1,s//8), by + bh * 2, cx + bw//2 + max(1,s//8), by + bh * 2 + lh], fill=primary)

    elif living_type == "Other":
        # Blobby monster
        bw = max(4, s // 3)
        bh = max(5, s // 2)
        by = s // 4
        d.ellipse([cx - bw, by, cx + bw, by + bh], fill=primary)
        # Spikes / horns
        for ox in [-bw//2, 0, bw//2]:
            d.polygon([
                (cx + ox, by - max(3, s//6)),
                (cx + ox - max(2, s//8), by),
                (cx + ox + max(2, s//8), by),
            ], fill=secondary)
        # Eyes (glowing)
        ey = by + bh // 3
        ew = max(2, s // 8)
        d.ellipse([cx - ew*2, ey, cx - ew, ey + ew], fill=secondary)
        d.ellipse([cx + ew, ey, cx + ew*2, ey + ew], fill=secondary)
        # Mouth
        my = by + bh * 2 // 3
        d.rectangle([cx - ew*2, my, cx + ew*2, my + max(1, s//12)], fill=(0,0,0,255))
        # Tentacle legs
        for ox in [-bw//2, 0, bw//2]:
            d.rectangle([cx + ox - max(1,s//16), by + bh, cx + ox + max(1,s//16), by + bh + max(3,s//5)], fill=primary)

    else:
        # Humanoid (default)
        head_s = max(4, s // 5)
        body_h = max(5, s // 3)
        leg_h  = max(3, s // 4)
        top    = s // 10
        # Head
        d.rectangle([cx - head_s//2, top, cx + head_s//2, top + head_s], fill=primary)
        # Body
        bt = top + head_s + 1
        d.rectangle([cx - head_s//2 - 1, bt, cx + head_s//2 + 1, bt + body_h], fill=secondary)
        # Arms
        d.rectangle([cx - head_s - max(1,s//8), bt, cx - head_s//2 - 1, bt + body_h - max(2,s//8)], fill=primary)
        d.rectangle([cx + head_s//2 + 1, bt, cx + head_s + max(1,s//8), bt + body_h - max(2,s//8)], fill=primary)
        # Legs
        lt = bt + body_h + 1
        d.rectangle([cx - head_s//2, lt, cx - 1, lt + leg_h], fill=secondary)
        d.rectangle([cx + 1, lt, cx + head_s//2, lt + leg_h], fill=primary)
        # Eyes
        ey  = top + head_s // 3
        ec  = (0, 0, 0, 255)
        epx = max(1, s // 20)
        d.rectangle([cx - head_s//3, ey, cx - head_s//3 + epx, ey + epx], fill=ec)
        d.rectangle([cx + head_s//3 - epx, ey, cx + head_s//3, ey + epx], fill=ec)

    return img

def hf_generate(prompt, size=512):
    model = "nerijs/pixel-art-xl"
    full  = f"pixel art sprite, {prompt}, {size}x{size}, game asset, crisp pixels, no blur, transparent background"
    headers = {"Authorization": f"Bearer {HF_KEY}"} if HF_KEY else {}
    try:
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers=headers,
            json={"inputs": full, "parameters": {"width": min(size*2,512), "height": min(size*2,512)}},
            timeout=60,
        )
        if r.status_code == 200 and "image" in r.headers.get("content-type",""):
            img = Image.open(io.BytesIO(r.content)).convert("RGBA")
            return img.resize((size, size), Image.NEAREST)
    except:
        pass
    return None

def build_spritesheet(base_img, animations, fps=8):
    sz     = base_img.width
    cols   = fps
    rows   = len(animations)
    sheet  = Image.new("RGBA", (sz * cols, sz * rows), (0,0,0,0))
    atlas  = {"frames": {}, "meta": {"size": {"w": sz*cols, "h": sz*rows}}}
    for ri, anim in enumerate(animations):
        for ci in range(cols):
            oy = 1 if (anim == "idle" and ci % 2 == 0) else \
                (1 if (anim in ("walk","run") and ci % 2 == 0) else
                (-1 if (anim in ("walk","run") and ci % 2 == 1) else 0))
            frame = Image.new("RGBA", (sz, sz), (0,0,0,0))
            paste_y = max(0, min(oy, sz - base_img.height))
            frame.paste(base_img, (0, paste_y), base_img)
            sheet.paste(frame, (ci * sz, ri * sz))
            key = f"{anim}_{ci:02d}"
            atlas["frames"][key] = {
                "frame": {"x": ci*sz, "y": ri*sz, "w": sz, "h": sz},
                "animation": anim, "frame_index": ci,
            }
    return sheet, atlas

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

    # 01 Living Type
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 01 — LIVING TYPE</div>', unsafe_allow_html=True)
    tcols = st.columns(3)
    for i, (lt, info) in enumerate(LIVING_TYPES.items()):
        with tcols[i]:
            active = st.session_state.living_type == lt
            if st.button(f"{info['icon']} {lt}", key=f"lt_{lt}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.living_type = lt
                st.rerun()
    if st.session_state.living_type:
        st.caption(f"▸ {LIVING_TYPES[st.session_state.living_type]['desc']}")
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

    if not GROQ_KEY:
        st.warning("Add GROQ_API_KEY to .streamlit/secrets.toml")
        if not HF_KEY:
            st.caption("Add HF_API_KEY for real images (optional — placeholders work without it)")

    can_go = bool(st.session_state.living_type and sel_anims and GROQ_KEY)

    if st.button("⚡ FORGE CHARACTER", use_container_width=True, type="primary", disabled=not can_go):
        lt   = st.session_state.living_type
        mode = st.session_state.mode

        with st.status("⚡ Forging...", expanded=True) as status:

            # Step 1 — AI designs character
            st.write("🤖 AI designing character...")
            sys_p = f"""You are an expert pixel art RPG character designer.
Design a unique {lt.lower()} character. Be specific and creative.
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
            usr_p = f"Living type: {lt}\nGender: {gender}\nSeed: {st.session_state.seed}"

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

            # Step 2 — Images
            gen_size = max(sprite_size * 4, 256)
            imgs = {}

            if mode == "full":
                st.write(f"🎨 Generating sprite ({sprite_size}px)...")
                img = hf_generate(data.get("image_prompt","pixel art character"), size=gen_size)
                if img is None:
                    st.write("⚠️ HF unavailable — using pixel placeholder (add HF_API_KEY for real images)")
                    img = make_placeholder(sprite_size, p1, p2, lt)
                else:
                    img = img.resize((sprite_size, sprite_size), Image.NEAREST)
                imgs["full"] = img

            else:  # modular
                parts = MODULAR_PARTS.get(lt, MODULAR_PARTS["Human"])
                modular = data.get("modular_parts", {})
                part_size = max(sprite_size * 4, 128)
                composite = Image.new("RGBA", (sprite_size, sprite_size), (0,0,0,0))

                for part in parts:
                    st.write(f"  ▸ {part}...")
                    pdesc  = modular.get(part, f"{part} for {data.get('species','character')}")
                    pprmt  = f"{data.get('art_style','pixel art')} {pdesc}, {data.get('color_palette','')}"
                    pimg   = hf_generate(pprmt, size=part_size)
                    if pimg is None:
                        pimg = make_placeholder(sprite_size, p1, p2, lt)
                    else:
                        pimg = pimg.resize((sprite_size, sprite_size), Image.NEAREST)
                    imgs[part] = pimg
                    composite  = Image.alpha_composite(composite, pimg)

                imgs["full"] = composite

            st.session_state.generated_images = imgs

            # Step 3 — Spritesheet
            st.write("📋 Building spritesheet...")
            sheet, atlas = build_spritesheet(imgs["full"], sel_anims, fps)
            st.session_state.final_sheet   = sheet
            st.session_state.final_atlas   = atlas
            st.session_state.selected_anims = sel_anims
            st.session_state.fps            = fps

            # Step 4 — GDScript
            st.write("🎮 Writing GDScript...")
            gd = build_gdscript(data["character_name"], data, sel_anims, sprite_size, fps)
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
                img  = st.session_state.generated_images["full"]
                sz   = img.width
                disp = min(sz * 8, 480)
                display_img = img.resize((disp, disp), Image.NEAREST)

                ci, cs = st.columns([1, 1])
                with ci:
                    # Dark bg for visibility
                    bg = Image.new("RGBA", (disp, disp), (13, 13, 26, 255))
                    bg.paste(display_img, (0,0), display_img)
                    st.image(bg, caption=f"{cn} — {sz}×{sz}px sprite", use_container_width=True)

                with cs:
                    p1h = d.get("color_primary", "#00ffcc")
                    p2h = d.get("color_secondary", "#ff6b35")
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
                            st.image(bg, caption=pname, use_container_width=True)
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
                st.image(bg, caption="Full spritesheet", use_container_width=True)

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
