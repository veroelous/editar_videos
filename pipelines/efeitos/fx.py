"""Biblioteca de efeitos (PIL) — referências reels_claude + nelmoricalde_meet.
Todas as funções desenham em uma camada RGBA (W x H) num instante t (segundos).
Convenção: t0 = início do elemento; animações com ease-out; nada linear.
Ordem de camadas recomendada por frame:
  vídeo  →  títulos/legendas "no espaço"  →  máscara da pessoa (restaura o sujeito por cima)
         →  UI flutuante (badges, toasts, cards)  →  legenda "chapada" (se não for atrás da pessoa)
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + name + ".otf", int(size))
    return _fc[k]

# paletas
PAL_TECH = dict(bg=(12, 12, 28), ink=(255, 255, 255), accent=(232, 115, 74), cream=(243, 227, 176), glow=(132, 96, 255), muted=(150, 150, 170))
PAL_EBO = dict(bg=(10, 10, 14), ink=(255, 255, 255), accent=(43, 107, 251), cream=(242, 238, 230), glow=(43, 107, 251), muted=(150, 150, 160))

def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.7): x = cl(x) - 1; return x * x * ((s + 1) * x + s) + 1
def pr(t, t0, d): return cl((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)
def tw(s, f): b = f.getbbox(s); return b[2] - b[0]

def with_alpha(img, a):
    if a >= 1: return img
    arr = np.asarray(img).copy(); arr[..., 3] = (arr[..., 3] * max(0, a)).astype(np.uint8); return Image.fromarray(arr)

def text_sprite(text, font, fill, shadow=True, pad=24):
    """Texto num sprite RGBA próprio (para poder desfocar/escalar isoladamente)."""
    b = font.getbbox(text); w, h = b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - b[0], pad - b[1] + 4), text, font=font, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((pad - b[0], pad - b[1]), text, font=font, fill=fill)
    return im, pad

def blur_reveal(sprite, k, max_blur=9):
    """k 0..1: desfocado+transparente -> nítido."""
    if k >= 1: return sprite
    s = sprite.filter(ImageFilter.GaussianBlur(max_blur * (1 - k))) if k < 0.98 else sprite
    return with_alpha(s, 0.25 + 0.75 * k)

# ---------------------------------------------------------------- 1. legenda em duas camadas
def caption2(layer, words, t, cx, cy, pal, size_small=46, size_big=62, maxw=860, t_end=None):
    """words: [(t_start, t_end, texto, forte:bool)] de UMA frase.
    Palavras de ligação em branco (linha de cima), palavras fortes maiores em creme (linha de baixo).
    Cada palavra entra com desfoque->foco; a frase sai desfocando em t_end."""
    fs, fb = F("InterDisplay-SemiBold", size_small), F("InterDisplay-ExtraBold", size_big)
    top = [w for w in words if not w[3]]; bot = [w for w in words if w[3]]
    if not bot: top, bot = words[:max(1, len(words) // 2)], words[max(1, len(words) // 2):]
    kout = pr(t, t_end - 0.12, 0.12) if t_end else 0
    for row, font, col, y in [(top, fs, pal["ink"], cy - size_big * 0.55), (bot, fb, pal["cream"], cy + size_small * 0.35)]:
        if not row: continue
        sp = tw(" ", font); widths = [tw(w[2], font) for w in row]
        x = cx - (sum(widths) + sp * (len(row) - 1)) / 2
        for (ts, te, txt, strong), wd in zip(row, widths):
            if t >= ts - 0.04:
                k = eo(pr(t, ts - 0.04, 0.14)) * (1 - kout)
                spr, pad = text_sprite(txt, font, col + (255,))
                spr = blur_reveal(spr, k if kout == 0 else 1 - kout, 10)
                layer.alpha_composite(spr, (int(x - pad), int(y - pad)))
            x += wd + sp

# ---------------------------------------------------------------- 2. badge numérico
def number_badge(layer, n, t, t0, t1, x, y, pal, size=118, color=None):
    if not (t0 <= t < t1 + 0.25): return
    k = back(pr(t, t0, 0.2), 2.2); ko = pr(t, t1, 0.25)
    s = size * k; col = color or pal["accent"]
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = size
    d.rounded_rectangle([c - s / 2 + 6, c - s / 2 + 12, c + s / 2 + 6, c + s / 2 + 12], radius=s * 0.24, fill=(0, 0, 0, 90))
    im = im.filter(ImageFilter.GaussianBlur(8)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([c - s / 2, c - s / 2, c + s / 2, c + s / 2], radius=s * 0.24, fill=col + (255,))
    if k > 0.6:
        f = F("InterDisplay-Black", int(size * 0.62)); b = f.getbbox(str(n))
        d.text((c - (b[2] - b[0]) / 2 - b[0], c - (b[3] - b[1]) / 2 - b[1]), str(n), font=f, fill=(255, 255, 255, 255))
    layer.alpha_composite(with_alpha(im, 1 - ko), (int(x - size), int(y - size)))

# ---------------------------------------------------------------- 3. toasts, chips e etiquetas
def toast(layer, text, t, t0, t1, x, y, pal, dot=(235, 64, 52), size=30):
    if not (t0 <= t < t1 + 0.25): return
    k = eo(pr(t, t0, 0.25)); ko = pr(t, t1, 0.25)
    f = F("Inter-SemiBold", size); w = tw(text, f) + 80; h = size + 34
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 26, w + 20, h + 26], radius=h / 2, fill=(0, 0, 0, 110)); im = im.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(im); d.rounded_rectangle([20, 20, w + 20, h + 20], radius=h / 2, fill=(22, 22, 30, 235), outline=(255, 255, 255, 40), width=2)
    pulse = 0.6 + 0.4 * math.sin(t * 6)
    d.ellipse([44, 20 + h / 2 - 8, 60, 20 + h / 2 + 8], fill=dot + (int(255 * pulse),))
    d.text((74, 20 + (h - size) / 2 - 3), text, font=f, fill=(235, 235, 240, 255))
    layer.alpha_composite(with_alpha(im, k * (1 - ko)), (int(x - 20), int(y - 20 + 14 * (1 - k))))

def chip_list(layer, items, t, x, y, pal, t1=None, w=360):
    """items: [(t_aparece, titulo, subtitulo)] — chips empilhados com número creme (lista de avisos)."""
    for i, (ta, title, sub) in enumerate(items):
        if t < ta: continue
        k = eo(pr(t, ta, 0.25)); ko = pr(t, t1, 0.25) if t1 else 0
        h = 86; im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 26, w + 20, h + 26], radius=18, fill=(0, 0, 0, 100)); im = im.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 20, w + 20, h + 20], radius=18, fill=(20, 20, 30, 235), outline=(255, 255, 255, 36), width=2)
        d.rounded_rectangle([36, 40, 82, 86], radius=10, fill=pal["cream"] + (255,))
        fn = F("InterDisplay-Black", 30); b = fn.getbbox(str(i + 1)); d.text((59 - (b[2] - b[0]) / 2 - b[0], 63 - (b[3] - b[1]) / 2 - b[1]), str(i + 1), font=fn, fill=(20, 20, 30, 255))
        d.text((98, 36), title, font=F("Inter-Bold", 28), fill=(245, 245, 248, 255)); d.text((98, 70), sub, font=F("Inter-Medium", 22), fill=pal["muted"] + (255,))
        layer.alpha_composite(with_alpha(im, k * (1 - ko)), (int(x - 20 + 40 * (1 - k)), int(y - 20 + i * (h + 14))))

def section_tag(layer, text, t, t0, t1, x, y, pal, size=26):
    if not (t0 <= t < t1 + 0.2): return
    k = back(pr(t, t0, 0.22)); ko = pr(t, t1, 0.2)
    f = F("InterDisplay-ExtraBold", size); w = tw(text, f) + 36; h = size + 22
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=10, fill=pal["cream"] + (255,)); d.text((18, 9), text, font=f, fill=(20, 20, 30, 255))
    im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.BICUBIC) if k < 1 else im
    layer.alpha_composite(with_alpha(im, 1 - ko), (int(x), int(y)))

# ---------------------------------------------------------------- 4. título cinético (letra a letra + espalhar)
def kinetic_title(layer, kicker, title, t, t0, cx, y, pal, size=150, exit_t=None, per_letter=0.05, color=None):
    col = color or pal["cream"]
    fk = F("Inter-Bold", int(size * 0.22)); kk = eo(pr(t, t0, 0.3))
    if kicker:
        spaced = " ".join(kicker.upper())
        spr, pad = text_sprite(spaced, fk, (255, 255, 255, 255)); spr = blur_reveal(spr, kk)
        if exit_t: spr = with_alpha(spr, 1 - pr(t, exit_t, 0.25))
        layer.alpha_composite(spr, (int(cx - spr.width / 2), int(y - size * 0.42 - pad)))
    f = F("InterDisplay-Black", size); total = tw(title, f); x = cx - total / 2
    rng = np.random.default_rng(len(title))
    for i, ch in enumerate(title):
        cw = tw(ch, f) if ch != " " else tw(" ", f)
        ts = t0 + 0.15 + i * per_letter
        if t >= ts and ch != " ":
            k = eo(pr(t, ts, 0.12)); spr, pad = text_sprite(ch, f, col + (255,))
            spr = blur_reveal(spr, k, 12); dx, dy, rot = 0, 18 * (1 - k), 0
            if exit_t and t >= exit_t:
                ke = eio(pr(t, exit_t + i * 0.02, 0.5)); ang = rng.uniform(-1, 1)
                dx, dy, rot = ang * 500 * ke, (rng.uniform(-1, 0.4)) * 400 * ke, ang * 220 * ke
                spr = with_alpha(spr.rotate(rot, expand=True, resample=Image.BICUBIC), 1 - ke)
            layer.alpha_composite(spr, (int(x - pad + dx), int(y - pad + dy)))
        x += cw

# ---------------------------------------------------------------- 5. painel de vidro
def glass_panel(frame_rgba, box, t, t0, t1, radius=36, tint=(255, 255, 255), alpha=0.18, blur=22):
    """Vidro fosco: desfoca o que está atrás dentro de box e aplica um véu claro + borda fina. Retorna o frame."""
    if not (t0 <= t < t1 + 0.3): return frame_rgba
    k = eo(pr(t, t0, 0.3)) * (1 - pr(t, t1, 0.3))
    x0, y0, x1, y1 = [int(v) for v in box]; y0 += int(30 * (1 - k)); y1 += int(30 * (1 - k))
    reg = frame_rgba.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    veil = Image.new("RGBA", reg.size, tint + (int(255 * alpha),)); reg.alpha_composite(veil)
    m = Image.new("L", reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=int(255 * k))
    frame_rgba.paste(reg, (x0, y0), m)
    d = ImageDraw.Draw(frame_rgba); d.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, int(90 * k)), width=2)
    return frame_rgba

# ---------------------------------------------------------------- 6. transição desfoque + encolher para card
def shrink_to_card(frame_rgb, k, card_box, bg, W, H, radius=40, glow=(132, 96, 255)):
    """k 0..1: tela cheia -> card (box). Primeiros 15% = desfoque forte; resto = encolhe com ease-out."""
    kb = cl(k / 0.15); ks = eo(cl((k - 0.1) / 0.9))
    src = frame_rgb.filter(ImageFilter.GaussianBlur(18 * (1 - abs(kb * 2 - 1)) if k < 0.2 else 0))
    x0, y0, x1, y1 = card_box
    bx = (0 + (x0 - 0) * ks, 0 + (y0 - 0) * ks, W + (x1 - W) * ks, H + (y1 - H) * ks)
    out = bg.copy() if isinstance(bg, Image.Image) else Image.new("RGB", (W, H), bg)
    w, h = int(bx[2] - bx[0]), int(bx[3] - bx[1])
    sw, sh = frame_rgb.size; ar = w / h
    cw = min(sw, sh * ar); ch = cw / ar; cx0 = (sw - cw) / 2; cy0 = (sh - ch) * 0.35
    piece = src.resize((max(1, w), max(1, h)), Image.BICUBIC, box=(cx0, cy0, cx0 + cw, cy0 + ch))
    m = Image.new("L", piece.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=int(radius * ks), fill=255)
    if ks > 0.05:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([bx[0] - 4, bx[1] - 4, bx[2] + 4, bx[3] + 4], radius=int(radius * ks) + 4, outline=glow + (int(200 * ks),), width=6)
        out = out.convert("RGBA"); out.alpha_composite(g.filter(ImageFilter.GaussianBlur(6))); out = out.convert("RGB")
    out.paste(piece, (int(bx[0]), int(bx[1])), m)
    return out

def dark_bg(W, H, pal):
    """Fundo azul-marinho com vinheta roxa (para demos/templates)."""
    y, x = np.mgrid[0:H, 0:W]; cx, cy = W / 2, H * 0.55
    r = np.sqrt(((x - cx) / W) ** 2 + ((y - cy) / H) ** 2)
    base = np.array(pal["bg"], np.float32); glow = np.array(pal["glow"], np.float32)
    img = base[None, None, :] + glow[None, None, :] * np.clip(0.28 - r * 0.5, 0, 1)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

# ---------------------------------------------------------------- 7. template "Exemplo N"
def example_template(bg, person_rgb, demo_rgba, kicker, title, caption_words, t, t0, pal, W=1080, H=1920):
    """Topo: demo (card). Base esq.: pessoa em card com borda brilhante. Base dir.: kicker + título + legenda curta."""
    out = bg.copy().convert("RGBA")
    k = eo(pr(t, t0, 0.35))
    if demo_rgba is not None:
        dm = with_alpha(demo_rgba, k); out.alpha_composite(dm, (int((W - dm.width) / 2), int(70 - 60 * (1 - k))))
    card = (40, int(H * 0.53), 470, int(H * 0.53) + 560)
    cw, ch = card[2] - card[0], card[3] - card[1]; sw, sh = person_rgb.size; ar = cw / ch
    pw = min(sw, sh * ar); ph = pw / ar; px0 = (sw - pw) / 2
    piece = person_rgb.resize((cw, ch), Image.BICUBIC, box=(px0, 0, px0 + pw, ph)).convert("RGBA")
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([card[0] - 5, card[1] - 5, card[2] + 5, card[3] + 5], radius=40, outline=pal["glow"] + (220,), width=7)
    out.alpha_composite(g.filter(ImageFilter.GaussianBlur(7)))
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=36, fill=255)
    out.paste(piece, card[:2], m)
    tx = card[2] + 40
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kt = eo(pr(t, t0 + 0.15, 0.3))
    spr, pad = text_sprite(" ".join(kicker.upper()), F("Inter-Bold", 24), (255, 255, 255, 230), shadow=False); lay.alpha_composite(blur_reveal(spr, kt), (tx - pad, card[1] + 20 - pad))
    ft = F("InterDisplay-Black", 64)
    words = title.upper().split(); lines, cur = [], ""
    for w_ in words:
        c = (cur + " " + w_).strip()
        if tw(c, ft) > W - tx - 40 and cur: lines.append(cur); cur = w_
        else: cur = c
    lines.append(cur)
    for j, l in enumerate(lines):
        spr, pad = text_sprite(l, ft, pal["cream"] + (255,)); lay.alpha_composite(blur_reveal(spr, eo(pr(t, t0 + 0.25 + 0.08 * j, 0.3))), (tx - pad, card[1] + 62 + j * 70 - pad))
    if caption_words:
        x = tx; y = card[1] + 90 + len(lines) * 70 + 40; fc = F("Inter-Bold", 30)
        for ts, te, txt, strong in caption_words:
            if t >= ts - 0.03:
                spr, pad = text_sprite(txt, fc, (pal["cream"] if strong else pal["ink"]) + (255,), shadow=False)
                lay.alpha_composite(blur_reveal(spr, eo(pr(t, ts - 0.03, 0.12))), (int(x - pad), int(y - pad)))
            x += tw(txt + " ", fc)
            if x > W - 60: x = tx; y += 40
    out.alpha_composite(lay)
    return out.convert("RGB")

# ---------------------------------------------------------------- 8. CTA: comentário fixado simulado + teclas
def comment_card(layer, handle, lines, t, t0, x, y, pal, w=860, avatar_col=(243, 200, 80)):
    """lines: [(t_aparece, texto, link)] — card estilo comentário do Instagram."""
    if t < t0: return
    k = eo(pr(t, t0, 0.3)); shown = [l for l in lines if t >= l[0]]
    h = 70 + 58 * len(shown)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 26, w + 20, h + 26], radius=22, fill=(0, 0, 0, 110)); im = im.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=22, fill=(18, 18, 26, 235), outline=(255, 255, 255, 40), width=2)
    d.ellipse([40, 36, 80, 76], fill=avatar_col + (255,)); d.text((52, 41), handle[0].upper(), font=F("Inter-Bold", 26), fill=(20, 20, 20, 255))
    d.text((94, 42), handle, font=F("Inter-Bold", 26), fill=(240, 240, 245, 255)); d.text((94 + tw(handle, F("Inter-Bold", 26)) + 14, 44), "agora", font=F("Inter-Medium", 22), fill=pal["muted"] + (255,))
    for j, (ta, txt, link) in enumerate(shown):
        kj = eo(pr(t, ta, 0.25)); yy = 92 + j * 58
        d.rounded_rectangle([40, yy, w, yy + 46], radius=12, fill=(40, 40, 52, int(255 * kj)))
        d.text((60, yy + 9), "🔗 " if False else "↗", font=F("Inter-Bold", 24), fill=pal["accent"] + (int(255 * kj),))
        d.text((92, yy + 9), txt, font=F("Inter-Bold", 24), fill=(240, 240, 245, int(255 * kj)))
        if link: d.text((92 + tw(txt, F("Inter-Bold", 24)) + 14, yy + 11), link, font=F("Inter-Medium", 20), fill=(110, 150, 255, int(255 * kj)))
    layer.alpha_composite(with_alpha(im, k), (int(x - 20), int(y - 20 + 20 * (1 - k))))

def keycaps(layer, caps, t, pal, size=84):
    """caps: [(t_aparece, x, y, rótulo)] — teclas brancas pipocando ao redor do rosto."""
    for ta, x, y, lab in caps:
        if t < ta: continue
        k = back(pr(t, ta, 0.18), 2.4); s = size * k
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = size
        d.rounded_rectangle([c - s / 2, c - s / 2 + 8, c + s / 2, c + s / 2 + 8], radius=s * 0.22, fill=(160, 160, 170, 255))
        d.rounded_rectangle([c - s / 2, c - s / 2, c + s / 2, c + s / 2], radius=s * 0.22, fill=(250, 250, 252, 255))
        if k > 0.7:
            f = F("InterDisplay-Black", int(size * 0.5)); b = f.getbbox(lab); d.text((c - (b[2] - b[0]) / 2 - b[0], c - (b[3] - b[1]) / 2 - b[1]), lab, font=f, fill=(25, 25, 30, 255))
        layer.alpha_composite(im, (int(x - size), int(y - size)))

# ---------------------------------------------------------------- 9. objeto na mão (PNG flutuando com brilho)
def object_float(layer, obj_rgba, t, t0, t1, x, y, size, glow_col=(255, 140, 80)):
    if not (t0 <= t < t1 + 0.3): return
    k = back(pr(t, t0, 0.35), 1.8); ko = pr(t, t1, 0.3); s = max(4, int(size * k))
    bob = 10 * math.sin((t - t0) * 3.2)
    g = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0)); gd = ImageDraw.Draw(g); c = size * 1.5
    for r, a in [(1.3, 40), (0.95, 70), (0.6, 110)]:
        gd.ellipse([c - size * r / 1.2, c - size * r / 1.2, c + size * r / 1.2, c + size * r / 1.2], fill=glow_col + (a,))
    g = g.filter(ImageFilter.GaussianBlur(size * 0.22))
    layer.alpha_composite(with_alpha(g, k * (1 - ko)), (int(x - c), int(y - c + bob)))
    o = obj_rgba.resize((s, s), Image.BICUBIC).rotate((1 - k) * 160, expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(with_alpha(o, 1 - ko), (int(x - o.width / 2), int(y - o.height / 2 + bob)))

# ---------------------------------------------------------------- áudio: "plim" de revelação
def chime(sr=48000, f=1318.5, d=0.7):
    t = np.arange(int(d * sr)) / sr
    s = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1), (1.5, .5), (2, .35), (3, .15)]) * np.exp(-t * 6)
    return (s / np.abs(s).max()).astype(np.float32)

# ---------------------------------------------------------------- 10. máscara só das mãos (pele abaixo do queixo)
def hand_mask(src_rgb, y_min, person_mask=None, grow=5, soft=2.5):
    """Detecta pele (YCbCr) abaixo de y_min — usado para as MÃOS passarem na frente da legenda,
    sem esconder o texto atrás do tronco. person_mask (L) opcional restringe à pessoa."""
    ycc = np.asarray(src_rgb.convert("YCbCr")).astype(np.int16)
    Y, Cb, Cr = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    rgb = np.asarray(src_rgb).astype(np.int16); R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # pele: clara (Y>=100), Cr 133-165, Cb 100-126, e R > G >= B (tecidos vinho/escuros têm B > G ou Y baixo)
    m = (Cr >= 133) & (Cr <= 165) & (Cb >= 100) & (Cb <= 126) & (Y >= 100) & (R > G) & (G >= B - 4) & (R - B > 25)
    m[: int(y_min)] = False
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    # descarta a pele ligada ao pescoço/rosto: tudo que encosta na linha y_min é removido (flood fill)
    yi = int(y_min); band = im.crop((0, yi, im.width, im.height)); bd = np.asarray(band)
    for x in np.where(bd[0] > 0)[0]:
        if band.getpixel((int(x), 0)) > 0: ImageDraw.floodfill(band, (int(x), 0), 0, thresh=0)
    im = Image.new("L", im.size, 0); im.paste(band, (0, yi))
    if person_mask is not None:
        im = Image.fromarray(np.minimum(np.asarray(im), np.asarray(person_mask)))
    im = im.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(soft))
    return im

# ---------------------------------------------------------------- 11. máscara de mãos precisa (MediaPipe)
class HandMasker:
    """Mãos via MediaPipe HandLandmarker (polígono dos 21 pontos, dilatado) ∩ classe 'pele do corpo'
    do segmentador multiclasse. Não pega pescoço nem rosto. Modelos (.task/.tflite) baixados do
    storage do MediaPipe; caminho padrão no scratchpad (passe models_dir para outro)."""
    def __init__(self, models_dir, video=True):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        self.mp = mp; self.video = video; self.ts = 0
        mode = vision.RunningMode.VIDEO if video else vision.RunningMode.IMAGE
        self.hands = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=f"{models_dir}/hand_landmarker.task"), running_mode=mode,
            num_hands=2, min_hand_detection_confidence=0.4, min_tracking_confidence=0.4))
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=f"{models_dir}/selfie_multiclass.tflite"), running_mode=mode,
            output_category_mask=True))
    def __call__(self, src_rgb, t=None, grow=1.25, soft=2.0):
        W, H = src_rgb.size; arr = np.ascontiguousarray(np.asarray(src_rgb.convert("RGB")))
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=arr)
        if self.video:
            self.ts = int((t if t is not None else self.ts / 1000 + 1 / 30) * 1000); hr = self.hands.detect_for_video(img, self.ts); sr = self.seg.segment_for_video(img, self.ts)
        else:
            hr = self.hands.detect(img); sr = self.seg.segment(img)
        poly = Image.new("L", (W, H), 0); d = ImageDraw.Draw(poly)
        for lm in hr.hand_landmarks:
            pts = np.array([(p.x * W, p.y * H) for p in lm]); c = pts.mean(0); pts = c + (pts - c) * grow
            from math import atan2
            hull = sorted(pts.tolist(), key=lambda p: atan2(p[1] - c[1], p[0] - c[0]))
            d.polygon([tuple(p) for p in hull], fill=255)
        poly = poly.filter(ImageFilter.MaxFilter(15))
        cat = np.squeeze(sr.category_mask.numpy_view() if hasattr(sr.category_mask, "numpy_view") else np.asarray(sr.category_mask))
        skin = Image.fromarray(((cat == 2) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)   # 2 = pele do corpo
        m = Image.fromarray(np.minimum(np.asarray(poly), np.asarray(skin)))
        return m.filter(ImageFilter.GaussianBlur(soft))

# ================================================================ referência 3 (nelmoricalde_chatgpt)
PAL_GOLD = dict(bg=(14, 12, 30), ink=(255, 255, 255), accent=(245, 197, 66), cream=(245, 197, 66), glow=(94, 230, 200), muted=(170, 170, 185))

def y_flip(img, k):
    """Giro no eixo Y (cartão/celular virando). k 0..1: 0 = de frente, 0.5 = de lado (invisível), 1 = de frente de novo.
    Use para trocar o conteúdo: desenhe o conteúdo antigo quando k<0.5 e o novo quando k>=0.5."""
    w, h = img.size; c = abs(math.cos(math.pi * k)); nw = max(2, int(w * c))
    sq = img.resize((nw, h), Image.BICUBIC)
    # leve perspectiva: o lado que se afasta encolhe na vertical
    persp = 0.12 * (1 - c); out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    coeffs = _persp_coeffs([(0, 0), (nw, 0), (nw, h), (0, h)],
                           [(0, h * persp), (nw, 0), (nw, h), (0, h * (1 - persp))] if k < 0.5 else [(0, 0), (nw, h * persp), (nw, h * (1 - persp)), (0, h)])
    sq = sq.transform((nw, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    out.alpha_composite(sq, ((w - nw) // 2, 0)); return out

def _persp_coeffs(src, dst):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def phone_mockup(screen_rgba, w=420, tilt=0.0):
    """Celular com moldura escura, cantos arredondados, ilha e brilho. screen_rgba é redimensionada para a tela."""
    h = int(w * 2.05); r = int(w * 0.16); bz = int(w * 0.035)
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 44, w + 30, h + 44], radius=r, fill=(0, 0, 0, 130)); im = im.filter(ImageFilter.GaussianBlur(16)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 30, w + 30, h + 30], radius=r, fill=(28, 28, 34, 255), outline=(120, 120, 135, 255), width=3)
    sw, sh = w - 2 * bz, h - 2 * bz; scr = screen_rgba.convert("RGBA").resize((sw, sh), Image.BICUBIC)
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=r - bz, fill=255)
    im.paste(scr, (30 + bz, 30 + bz), m)
    d.rounded_rectangle([30 + w / 2 - w * 0.14, 30 + bz + 14, 30 + w / 2 + w * 0.14, 30 + bz + 14 + w * 0.07], radius=w * 0.035, fill=(0, 0, 0, 255))
    gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).polygon([(30 + bz, 30 + bz), (30 + w * 0.55, 30 + bz), (30 + bz, 30 + h * 0.4)], fill=(255, 255, 255, 22))
    im.alpha_composite(gl)
    return im.rotate(tilt, expand=True, resample=Image.BICUBIC) if tilt else im

def push_notification(layer, app, text, t, t0, t1, W, pal, y=40, icon_col=(30, 30, 30), progress=True):
    if not (t0 <= t < t1 + 0.3): return
    k = eo(pr(t, t0, 0.35)); ko = eo(pr(t, t1, 0.3))
    w = W - 80; h = 150
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 28, w + 20, h + 28], radius=34, fill=(0, 0, 0, 120)); im = im.filter(ImageFilter.GaussianBlur(14)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=34, fill=(32, 32, 40, 238), outline=(255, 255, 255, 30), width=2)
    d.rounded_rectangle([46, 46, 106, 106], radius=16, fill=icon_col + (255,)); d.text((62, 52), "✦" if False else app[0], font=F("Inter-Bold", 38), fill=(255, 255, 255, 255))
    d.text((126, 44), app, font=F("Inter-Bold", 30), fill=(245, 245, 248, 255)); d.text((w - 70, 46), "agora", font=F("Inter-Medium", 24), fill=pal["muted"] + (255,))
    fb = F("Inter-Medium", 28); words = text.split(); line, ly = "", 84
    for wd in words:
        if tw(line + " " + wd, fb) > w - 160: d.text((126, ly), line.strip(), font=fb, fill=(220, 220, 228, 255)); line, ly = wd, ly + 34
        else: line += " " + wd
    d.text((126, ly), line.strip(), font=fb, fill=(220, 220, 228, 255))
    if progress:
        kp = cl((t - t0 - 0.3) / max(0.1, t1 - t0 - 0.6)); d.rounded_rectangle([126, h + 4, w - 40, h + 10], radius=3, fill=(70, 70, 80, 255))
        d.rounded_rectangle([126, h + 4, 126 + (w - 166) * kp, h + 10], radius=3, fill=pal["glow"] + (255,))
    layer.alpha_composite(with_alpha(im, k), (20, int(y - (h + 60) * (1 - k) - (h + 80) * ko)))

def evolving_card(layer, img_rgb, caption, states, t, t0, t1, x, y, pal, w=300, rot=-4):
    """Polaroid que evolui com a fala. states: [(t, 'gif'|'2x'|'film'|texto)] — selos que pipocam e,
    se 'film', vira tira de filme com o quadro atual destacado."""
    if not (t0 <= t < t1 + 0.3): return
    k = back(pr(t, t0, 0.3)); ko = pr(t, t1, 0.3)
    film = any(s == "film" and t >= ts for ts, s in states)
    if not film:
        h = int(w * 1.18); im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle([20, 28, w + 20, h + 28], fill=(0, 0, 0, 90)); im = im.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(im)
        d.rectangle([20, 20, w + 20, h + 20], fill=(250, 250, 250, 255))
        ph = img_rgb.convert("RGBA").resize((w - 28, w - 28), Image.BICUBIC); im.paste(ph, (34, 34))
        d.text((36, w + 18), caption, font=F("Inter-Bold", 24), fill=(30, 30, 35, 255))
        for ts, s in states:
            if t < ts or s == "film": continue
            kb = back(pr(t, ts, 0.25), 2.2)
            if s == "gif":
                bw, bh = 74 * kb, 40 * kb; d.rounded_rectangle([w + 20 - bw + 14, 14, w + 34, 14 + bh], radius=10, fill=(40, 190, 120, 255))
                if kb > 0.8: d.text((w + 34 - 62, 18), "GIF", font=F("Inter-Bold", 26), fill=(255, 255, 255, 255))
            elif s == "2x":
                r = 38 * kb; cx, cy = w + 4, w - 6; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["accent"] + (255,))
                if kb > 0.8: d.text((cx - 22, cy - 18), "2x", font=F("InterDisplay-Black", 32), fill=(30, 20, 0, 255))
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    else:
        n = 5; fh = int(w * 0.62); im = Image.new("RGBA", (int(w * 0.62) + 36, n * (fh + 10) + 30), (12, 12, 14, 240)); d = ImageDraw.Draw(im)
        for j in range(n * 2): d.rectangle([4, 10 + j * (fh + 10) / 2, 14, 18 + j * (fh + 10) / 2], fill=(220, 220, 220, 255)); d.rectangle([im.width - 14, 10 + j * (fh + 10) / 2, im.width - 4, 18 + j * (fh + 10) / 2], fill=(220, 220, 220, 255))
        cur = int((t - t0) * 6) % n
        for j in range(n):
            fr = img_rgb.convert("RGBA").resize((int(w * 0.62) - 8, fh), Image.BICUBIC); im.paste(fr, (22, 15 + j * (fh + 10)))
            if j == cur: d.rectangle([20, 13 + j * (fh + 10), 22 + int(w * 0.62) - 6, 15 + j * (fh + 10) + fh + 2], outline=pal["accent"] + (255,), width=4)
    layer.alpha_composite(with_alpha(im, 1 - ko), (int(x - im.width / 2), int(y - im.height / 2 + 30 * (1 - min(1, k)))))

def cards_to_sphere(layer, thumbs, t, t0, t_conv, cx, cy, W, H, radius=230, n=90, seed=3):
    """Chuva de miniaturas caindo do topo (t0..t_conv) que convergem numa esfera girando em (cx,cy)."""
    if t < t0: return
    rng = np.random.default_rng(seed); spin = (t - t0) * 0.9
    ph = np.arccos(1 - 2 * (np.arange(n) + 0.5) / n); th = np.pi * (1 + 5 ** 0.5) * np.arange(n)
    items = []
    for i in range(n):
        sx, sy = rng.uniform(0, W), rng.uniform(-H * 0.6, -60); vy = rng.uniform(0.9, 1.4) * H * 0.7; rot0 = rng.uniform(-40, 40)
        x3 = math.sin(ph[i]) * math.cos(th[i] + spin); y3 = math.cos(ph[i]); z3 = math.sin(ph[i]) * math.sin(th[i] + spin)
        tx, ty = cx + x3 * radius, cy + y3 * radius
        fall_y = sy + vy * (t - t0); fall_x = sx
        kc = eio(pr(t, t_conv + (i % 15) * 0.02, 0.6))
        x = fall_x + (tx - fall_x) * kc; yv = fall_y + (ty - fall_y) * kc
        size = (70 + 30 * rng.uniform()) * (1 - kc) + (34 + 18 * (z3 + 1) / 2) * kc
        items.append((z3 * kc - 2 * (1 - kc), x, yv, size, rot0 * (1 - kc), i))
    for z, x, yv, size, rot, i in sorted(items):
        th_img = thumbs[i % len(thumbs)].convert("RGBA").resize((int(size), int(size)), Image.BICUBIC)
        card = Image.new("RGBA", (int(size) + 8, int(size) + 8), (255, 255, 255, 255)); card.paste(th_img, (4, 4))
        if rot: card = card.rotate(rot, expand=True, resample=Image.BICUBIC)
        a = 0.55 + 0.45 * (z + 1) / 2 if z > -1.5 else 1.0
        layer.alpha_composite(with_alpha(card, a), (int(x - card.width / 2), int(yv - card.height / 2)))

def disintegrate(sprite, k, seed=5, cell=6, drift=(160, -260)):
    """Esfarela um sprite RGBA em partículas que voam e somem (k 0..1). Varre da esquerda para a direita."""
    if k <= 0: return sprite
    w, h = sprite.size; out = Image.new("RGBA", (w + abs(drift[0]) * 2, h + abs(drift[1]) * 2), (0, 0, 0, 0))
    ox, oy = abs(drift[0]), abs(drift[1]); arr = np.asarray(sprite); rng = np.random.default_rng(seed)
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            blk = arr[yy:yy + cell, xx:xx + cell]
            if blk[..., 3].max() < 20: continue
            start = (xx / w) * 0.6 + rng.uniform(0, 0.15); kk = cl((k - start) / 0.4)
            if kk >= 1: continue
            dx = drift[0] * kk * rng.uniform(0.5, 1.5); dy = drift[1] * kk * rng.uniform(0.5, 1.5)
            b = Image.fromarray(blk.copy()); b = with_alpha(b, 1 - kk)
            out.alpha_composite(b, (int(ox + xx + dx), int(oy + yy + dy)))
    return out.crop((ox - 0, oy - 0, ox + w + abs(drift[0]), oy + h)) if False else out

def strike_x(layer, box, t, t0, color=(235, 52, 52), width=16):
    """✕ vermelho desenhado em dois traços sobre box (x0,y0,x1,y1)."""
    if t < t0: return
    x0, y0, x1, y1 = box; d = ImageDraw.Draw(layer)
    k1 = eo(pr(t, t0, 0.14)); k2 = eo(pr(t, t0 + 0.12, 0.14))
    d.line([(x0, y0), (x0 + (x1 - x0) * k1, y0 + (y1 - y0) * k1)], fill=color + (255,), width=width)
    if k2 > 0: d.line([(x1, y0), (x1 - (x1 - x0) * k2, y0 + (y1 - y0) * k2)], fill=color + (255,), width=width)

def orbit_recap(layer, sprites, t, t0, cx, cy, W, H, rx=460, ry=170, speed=0.7, speed_lines=True, front_layer=None):
    """Recapitulação: sprites (cards/títulos já usados no vídeo) orbitando a pessoa + linhas radiais de velocidade.
    Desenhe ANTES de restaurar a pessoa com a máscara para os itens 'de trás' ficarem atrás dela."""
    if t < t0: return
    k = eo(pr(t, t0, 0.5)); d = ImageDraw.Draw(layer)
    if speed_lines:
        for i in range(36):
            a = i / 36 * 2 * math.pi + (t - t0) * 0.15; r0 = 260 + 40 * (i % 3)
            d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * 1400, cy + math.sin(a) * 1400)], fill=(255, 255, 255, int(28 * k)), width=2)
    n = len(sprites); items = []
    for i, sp in enumerate(sprites):
        a = 2 * math.pi * i / n + (t - t0) * speed
        x = cx + math.cos(a) * rx * k; y = cy + math.sin(a) * ry * k; z = math.sin(a)
        s = 0.55 + 0.35 * (z + 1) / 2; items.append((z, x, y, s, sp))
    for z, x, y, s, sp in sorted(items, key=lambda q: q[0]):
        im = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BICUBIC)
        tgt = front_layer if (front_layer is not None and z >= 0) else layer   # metade da frente passa NA FRENTE da pessoa
        tgt.alpha_composite(with_alpha(im, k * (0.6 + 0.4 * (z + 1) / 2)), (int(x - im.width / 2), int(y - im.height / 2)))
