"""Estilo ELEGANTE 16:9 (mesma identidade dos reels: grafite + grão, Inter + Instrument Serif itálico dourado).
Layouts: CENTER (câmera ao centro), COL (câmera à esquerda + coluna de texto), FULL (texto em tela cheia + câmera no canto),
CARD (vinheta, sem câmera). Blocos: c_* (coluna), f_* (tela cheia), chapter, intro, endcard."""
import math, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/user/editar_videos/pipelines/reels_meet"); sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
from estilo import font, sprite, rich, INK, MUTED, GOLD, BG0, BG1, LINE
from fx import eo, eio, back, pr, cl, tw, with_alpha, blur_reveal

W, H = 1920, 1080
BOX = {"center": (480, 80, 1400, 1000), "col": (110, 130, 930, 950), "full": (1590, 760, 1850, 1020), "card": (1590, 760, 1850, 1020)}
CX0, CX1 = 1030, 1810            # coluna de texto
CMID = (CX0 + CX1) / 2
FX = 860                         # centro dos blocos de tela cheia (960 quando não há câmera)
def set_audio_only():
    global CX0, CX1, CMID, FX
    CX0, CX1, FX = 360, 1560, 960; CMID = (CX0 + CX1) / 2

def env(t, t0, t1, din=0.5, dout=0.4): return eo(pr(t, t0, din)) * (1 - eio(pr(t, t1 - dout, dout)))

def line_rich(layer, line, x, y, size, k, base="serif", col=INK, align="left", maxw=780, alpha=1.0):
    """Linha com *destaque*; align left (x = início) ou center (x = centro). y = topo. Retorna tamanho usado."""
    while True:
        parts = rich(line, size, base, col); wsum = sum(tw(p[0], p[1]) for p in parts)
        if wsum <= maxw or size < 28: break
        size = int(size * 0.95)
    asc = parts[0][1].getmetrics()[0] if parts else size
    xx = x if align == "left" else x - wsum / 2
    for txt, f, c in parts:
        im = Image.new("RGBA", (tw(txt, f) + 60, int(size * 1.7)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((30 - f.getbbox(txt)[0], 30 + asc - f.getmetrics()[0]), txt, font=f, fill=c + (255,))
        if k < 1 or alpha < 1: im = with_alpha(blur_reveal(im, k, 8), alpha)
        layer.alpha_composite(im, (int(xx - 30), int(y - 30 + 22 * (1 - eo(k)))))
        xx += tw(txt, f)
    return size

def wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if tw(c, f) > maxw and cur: out.append(cur); cur = w
        else: cur = c
    if cur: out.append(cur)
    return out

def kicker(layer, text, x, y, k, align="left", col=GOLD, size=24):
    f = font("caps", size); s = " ".join(text.upper()); w = tw(s, f)
    ImageDraw.Draw(layer).text((x if align == "left" else x - w / 2, y), s, font=f, fill=col + (int(255 * k),))
    return w

# ------------------------------------------------------------------ fundo, barra e moldura
_grain = None; _bgc = {}
def background(t):
    global _grain
    if _grain is None:
        rng = np.random.default_rng(1)
        _grain = [Image.fromarray(np.dstack([np.full((H, W), 255, np.uint8)] * 3 + [(rng.random((H, W)) * 14).astype(np.uint8)]), "RGBA") for _ in range(3)]
    key = round(t * 4)
    if key not in _bgc:
        if len(_bgc) > 4: _bgc.clear()
        tt = key / 4; g = np.linspace(0, 1, 54)[:, None, None]
        img = np.repeat(np.array(BG0, np.float32) * (1 - g) + np.array(BG1, np.float32) * g, 96, axis=1)
        yy, xx = np.mgrid[0:54, 0:96].astype(np.float32)
        glow = np.exp(-((xx - 48 - 10 * math.sin(tt * 0.13)) ** 2 / 900 + (yy - 22) ** 2 / 500))[..., None]
        img = img + glow * np.array(GOLD, np.float32) * (0.05 + 0.02 * math.sin(tt * 0.3))
        _bgc[key] = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert("RGBA")
    bg = _bgc[key].copy(); bg.alpha_composite(_grain[int(t * 12) % 3]); return bg

def topbar(layer, t, total, left, right, a=1.0):
    d = ImageDraw.Draw(layer); d.rectangle([0, 0, W * min(1, t / total), 3], fill=GOLD + (220,))
    if a <= 0: return
    f = font("caps", 21); L = " ".join(left.upper()); R = " ".join(right.replace("*", "").upper())
    d.text((110, 46), L, font=f, fill=MUTED + (int(255 * a),)); d.text((W - 110 - tw(R, f), 46), R, font=f, fill=MUTED + (int(255 * a),))

_fc = {}
def cam(img, box, z, alpha=1.0, pulse=0.0):
    x0, y0, x1, y1 = box; pw, ph = int(x1 - x0), int(y1 - y0)
    if pw < 4 or alpha <= 0.01: return None, (0, 0)
    s = img.width; cw = s / z; c0 = (s - cw) / 2; cy0 = min(max(0, s * 0.46 - cw / 2), s - cw)
    piece = img.resize((pw, ph), Image.BICUBIC, box=(c0, cy0, c0 + cw, cy0 + cw)).convert("RGBA")
    if pulse > 0.05: piece = piece.filter(ImageFilter.GaussianBlur(2 * pulse))
    r = max(10, int(26 * pw / 820))
    if (pw, ph) not in _fc:
        if len(_fc) > 60: _fc.clear()
        sh = Image.new("RGBA", (pw + 160, ph + 160), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([80, 100, pw + 80, ph + 100], radius=r + 4, fill=(0, 0, 0, 150))
        m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=r, fill=255)
        _fc[(pw, ph)] = (sh.filter(ImageFilter.GaussianBlur(28)), m)
    shb, m = _fc[(pw, ph)]; lay = shb.copy(); lay.paste(piece, (80, 80), m)
    ImageDraw.Draw(lay).rounded_rectangle([80, 80, 80 + pw - 1, 80 + ph - 1], radius=r, outline=LINE + (46,), width=2)
    return (with_alpha(lay, alpha) if alpha < 1 else lay), (int(x0) - 80, int(y0) - 80)

# ------------------------------------------------------------------ blocos de coluna
def c_title(L, t, e):
    a = env(t, e["t0"], e["t1"]);  y = e.get("y", 430); size = e.get("size", 92)
    if a <= 0: return
    if e.get("kicker"): kicker(L, e["kicker"], CX0, y - 60, a)
    for j, ln in enumerate(e["lines"]):
        k = eo(pr(t, e["t0"] + 0.12 * j, 0.55)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        size = line_rich(L, ln, CX0, y, size, k, alpha=min(1, k * 1.5)); y += size * 1.08

def c_verse(L, t, e):
    a = env(t, e["t0"], e["t1"], 0.6)
    if a <= 0: return
    f = font("serif_i", e.get("size", 56)); lines = wrap(e["text"], f, CX1 - CX0)
    y = 540 - (len(lines) * f.size * 1.2 + 90) / 2
    kicker(L, e["ref"], CX0, y, a); ImageDraw.Draw(L).line([(CX0, y + 44), (CX0 + 80 * eo(pr(t, e["t0"] + 0.2, 0.5)), y + 44)], fill=GOLD + (int(200 * a),), width=2)
    y += 80
    for j, ln in enumerate(lines):
        k = eo(pr(t, e["t0"] + 0.25 + 0.15 * j, 0.6)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        im, pad, b = sprite(ln, f, INK); L.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int(CX0 - pad), int(y - pad + 18 * (1 - k)))); y += f.size * 1.2

def c_statement(L, t, e):
    if not (e["t0"] <= t < e["t1"]): return
    size = e.get("size", 64); n = len(e["lines"]); y = 540 - n * size * 1.15 / 2
    for ln, tl in e["lines"]:
        k = eo(pr(t, tl - 0.1, 0.6)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k > 0: line_rich(L, ln, CX0, y, size, k, alpha=min(1, k * 1.4))
        y += size * 1.15

def c_list(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    gap = e.get("gap", 92); n = len(e["items"]); y = 540 - (n * gap + 60) / 2; d = ImageDraw.Draw(L)
    if e.get("title"): kicker(L, e["title"], CX0, y, a); y += 70
    fs = font("sans", e.get("size", 46)); fn = font("serif_i", 54); num = e.get("numbered", True)
    for j, it in enumerate(e["items"]):
        k = eo(pr(t, it[0] - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k > 0:
            if num:
                im, pad, _ = sprite(f"{j + 1:02d}", fn, GOLD); L.alpha_composite(with_alpha(im, k), (int(CX0 - pad), int(y - pad - 6)))
            tx = CX0 + (90 if num else 0)
            im, pad, b = sprite(it[1], fs, INK); L.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int(tx - pad + 20 * (1 - k)), int(y - pad)))
            if e.get("strike") is not None and t >= e["strike"] + 0.1 * j:
                ks = eo(pr(t, e["strike"] + 0.1 * j, 0.35)); yy = y + (b[3] - b[1]) / 2 + 2
                d.line([(tx - 6, yy), (tx - 6 + (b[2] - b[0] + 12) * ks, yy)], fill=GOLD + (int(230 * k),), width=3)
            if j < n - 1: d.line([(CX0, y + gap - 24), (CX1, y + gap - 24)], fill=LINE + (int(22 * k),), width=1)
        y += gap

def c_versus(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(L); cx = CMID; kv = eo(pr(t, e["t0"], 0.6))
    d.line([(cx, 380), (cx, 380 + 320 * kv)], fill=LINE + (int(60 * a),), width=1)
    for side, (lab, txt, ti) in (("l", e["left"]), ("r", e["right"])):
        k = eo(pr(t, ti - 0.1, 0.55)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k <= 0: continue
        x = cx - 40 if side == "l" else cx + 40; f = font("caps", 22); s = " ".join(lab.upper()); w = tw(s, f)
        d.text(((x - w) if side == "l" else x, 400), s, font=f, fill=(MUTED if side == "l" else GOLD) + (int(255 * k),))
        y = 460
        for ln in txt.split("|"):
            f2 = font("serif" if side == "l" else "serif_i", 68); im, pad, b = sprite(ln, f2, INK if side == "l" else GOLD)
            L.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int((x - (b[2] - b[0]) - pad) if side == "l" else (x - pad)), int(y - pad + 20 * (1 - k)))); y += 80

def c_counter(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    y = 330; d = ImageDraw.Draw(L)
    for j, (ti, num, lab) in enumerate(e["rows"]):
        k = eo(pr(t, ti - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4))); last = j == len(e["rows"]) - 1
        if k > 0:
            m = re.match(r"([^\d]*)(\d+)(.*)", num); shown = f"{m.group(1)}{int(round(int(m.group(2)) * eo(pr(t, ti, 0.6))))}{m.group(3)}" if m else num
            f = font("serif_i" if last else "serif", 120 if last else 96); im, pad, b = sprite(shown, f, GOLD if last else INK)
            L.alpha_composite(with_alpha(im, k), (int(CX0 - pad), int(y - pad)))
            im2, p2, b2 = sprite(lab, font("sans", 42), INK if last else MUTED)
            L.alpha_composite(with_alpha(blur_reveal(im2, k, 6), k), (int(CX0 + 250 - p2), int(y + (b[3] - b[1]) - (b2[3] - b2[1]) - p2 - 6)))
            if last: d.line([(CX0, y - 24), (CX0 + 600 * eo(k), y - 24)], fill=LINE + (int(60 * k),), width=1)
        y += 150 if not last else 170

def c_flow(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    gap = e.get("gap", 100); n = len(e["steps"]); y = 540 - (n * gap + 60) / 2; d = ImageDraw.Draw(L); x0 = CX0 + 20
    if e.get("title"): kicker(L, e["title"], CX0, y - 10, a); y += 70
    for j, (ti, txt) in enumerate(e["steps"]):
        k = eo(pr(t, ti - 0.08, 0.45)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k <= 0: break
        if j > 0: d.line([(x0, y - gap + 18), (x0, y - gap + 18 + (gap - 36) * eo(k))], fill=GOLD + (int(150 * k),), width=2)
        r = 10; d.ellipse([x0 - r, y + 8, x0 + r, y + 8 + 2 * r], outline=GOLD + (int(255 * k),), width=2, fill=(GOLD + (int(255 * k),)) if j == n - 1 else None)
        im, pad, _ = sprite(txt, font("sans", 46), INK); L.alpha_composite(with_alpha(blur_reveal(im, k, 6), k), (int(x0 + 44 - pad + 20 * (1 - k)), int(y - pad - 4)))
        y += gap

def c_dots(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(L); n = e["n"]; sp = 70; x0 = CMID - sp * (n - 1) / 2; y = 430
    kf = eo(pr(t, e["fade_at"], 0.9))
    for j in range(n):
        kj = eo(pr(t, e["t0"] + 0.06 * j, 0.4)) * a; one = j == e.get("one", 6); r = 18 + (7 * kf if one else 0)
        al = kj * (1 if one else 1 - 0.8 * kf); col = GOLD if (one and kf > 0.3) else INK; dy = -26 * kf if one else 0
        d.ellipse([x0 + j * sp - r, y - r + dy, x0 + j * sp + r, y + r + dy], fill=col + (int(255 * al),))
    for (ti, txt, yy, sty) in e.get("labels", []):
        k = eo(pr(t, ti - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k > 0: line_rich(L, txt, CMID, yy, 76 if sty == "big" else 44, k, base="serif" if sty == "big" else "sans", col=INK if sty == "big" else MUTED, align="center")

def c_timeline(L, t, e):
    """passado → presente → futuro: 'explica' (seta dourada) e 'não determina' (seta riscada)."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(L); xs = [CX0 + 40, CMID, CX1 - 40]; y = 520
    names = ["passado", "presente", "futuro"]
    for j, (x, nm) in enumerate(zip(xs, names)):
        k = eo(pr(t, e["t0"] + 0.2 * j, 0.5)) * a
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(GOLD if j == 0 else INK) + (int(255 * k),))
        im, pad, b = sprite(nm, font("serif_i" if j == 0 else "serif", 54), INK); L.alpha_composite(with_alpha(im, k), (int(x - (b[2] - b[0]) / 2 - pad), int(y + 30 - pad)))
    ke = eo(pr(t, e["explica"], 0.6)) * a
    if ke > 0:
        d.line([(xs[0] + 20, y), (xs[0] + 20 + (xs[1] - xs[0] - 40) * ke, y)], fill=GOLD + (int(230 * ke),), width=3)
        im, pad, b = sprite("explica", font("sans", 36), GOLD); L.alpha_composite(with_alpha(im, ke), (int((xs[0] + xs[1]) / 2 - (b[2] - b[0]) / 2 - pad), int(y - 70 - pad)))
    kn = eo(pr(t, e["nao"], 0.6)) * a
    if kn > 0:
        for xx in range(int(xs[1] + 20), int(xs[1] + 20 + (xs[2] - xs[1] - 40) * kn), 18): d.line([(xx, y), (xx + 9, y)], fill=MUTED + (int(200 * kn),), width=3)
        im, pad, b = sprite("não determina", font("sans", 36), MUTED); L.alpha_composite(with_alpha(im, kn), (int((xs[1] + xs[2]) / 2 - (b[2] - b[0]) / 2 - pad), int(y - 70 - pad)))
        kx = eo(pr(t, e["nao"] + 0.5, 0.4)) * a; cx_, cy_ = (xs[1] + xs[2]) / 2, y
        if kx > 0:
            d.line([(cx_ - 22, cy_ - 22), (cx_ - 22 + 44 * kx, cy_ - 22 + 44 * kx)], fill=GOLD + (255,), width=4)
            d.line([(cx_ + 22, cy_ - 22), (cx_ + 22 - 44 * kx, cy_ - 22 + 44 * kx)], fill=GOLD + (255,), width=4)

def c_lanes(L, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(L); fin = CX1 - 20; top = 300
    kicker(L, "largadas", CX0, top, a, col=MUTED); s = " ".join("CHEGADA"); f = font("caps", 24)
    d.text((fin - tw(s, f), top), s, font=f, fill=MUTED + (int(255 * a),))
    for yy in range(top + 50, 820, 18): d.line([(fin, yy), (fin, yy + 8)], fill=LINE + (int(90 * a),), width=2)
    act = None
    for name, t0 in e["active"]:
        if t >= t0: act = name
    ta = dict(e["active"]); t_all = ta.get("all", 1e9)
    for Ln, (y, xs) in e["lanes"].items():
        t_on = ta[Ln]; seen = t >= t_on or act == "all"; on = act in (Ln, "all")
        if not seen: continue
        kL = eo(pr(t, t_on, 0.6)) * a; dim = 1 if on else 0.4
        p = 0.25 * eio(pr(t, t_on, 3)) + 0.35 * eio(pr(t, t_all, 4)); xr = xs + (fin - 40 - xs) * p
        d.line([(xs, y), (fin, y)], fill=LINE + (int(40 * kL),), width=1)
        d.line([(xs, y), (xr, y)], fill=(GOLD if on else MUTED) + (int(230 * kL * dim),), width=3)
        d.ellipse([xr - 8, y - 8, xr + 8, y + 8], fill=(GOLD if on else MUTED) + (int(255 * kL * dim),))
        im, pad, b = sprite(Ln, font("serif_i", 60), GOLD if on else MUTED); L.alpha_composite(with_alpha(im, kL), (int(CX0 - pad), int(y - (b[3] - b[1]) / 2 - pad - 8)))
        x = xs; fc = font("sans", 32)
        for tc, txt in e["labels"][Ln]:
            if t < tc - 0.05: continue
            kc = eo(pr(t, tc - 0.05, 0.4)) * a; im, pad, b = sprite(txt, fc, INK)
            L.alpha_composite(with_alpha(blur_reveal(im, kc, 5), kc * (1 if on else 0.55)), (int(x - pad), int(y + 20 - pad + 12 * (1 - kc))))
            x += (b[2] - b[0]) + 30

# ------------------------------------------------------------------ tela cheia
def f_word(L, t, e):
    if not (e["t0"] <= t < e["t1"]): return
    size = e.get("size", 130); n = len(e["lines"]); y = 470 - n * size * 1.05 / 2
    a = env(t, e["t0"], e["t1"])
    if e.get("kicker"): kicker(L, e["kicker"], FX, y - 70, a, "center")
    for j, ln in enumerate(e["lines"]):
        k = eo(pr(t, e["t0"] + 0.25 * j, 0.7)) * (1 - eio(pr(t, e["t1"] - 0.35, 0.35)))
        if k > 0: line_rich(L, ln, FX, y, size, k, align="center", maxw=1400, alpha=min(1, k * 1.3))
        y += size * 1.05
    kr = eo(pr(t, e["t0"] + 0.5, 0.8)) * (1 - eio(pr(t, e["t1"] - 0.35, 0.35)))
    if kr > 0: ImageDraw.Draw(L).line([(FX - 120 * kr, y + 28), (FX + 120 * kr, y + 28)], fill=GOLD + (int(200 * kr),), width=2)

def f_verse(L, t, e):
    a = env(t, e["t0"], e["t1"], 0.7, 0.5)
    if a <= 0: return
    f = font("serif_i", e.get("size", 64)); lines = wrap(e["text"], f, 1300)
    y = 470 - (len(lines) * f.size * 1.22 + 90) / 2
    kicker(L, e["ref"], FX, y, a, "center"); ImageDraw.Draw(L).line([(FX - 50 * a, y + 46), (FX + 50 * a, y + 46)], fill=GOLD + (int(200 * a),), width=2)
    y += 90
    for j, ln in enumerate(lines):
        k = eo(pr(t, e["t0"] + 0.3 + 0.22 * j, 0.7)) * (1 - eio(pr(t, e["t1"] - 0.5, 0.5)))
        im, pad, b = sprite(ln, f, INK); L.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int(FX - (b[2] - b[0]) / 2 - pad), int(y - pad + 18 * (1 - k)))); y += f.size * 1.22

def chapter(L, t, e):
    a = env(t, e["t0"], e["t1"], 0.5, 0.45)
    if a <= 0: return
    num = f"{e['n']:02d}"; im, pad, b = sprite(num, font("serif_i", 150), GOLD)
    L.alpha_composite(with_alpha(im, a), (int(W / 2 - (b[2] - b[0]) / 2 - pad), int(300 - pad + 20 * (1 - a))))
    kicker(L, "capítulo", W / 2, 500, a, "center", col=MUTED)
    line_rich(L, e["title"], W / 2, 560, 104, eo(pr(t, e["t0"] + 0.2, 0.6)) * (1 - eio(pr(t, e["t1"] - 0.45, 0.45))), align="center", maxw=1500)
    kr = eo(pr(t, e["t0"] + 0.4, 0.7)) * a
    ImageDraw.Draw(L).line([(W / 2 - 90 * kr, 720), (W / 2 + 90 * kr, 720)], fill=GOLD + (int(200 * kr),), width=2)

def intro(L, t, e):
    a = env(t, e["t0"], e["t1"], 0.8, 0.6)
    if a <= 0: return
    kicker(L, e["kicker"], W / 2, 330, a, "center", col=MUTED)
    line_rich(L, e["title"], W / 2, 390, 170, eo(pr(t, e["t0"] + 0.3, 0.9)) * (1 - eio(pr(t, e["t1"] - 0.6, 0.6))), align="center", maxw=1600)
    kr = eo(pr(t, e["t0"] + 0.8, 0.8)) * a
    ImageDraw.Draw(L).line([(W / 2 - 140 * kr, 640), (W / 2 + 140 * kr, 640)], fill=GOLD + (int(200 * kr),), width=2)
    im, pad, b = sprite(e["sub"], font("sans", 34), MUTED); L.alpha_composite(with_alpha(im, eo(pr(t, e["t0"] + 1.0, 0.7)) * a), (int(W / 2 - (b[2] - b[0]) / 2 - pad), int(680 - pad)))

def endcard(L, t, e):
    a = eo(pr(t, e["t0"], 0.8))
    kicker(L, "estudo bíblico", 160, 330, a, col=MUTED)
    y = 380
    for j, ln in enumerate(e["lines"]):
        line_rich(L, ln, 160, y, 140, eo(pr(t, e["t0"] + 0.3 * j, 0.8)), maxw=900); y += 150
    im, pad, b = sprite(e["sub"], font("sans", 34), MUTED); L.alpha_composite(with_alpha(im, eo(pr(t, e["t0"] + 1.0, 0.7))), (int(160 - pad), int(y + 30 - pad)))

def lower3(L, t, e):
    k = eo(pr(t, e["t0"], 0.5)) * (1 - eio(pr(t, e["t1"] - 0.5, 0.5)))
    if k <= 0: return
    x, y, sz = e.get("x", CX0), e.get("y", 860), e.get("size", 52)
    im, pad, b = sprite(e["name"], font("serif", sz), INK); L.alpha_composite(with_alpha(im, k), (int(x - pad + 20 * (1 - k)), int(y - pad)))
    kicker(L, e["role"], x, y + sz * 1.27, k, col=GOLD, size=20)

BLOCKS = dict(c_title=c_title, c_verse=c_verse, c_statement=c_statement, c_list=c_list, c_versus=c_versus, c_counter=c_counter,
              c_flow=c_flow, c_dots=c_dots, c_timeline=c_timeline, c_lanes=c_lanes, f_word=f_word, f_verse=f_verse,
              chapter=chapter, intro=intro, endcard=endcard, lower3=lower3)
STATE = {"f_word": "full", "f_verse": "full", "chapter": "card", "intro": "card", "endcard": "card"}
