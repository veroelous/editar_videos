"""Estilo ELEGANTE para reels (editorial, sóbrio): fundo grafite com grão, moldura limpa, tipografia
Inter + Instrument Serif (itálico como destaque), um único acento dourado, entradas com desfoque suave.
Marcação de texto: trechos entre *asteriscos* saem em serifa itálica dourada.
Todas as funções desenham numa camada RGBA (W x H) no instante t."""
import math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, os
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
from fx import eo, eio, back, pr, cl, tw, with_alpha, blur_reveal

FD = "/usr/share/fonts/opentype/inter/"; SERIF = "/home/user/editar_videos/pipelines/efeitos/fonts/"
_f = {}
def font(kind, size):
    k = (kind, int(size))
    if k not in _f:
        path = {"sans": FD + "InterDisplay-Medium.otf", "sans_b": FD + "InterDisplay-SemiBold.otf", "sans_x": FD + "InterDisplay-Bold.otf",
                "caps": FD + "Inter-Medium.otf", "serif": SERIF + "InstrumentSerif-Regular.ttf", "serif_i": SERIF + "InstrumentSerif-Italic.ttf"}[kind]
        _f[k] = ImageFont.truetype(path, int(size))
    return _f[k]

W, H = 1080, 1920
INK = (244, 241, 234); MUTED = (150, 148, 142); GOLD = (214, 182, 122); BG0 = (19, 19, 21); BG1 = (9, 9, 11); LINE = (255, 255, 255)
FB = (70, 176, 1010, 1116)          # moldura do rosto (940x940)
ZONE = (70, 1330, 1010, 1840)       # área dos gráficos

def sprite(text, f, col, pad=30):
    b = f.getbbox(text); w, h = b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0)); ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), text, font=f, fill=col + (255,))
    return im, pad, b

def rich(line, size, base="serif", col=INK, acc=GOLD, ital="serif_i"):
    """Linha com marcação *destaque*: retorna lista de (texto, fonte, cor)."""
    out = []
    for j, part in enumerate(re.split(r"\*", line)):
        if not part: continue
        out.append((part, font(ital, size) if j % 2 else font(base, size), acc if j % 2 else col))
    return out

def draw_rich(layer, line, cx, y, size, k, base="serif", col=INK, align="center", x0=None, maxw=920, alpha=1.0):
    """Desenha uma linha rica centralizada (ou à esquerda em x0) com entrada suave (k 0..1). y = topo da caixa."""
    while True:
        parts = rich(line, size, base, col); wsum = sum(tw(p[0], p[1]) for p in parts)
        if wsum <= maxw or size < 30: break
        size = int(size * 0.94)
    asc = font(base, size).getmetrics()[0]
    x = (cx - wsum / 2) if align == "center" else x0
    for txt, f, c in parts:
        im = Image.new("RGBA", (tw(txt, f) + 60, int(size * 1.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        b = f.getbbox(txt); d.text((30 - b[0], 30 + asc - f.getmetrics()[0]), txt, font=f, fill=c + (255,))
        im = with_alpha(blur_reveal(im, k, 8), alpha) if k < 1 or alpha < 1 else im
        layer.alpha_composite(im, (int(x - 30), int(y - 30 + 26 * (1 - eo(k)))))
        x += tw(txt, f) + (font(base, size).getlength(" ") if False else 0)
    return size

def env(t, t0, t1, din=0.5, dout=0.4):
    return eo(pr(t, t0, din)) * (1 - eio(pr(t, t1 - dout, dout)))

# ------------------------------------------------------------------ fundo
_grain = None
_bgc = {}
def background(t):
    key = round(t * 5)
    if key not in _bgc:
        if len(_bgc) > 4: _bgc.clear()
        _bgc[key] = _background(key / 5)
    bg = _bgc[key].copy(); bg.alpha_composite(_grain[int(t * 12) % 3]); return bg
def _background(t):
    global _grain
    g = np.linspace(0, 1, 96)[:, None, None]
    base = np.array(BG0, np.float32) * (1 - g) + np.array(BG1, np.float32) * g
    img = np.repeat(base, 54, axis=1)
    yy, xx = np.mgrid[0:96, 0:54].astype(np.float32)
    br = 0.5 + 0.5 * math.sin(t * 0.35)
    glow = np.exp(-((xx - 27 - 4 * math.sin(t * 0.2)) ** 2 / 500 + (yy - 34) ** 2 / 900))[..., None]
    img = img + glow * np.array(GOLD, np.float32) * (0.06 + 0.03 * br)
    bg = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert("RGBA")
    if _grain is None:
        rng = np.random.default_rng(1)
        _grain = [Image.fromarray(np.dstack([np.full((H, W), 255, np.uint8)] * 3 + [(rng.random((H, W)) * 16).astype(np.uint8)]), "RGBA") for _ in range(3)]
    return bg

def topbar(layer, t, total, left, right):
    d = ImageDraw.Draw(layer)
    d.rectangle([0, 0, W * min(1, t / total), 3], fill=GOLD + (230,))
    f = font("caps", 25); L = " ".join(left.upper()); R = " ".join(right.upper())
    d.text((FB[0], 98), L, font=f, fill=MUTED + (255,))
    d.text((FB[2] - tw(R, f), 98), R, font=f, fill=MUTED + (255,))
    x1 = FB[0] + tw(L, f) + 24; x2 = FB[2] - tw(R, f) - 24
    if x2 > x1: d.line([(x1, 112), (x2, 112)], fill=LINE + (40,), width=1)

# ------------------------------------------------------------------ moldura
_fcache = {}
def frame(img, t, z, pulse=0.0, pop=1.0):
    """Recorte do rosto (img quadrada) com zoom z, cantos arredondados, sombra suave e filete claro."""
    s = img.width; cw = s / z; c0 = (s - cw) / 2; cy0 = min(max(0, s * 0.47 - cw / 2), s - cw)
    fw, fh = FB[2] - FB[0], FB[3] - FB[1]
    sc = 1 + 0.012 * pulse
    pw, ph = int(fw * sc), int(fh * sc)
    piece = img.resize((pw, ph), Image.BICUBIC, box=(c0, cy0, c0 + cw, cy0 + cw)).convert("RGBA")
    if pulse > 0.05: piece = piece.filter(ImageFilter.GaussianBlur(2.2 * pulse))
    if (pw, ph) not in _fcache:
        sh = Image.new("RGBA", (pw + 160, ph + 160), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([80, 100, pw + 80, ph + 100], radius=30, fill=(0, 0, 0, 150))
        m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=26, fill=255)
        if len(_fcache) > 40: _fcache.clear()
        _fcache[(pw, ph)] = (sh.filter(ImageFilter.GaussianBlur(30)), m)
    shb, m = _fcache[(pw, ph)]
    lay = shb.copy()
    lay.paste(piece, (80, 80), m)
    ImageDraw.Draw(lay).rounded_rectangle([80, 80, 80 + pw - 1, 80 + ph - 1], radius=26, outline=LINE + (46,), width=2)
    return lay, (FB[0] + fw / 2, FB[1] + fh / 2)

# ------------------------------------------------------------------ legenda (ordem natural, palavra acende ao ser dita)
def caption(layer, words, t, cy=1250, size=54, maxw=920, t_end=None):
    """words: [(t0, t1, texto, destaque)] — frase inteira aparece suave; palavras ainda não ditas ficam a 35%."""
    if not words: return
    k_in = eo(pr(t, words[0][0] - 0.12, 0.2)); k_out = 1 - pr(t, t_end - 0.15, 0.15) if t_end else 1
    if k_in <= 0 or k_out <= 0: return
    items = []
    for (s0, s1, txt, strong) in words:
        f = font("serif_i", size * 1.18) if strong else font("sans", size)
        items.append((txt, f, GOLD if strong else INK, s0))
    sp = font("sans", size).getlength(" ")
    lines, cur, cw = [], [], 0
    for it in items:
        w = tw(it[0], it[1])
        if cur and cw + sp + w > maxw: lines.append((cur, cw)); cur, cw = [], 0
        cur.append((it, w)); cw += (sp if len(cur) > 1 else 0) + w
    lines.append((cur, cw))
    lh = size * 1.32; y0 = cy - lh * len(lines) / 2
    asc = font("sans", size).getmetrics()[0]
    for li, (row, rw) in enumerate(lines):
        x = W / 2 - rw / 2; y = y0 + li * lh
        for (txt, f, col, s0), w in row:
            said = eo(pr(t, s0 - 0.05, 0.12)); a = (0.32 + 0.68 * said) * k_in * k_out
            im = Image.new("RGBA", (w + 40, int(size * 1.7)), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((20 - f.getbbox(txt)[0], 20 + asc - f.getmetrics()[0]), txt, font=f, fill=col + (int(255 * a),))
            layer.alpha_composite(im, (int(x - 20), int(y - 20 + 10 * (1 - k_in))))
            x += w + sp

# ------------------------------------------------------------------ blocos gráficos
def kicker(layer, text, x, y, k, align="left", col=GOLD):
    f = font("caps", 27); s = " ".join(text.upper()); d = ImageDraw.Draw(layer)
    w = tw(s, f); xx = x if align == "left" else x - w / 2
    d.text((xx, y), s, font=f, fill=col + (int(255 * k),))
    return w

def rule(layer, x0, y, w, k, col=GOLD, a=200):
    if k > 0: ImageDraw.Draw(layer).line([(x0, y), (x0 + w * eo(k), y)], fill=col + (int(a * min(1, k * 2)),), width=2)

def b_cover(layer, t, e):
    """Capa (visível já no quadro 0): kicker + título em serifa com destaque itálico."""
    a = 1 - eio(pr(t, e["t1"] - 0.45, 0.45))
    if a <= 0: return
    y = 1330; kk = 1.0
    sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if e.get("kicker"): kicker(sub, e["kicker"], W / 2, y, 1, "center"); y += 64
    size = e.get("size", 128)
    for j, ln in enumerate(e["lines"]):
        size = draw_rich(sub, ln, W / 2, y, size, 1.0) ; y += size * 1.02
    layer.alpha_composite(with_alpha(sub, a), (0, int(-30 * eio(pr(t, e["t1"] - 0.45, 0.45)))))

def b_title(layer, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    y = e.get("y", 1400); size = e.get("size", 112)
    if e.get("kicker"): kicker(layer, e["kicker"], W / 2, y - 64, a, "center")
    for j, ln in enumerate(e["lines"]):
        k = eo(pr(t, e["t0"] + 0.12 * j, 0.55)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        size = draw_rich(layer, ln, W / 2, y, size, k, alpha=min(1, k * 1.5)); y += size * 1.05

def b_verse(layer, t, e):
    a = env(t, e["t0"], e["t1"], 0.6)
    if a <= 0: return
    x0 = ZONE[0] + 30; y = 1370
    kicker(layer, e["ref"], x0, y, a)
    rule(layer, x0, y + 46, 80, pr(t, e["t0"] + 0.2, 0.5))
    f = font("serif_i", e.get("size", 62)); words = e["text"].split(); line = ""; lines = []
    for w in words:
        if tw((line + " " + w).strip(), f) > 880 and line: lines.append(line); line = w
        else: line = (line + " " + w).strip()
    lines.append(line); y += 84
    for j, ln in enumerate(lines):
        k = eo(pr(t, e["t0"] + 0.25 + 0.18 * j, 0.6)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        im, pad, b = sprite(ln, f, INK); layer.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int(x0 - pad), int(y - pad + 20 * (1 - k))))
        y += f.size * 1.18

def b_statement(layer, t, e):
    if not (e["t0"] <= t < e["t1"]): return
    y = e.get("y", 1385); size = e.get("size", 78)
    for ln, tl in e["lines"]:
        k = eo(pr(t, tl - 0.1, 0.6)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k > 0: size_ = draw_rich(layer, ln, W / 2, y, size, k, alpha=min(1, k * 1.4))
        y += size * 1.12

def b_list(layer, t, e):
    """Lista editorial: numerais em serifa + texto; risco fino opcional em todos os itens."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    x0 = ZONE[0] + 30; y = 1360
    if e.get("title"): kicker(layer, e["title"], x0, y, a); y += 64
    fs = font("sans", e.get("size", 50)); fn = font("serif_i", 58); d = ImageDraw.Draw(layer)
    for j, it in enumerate(e["items"]):
        ti, txt = it[0], it[1]
        k = eo(pr(t, ti - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k <= 0: y += e.get("gap", 96); continue
        if e.get("numbered", True):
            im, pad, _ = sprite(f"{j + 1:02d}", fn, GOLD); layer.alpha_composite(with_alpha(im, k), (int(x0 - pad), int(y - pad - 6)))
        tx = x0 + (100 if e.get("numbered", True) else 0)
        im, pad, b = sprite(txt, fs, INK); layer.alpha_composite(with_alpha(blur_reveal(im, k, 8), k), (int(tx - pad + 20 * (1 - k)), int(y - pad)))
        if e.get("strike") is not None and t >= e["strike"] + 0.1 * j:
            ks = eo(pr(t, e["strike"] + 0.1 * j, 0.35)); yy = y + (b[3] - b[1]) / 2 + 2
            d.line([(tx - 6, yy), (tx - 6 + (b[2] - b[0] + 12) * ks, yy)], fill=GOLD + (int(230 * k),), width=3)
        if j < len(e["items"]) - 1: d.line([(x0, y + e.get("gap", 96) - 24), (ZONE[2] - 30, y + e.get("gap", 96) - 24)], fill=LINE + (int(22 * k),), width=1)
        y += e.get("gap", 96)

def b_versus(layer, t, e):
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(layer); cx = W / 2
    kv = eo(pr(t, e["t0"], 0.6)); d.line([(cx, 1380), (cx, 1380 + 380 * kv)], fill=LINE + (int(60 * a),), width=1)
    for side, (lab, txt, ti) in (("l", e["left"]), ("r", e["right"])):
        k = eo(pr(t, ti - 0.1, 0.55)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k <= 0: continue
        x = cx - 40 if side == "l" else cx + 40
        f = font("caps", 22); s = " ".join(lab.upper()); w = tw(s, f)
        d.text(((x - w) if side == "l" else x, 1400), s, font=f, fill=(MUTED if side == "l" else GOLD) + (int(255 * k),))
        y = 1460
        for ln in txt.split("|"):
            f2 = font("serif" if side == "l" else "serif_i", 66); im, pad, b = sprite(ln, f2, INK if side == "l" else GOLD)
            im = with_alpha(blur_reveal(im, k, 8), k)
            layer.alpha_composite(im, (int((x - (b[2] - b[0]) - pad) if side == "l" else (x - pad)), int(y - pad + 20 * (1 - k)))); y += 78

def b_counter(layer, t, e):
    """Linhas com número grande em serifa + rótulo; a última em dourado (total). Números contam até o valor."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    x0 = ZONE[0] + 40; y = 1370; d = ImageDraw.Draw(layer)
    for j, (ti, num, lab) in enumerate(e["rows"]):
        k = eo(pr(t, ti - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        last = j == len(e["rows"]) - 1 and e.get("total", True)
        if k > 0:
            m = re.match(r"([^\d]*)(\d+)(.*)", num)
            if m:
                v = int(m.group(2)); shown = f"{m.group(1)}{int(round(v * eo(pr(t, ti, 0.6))))}{m.group(3)}"
            else: shown = num
            f = font("serif_i" if last else "serif", 120 if last else 96)
            im, pad, b = sprite(shown, f, GOLD if last else INK); layer.alpha_composite(with_alpha(im, k), (int(x0 - pad), int(y - pad)))
            fl = font("sans", 44); im2, p2, b2 = sprite(lab, fl, INK if last else MUTED)
            layer.alpha_composite(with_alpha(blur_reveal(im2, k, 6), k), (int(x0 + 230 - p2), int(y + (b[3] - b[1]) - (b2[3] - b2[1]) - p2 - 6)))
        if last and k > 0: d.line([(x0, y - 22), (x0 + 600 * eo(k), y - 22)], fill=LINE + (int(60 * k),), width=1)
        y += 150 if not last else 170

def b_flow(layer, t, e):
    """Linha do tempo vertical: pontos ligados por fio fino, um passo por palavra."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    x0 = ZONE[0] + 60; y = 1370; d = ImageDraw.Draw(layer); gap = e.get("gap", 82)
    if e.get("title"): kicker(layer, e["title"], ZONE[0] + 30, y - 10, a); y += 60
    for j, (ti, txt) in enumerate(e["steps"]):
        k = eo(pr(t, ti - 0.08, 0.45)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k <= 0: break
        if j > 0: d.line([(x0, y - gap + 16), (x0, y - gap + 16 + (gap - 32) * eo(k))], fill=GOLD + (int(150 * k),), width=2)
        r = 9; d.ellipse([x0 - r, y - r + 16, x0 + r, y + r + 16], outline=GOLD + (int(255 * k),), width=2,
                         fill=(GOLD + (int(255 * k),)) if j == len(e["steps"]) - 1 else None)
        im, pad, _ = sprite(txt, font("sans", 46), INK); layer.alpha_composite(with_alpha(blur_reveal(im, k, 6), k), (int(x0 + 40 - pad + 20 * (1 - k)), int(y - pad - 6)))
        y += gap

def b_dots(layer, t, e):
    """n pessoas como pontos; em fade_at somem todos menos um, que acende em dourado."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(layer); n = e["n"]; cx = W / 2; y = 1480; sp = 80; x0 = cx - sp * (n - 1) / 2
    kf = eo(pr(t, e["fade_at"], 0.9)) if e.get("fade_at") else 0
    for j in range(n):
        kj = eo(pr(t, e["t0"] + 0.06 * j, 0.4)) * a
        one = j == e.get("one", 6)
        r = 20 + (8 * kf if one else 0)
        alpha = kj * (1 if one else 1 - 0.8 * kf)
        col = GOLD if (one and kf > 0.3) else INK
        d.ellipse([x0 + j * sp - r, y - r - (30 * kf if one else 0), x0 + j * sp + r, y + r - (30 * kf if one else 0)], fill=col + (int(255 * alpha),))
    for (ti, txt, yy, sty) in e.get("labels", []):
        k = eo(pr(t, ti - 0.08, 0.5)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
        if k > 0: draw_rich(layer, txt, W / 2, yy, 70 if sty == "big" else 48, k, base="serif" if sty == "big" else "sans", col=INK if sty == "big" else MUTED)

def b_lanes(layer, t, e):
    """Pistas de largada em traço fino (A, B, C) com rótulos em versalete; um ponto avança em cada pista."""
    a = env(t, e["t0"], e["t1"])
    if a <= 0: return
    d = ImageDraw.Draw(layer); fin = ZONE[2] - 40; top = 1390
    kicker(layer, "largadas", ZONE[0] + 30, top - 30, a, col=MUTED); s = " ".join("CHEGADA"); f = font("caps", 24)
    d.text((fin - tw(s, f), top - 30), s, font=f, fill=MUTED + (int(255 * a),))
    for yy in range(top + 20, 1830, 18): d.line([(fin, yy), (fin, yy + 8)], fill=LINE + (int(90 * a),), width=2)
    act = None
    for name, t0 in e["active"]:
        if t >= t0: act = name
    t_all = dict(e["active"]).get("all", 1e9)
    for L, (y, xs) in e["lanes"].items():
        t_on = dict(e["active"])[L]; seen = t >= t_on or act == "all"; on = act in (L, "all")
        if not seen: continue
        kL = eo(pr(t, t_on, 0.6)) * a; dim = 1 if on else 0.4
        p = 0.25 * eio(pr(t, t_on, 3)) + 0.35 * eio(pr(t, t_all, 4))
        xr = xs + (fin - 40 - xs) * p
        d.line([(xs, y), (fin, y)], fill=LINE + (int(40 * kL),), width=1)
        d.line([(xs, y), (xr, y)], fill=(GOLD if on else MUTED) + (int(230 * kL * dim),), width=3)
        d.ellipse([xr - 8, y - 8, xr + 8, y + 8], fill=(GOLD if on else MUTED) + (int(255 * kL * dim),))
        fL = font("serif_i", 64); im, pad, b = sprite(L, fL, GOLD if on else MUTED)
        layer.alpha_composite(with_alpha(im, kL), (int(ZONE[0] + 30 - pad), int(y - (b[3] - b[1]) / 2 - pad - 8)))
        x = xs
        for tc, txt in e["labels"][L]:
            if t < tc - 0.05: continue
            kc = eo(pr(t, tc - 0.05, 0.4)) * a
            fc = font("sans", 40); im, pad, b = sprite(txt, fc, INK)
            layer.alpha_composite(with_alpha(blur_reveal(im, kc, 5), kc * (1 if on else 0.55)), (int(x - pad), int(y + 22 - pad + 12 * (1 - kc))))
            x += (b[2] - b[0]) + 26
            if x < fin - 40:
                d.text((x - 18, y + 22), "·", font=fc, fill=MUTED + (int(200 * kc),))

def b_hero(layer, t, e):
    """Clímax: título grande em serifa, entrada lenta com desfoque e um filete dourado que se abre."""
    if not (e["t0"] <= t < e["t1"]): return
    y = e.get("y", 1380); size = e.get("size", 140)
    for j, ln in enumerate(e["lines"]):
        k = eo(pr(t, e["t0"] + 0.35 * j, 0.8)) * (1 - eio(pr(t, e["t1"] - 0.35, 0.35)))
        if k > 0: draw_rich(layer, ln, W / 2, y, size, k, alpha=min(1, k * 1.3))
        y += size * 1.02
    kr = eo(pr(t, e["t0"] + 0.5, 0.9)) * (1 - eio(pr(t, e["t1"] - 0.35, 0.35)))
    if kr > 0: ImageDraw.Draw(layer).line([(W / 2 - 160 * kr, y + 30), (W / 2 + 160 * kr, y + 30)], fill=GOLD + (int(220 * kr),), width=2)

def b_cta(layer, t, e):
    k = eo(pr(t, e["t0"], 0.6))
    if k <= 0: return
    kicker(layer, "comente", W / 2, 1400, k, "center", col=MUTED)
    draw_rich(layer, f"*{e['word']}*", W / 2, 1460, 170, k)
    if e.get("line"):
        k2 = eo(pr(t, e["t0"] + 0.5, 0.6)); im, pad, b = sprite(e["line"], font("sans", 40), MUTED)
        layer.alpha_composite(with_alpha(im, k2), (int(W / 2 - (b[2] - b[0]) / 2 - pad), int(1690 - pad)))

BLOCKS = dict(cover=b_cover, title=b_title, verse=b_verse, statement=b_statement, list=b_list, versus=b_versus, counter=b_counter,
              flow=b_flow, dots=b_dots, lanes=b_lanes, hero=b_hero, cta=b_cta)
