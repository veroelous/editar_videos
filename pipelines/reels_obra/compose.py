"""Reels "Diário da Reforma" — vídeo de passeio SEM fala (cliente G2B Esquadrias e Vidros, EP.01 "O antes").
Texto (headlines + legendas) é copy escrita, não transcrição. Uso:
  PROJ=brutos/g2b python3 compose.py <frame_ini> <frame_fim> <saida_dir>
Lê PROJ/src/%05d.jpg (frames do bruto já gradeados, 30 fps) e escreve PNGs 1080x1920.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "efeitos"))
from fx import *  # noqa

PROJ = os.environ.get("PROJ", "brutos/g2b")
W, H, FPS = 1080, 1920, 30
SRC_FPS, SRC_N = 30, len(os.listdir(f"{PROJ}/src"))
PAL = dict(bg=(9, 13, 22), ink=(255, 255, 255), accent=(245, 197, 66), cream=(245, 197, 66), glow=(245, 197, 66), muted=(160, 168, 185))
Y = PAL["accent"]

# ---------------------------------------------------------------- linha do tempo (cortes nas batidas de 120 bpm)
# (out_ini, out_fim, src_ini, src_fim, zoom_ini, zoom_fim, transição_de_entrada)
SEGS = [
    (0.0, 4.0, 0.0, 4.4, 1.00, 1.10, None),
    (4.0, 8.5, 9.7, 17.4, 1.12, 1.02, "whip_x"),
    (8.5, 12.5, 17.4, 24.2, 1.02, 1.12, "zoom"),
    (12.5, 18.5, 25.0, 37.4, 1.10, 1.00, "leak"),
    (18.5, 22.5, 38.6, 45.2, 1.00, 1.10, "whip_y"),
    (22.5, 28.0, 46.0, 56.3, 1.04, 1.16, "zoom"),
]
END0, END1 = 28.0, 33.5
FREEZE_SRC = 4.2  # quadro do "antes" no cartão final (portão aberto)

def src_frame(ts):
    i = int(round(ts * SRC_FPS)) + 1; i = max(1, min(SRC_N, i))
    return Image.open(f"{PROJ}/src/{i:05d}.jpg").convert("RGB")

def fit(img, z=1.0, dx=0.0, dy=0.0):
    """Escala o quadro para cobrir 1080x1920 com zoom z e deslocamento (px de saída)."""
    s = max(W / img.width, H / img.height) * z
    w, h = int(img.width * s + 0.5), int(img.height * s + 0.5)
    im = img.resize((w, h), Image.LANCZOS)
    x0 = int((w - W) / 2 - dx); y0 = int((h - H) / 2 - dy)
    x0 = max(0, min(w - W, x0)); y0 = max(0, min(h - H, y0))
    return im.crop((x0, y0, x0 + W, y0 + H))

def motion_blur(img, amt, axis="x"):
    """Desfoque direcional (whip). amt em px."""
    n = max(1, int(amt / 6))
    if n <= 1: return img
    a = np.asarray(img).astype(np.float32); acc = np.zeros_like(a)
    for k in range(n):
        o = int((k - n / 2) * amt / n)
        acc += np.roll(a, o, axis=1 if axis == "x" else 0)
    return Image.fromarray((acc / n).astype(np.uint8))

def rgb_split(img, px):
    if px < 1: return img
    r, g, b = img.split()
    r = ImageChops_offset(r, int(px), 0); b = ImageChops_offset(b, -int(px), 0)
    return Image.merge("RGB", (r, g, b))

def ImageChops_offset(ch, dx, dy):
    a = np.roll(np.asarray(ch), (dy, dx), axis=(0, 1)); return Image.fromarray(a)

def vignette():
    yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    v = np.clip(1 - 0.55 * np.clip(d - 0.55, 0, 1) ** 1.4, 0, 1)
    return v[..., None].astype(np.float32)
VIG = vignette()

def grade_bottom(fr):
    """Escurece a parte de baixo (legibilidade da legenda) + vinheta."""
    a = np.asarray(fr).astype(np.float32) * VIG
    g = np.linspace(0, 1, H)[:, None, None]; g = np.clip((g - 0.55) / 0.45, 0, 1) ** 1.5
    a = a * (1 - 0.55 * g)
    gt = np.clip((0.16 - np.linspace(0, 1, H)) / 0.16, 0, 1)[:, None, None]
    a = a * (1 - 0.45 * gt)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ---------------------------------------------------------------- copy (legendas escritas)
def ph(t0, top, bot, t_end, step=0.11):
    ws, t = [], t0
    for w in top.split(): ws.append((t, t + 0.3, w, False)); t += step
    for w in bot.split(): ws.append((t, t + 0.3, w, True)); t += step
    return (ws, t_end)

PHRASES = [
    ph(1.75, "Guarde bem", "essa imagem.", 3.85),
    ph(4.35, "Essa é a sede da", "G2B hoje.", 8.3),
    ph(8.85, "Onde cada vidro e esquadria", "ganha forma.", 12.3),
    ph(12.9, "Aqui o trabalho", "não para…", 15.35),
    ph(15.55, "…mas chegou a hora de", "EVOLUIR.", 18.3),
    ph(18.85, "Cada canto", "vai mudar.", 22.3),
    ph(22.85, "Daqui a pouco,", "nada disso vai existir.", 27.6),
]

def cap_layer(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for ws, te in PHRASES:
        if ws[0][0] - 0.1 <= t < te + 0.02:
            caption2(L, ws, t, W / 2, 1470, PAL, size_small=50, size_big=78, t_end=te)
    return L

# ---------------------------------------------------------------- elementos de UI
def progress_pill(L, t, t0, t1, pct_from, pct_to, x, y):
    if not (t0 <= t < t1 + 0.2): return
    k = back(pr(t, t0, 0.3)); ko = pr(t, t1, 0.2)
    w, h = 330, 74; im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 26, w + 20, h + 26], radius=18, fill=(0, 0, 0, 110)); im = im.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=18, fill=(14, 18, 28, 225), outline=(255, 255, 255, 40), width=2)
    pct = pct_from + (pct_to - pct_from) * eio(pr(t, t0 + 0.4, max(0.1, t1 - t0 - 0.8)))
    d.text((40, 30), "REFORMA", font=F("Inter-Bold", 20), fill=(200, 205, 215, 255))
    s = f"{pct:.0f}%"; f = F("InterDisplay-Black", 26); d.text((w + 20 - 20 - tw(s, f), 27), s, font=f, fill=Y + (255,))
    bx0, by0, bx1, by1 = 40, 66, w, 78
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=6, fill=(255, 255, 255, 40))
    fw = max(12, (bx1 - bx0) * pct / 100)
    d.rounded_rectangle([bx0, by0, bx0 + fw, by1], radius=6, fill=Y + (255,))
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BICUBIC) if k < 1 else im
    L.alpha_composite(with_alpha(im, 1 - ko), (int(x - 20), int(y - 20)))

def tape(L, t, t0, d=0.55, angle=-14, n_strips=2):
    """Faixa zebrada amarela/preta (fita de obra) que atravessa a tela — transição temática."""
    if not (t0 <= t < t0 + d): return
    k = eio(pr(t, t0, d))
    band = Image.new("RGBA", (2600, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rectangle([0, 0, 2600, 230], fill=Y + (255,))
    for x in range(-300, 2900, 120): bd.polygon([(x, 0), (x + 60, 0), (x - 60, 230), (x - 120, 230)], fill=(16, 16, 18, 255))
    bd.rectangle([0, 60, 2600, 170], fill=(16, 16, 18, 255))
    f = F("InterDisplay-Black", 70); txt = "EM OBRAS  •  EM OBRAS  •  EM OBRAS  •  EM OBRAS  •  EM OBRAS"
    bd.text((40 - 400 * k, 72), txt, font=f, fill=Y + (255,))
    for j in range(n_strips):
        b = band.rotate(angle + 26 * j, expand=True, resample=Image.BICUBIC)
        off = (1 - 2 * k) * 1800 * (1 if j == 0 else -1)
        L.alpha_composite(b, (int(W / 2 - b.width / 2 + off), int((700 if j == 0 else 1250) - b.height / 2)))

def rec_dot(L, t, t0, t1):
    toast(L, "REGISTRANDO O INÍCIO DA REFORMA", t, t0, t1, 120, 300, PAL, dot=(235, 52, 52), size=26)

# ---------------------------------------------------------------- cartão final (ANTES | DEPOIS)
FREEZE = None
def end_card(t):
    global FREEZE
    if FREEZE is None: FREEZE = fit(src_frame(FREEZE_SRC), 1.0)
    te = t - END0
    bg = dark_bg(W, H, PAL).convert("RGBA")
    # painel ANTES (P&B) desce de cima; painel DEPOIS (escuro) sobe de baixo
    k1 = eo(pr(te, 0.0, 0.45)); k2 = eo(pr(te, 0.25, 0.45))
    pw, phh = 900, 640; px = (W - pw) // 2
    antes = ImageOps.grayscale(FREEZE).convert("RGB").resize((pw, int(pw * H / W)), Image.LANCZOS)
    antes = antes.crop((0, (antes.height - phh) // 2, pw, (antes.height - phh) // 2 + phh))
    m = Image.new("L", (pw, phh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, phh - 1], radius=34, fill=255)
    ya = int(170 - 900 * (1 - k1)); bg.paste(antes, (px, ya), m)
    d = ImageDraw.Draw(bg)
    # selo ANTES
    f = F("InterDisplay-Black", 64); s = "ANTES"; sw = tw(s, f)
    d.rounded_rectangle([px + 30, ya + 30, px + 30 + sw + 44, ya + 30 + 92], radius=14, fill=(255, 255, 255, 255))
    d.text((px + 52, ya + 38), s, font=f, fill=(16, 16, 18, 255))
    # DEPOIS
    yd = int(860 + 900 * (1 - k2))
    dep = Image.new("RGBA", (pw, phh), (0, 0, 0, 0)); dd = ImageDraw.Draw(dep)
    dd.rounded_rectangle([0, 0, pw - 1, phh - 1], radius=34, fill=(22, 26, 38, 255), outline=Y + (255,), width=4)
    # listras de obra no topo do card
    for x in range(-40, pw + 40, 56): dd.polygon([(x, 0), (x + 28, 0), (x + 8, 22), (x - 20, 22)], fill=Y + (200,))
    q = F("InterDisplay-Black", 300); pulse = 1 + 0.06 * math.sin(te * 7)
    qs, qp = text_sprite("?", q, Y + (255,)); qs = qs.resize((int(qs.width * pulse), int(qs.height * pulse)), Image.BICUBIC)
    dep.alpha_composite(qs, (int(pw / 2 - qs.width / 2), int(phh / 2 - qs.height / 2 - 30)))
    f2 = F("InterDisplay-Black", 64); s2 = "DEPOIS"; s2w = tw(s2, f2)
    dd.rounded_rectangle([30, 30 + 14, 30 + s2w + 44, 30 + 14 + 92], radius=14, fill=Y + (255,))
    dd.text((52, 38 + 14), s2, font=f2, fill=(16, 16, 18, 255))
    # barra "carregando"
    lk = pr(te, 0.8, 3.6); bx0, bx1, by = 60, pw - 60, phh - 70
    dd.rounded_rectangle([bx0, by, bx1, by + 18], radius=9, fill=(255, 255, 255, 40))
    dd.rounded_rectangle([bx0, by, bx0 + max(18, (bx1 - bx0) * 0.05 * eo(lk)), by + 18], radius=9, fill=Y + (255,))
    dd.text((bx0, by - 44), "EM CONSTRUÇÃO…", font=F("Inter-Bold", 26), fill=(210, 215, 225, 255))
    pct = f"{5 * eo(lk):.0f}%"; fp = F("InterDisplay-Black", 30); dd.text((bx1 - tw(pct, fp), by - 48), pct, font=fp, fill=Y + (255,))
    bg.alpha_composite(dep, (px, yd))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kinetic_title(L, "acompanhe cada etapa", "SIGA A G2B", t, END0 + 0.9, W / 2, 1600, PAL, size=118, per_letter=0.045, color=(255, 255, 255))
    if te > 2.2:
        k3 = eo(pr(te, 2.2, 0.35)); f3 = F("Inter-SemiBold", 34)
        s3 = "e ative as notificações para não perder o DEPOIS"
        spr, pad = text_sprite(s3, f3, (220, 225, 235, 255)); spr = blur_reveal(spr, k3)
        L.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(1770 - pad + 14 * (1 - k3))))
    push_notification(L, "G2B Esquadrias e Vidros", "Nova etapa da reforma chegando. Ative o sininho para ver primeiro.", t, END0 + 3.0, END1 + 1, W, PAL, y=24, icon_col=(30, 34, 46), progress=False)
    bg.alpha_composite(L)
    return bg.convert("RGB")

# ---------------------------------------------------------------- frame
TR = 0.2  # meia-duração das transições
def seg_at(t):
    for i, s in enumerate(SEGS):
        if s[0] <= t < s[1]: return i, s
    return None, None

def base_frame(t):
    i, s = seg_at(t)
    o0, o1, s0, s1, z0, z1, _ = s
    k = (t - o0) / (o1 - o0)
    ts = s0 + (s1 - s0) * k
    z = z0 + (z1 - z0) * eio(k)
    fx_amt, axis, zoom_extra, flash, split = 0, "x", 0, 0, 0
    # saída: transição do próximo segmento
    nxt = SEGS[i + 1][6] if i + 1 < len(SEGS) else "end"
    dt_out = o1 - t; dt_in = t - o0
    if dt_out < TR:
        q = 1 - dt_out / TR
        if nxt in ("whip_x", "whip_y"): fx_amt = 260 * q ** 2; axis = nxt[-1]
        elif nxt == "zoom": zoom_extra = 0.35 * q ** 2; split = 14 * q
        elif nxt == "leak": flash = q ** 2 * 0.9; split = 10 * q
        elif nxt == "end": flash = q ** 2 * 0.6
    tin = s[6]
    if tin and dt_in < TR:
        q = 1 - dt_in / TR
        if tin in ("whip_x", "whip_y"): fx_amt = 260 * q ** 2; axis = tin[-1]
        elif tin == "zoom": zoom_extra = -0.18 * q ** 2; split = 14 * q
        elif tin == "leak": flash = q ** 2 * 0.9; split = 10 * q
    shift = 0
    if fx_amt: shift = (fx_amt * 2.2) * (1 if dt_out < TR else -1)
    fr = fit(src_frame(ts), z + zoom_extra, dx=shift if axis == "x" else 0, dy=shift if axis == "y" else 0)
    if fx_amt: fr = motion_blur(fr, fx_amt, axis)
    if zoom_extra > 0.05: fr = fr.filter(ImageFilter.GaussianBlur(zoom_extra * 14))
    if split: fr = rgb_split(fr, split)
    fr = grade_bottom(fr)
    if flash:
        warm = Image.new("RGB", (W, H), (255, 236, 200)); fr = Image.blend(fr, warm, min(0.95, flash))
    return fr

def render(t):
    if t >= END0:
        fr = end_card(t)
        if t - END0 < 0.18: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 1 - (t - END0) / 0.18)
        return fr
    fr = base_frame(t).convert("RGBA")
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # gancho
    kinetic_title(L, "diário da reforma", "O ANTES", t, 0.05, W / 2, 520, PAL, size=190, exit_t=3.6, per_letter=0.07)
    rec_dot(L, t, 0.6, 3.6)
    # persistentes
    section_tag(L, "EP. 01  •  O INÍCIO", t, 4.15, 27.8, 60, 120, PAL, size=30)
    progress_pill(L, t, 4.35, 27.8, 0, 3, W - 60 - 330, 110)
    tape(L, t, 27.45, d=0.6)
    fr.alpha_composite(L); fr.alpha_composite(cap_layer(t))
    return fr.convert("RGB")

if __name__ == "__main__":
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    os.makedirs(out, exist_ok=True)
    N = int(END1 * FPS)
    for f in range(a, min(b, N)):
        render(f / FPS).save(f"{out}/{f:05d}.png", compress_level=1)
