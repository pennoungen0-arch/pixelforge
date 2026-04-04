import streamlit as st
import requests
import json
import random
import io
import base64
import zipfile
import math
import time
import threading
import urllib.parse
from PIL import Image, ImageDraw
import numpy as np

st.set_page_config(
    page_title="PixelForge",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Keys ──────────────────────────────────────────────────────────────────────
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
HF_KEY   = st.secrets.get("HF_API_KEY", "")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Share+Tech+Mono&display=swap');
:root {
    --bg:#0a0a0f; --surface:#12121a; --panel:#1a1a28;
    --border:#2a2a40; --accent:#00ffcc; --accent2:#ff6b35;
    --accent3:#a855f7; --text:#e2e8f0; --muted:#64748b;
}
html,body,[data-testid="stAppViewContainer"]{
    background:var(--bg)!important; color:var(--text)!important;
    font-family:'Share Tech Mono',monospace!important;
}
[data-testid="stAppViewContainer"]{
    background-image:linear-gradient(rgba(0,255,204,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,204,.03) 1px,transparent 1px);
    background-size:32px 32px;
}
[data-testid="stHeader"]{background:transparent!important;}
section.main>div{padding-top:.5rem!important;}
.pf-header{display:flex;align-items:center;gap:1.5rem;padding:1.2rem 2rem;
    background:var(--surface);border-bottom:1px solid var(--border);margin-bottom:1.5rem;}
.pf-title{font-family:'Press Start 2P',monospace;font-size:clamp(.9rem,2vw,1.4rem);
    color:var(--accent);text-shadow:0 0 20px rgba(0,255,204,.5);}
.pf-sub{color:var(--muted);font-size:.8rem;margin-top:4px;}
.pf-badge{font-size:.5rem;padding:2px 8px;background:rgba(0,255,204,.1);
    border:1px solid var(--accent);color:var(--accent);border-radius:2px;
    margin-left:10px;font-family:'Press Start 2P',monospace;}
.pf-card{background:var(--panel);border:1px solid var(--border);
    border-radius:4px;padding:1rem;margin-bottom:1rem;}
.pf-card-title{font-family:'Press Start 2P',monospace;font-size:.5rem;
    color:var(--accent);letter-spacing:2px;margin-bottom:.8rem;
    padding-bottom:.5rem;border-bottom:1px solid var(--border);}
.result-name{font-family:'Press Start 2P',monospace;font-size:.85rem;
    color:var(--accent);text-shadow:0 0 12px rgba(0,255,204,.4);}
.result-tag{display:inline-block;padding:2px 8px;background:rgba(168,85,247,.15);
    border:1px solid var(--accent3);border-radius:2px;color:var(--accent3);
    font-size:.72rem;margin:2px;}
.result-tag.orange{background:rgba(255,107,53,.15);border-color:var(--accent2);color:var(--accent2);}
div[data-testid="stButton"]>button{
    background:transparent!important;border:1px solid var(--accent)!important;
    color:var(--accent)!important;font-family:'Press Start 2P',monospace!important;
    font-size:.5rem!important;border-radius:2px!important;letter-spacing:1px;}
div[data-testid="stButton"]>button:hover{background:rgba(0,255,204,.1)!important;}
div[data-testid="stButton"]>button[kind="primary"]{
    background:rgba(0,255,204,.12)!important;}
div[data-testid="stDownloadButton"]>button{
    background:rgba(168,85,247,.15)!important;border:1px solid var(--accent3)!important;
    color:var(--accent3)!important;font-family:'Press Start 2P',monospace!important;
    font-size:.45rem!important;border-radius:2px!important;}
div[data-testid="stSelectbox"] label,div[data-testid="stRadio"] label,
div[data-testid="stSlider"] label,div[data-testid="stTextArea"] label,
div[data-testid="stMultiSelect"] label,div[data-testid="stNumberInput"] label{
    color:var(--muted)!important;font-family:'Share Tech Mono',monospace!important;font-size:.78rem!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--surface)!important;border-bottom:1px solid var(--border)!important;}
.stTabs [data-baseweb="tab"]{font-family:'Press Start 2P',monospace!important;font-size:.45rem!important;
    color:var(--muted)!important;background:transparent!important;border:none!important;
    padding:.6rem 1rem!important;letter-spacing:1px;}
.stTabs [aria-selected="true"]{color:var(--accent)!important;border-bottom:2px solid var(--accent)!important;}
div[data-testid="stAlert"]{background:rgba(0,255,204,.04)!important;
    border:1px solid var(--border)!important;border-radius:2px!important;color:var(--text)!important;}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pf-header">
    <div style="font-size:2.2rem;filter:drop-shadow(0 0 12px rgba(0,255,204,.6))">⚔️</div>
    <div>
        <div class="pf-title">PIXELFORGE <span class="pf-badge">v2.0</span></div>
        <div class="pf-sub">AI pixel character asset creator → Godot-ready export</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LIVING_TYPES = {
    "Human":  {"icon": "🧑", "desc": "Humans, warriors, mages, rogues, demi-humans"},
    "Animal": {"icon": "🐺", "desc": "Beast-folk, familiars, mounts, creatures"},
    "Other":  {"icon": "👾", "desc": "Monsters, aliens, plants, mystical beings"},
}
CHARACTER_CLASSES = {
    "Human": {
        "Fantasy": ["⚔️ Warrior","🔮 Mage","🗡️ Rogue","🛡️ Paladin","🏹 Ranger","✨ Cleric","🔥 Warlock","📜 Scholar"],
        "Sci-Fi":  ["🤖 Cyborg","👨‍🚀 Pilot","🔬 Scientist","💻 Hacker","🪖 Soldier","🧬 Bio-Mech","⚡ Gunner","🕵️ Agent"],
        "Modern":  ["🥊 Fighter","🏃 Runner","🎭 Performer","🧑‍🍳 Crafter","🕵️ Detective","🧑‍⚕️ Medic","🧑‍🔧 Engineer","🎯 Sniper"],
    },
    "Animal": {
        "Fantasy": ["🐺 Wolf-folk","🦊 Fox-folk","🐉 Dragonkin","🦁 Lion-folk","🐻 Bear-folk","🦅 Bird-folk","🐍 Snake-folk","🦋 Fae-beast"],
        "Sci-Fi":  ["🤖 Mech-beast","🧬 Mutant","👾 Alien-pet","🦾 Cyborg-pet"],
        "Wild":    ["🐯 Hunter","🦌 Scout","🐗 Berserker","🦜 Trickster"],
    },
    "Other": {
        "Fantasy":  ["👹 Demon","👼 Angel","🧟 Undead","🧚 Fae","🌿 Plant","🪨 Golem","💀 Lich","🌊 Elemental"],
        "Sci-Fi":   ["👽 Alien","🤖 Android","🌌 Cosmic","🦠 Parasite","☢️ Mutant","🔮 Psionic","🛸 Drone","💠 Crystal"],
        "Mystical": ["🐲 Dragon","🦄 Unicorn","🔱 Titan","🌑 Shadow","⭐ Celestial","🍄 Shroom","🌀 Void","🕯️ Wraith"],
    },
}
ANIMATIONS   = ["idle","walk","run","jump","attack","hurt","die"]
SPRITE_SIZES = [32, 48, 64, 96, 128]

FRAME_POSES = {
    "idle":   ["standing relaxed, arms at sides, weight even",
               "slight breath in, chest expanded, shoulders back",
               "arms slightly forward, weight shifted slightly",
               "breath out, shoulders relaxed, neutral"],
    "walk":   ["left foot stepping forward, right arm forward",
               "weight on left foot, body upright, mid-transfer",
               "right foot stepping forward, left arm forward",
               "weight on right foot, pushing off left foot"],
    "run":    ["left knee high, right arm pumping, leaning forward",
               "both feet airborne, body extended horizontal",
               "right knee high, left arm pumping, leaning forward",
               "landing on left foot, knee bent absorbing impact"],
    "jump":   ["crouching to jump, knees bent, arms swinging back",
               "launching upward, legs extending, arms raised",
               "peak of jump, airborne, knees tucked, arms wide",
               "landing, knees bending, arms out for balance"],
    "attack": ["combat ready stance, weapon raised, weight back",
               "winding up strike, weapon pulled back, torso twisting",
               "full power swing, weapon slashing, torso rotated",
               "follow-through, weapon extended, recovering guard"],
    "hurt":   ["hit reaction, body snapping backward, eyes wide",
               "stumbling, off-balance, arm guarding head",
               "hunched in pain, arms clutching torso, head down",
               "recovering, straightening, wincing, guard rising"],
    "die":    ["critically wounded, staggering, knees buckling",
               "falling forward, losing balance, arms reaching out",
               "hitting ground, collapsed on hands and knees",
               "lying face down, completely still"],
}

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "living_type": None, "char_class": None, "char_genre": "Fantasy",
    "mode": "full", "character_data": None,
    "generated_images": {}, "final_sheet": None, "final_atlas": None,
    "gdscript": None, "selected_anims": [], "fps": 8,
    "seed": random.randint(10000, 99999),
    "gen_log": [], "gen_done": False, "gen_running": False,
    "gen_sheet": None, "gen_atlas": None, "gen_preview": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def call_groq(system, user, temperature=0.95, max_tokens=2500):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role":"system","content":system},{"role":"user","content":user}],
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

def hex_to_rgba(h, a=255):
    h = h.lstrip("#")
    try: return tuple(int(h[i:i+2],16) for i in (0,2,4))+(a,)
    except: return (100,100,200,a)

def to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def to_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():
            z.writestr(name, data.encode() if isinstance(data,str) else data)
    return buf.getvalue()

def remove_bg(img: Image.Image) -> Image.Image:
    """Remove background: try rembg first, fall back to edge flood-fill."""
    try:
        from rembg import remove as rembg_remove, new_session
        session = new_session("u2net")
        buf = io.BytesIO()
        img.convert("RGBA").save(buf, format="PNG")
        result = rembg_remove(buf.getvalue(), session=session,
                              alpha_matting=True,
                              alpha_matting_foreground_threshold=240,
                              alpha_matting_background_threshold=10)
        out = Image.open(io.BytesIO(result)).convert("RGBA")
        if (np.array(out)[:,:,3] > 10).sum() > (img.width * img.height * 0.03):
            return out
    except Exception:
        pass

    # Flood-fill fallback
    img = img.convert("RGBA")
    arr = np.array(img, dtype=np.int32)
    rv, gv, bv = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    h, w = rv.shape
    corners = [(0,0),(0,w-1),(h-1,0),(h-1,w-1)]
    bg_rgb  = tuple(sum(int(c[rv[y,x],gv[y,x],bv[y,x]][i]) for c in [{}]
                        for i in range(3)) for y,x in corners[:1])
    avg_bg  = tuple(
        sum(int([rv,gv,bv][ch][y,x]) for y,x in corners)//4
        for ch in range(3)
    )
    bg  = np.zeros((h,w), dtype=bool)
    vis = np.zeros((h,w), dtype=bool)
    def is_bg(py,px):
        diff = sum(abs(int([rv,gv,bv][i][py,px]) - avg_bg[i]) for i in range(3))
        return diff < 55
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
    res[bg,3] = 0
    return Image.fromarray(res,"RGBA")

def fetch_one(prompt: str, size: int, seed: int = 0) -> Image.Image | None:
    """Fetch one image from Pollinations + remove background."""
    encoded = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{encoded}"
           f"?width=512&height=512&nologo=true&model=flux&enhance=false&seed={seed}")
    for attempt in range(2):
        if attempt > 0:
            time.sleep(3)
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and "image" in r.headers.get("content-type",""):
                img = Image.open(io.BytesIO(r.content)).convert("RGBA")
                cleaned = remove_bg(img)
                visible = (np.array(cleaned)[:,:,3] > 10).sum()
                if visible > (size * size * 0.04):
                    return cleaned.resize((size, size), Image.NEAREST)
                # rembg over-removed — return without bg removal
                return img.resize((size, size), Image.NEAREST)
        except Exception:
            continue
    return None

def make_placeholder(size, p1, p2, lt="Human"):
    """Pixel art placeholder matching character colors."""
    scale = 4
    w = size * scale
    img = Image.new("RGBA",(w,w),(0,0,0,0))
    d   = ImageDraw.Draw(img)
    cx  = w // 2
    u   = w // 16

    if lt == "Animal":
        bw,bh,by = w//3, w//4, w//3
        d.ellipse([cx-bw,by,cx+bw,by+bh*2],fill=p1)
        d.ellipse([cx-w//5,by-w//5,cx+w//5,by+w//5],fill=p1)
        d.rectangle([cx-w//5,by-w//5-u*2,cx-w//8,by-w//5],fill=p1)
        d.rectangle([cx+w//8,by-w//5-u*2,cx+w//5,by-w//5],fill=p1)
        d.rectangle([cx-bw//2-u,by+bh*2,cx-u,by+bh*2+w//5],fill=p1)
        d.rectangle([cx+u,by+bh*2,cx+bw//2+u,by+bh*2+w//5],fill=p1)
    elif lt == "Other":
        bw,bh,by = w//3+u, w//2, w//4
        d.ellipse([cx-bw,by,cx+bw,by+bh],fill=p1)
        d.polygon([(cx-u*2,by-u*3),(cx-u*4,by),(cx,by)],fill=p2)
        d.polygon([(cx+u*2,by-u*3),(cx+u*4,by),(cx,by)],fill=p2)
        d.ellipse([cx-u*3,by+bh//3,cx-u,by+bh//3+u*2],fill=p2)
        d.ellipse([cx+u,by+bh//3,cx+u*3,by+bh//3+u*2],fill=p2)
        d.rectangle([cx-bw,by+bh,cx-u,by+bh+w//4],fill=p1)
        d.rectangle([cx+u,by+bh,cx+bw,by+bh+w//4],fill=p1)
    else:
        hs,bh,lh = w//5, w//3, w//4
        top = w//10
        skin = (255,220,177,255)
        d.rectangle([cx-hs//2,top,cx+hs//2,top+hs],fill=skin)
        d.rectangle([cx-hs//2-u,top+hs,cx+hs//2+u,top+hs+bh],fill=p2)
        d.rectangle([cx-hs-u,top+hs,cx-hs//2-u,top+hs+bh-u],fill=p1)
        d.rectangle([cx+hs//2+u,top+hs,cx+hs+u,top+hs+bh-u],fill=p1)
        lt2 = top+hs+bh+u//2
        d.rectangle([cx-hs//2,lt2,cx-u//2,lt2+lh],fill=p2)
        d.rectangle([cx+u//2,lt2,cx+hs//2,lt2+lh],fill=p1)
        ey = top+hs//3
        d.rectangle([cx-hs//3,ey,cx-hs//4,ey+u//2],fill=(0,0,0,255))
        d.rectangle([cx+hs//4,ey,cx+hs//3,ey+u//2],fill=(0,0,0,255))

    return img.resize((size,size),Image.NEAREST)

def build_gdscript(char_name, char_data, animations, sprite_size, fps):
    cn = "".join(w.capitalize() for w in char_name.replace("-"," ").split())
    anim_consts = "\n".join([f'const ANIM_{a.upper()} = "{a}"' for a in animations])
    anim_list   = ", ".join([f'"{a}"' for a in animations])
    return f'''extends CharacterBody2D
# ═══════════════════════════════════════
#  {char_name} | {char_data.get("species","?")}
#  Generated by PixelForge
#  Sprite: {sprite_size}px | FPS: {fps}
# ═══════════════════════════════════════

const SPEED      = 180.0
const RUN_SPEED  = 320.0
const JUMP_FORCE = -420.0

{anim_consts}

@onready var sprite : AnimatedSprite2D = $AnimatedSprite2D
var current_anim : String = ANIM_IDLE
var is_attacking : bool   = false
var is_hurt      : bool   = false

func _ready() -> void:
    play(ANIM_IDLE)

func _physics_process(delta: float) -> void:
    if not is_on_floor(): velocity += get_gravity() * delta
    _handle_movement()
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_FORCE; play(ANIM_JUMP)
    move_and_slide()

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_just_pressed("attack"): attack()

func _handle_movement() -> void:
    if is_attacking or is_hurt: return
    var dir := Input.get_axis("ui_left","ui_right")
    var run := Input.is_action_pressed("run")
    if dir != 0:
        velocity.x    = dir * (RUN_SPEED if run else SPEED)
        sprite.flip_h = dir < 0
        if is_on_floor(): play(ANIM_RUN if run else ANIM_WALK)
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED*2)
        if is_on_floor() and not is_attacking and not is_hurt: play(ANIM_IDLE)

func attack() -> void:
    if is_attacking: return
    is_attacking = true; play(ANIM_ATTACK)
    await get_tree().create_timer(0.5).timeout
    is_attacking = false; play(ANIM_IDLE)

func take_damage(amount: int) -> void:
    if is_hurt: return
    is_hurt = true; play(ANIM_HURT)
    await get_tree().create_timer(0.3).timeout
    is_hurt = false; play(ANIM_IDLE)

func die() -> void:
    play(ANIM_DIE); set_physics_process(false)
    await get_tree().create_timer(1.0).timeout; queue_free()

func play(anim: String) -> void:
    if current_anim == anim: return
    current_anim = anim
    if sprite.sprite_frames and sprite.sprite_frames.has_animation(anim):
        sprite.play(anim)

# Project > Input Map: add "attack" and "run"
'''

# ── Background generation thread ──────────────────────────────────────────────
def _anim_frame(base: Image.Image, anim: str, frame_idx: int, total: int) -> Image.Image:
    """
    Animation using full-sprite compositing.
    We NEVER split the body into separate pieces.
    Instead we paste the FULL sprite at an offset, then mask/overlay
    specific regions to create the illusion of limb movement.
    This avoids gaps, seams, and torn-apart looks.
    """
    sz    = base.width
    t     = frame_idx / max(total - 1, 1)
    u     = max(1, sz // 20)
    sin_t = math.sin(t * math.pi * 2)
    pad   = sz // 4

    W, H  = sz + pad*2, sz + pad*2
    bx, by = pad, pad

    def make(ox=0, oy=0, alpha=255, flip_x=False):
        """Paste full sprite at offset, optional alpha."""
        c   = Image.new("RGBA",(W,H),(0,0,0,0))
        img = base.transpose(Image.FLIP_LEFT_RIGHT) if flip_x else base
        c.paste(img,(bx+ox, by+oy), img)
        if alpha < 255:
            r2,g2,b2,a2 = c.split()
            a2 = a2.point(lambda p: int(p*alpha/255))
            c  = Image.merge("RGBA",(r2,g2,b2,a2))
        return c.crop((pad,pad,pad+sz,pad+sz))

    def overlay_red(base_frame, intensity):
        """Overlay red tint on a frame."""
        red = Image.new("RGBA", base_frame.size, (255,50,50,intensity))
        return Image.alpha_composite(base_frame, red)

    if anim == "idle":
        # Gentle bob — whole sprite, very subtle
        bob = int(math.sin(t * math.pi * 2) * max(1, u // 3))
        return make(oy=bob)

    elif anim == "walk":
        # Step: alternate lean left/right + bob up on each step
        bob  = int(abs(sin_t) * u)
        lean = int(sin_t * max(1, u // 2))
        return make(ox=lean, oy=-bob)

    elif anim == "run":
        # Run: bigger lean + more aggressive bob
        bob  = int(abs(sin_t) * u * 2)
        lean = int(sin_t * u)
        return make(ox=lean, oy=-bob)

    elif anim == "jump":
        # Proper jump arc — crouch → launch → peak → land
        if t < 0.12:
            # Crouch: squat down
            squat = int(u * 2 * (t / 0.12))
            return make(oy=squat)
        elif t < 0.45:
            # Launch: rapid rise
            progress = (t - 0.12) / 0.33
            rise = int(u * 9 * math.sin(progress * math.pi * 0.7))
            return make(oy=-rise)
        elif t < 0.65:
            # Peak: hold at top, slight tilt forward
            lean = int(u * 1.5 * ((t - 0.45) / 0.2))
            return make(ox=lean, oy=-int(u*9))
        else:
            # Fall + land impact
            progress = (t - 0.65) / 0.35
            fall = int(u * 9 * progress)
            # Squish on landing
            return make(ox=int(u*1.5), oy=-int(u*9)+fall)

    elif anim == "attack":
        if t < 0.15:
            # Wind-up: pull back
            pull = int(u * 2 * (t / 0.15))
            return make(ox=-pull)
        elif t < 0.45:
            # Strike: explosive lunge forward
            progress = (t - 0.15) / 0.30
            lunge    = int(u * 5 * progress)
            return make(ox=lunge)
        elif t < 0.65:
            # Hold extension
            return make(ox=int(u * 5))
        else:
            # Recover
            progress = (t - 0.65) / 0.35
            lunge    = int(u * 5 * (1 - progress))
            return make(ox=lunge)

    elif anim == "hurt":
        knockback = int(u * 4 * (1 - t))
        frame = make(ox=-knockback)
        if t < 0.5:
            intensity = int(160 * (1 - t * 2))
            frame = overlay_red(frame, intensity)
        return frame

    elif anim == "die":
        # Fall sideways with fade
        fall_x = int(t * sz * 0.35)
        fall_y = int(t * sz * 0.2)
        alpha  = max(0, int(255 * (1 - t * 1.3)))
        return make(ox=fall_x, oy=fall_y, alpha=alpha)

    return make()

def run_generation(char_data, animations, sprite_size, fps, result_store):
    """
    Background thread:
    1. Fetch ONE clean AI character image
    2. Use it consistently across all animation rows
    3. Apply smooth motion offsets per frame per animation
    This gives consistent character appearance + proper animation feel.
    """
    sz        = sprite_size
    n_frames  = 8
    lt        = char_data.get("living_type","Human")
    p1        = hex_to_rgba(char_data.get("color_primary","#7c3aed"))
    p2        = hex_to_rgba(char_data.get("color_secondary","#ff6b35"))
    base_seed = abs(hash(char_data.get("character_name","char"))) % 100000
    log       = result_store["log"]

    sheet = Image.new("RGBA",(sz*n_frames, sz*len(animations)),(0,0,0,0))
    atlas = {"frames":{},"meta":{"size":{"w":sz*n_frames,"h":sz*len(animations)}}}

    # ── Step 1: Generate ONE base image ──────────────────────────────────────
    log.append("🎨 Generating character base image...")
    species  = char_data.get("species","")
    outfit   = char_data.get("outfit","")
    palette  = char_data.get("color_palette","")
    art_style= char_data.get("art_style","pixel art 16-bit RPG")

    prompt = (
        f"{art_style}, {species} character, {outfit}, {palette}, "
        f"side view full body standing pose, neutral idle stance, "
        f"SNES Chrono Trigger Final Fantasy 6 style, "
        f"black pixel outlines, flat cel shading, limited color palette, "
        f"plain white background, isolated character, no scenery, no ground"
    )

    base_img = fetch_one(prompt, sz, seed=base_seed)
    if base_img is None:
        log.append("⚠️ AI image failed — using pixel placeholder")
        base_img = make_placeholder(sz, p1, p2, lt)
    else:
        log.append("✅ Base character image ready!")

    # ── Step 2: Build all animation frames from base image ────────────────────
    total = len(animations) * n_frames
    count = 0
    for ri, anim in enumerate(animations):
        log.append(f"🎬 Building {anim} animation ({ri+1}/{len(animations)})...")
        for ci in range(n_frames):
            count += 1
            frame = _anim_frame(base_img, anim, ci, n_frames)
            if frame.size != (sz,sz):
                frame = frame.resize((sz,sz), Image.NEAREST)
            sheet.paste(frame,(ci*sz, ri*sz))
            atlas["frames"][f"{anim}_{ci:02d}"] = {
                "frame":{"x":ci*sz,"y":ri*sz,"w":sz,"h":sz},
                "animation":anim,"frame_index":ci,
            }
        log.append(f"✅ {anim} done ({n_frames} frames)")

    result_store["sheet"]   = sheet
    result_store["atlas"]   = atlas
    result_store["preview"] = sheet.crop((0,0,sz,sz))
    result_store["done"]    = True
    result_store["n_frames"]= n_frames
    log.append("🎉 All animations complete!")

# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1,1.7], gap="large")

with left:
    # 01 Living Type
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 01 — LIVING TYPE</div>', unsafe_allow_html=True)
    tcols = st.columns(3)
    for i,(lt,info) in enumerate(LIVING_TYPES.items()):
        with tcols[i]:
            active = st.session_state.living_type == lt
            if st.button(f"{info['icon']} {lt}", key=f"lt_{lt}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.living_type = lt
                st.session_state.char_class  = None
                st.rerun()

    if st.session_state.living_type:
        lt   = st.session_state.living_type
        genres = list(CHARACTER_CLASSES[lt].keys())
        st.write("")
        gcols = st.columns(len(genres))
        for gi,genre in enumerate(genres):
            with gcols[gi]:
                active_g = st.session_state.char_genre == genre
                if st.button(genre, key=f"genre_{genre}", use_container_width=True,
                             type="primary" if active_g else "secondary"):
                    st.session_state.char_genre = genre
                    st.session_state.char_class = None
                    st.rerun()

        genre = st.session_state.char_genre
        if genre not in CHARACTER_CLASSES[lt]:
            genre = list(CHARACTER_CLASSES[lt].keys())[0]
            st.session_state.char_genre = genre

        classes = CHARACTER_CLASSES[lt][genre]
        st.write("")
        for row_s in range(0,len(classes),4):
            row_c = classes[row_s:row_s+4]
            ccols = st.columns(len(row_c))
            for ci2,cls in enumerate(row_c):
                with ccols[ci2]:
                    active_c = st.session_state.char_class == cls
                    if st.button(cls, key=f"cls_{cls}", use_container_width=True,
                                 type="primary" if active_c else "secondary"):
                        st.session_state.char_class = cls
                        st.rerun()
        if st.session_state.char_class:
            st.caption(f"▸ {genre} {lt} — {st.session_state.char_class}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 02 Gender
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 02 — GENDER</div>', unsafe_allow_html=True)
    gender = st.radio("Gender", ["Male","Female","Non-binary"], horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # 03 Mode
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 03 — MODE</div>', unsafe_allow_html=True)
    mc = st.columns(2)
    with mc[0]:
        if st.button("⚡ FULL", use_container_width=True,
                     type="primary" if st.session_state.mode=="full" else "secondary"):
            st.session_state.mode = "full"; st.rerun()
    with mc[1]:
        if st.button("🧩 MODULAR", use_container_width=True,
                     type="primary" if st.session_state.mode=="modular" else "secondary"):
            st.session_state.mode = "modular"; st.rerun()
    st.caption("▸ Full: complete character | Modular: separate parts")
    st.markdown('</div>', unsafe_allow_html=True)

    # 04 Settings
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 04 — SPRITE SETTINGS</div>', unsafe_allow_html=True)
    sprite_size = st.select_slider("Sprite Size (px)", options=SPRITE_SIZES, value=64)
    fps         = st.slider("Animation FPS", 4, 24, 8)
    sel_anims   = st.multiselect("Animations", ANIMATIONS, default=["idle","walk","run","jump","attack"])
    st.markdown('</div>', unsafe_allow_html=True)

    # 05 Hint
    st.markdown('<div class="pf-card"><div class="pf-card-title">// 05 — STYLE HINT (OPTIONAL)</div>', unsafe_allow_html=True)
    hint = st.text_area("Style Hint", placeholder="e.g. dark fire mage, glowing eyes, carries a staff...",
                        height=60, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # Seed
    sc,rc = st.columns([4,1])
    with sc:
        seed = st.number_input("Seed", value=st.session_state.seed, min_value=0, max_value=999999)
        st.session_state.seed = seed
    with rc:
        st.write(""); st.write("")
        if st.button("🎲", use_container_width=True):
            st.session_state.seed = random.randint(10000,99999); st.rerun()

    st.write("")
    can_go = bool(st.session_state.living_type and sel_anims and GROQ_KEY)
    if not GROQ_KEY:
        st.warning("Add GROQ_API_KEY to Streamlit secrets.")

    if st.button("⚡ FORGE CHARACTER", use_container_width=True, type="primary", disabled=not can_go):
        if not GROQ_KEY:
            st.error("GROQ_API_KEY missing."); st.stop()

        lt          = st.session_state.living_type
        char_class  = st.session_state.char_class or ""
        char_genre  = st.session_state.char_genre or "Fantasy"
        class_desc  = f"{char_genre} {lt} — {char_class}" if char_class else f"{char_genre} {lt}"

        # Step 1: Groq designs the character (fast, ~3s)
        with st.spinner("🤖 AI designing character..."):
            sys_p = f"""You are an expert pixel art RPG character designer.
Design a unique {class_desc} character. Be specific and creative.
{"User hint: " + hint.strip() if hint.strip() else "Full randomization."}
Return ONLY valid JSON, no markdown:
{{
  "character_name":"string","living_type":"{lt}","gender":"{gender}",
  "species":"string (specific)","art_style":"string",
  "body_type":"string","outfit":"string (detailed)",
  "color_primary":"hex e.g. #3a7bd5","color_secondary":"hex e.g. #ff6b35",
  "color_palette":"string","personality":"string",
  "weapon_or_item":"string","special_ability":"string",
  "backstory":"string (2 sentences)"
}}"""
            usr_p = f"Type:{lt}\nGenre:{char_genre}\nClass:{char_class or 'random'}\nGender:{gender}\nSeed:{seed}"
            try:
                raw  = call_groq(sys_p, usr_p, temperature=1.0, max_tokens=1500)
                data = parse_json(raw)
                st.session_state.character_data = data
            except Exception as e:
                st.error(f"Groq failed: {e}"); st.stop()

        # Step 2: Start background generation thread
        result_store = {"done": False, "log": [], "sheet": None, "atlas": None, "preview": None}

        t = threading.Thread(
            target=run_generation,
            args=(data, sel_anims, sprite_size, fps, result_store),
            daemon=True
        )
        t.start()

        # Step 3: Poll until done, updating progress in UI
        log_placeholder = st.empty()
        prog_bar        = st.progress(0)
        total_frames    = len(sel_anims) * 4

        st.info("⏳ Fetching 1 AI image then building all animations. Takes ~30 seconds.")

        while not result_store["done"]:
            time.sleep(1.5)
            log = result_store["log"]
            done_steps = sum(1 for l in log if "✅" in l or "⚠️" in l)
            prog_bar.progress(min(done_steps / max(len(sel_anims)+1, 1), 0.99))
            if log:
                log_placeholder.markdown("\n\n".join(f"`{l}`" for l in log[-6:]))

        prog_bar.progress(1.0)
        log_placeholder.markdown("\n\n".join(f"`{l}`" for l in result_store["log"][-5:]))

        # Store results
        st.session_state.final_sheet    = result_store["sheet"]
        st.session_state.final_atlas    = result_store["atlas"]
        st.session_state.selected_anims = sel_anims
        st.session_state.fps            = fps
        st.session_state.generated_images = {"full": result_store["preview"]}

        # GDScript
        gd = build_gdscript(data["character_name"], data, sel_anims, sprite_size, fps)
        st.session_state.gdscript = gd
        st.rerun()

# ── RIGHT PANEL ───────────────────────────────────────────────────────────────
with right:
    if not st.session_state.character_data:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    height:520px;border:1px dashed #2a2a40;border-radius:4px;gap:1.5rem;">
            <div style="font-size:5rem;filter:drop-shadow(0 0 24px rgba(0,255,204,.3))">⚔️</div>
            <div style="font-family:'Press Start 2P',monospace;font-size:.55rem;color:#2a2a40;
                        text-align:center;line-height:2.5">
                01 · PICK LIVING TYPE<br>02 · CHOOSE GENDER<br>
                03 · SELECT MODE<br>04 · HIT FORGE
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        d  = st.session_state.character_data
        cn = d.get("character_name","Unknown")

        st.markdown(f'<div class="result-name">{cn}</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin:8px 0 14px">
            <span class="result-tag">{d.get('species','?')}</span>
            <span class="result-tag">{d.get('living_type','?')}</span>
            <span class="result-tag">{d.get('gender','?')}</span>
            <span class="result-tag orange">{d.get('art_style','?')}</span>
            <span class="result-tag orange">{d.get('personality','?')}</span>
        </div>
        <div style="color:#94a3b8;font-style:italic;font-size:.82rem;margin-bottom:1rem">
            {d.get('backstory','')}
        </div>""", unsafe_allow_html=True)

        t1,t2,t3,t4 = st.tabs(["🖼️ PREVIEW","🧩 PARTS","📋 SPRITESHEET","🎮 GODOT"])

        # ── Preview ───────────────────────────────────────────────────────────
        with t1:
            if st.session_state.final_sheet and st.session_state.selected_anims:
                sheet   = st.session_state.final_sheet
                anims   = st.session_state.selected_anims
                fps_val = st.session_state.fps
                sz      = sheet.height // len(anims)

                # Build animated preview from spritesheet frames
                frames_b64 = {}
                n_fr = sheet.width // sz
                for ri,anim in enumerate(anims):
                    frames_b64[anim] = []
                    for ci in range(n_fr):
                        x,y = ci*sz, ri*sz
                        frame = sheet.crop((x,y,x+sz,y+sz))
                        disp_sz = min(sz*5, 320)
                        frame_d = frame.resize((disp_sz,disp_sz), Image.NEAREST)
                        bg_f = Image.new("RGBA",(disp_sz,disp_sz),(13,13,26,255))
                        bg_f.paste(frame_d,(0,0),frame_d)
                        buf = io.BytesIO(); bg_f.save(buf,format="PNG")
                        frames_b64[anim].append(base64.b64encode(buf.getvalue()).decode())

                frames_json = json.dumps(frames_b64)
                anims_json  = json.dumps(anims)

                ci_col, info_col = st.columns([1,1])
                with ci_col:
                    preview_html = f"""<!DOCTYPE html><html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#0a0a0f;font-family:'Courier New',monospace;color:#e2e8f0;}}
#viewer{{display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px;}}
#canvas-wrap{{
    background:repeating-conic-gradient(#1a1a28 0% 25%,#12121a 0% 50%) 0 0/16px 16px;
    border:2px solid #2a2a40;border-radius:4px;
    display:flex;align-items:center;justify-content:center;width:200px;height:200px;}}
#sprite{{image-rendering:pixelated;width:180px;height:180px;}}
#anim-btns{{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;}}
.anim-btn{{padding:3px 8px;background:#1a1a28;border:1px solid #2a2a40;
    color:#64748b;font-size:9px;cursor:pointer;border-radius:2px;text-transform:uppercase;}}
.anim-btn.active{{border-color:#00ffcc;color:#00ffcc;background:rgba(0,255,204,.08);}}
#playbar{{display:flex;align-items:center;gap:6px;}}
.ctrl-btn{{width:28px;height:28px;background:#1a1a28;border:1px solid #2a2a40;
    color:#00ffcc;font-size:13px;cursor:pointer;border-radius:2px;
    display:flex;align-items:center;justify-content:center;}}
input[type=range]{{-webkit-appearance:none;width:70px;height:3px;
    background:#2a2a40;border-radius:2px;outline:none;}}
input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:10px;height:10px;
    background:#00ffcc;border-radius:0;cursor:pointer;}}
#frame-info{{font-size:9px;color:#2a2a40;}}
</style></head><body>
<div id="viewer">
<div id="canvas-wrap"><img id="sprite" src="" alt=""/></div>
<div id="anim-btns"></div>
<div id="playbar">
  <button class="ctrl-btn" id="prev">&#9664;</button>
  <button class="ctrl-btn" id="play">&#9646;&#9646;</button>
  <button class="ctrl-btn" id="next">&#9654;</button>
  <input type="range" id="fps-sl" min="1" max="24" value="{fps_val}"/>
  <span style="font-size:9px;color:#64748b" id="fps-lbl">{fps_val}fps</span>
  <span id="frame-info">0/0</span>
</div>
</div>
<script>
const F={frames_json},AL={anims_json};
let ca=AL[0],cf=0,playing=true,fps={fps_val},timer=null;
const sp=document.getElementById('sprite'),
      fi=document.getElementById('frame-info'),
      fsl=document.getElementById('fps-sl'),
      fbl=document.getElementById('fps-lbl'),
      ab=document.getElementById('anim-btns');
AL.forEach(a=>{{
  const b=document.createElement('button');
  b.className='anim-btn'+(a===ca?' active':'');
  b.textContent=a;
  b.onclick=()=>{{ca=a;cf=0;document.querySelectorAll('.anim-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');show();}};
  ab.appendChild(b);
}});
function show(){{const fr=F[ca]||[];if(!fr.length)return;sp.src='data:image/png;base64,'+fr[cf%fr.length];fi.textContent=(cf+1)+'/'+fr.length;}}
function tick(){{const fr=F[ca]||[];cf=(cf+1)%Math.max(fr.length,1);show();}}
function startPlay(){{if(timer)clearInterval(timer);timer=setInterval(tick,1000/fps);}}
function stopPlay(){{if(timer){{clearInterval(timer);timer=null;}}}}
document.getElementById('play').onclick=()=>{{playing=!playing;document.getElementById('play').innerHTML=playing?'&#9646;&#9646;':'&#9654;';playing?startPlay():stopPlay();}};
document.getElementById('prev').onclick=()=>{{const fr=F[ca]||[];cf=(cf-1+fr.length)%Math.max(fr.length,1);show();}};
document.getElementById('next').onclick=()=>{{tick();}};
fsl.oninput=()=>{{fps=parseInt(fsl.value);fbl.textContent=fps+'fps';if(playing)startPlay();}};
show();if(playing)startPlay();
</script></body></html>"""
                    st.components.v1.html(preview_html, height=360, scrolling=False)

                with info_col:
                    p1h = d.get("color_primary","#00ffcc")
                    p2h = d.get("color_secondary","#ff6b35")
                    st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center">
                        <div style="width:28px;height:28px;background:{p1h};border:1px solid #444;border-radius:2px"></div>
                        <div style="width:28px;height:28px;background:{p2h};border:1px solid #444;border-radius:2px"></div>
                        <span style="color:#64748b;font-size:.72rem">{p1h} · {p2h}</span></div>""",
                        unsafe_allow_html=True)
                    for label,key in [("Species","species"),("Outfit","outfit"),
                                      ("Weapon","weapon_or_item"),("Ability","special_ability"),("Palette","color_palette")]:
                        st.markdown(f"**{label}:** {d.get(key,'—')}")
            else:
                st.info("Generate a character to see the animated preview.")

        # ── Parts ─────────────────────────────────────────────────────────────
        with t2:
            st.info("Modular parts mode coming in next update.")

        # ── Spritesheet ───────────────────────────────────────────────────────
        with t3:
            if st.session_state.final_sheet:
                sheet   = st.session_state.final_sheet
                atlas   = st.session_state.final_atlas
                anims   = st.session_state.selected_anims
                fps_val = st.session_state.fps

                st.caption(f"{len(anims)} anims × 4 frames = {len(anims)*4} total | {sheet.width}×{sheet.height}px")

                scale = max(1, min(4, 600//sheet.width))
                ds    = sheet.resize((sheet.width*scale,sheet.height*scale),Image.NEAREST)
                bg    = Image.new("RGBA",ds.size,(13,13,26,255))
                bg.paste(ds,(0,0),ds)
                st.image(bg, caption="Full spritesheet", use_container_width=True)

                st.markdown("**Rows:** "+"".join([
                    f'<span class="result-tag">{i}: {a}</span>' for i,a in enumerate(anims)
                ]), unsafe_allow_html=True)

                dc1,dc2 = st.columns(2)
                with dc1:
                    st.download_button("⬇️ SPRITESHEET PNG", to_bytes(sheet),
                        f"{cn.replace(' ','_')}_sheet.png","image/png", use_container_width=True)
                with dc2:
                    st.download_button("⬇️ ATLAS JSON", json.dumps(atlas,indent=2),
                        f"{cn.replace(' ','_')}_atlas.json","application/json", use_container_width=True)

        # ── Godot ─────────────────────────────────────────────────────────────
        with t4:
            if st.session_state.gdscript:
                gd    = st.session_state.gdscript
                anims = st.session_state.selected_anims
                clsnm = "".join(w.capitalize() for w in cn.replace("-"," ").split())

                with st.expander("📄 View GDScript", expanded=False):
                    st.code(gd, language="gdscript")

                readme = f"""PixelForge Export — {cn}
{'='*40}
1. Copy folder → res://characters/{clsnm}/
2. Godot: Create CharacterBody2D scene
3. Add child: AnimatedSprite2D
4. Add child: CollisionShape2D
5. Attach {clsnm}.gd as the script
6. SpriteFrames editor → import PNG sheet
7. Map rows:
{chr(10).join([f"   Row {i}: {a}" for i,a in enumerate(anims)])}
8. Set FPS: {st.session_state.fps}
9. Project > Input Map → add "attack" + "run"
{'='*40}"""

                zip_files = {
                    f"{clsnm}.gd": gd,
                    f"{cn.replace(' ','_')}_sheet.png": to_bytes(st.session_state.final_sheet),
                    f"{cn.replace(' ','_')}_atlas.json": json.dumps(atlas,indent=2),
                    "README.txt": readme,
                }

                st.download_button(
                    "⬇️ DOWNLOAD FULL GODOT PACKAGE (.ZIP)",
                    to_zip(zip_files),
                    f"{clsnm}_PixelForge.zip","application/zip",
                    use_container_width=True,
                )

                st.code(f"""res://characters/{clsnm}/
├── {clsnm}.gd
├── {cn.replace(' ','_')}_sheet.png
├── {cn.replace(' ','_')}_atlas.json
└── README.txt""", language="bash")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""<div style="text-align:center;padding:2rem 0 1rem;
    color:#1e1e30;font-size:.55rem;font-family:'Press Start 2P',monospace;letter-spacing:2px">
    PIXELFORGE v2.0 · GROQ + POLLINATIONS + REMBG · GODOT READY
</div>""", unsafe_allow_html=True)
