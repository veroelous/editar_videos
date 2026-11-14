"""Compositor frame a frame no estilo reels_claude.
Camadas (de baixo p/ cima): video | palavra-heroi | sujeito (mascara) | UI | legenda (por ultimo).
Cartoes em tela cheia substituem o video (o audio continua)."""
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

E = "/home/user/editar_videos/brutos/edit"
FPS, W, H = 30, 1080, 1920
J = json.load(open(f"{E}/edl_out.json"))
WD = {w["i"]: w for w in J["words"]}
BASE_T = J["total"]
TOTAL = round(BASE_T + 2.1, 3)
NFR = int(round(TOTAL * FPS))
ONLY = None  # (t0,t1) to render a subset for previews
if len(sys.argv) > 2:
    ONLY = (float(sys.argv[1]), float(sys.argv[2]))
OUT = sys.argv[3] if len(sys.argv) > 3 else f"{E}/video_gfx.mp4"

CREAM = (242, 238, 230); INK = (17, 17, 17); BLUE = (43, 107, 251)
DARK = (10, 10, 14); WHITE = (255, 255, 255); GRAY = (150, 150, 150)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name + ".otf", size)
    return _fc[k]

def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def back(x, s=1.70158):
    x = cl(x) - 1; return x * x * ((s + 1) * x + s) + 1
def pr(t, t0, d): return cl((t - t0) / d)
def S(i): return WD[i]["start"]
def lerp(a, b, k): return tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(len(a)))
def tw(text, font):
    b = font.getbbox(text); return b[2] - b[0]

# ---------------------------------------------------------------- masks
print("loading masks", flush=True)
mw, mh = 360, 640
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{E}/mask.mkv", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                     capture_output=True, check=True).stdout
MASKS = np.frombuffer(raw, np.uint8).reshape(-1, mh, mw)
print("masks", MASKS.shape, flush=True)

def mask_full(fi):
    m = MASKS[min(fi, len(MASKS) - 1)]
    im = Image.fromarray(m).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
    return im

def head_top(fi0, fi1):
    tops = []
    for fi in range(fi0, min(fi1, len(MASKS))):
        c = MASKS[fi][:, int(mw * 0.3):int(mw * 0.7)] > 128
        rows = np.where(c.mean(1) > 0.25)[0]
        if len(rows) and rows[0] * 3 >= 60: tops.append(rows[0] * 3)
    return int(np.percentile(tops, 3)) if tops else 0

# ---------------------------------------------------------------- timeline
CUTS = [r["out_start"] for r in J["ranges"]]
RNG = J["ranges"]
def _rng(i):
    for r in RNG:
        if i in r["words"]: return r
    raise KeyError(i)
def SS(i): return _rng(i)["out_start"]
def SE(i): r = _rng(i); return round(r["out_start"] + r["dur"], 3)
CARDS = [("verse", SS(7), SE(15)), ("list", SS(32), SE(40)), ("event", S(79) - 0.03, SE(88)),
         ("ebo", SS(89), SE(94)), ("end", SS(158), TOTAL + 1)]
def snap(t): return t
PHRASES = [  # (word ids, clear time, sparks)
    (list(range(0, 7)), SS(7), False),
    (list(range(20, 30)), SS(30), True),
    ([30, 31], SS(32), False),
    (list(range(41, 52)), SE(51), False),
    (list(range(52, 60)), SE(59), True),
    ([60, 61, 62], SE(62), False),
    (list(range(63, 69)), SE(68), False),
    (list(range(69, 79)), S(79) - 0.03, False),
    (list(range(96, 105)), SE(104), True),
    (list(range(115, 121)), SS(133), False),
    ([133, 134], SE(134), False),
    (list(range(135, 141)), SE(140), False),
    (list(range(141, 145)), SS(158), False),
]
PHRASES = [(ids, max(c, WD[ids[-1]]["end"] + 0.05) if c <= WD[ids[-1]]["start"] else c, sp) for ids, c, sp in PHRASES]
for k in range(len(PHRASES) - 1):  # nunca sobrepor a próxima frase
    ids, c, sp = PHRASES[k]; nxt = S(PHRASES[k + 1][0][0]) - 0.03
    PHRASES[k] = (ids, min(c, nxt) if nxt > S(ids[-1]) else c, sp)
HEROES = [  # text, t0, t1, decoration
    ("Bíblia", S(6) - 0.05, SS(7), None),
    ("tanta coisa", S(30) - 0.05, SS(32), "underline"),
    ("Paulo", S(49) - 0.05, SE(51), None),
    ("profundo", S(68) - 0.12, SE(68), "underline"),
    ("investigar", S(76) - 0.05, S(79) - 0.03, "wave"),
    ("igreja", S(101) - 0.05, SE(104), None),
    ("participar?", S(134) - 0.05, SE(134), "box"),
]
GLITCH_AT = [SS(1), SS(60)]
print("CARDS", [(n, round(a, 2), round(b, 2)) for n, a, b in CARDS], flush=True)
print("GLITCH", GLITCH_AT, flush=True)

def card_at(t):
    for n, a, b in CARDS:
        if a <= t < b: return n, a
    return None, None

# ---------------------------------------------------------------- captions
CAP_F = F("Inter-SemiBold", 44); CAP_Y = 72; CAP_LH = 56; CAP_MAXW = 900
def layout_phrase(ids):
    words = [WD[i]["text"].lower() if k == 0 and WD[i]["text"] not in ("EBO,", "EBO.") else WD[i]["text"] for k, i in enumerate(ids)]
    words = [w if not w.startswith("EBO") else w for w in words]
    sp = tw(" ", CAP_F)
    lines, cur, curw = [], [], 0
    for k, w in enumerate(words):
        ww = tw(w, CAP_F)
        if cur and curw + sp + ww > CAP_MAXW:
            lines.append(cur); cur, curw = [], 0
        cur.append((ids[k], w, ww)); curw += (sp if len(cur) > 1 else 0) + ww
    if cur: lines.append(cur)
    pos = []
    for li, line in enumerate(lines):
        lw = sum(x[2] for x in line) + sp * (len(line) - 1)
        x = (W - lw) // 2
        for i, w, ww in line:
            pos.append((i, w, x, CAP_Y + li * CAP_LH)); x += ww + sp
    return pos, len(lines)
PH_LAYOUT = [(layout_phrase(ids), ids, c, sp) for ids, c, sp in PHRASES]

def draw_sparks(d, x, y, k, col=BLUE):
    # 3 tracos curtos irradiando para o texto
    L = 20 * eo(k)
    for ang in (-35, 0, 35):
        a = math.radians(ang)
        x1, y1 = x - 34 * math.cos(a), y - 34 * math.sin(a)
        x2, y2 = x1 + L * math.cos(a), y1 + L * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=col + (255,), width=5)

def draw_captions(layer, t):
    for h in HEROES:
        if h[1] <= t < h[2] and hero_spec(h).get("hide_cap"): return 0
    d = ImageDraw.Draw(layer)
    for (pos, nl), ids, clear, sparks in PH_LAYOUT:
        if not (S(ids[0]) - 0.03 <= t < clear): continue
        shadow = Image.new("RGBA", (W, CAP_Y + nl * CAP_LH + 40), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        items = []
        for i, w, x, y in pos:
            if t < S(i) - 0.03: continue
            k = pr(t, S(i) - 0.03, 0.1)
            a = int(255 * (0.4 + 0.6 * k))
            items.append((w, x, y, a))
            sd.text((x, y + 3), w, font=CAP_F, fill=(0, 0, 0, int(a * 0.55)))
        layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)), (0, 0))
        for w, x, y, a in items:
            d.text((x, y), w, font=CAP_F, fill=WHITE + (a,))
        if sparks and items:
            draw_sparks(d, pos[0][2] - 8, CAP_Y + 30, pr(t, S(ids[0]), 0.12))
        return CAP_Y + nl * CAP_LH
    return 0

# ---------------------------------------------------------------- hero words
HERO_F_NAME = "InterDisplay-ExtraBold"
_hero_cache = {}
def hero_spec(h):
    text, t0, t1, deco = h
    if text in _hero_cache: return _hero_cache[text]
    top_head = head_top(int(t0 * FPS), int(t1 * FPS))
    nl = 1
    for (pos, n), ids, clear, sp_ in PH_LAYOUT:
        if S(ids[0]) - 0.03 <= t0 + 0.1 < clear: nl = n
    cap_bottom = CAP_Y + CAP_LH * nl + 14
    def fit(size):
        while tw(text, F(HERO_F_NAME, size)) > 960: size -= 6
        font = F(HERO_F_NAME, size); bb = font.getbbox(text)
        gw, gh = bb[2] - bb[0], bb[3] - bb[1]
        return size, font, bb, gw, gh
    best = None
    for cb, size0 in [(cap_bottom, 210), (cap_bottom, 180), (40, 210), (40, 185), (40, 160)]:
        size, font, bb, gw, gh = fit(size0)
        top = max(cb, top_head - 0.62 * gh)
        tl = Image.new("L", (W, H), 0)
        ImageDraw.Draw(tl).text(((W - gw) // 2 - bb[0], int(top) - bb[1]), text, font=font, fill=255)
        ta = np.asarray(tl.resize((mw, mh), Image.BILINEAR), np.float32) / 255
        covs = [float((ta * (MASKS[fi] / 255.0)).sum() / (ta.sum() + 1e-6))
                for fi in range(int(t0 * FPS), min(int(t1 * FPS), len(MASKS)), 2)]
        cov = float(np.percentile(covs, 90)) if covs else 1
        print("  try", text, size, "cov", round(cov, 2), flush=True)
        if top_head >= 90 and cov <= 0.30:
            best = (size, font, bb, gw, gh, top, "behind", cb == 40); break
    if best is None:
        size, font, bb, gw, gh = fit(210); best = (size, font, bb, gw, gh, 1240, "chest", False)
    size, font, bb, gw, gh, top, mode, hide = best
    spec = dict(font=font, bb=bb, gw=gw, gh=gh, x=(W - gw) // 2 - bb[0], y=int(top) - bb[1], top=int(top), mode=mode, size=size, hide_cap=hide)
    _hero_cache[text] = spec
    print("hero", text, mode, "hidecap", hide, "size", size, "top", spec["top"], "headtop", top_head, flush=True)
    return spec

def draw_hero(layer, h, t):
    text, t0, t1, deco = h
    sp = hero_spec(h)
    k = eo(pr(t, t0, 0.13))
    col = lerp((175, 175, 178), WHITE, k)
    d = ImageDraw.Draw(layer)
    x, y, gw, gh, top = sp["x"], sp["y"], sp["gw"], sp["gh"], sp["top"]
    left = (W - gw) // 2
    if deco == "box":
        kb = eo(pr(t, t0 + 0.08, 0.16))
        if kb > 0:
            d.rectangle([left - 22, top - 18, left - 22 + (gw + 44) * kb, top + gh + 24], fill=BLUE + (255,))
            if kb >= 1:
                for cx, cy in [(left - 22, top - 18), (left + gw + 22, top - 18), (left - 22, top + gh + 24), (left + gw + 22, top + gh + 24)]:
                    d.rectangle([cx - 9, cy - 9, cx + 9, cy + 9], fill=WHITE + (255,), outline=BLUE + (255,), width=3)
    # sombra suave p/ legibilidade
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x, y + 6), text, font=sp["font"], fill=(0, 0, 0, int(90 * k)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.text((x, y), text, font=sp["font"], fill=col + (int(255 * k),))
    if deco == "underline":
        ku = eo(pr(t, t0 + 0.14, 0.22))
        if ku > 0:
            uy = top + gh + 26
            d.rounded_rectangle([left, uy, left + max(14, gw * ku), uy + 13], radius=6, fill=BLUE + (255,))
    if deco == "wave":
        kw = eo(pr(t, t0 + 0.14, 0.35))
        if kw > 0:
            uy = top + gh + 30; pts = []
            n = int(80 * kw) + 2
            for j in range(n):
                xx = left + gw * kw * j / (n - 1)
                pts.append((xx, uy + 9 * math.sin((xx - left) / 26.0)))
            d.line(pts, fill=BLUE + (255,), width=10, joint="curve")

# ---------------------------------------------------------------- cards
def grid(img, col, alpha):
    d = ImageDraw.Draw(img, "RGBA")
    for gx in range(0, W, 135): d.line([(gx, 0), (gx, H)], fill=col + (alpha,), width=1)
    for gy in range(0, H, 135): d.line([(0, gy), (W, gy)], fill=col + (alpha,), width=1)

def label(d, text, x, y, col, size=40, center=False, dot=BLUE):
    f = F("Inter-SemiBold", size)
    w = tw(text, f) + 30
    if center: x = (W - w) // 2
    d.ellipse([x, y + size * 0.38, x + 14, y + size * 0.38 + 14], fill=dot + (255,))
    d.text((x + 30, y), text, font=f, fill=col + (255,))

def word_in(t, t0):
    return pr(t, t0 - 0.03, 0.1)

VERSE_WORDS = [(7, "Tudo"), (8, "que"), (9, "o"), (10, "homem"), (11, "semear,"), (12, "isso"),
               (13, "ele"), (14, "também"), (15, "ceifará.")]
def card_verse(t, t0):
    img = Image.new("RGBA", (W, H), CREAM + (255,)); grid(img, INK, 10)
    d = ImageDraw.Draw(img)
    d.text((96, 420), "“", font=F("InterDisplay-Black", 260), fill=BLUE + (255,))
    label(d, "Gálatas 6:7", 110, 700, INK)
    f = F("InterDisplay-Bold", 100); sp = tw(" ", f); x, y = 110, 790
    for i, w in VERSE_WORDS:
        ww = tw(w, f)
        if x + ww > 990: x, y = 110, y + 118
        if t >= S(i) - 0.03:
            k = word_in(t, S(i))
            base = BLUE if i in (11, 15) else INK
            d.text((x, y), w, font=f, fill=base + (int(255 * (0.35 + 0.65 * k)),))
        x += ww + sp
    return img

LIST_ITEMS = [(32, "dinheiro"), (33, "prosperidade"), (36, "castigo"), (39, "recompensa")]
def card_list(t, t0):
    img = Image.new("RGBA", (W, H), DARK + (255,)); grid(img, WHITE, 9)
    d = ImageDraw.Draw(img)
    label(d, "o que dizem por aí", 0, 560, (200, 200, 205), center=True)
    f = F("InterDisplay-ExtraBold", 132)
    strike0 = S(40)
    for k, (i, w) in enumerate(LIST_ITEMS):
        if t < S(i) - 0.03: continue
        kp = back(pr(t, S(i) - 0.03, 0.2))
        size = max(20, int(132 * (0.6 + 0.4 * kp)))
        ff = F("InterDisplay-ExtraBold", size)
        bw = tw(w, f); ww = tw(w, ff)
        cy = 760 + k * 170
        ks = eo(pr(t, strike0 + 0.07 * k, 0.16))
        a = int(255 * min(1, pr(t, S(i) - 0.03, 0.08)) * (1 - 0.45 * ks))
        bb = ff.getbbox(w)
        d.text(((W - ww) // 2 - bb[0], cy + (132 - size) // 2), w, font=ff, fill=WHITE + (a,))
        if ks > 0:
            x0 = (W - bw) // 2 - 34; x1 = x0 + (bw + 68) * ks
            ym = cy + 70
            d.line([(x0, ym + 10), (x1, ym + 10 - 22 * ks)], fill=BLUE + (255,), width=20)
    return img

def card_event(t, t0):
    img = Image.new("RGBA", (W, H), CREAM + (255,)); grid(img, INK, 10)
    d = ImageDraw.Draw(img)
    label(d, "próximo encontro", 0, 560, INK, center=True)
    f1 = F("InterDisplay-ExtraBold", 150)
    k1 = back(pr(t, S(79) - 0.03, 0.2))
    if k1 > 0:
        s = max(20, int(150 * (0.7 + 0.3 * k1))); ff = F("InterDisplay-ExtraBold", s)
        txt = "quinta-feira"; bb = ff.getbbox(txt)
        d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], 680 + (150 - s) // 2), txt, font=ff, fill=INK + (int(255 * min(1, k1)),))
    if t >= S(81) - 0.05:
        k2 = eo(pr(t, S(81) - 0.05, 0.18))
        f2 = F("InterDisplay-Black", 400); txt = "20h"; bb = f2.getbbox(txt)
        layer = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(((W - (bb[2] - bb[0])) // 2 - bb[0], 40), txt, font=f2, fill=BLUE + (int(255 * k2),))
        if k2 < 1: layer = layer.filter(ImageFilter.GaussianBlur(6 * (1 - k2)))
        img.alpha_composite(layer, (0, int(820 + 70 * (1 - k2))))
    # linha "estudo bíblico [online]"
    f3 = F("Inter-SemiBold", 60); fp = F("Inter-Bold", 58)
    parts = [(86, "estudo"), (87, "bíblico")]
    sp = tw(" ", f3); pill_w = tw("online", fp) + 64
    total = tw("estudo", f3) + sp + tw("bíblico", f3) + sp + pill_w
    x = (W - total) // 2; y = 1430
    for i, w in parts:
        if t >= S(i) - 0.03:
            d.text((x, y), w, font=f3, fill=INK + (int(255 * (0.35 + 0.65 * word_in(t, S(i)))),))
        x += tw(w, f3) + sp
    if t >= S(88) - 0.03:
        kp = back(pr(t, S(88) - 0.03, 0.2))
        pw, ph = pill_w * kp, 92 * kp
        cx, cy = x + pill_w / 2, y + 36
        d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], radius=46 * kp, fill=BLUE + (255,))
        if kp > 0.8:
            d.text((x + 32, y + 2), "online", font=fp, fill=WHITE + (255,))
    return img

def card_ebo(t, t0):
    img = Image.new("RGBA", (W, H), BLUE + (255,)); grid(img, WHITE, 16)
    d = ImageDraw.Draw(img)
    f = F("Inter-SemiBold", 50); words = [(89, "ou"), (90, "mais"), (91, "conhecido"), (92, "como"), (93, "o")]
    sp = tw(" ", f); total = sum(tw(w, f) for _, w in words) + sp * (len(words) - 1)
    x = (W - total) // 2
    for i, w in words:
        if t >= S(i) - 0.03:
            d.text((x, 560), w, font=f, fill=WHITE + (int(255 * (0.4 + 0.6 * word_in(t, S(i)))),))
        x += tw(w, f) + sp
    t_e = S(94) - 0.05
    ft = F("InterDisplay-Black", 128); fr = F("InterDisplay-ExtraBold", 128)
    rows = [("E", "studo"), ("B", "íblico"), ("O", "nline")]
    TS = 172; bx = 170
    for r, (L, rest) in enumerate(rows):
        ty = 760 + r * 214
        kt = back(pr(t, t_e + 0.07 * r, 0.16))
        if kt > 0:
            s = TS * kt; cx, cy = bx + TS / 2, ty + TS / 2
            d.rounded_rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], radius=20 * kt, fill=WHITE + (255,))
            if kt > 0.85:
                bb = ft.getbbox(L)
                d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), L, font=ft, fill=BLUE + (255,))
        kr = eo(pr(t, t_e + 0.32 + 0.07 * r, 0.2))
        if kr > 0:
            bb = fr.getbbox("E")
            d.text((bx + TS + 22 - 30 * (1 - kr), ty + TS / 2 - (bb[3] - bb[1]) / 2 - bb[1]), rest, font=fr, fill=WHITE + (int(255 * kr),))
    return img

END_WORDS = [(158, "te"), (159, "espero"), (160, "lá")]
def brace_line(d, t, t0, words, y, size, txt_col, br_col, final_w=None):
    f = F("InterDisplay-Bold", size); fb = F("Inter-Light", int(size * 1.15)); fa = F("Inter-Regular", int(size * 0.8))
    sp = tw(" ", f)
    tot = sum(tw(w, f) for _, w in words) + sp * (len(words) - 1)
    pad = 34; bw = tw("{", fb)
    inner = tot + 2 * pad
    lx = (W - inner) // 2 - bw; rx = (W + inner) // 2
    ka = eo(pr(t, t0 + 0.06, 0.12))
    by = y - int(size * 0.14)
    d.text((lx, by), "{", font=fb, fill=br_col + (255,))
    d.text((rx, by), "}", font=fb, fill=br_col + (255,))
    for xx in (lx + bw // 2, rx + bw // 2):
        d.ellipse([xx - 5, y - 30, xx + 5, y - 20], fill=txt_col + (255,))
    if ka > 0:
        aw = tw("→", fa)
        d.text((lx - 16 - aw - 20 * (1 - ka), y + 4), "←", font=fa, fill=br_col + (int(255 * ka),))
        d.text((rx + bw + 16 + 20 * (1 - ka), y + 4), "→", font=fa, fill=br_col + (int(255 * ka),))
    x = lx + bw + pad
    for i, w in words:
        if t >= S(i) - 0.03:
            d.text((x, y), w, font=f, fill=txt_col + (int(255 * (0.35 + 0.65 * word_in(t, S(i)))),))
        x += tw(w, f) + sp
    return lx, rx + bw

def card_end(t, t0):
    img = Image.new("RGBA", (W, H), CREAM + (255,)); grid(img, INK, 10)
    d = ImageDraw.Draw(img)
    label(d, "estudo bíblico online · quinta, 20h", 0, 700, (90, 90, 95), size=38, center=True)
    brace_line(d, t, t0, END_WORDS, 820, 110, INK, BLUE)
    tb = S(160) + 0.45
    kb = back(pr(t, tb, 0.22), 2.2)
    if kb > 0:
        fb = F("Inter-Bold", 54); txt = "manda EBO na DM →"
        bw, bh = tw(txt, fb) + 80, 118
        cx, cy = W / 2, 1060
        s = kb
        d.rounded_rectangle([cx - bw * s / 2, cy - bh * s / 2, cx + bw * s / 2, cy + bh * s / 2], radius=22 * s, fill=BLUE + (255,))
        if kb > 0.85:
            bb = fb.getbbox(txt)
            d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=fb, fill=WHITE + (255,))
        kh = pr(t, tb + 0.3, 0.05)
        if kh > 0:
            o = 12; x0, y0, x1, y1 = cx - bw / 2 - o, cy - bh / 2 - o, cx + bw / 2 + o, cy + bh / 2 + o
            d.rectangle([x0, y0, x1, y1], outline=BLUE + (255,), width=3)
            for hx, hy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
                d.rectangle([hx - 9, hy - 9, hx + 9, hy + 9], fill=WHITE + (255,), outline=BLUE + (255,), width=3)
    return img

CARD_FN = {"verse": card_verse, "list": card_list, "event": card_event, "ebo": card_ebo, "end": card_end}

# ---------------------------------------------------------------- UI overlays on face
VERSES = [("7", "Não erreis: Deus não se deixa escarnecer; porque tudo o que o homem semear, isso também ceifará."),
          ("8", "Porque o que semeia na sua carne, da carne ceifará a corrupção; mas o que semeia no Espírito, do Espírito ceifará a vida eterna."),
          ("9", "E não nos cansemos de fazer bem, porque a seu tempo ceifaremos, se não houvermos desfalecido.")]
def wrap(text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if tw(c, font) > maxw and cur: out.append(cur); cur = w
        else: cur = c
    if cur: out.append(cur)
    return out
_bible = {}
def bible_content():
    if _bible: return _bible["img"], _bible["spans"]
    fv = F("Inter-Medium", 36); fn = F("Inter-Bold", 36)
    cw = 880; y = 10; spans = []; lines_all = []
    for n, txt in VERSES:
        ls = wrap(txt, fv, cw - 70)
        spans.append((y - 8, y + len(ls) * 50 + 6)); lines_all.append((n, ls, y)); y += len(ls) * 50 + 26
    img = Image.new("RGBA", (cw, y + 400), (255, 255, 255, 0)); d = ImageDraw.Draw(img)
    for n, ls, yy in lines_all:
        d.text((8, yy), n, font=fn, fill=BLUE + (255,))
        for j, l in enumerate(ls): d.text((62, yy + j * 50), l, font=fv, fill=(40, 40, 45, 255))
    _bible.update(img=img, spans=spans)
    return img, spans

def ui_bible(layer, t):
    t0, t1 = S(56) - 0.05, SE(62)
    if not (t0 <= t < t1): return
    k = pr(t, t0, 0.38); ke = back(k, 1.4)
    cw, ch = 960, 560
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=40, fill=(255, 255, 255, 250))
    d.ellipse([40, 38, 96, 94], fill=BLUE + (255,))
    d.text((56, 44), "†", font=F("Inter-Bold", 38), fill=WHITE + (255,))
    d.text((116, 42), "Gálatas 6", font=F("InterDisplay-Bold", 48), fill=INK + (255,))
    d.text((cw - 120, 52), "ARC", font=F("Inter-SemiBold", 32), fill=GRAY + (255,))
    d.line([(40, 122), (cw - 40, 122)], fill=(230, 230, 232, 255), width=2)
    content, spans = bible_content()
    active = 0
    if t >= S(57) - 0.05: active = 1
    if t >= S(60) - 0.05: active = 2
    ta = [S(56) - 0.05, S(57) - 0.05, S(60) - 0.05][active]
    prev = max(0, active - 1)
    kk = eo(pr(t, ta, 0.3)) if active else 1
    off = spans[prev][0] + (spans[active][0] - spans[prev][0]) * kk
    view = Image.new("RGBA", (880, ch - 150), (0, 0, 0, 0)); vd = ImageDraw.Draw(view)
    hy0 = spans[prev][0] + (spans[active][0] - spans[prev][0]) * kk - off
    hy1 = spans[prev][1] + (spans[active][1] - spans[prev][1]) * kk - off
    vd.rounded_rectangle([0, hy0 + 4, 880, hy1 + 4], radius=16, fill=BLUE + (34,))
    vd.rectangle([0, hy0 + 4, 6, hy1 + 4], fill=BLUE + (255,))
    view.alpha_composite(content.crop((0, int(off), 880, int(off) + ch - 150)), (0, 0))
    card.alpha_composite(view, (40, 140))
    # fade bottom
    rot = -7 * (1 - ke)
    sh = Image.new("RGBA", (cw + 120, ch + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([60, 74, cw + 60, ch + 74], radius=40, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    combo = sh.copy(); combo.alpha_composite(card, (60, 60))
    combo = combo.rotate(rot, resample=Image.BICUBIC, expand=True)
    if k < 1:
        a = np.asarray(combo).copy(); a[..., 3] = (a[..., 3] * min(1, k * 3)).astype(np.uint8); combo = Image.fromarray(a)
    cx = W // 2; cy = 1430 + int(420 * (1 - ke))
    layer.alpha_composite(combo, (cx - combo.width // 2, cy - combo.height // 2))

def ui_braces(layer, t):
    t0, t1 = S(115) - 0.03, SS(133)
    if not (t0 <= t < t1): return
    d = ImageDraw.Draw(layer)
    sh = Image.new("RGBA", (W, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    items = [(121, "questionar,"), (123, "aprender,"), (125, "discutir")]
    brace_line(sd, t, t0, items, 158, 54, WHITE, BLUE)
    if t >= S(126) - 0.03:
        fs = F("Inter-SemiBold", 46); txt_words = [(126, "sobre"), (127, "a"), (128, "Bíblia.")]
        sp = tw(" ", fs); tot = sum(tw(w, fs) for _, w in txt_words) + sp * 2
        x = (W - tot) // 2
        for i, w in txt_words:
            if t >= S(i) - 0.03:
                sd.text((x, 246), w, font=fs, fill=WHITE + (int(255 * (0.4 + 0.6 * word_in(t, S(i)))),))
            x += tw(w, fs) + sp
    shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    a = np.asarray(sh)[..., 3]
    shadow.putalpha(Image.fromarray((a * 0.5).astype(np.uint8)))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)), (0, 4))
    layer.alpha_composite(sh, (0, 0))

def ui_chat(layer, t):
    t0, t1 = S(139) - 0.05, SS(158)
    if not (t0 <= t < t1): return
    k = eo(pr(t, t0, 0.28))
    d = ImageDraw.Draw(layer)
    y0 = 1600 + int(260 * (1 - k)); x0, x1 = 70, 1010; h = 124
    sh = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, 70, x1, 70 + h], radius=62, fill=(0, 0, 0, int(110 * k)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (0, y0 - 60))
    d.rounded_rectangle([x0, y0, x1, y0 + h], radius=62, fill=(255, 255, 255, int(255 * k)))
    tsend = S(144) + 0.42
    typed = ""
    for j, ch in enumerate("EBO"):
        if t >= S(144) - 0.03 + j * 0.08: typed += ch
    if t >= tsend: typed = ""
    fi = F("Inter-SemiBold", 48)
    if typed:
        d.text((x0 + 56, y0 + 34), typed, font=fi, fill=INK + (255,))
        cxp = x0 + 56 + tw(typed, fi) + 6
    else:
        d.text((x0 + 56, y0 + 34), "Mensagem...", font=F("Inter-Medium", 46), fill=(160, 160, 165, int(255 * k)))
        cxp = x0 + 52
    if int(t * 2.5) % 2 == 0 or typed:
        d.rectangle([cxp, y0 + 32, cxp + 4, y0 + 92], fill=BLUE + (int(255 * k),))
    ps = 1 + 0.18 * math.sin(math.pi * pr(t, tsend - 0.05, 0.2))
    r = 42 * ps; cx, cy = x1 - 66, y0 + h / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE + (int(255 * k),))
    d.line([(cx, cy + 18), (cx, cy - 18)], fill=WHITE + (int(255 * k),), width=7)
    d.line([(cx - 15, cy - 3), (cx, cy - 19), (cx + 15, cy - 3)], fill=WHITE + (int(255 * k),), width=7, joint="curve")
    if t >= tsend:
        kb = back(pr(t, tsend, 0.22), 2.0)
        fb = F("Inter-Bold", 56); bw, bh = tw("EBO", fb) + 80, 112
        bx1, by1 = x1 - 10, y0 - 40
        s = kb
        d.rounded_rectangle([bx1 - bw * s, by1 - bh * s, bx1, by1], radius=40 * s, fill=BLUE + (255,))
        if kb > 0.85:
            d.text((bx1 - bw + 40, by1 - bh + 24), "EBO", font=fb, fill=WHITE + (255,))
        if t >= tsend + 0.25:
            d.text((bx1 - 160, by1 + 8), "Enviado ✓", font=F("Inter-SemiBold", 30), fill=WHITE + (int(220 * pr(t, tsend + 0.25, 0.1)),))

# ---------------------------------------------------------------- main loop
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{E}/base.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
last = None
f0 = int(ONLY[0] * FPS) if ONLY else 0
f1 = int(ONLY[1] * FPS) if ONLY else NFR
for fi in range(NFR):
    b = dec.stdout.read(W * H * 3)
    if len(b) == W * H * 3: last = b
    if fi < f0: continue
    if fi >= f1: break
    t = fi / FPS
    name, ct0 = card_at(t)
    if name:
        frame = CARD_FN[name](t, ct0).convert("RGB")
        # entrada do cartao: leve zoom 0.97->1 em 4 frames
        kz = eo(pr(t, ct0, 0.13))
        if kz < 1:
            s = 0.97 + 0.03 * kz
            sm = frame.resize((int(W * s), int(H * s)), Image.BILINEAR)
            bg = Image.new("RGB", (W, H), frame.getpixel((5, 5))); bg.paste(sm, ((W - sm.width) // 2, (H - sm.height) // 2)); frame = bg
        enc.stdin.write(frame.tobytes()); continue
    src = Image.frombytes("RGB", (W, H), last)
    if any(abs(t - g) < 0.5 / FPS for g in GLITCH_AT):
        band = src.crop((0, 0, W, int(H * 0.42))).resize((W, H // 5))
        g = Image.new("RGB", (W, H))
        for j in range(5): g.paste(band, (0, j * (H // 5)))
        frame = g.filter(ImageFilter.BoxBlur(3)); enc.stdin.write(frame.tobytes()); continue
    frame = src.convert("RGBA")
    heroes = [h for h in HEROES if h[1] <= t < h[2]]
    for h in heroes:
        sp = hero_spec(h)
        hl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw_hero(hl, h, t)
        if sp["mode"] == "behind":
            frame.alpha_composite(hl)
            frame = Image.composite(src.convert("RGBA"), frame, mask_full(fi))
        else:
            frame.alpha_composite(hl)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ui_bible(ui, t); ui_braces(ui, t); ui_chat(ui, t)
    frame.alpha_composite(ui)
    cap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_captions(cap, t)  # legenda SEMPRE por ultimo
    frame.alpha_composite(cap)
    enc.stdin.write(frame.convert("RGB").tobytes())
    if fi % 150 == 0: print("frame", fi, "/", NFR, flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
print("done", OUT, "total", TOTAL)
