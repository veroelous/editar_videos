"""Visual compartilhado dos reels G2B: paleta da marca, logo, enquadramento 9:16, transições e grade azul."""
import numpy as np
from PIL import Image
W, H, FPS = 1080, 1920, 30
# Paleta G2B: azul-marinho da marca (#20314D) + azul-céu de destaque + branco
NAVY = (32, 49, 77); SKY = (125, 184, 255)
PAL = dict(bg=(14, 23, 40), ink=(255, 255, 255), accent=SKY, cream=SKY, glow=(70, 120, 200), muted=(165, 180, 205))

def load_logo(path):
    """Logo branco (PNG transparente) recortado no conteúdo; devolve função tamanho->sprite."""
    lg = Image.open(path).convert("RGBA"); lg = lg.crop(lg.getbbox())
    return lambda w: lg.resize((int(w), int(lg.height * w / lg.width)), Image.LANCZOS)

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

DEEP = np.array([12, 22, 42], np.float32); NAVY_A = np.array(NAVY, np.float32)
GB = np.clip((np.linspace(0, 1, H) - 0.55) / 0.45, 0, 1)[:, None, None] ** 1.5
GT = np.clip((0.17 - np.linspace(0, 1, H)) / 0.17, 0, 1)[:, None, None]
def grade_bottom(fr):
    """Grade azul G2B: sombras puxadas para o azul-marinho da marca, leve tom frio,
    degradês azul-marinho em cima e embaixo (legibilidade) + vinheta."""
    a = np.asarray(fr).astype(np.float32)
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None] / 255
    a = a + (NAVY_A * 1.25 - a) * (0.42 * (1 - lum) ** 1.6)          # split-tone: sombras azuis
    a = a * np.array([0.93, 0.98, 1.07], np.float32)                 # balanço frio
    a = a * VIG + DEEP * (1 - VIG)
    a = a + (DEEP - a) * (0.62 * GB) + (DEEP - a) * (0.5 * GT)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
