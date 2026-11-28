"""Reels de PORTFÓLIO G2B (trabalho concluído, vídeo SEM fala): capa → gancho → destaques → detalhe → CTA.
Mesma identidade dos episódios da reforma (paleta azul, logo, legenda em 2 camadas, transições na batida).
O roteiro de cada trabalho fica em trabalhos/<JOB>.py. Uso:
  PROJ=brutos/g2b_pergolado JOB=g2b_pergolado python3 portfolio.py <frame_ini> <frame_fim> <saida_dir>
"""
import os, sys, math, importlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "efeitos")); sys.path.insert(0, HERE)
from fx import *  # noqa
from visual import *  # noqa

PROJ = os.environ.get("PROJ", "brutos/g2b_pergolado")
JOB = os.environ.get("JOB", "g2b_pergolado")
_job = importlib.import_module(f"trabalhos.{JOB}")
globals().update({k: v for k, v in vars(_job).items() if k.isupper()})
SRC_FPS, SRC_N = 30, len(os.listdir(f"{PROJ}/src"))
logo_sz = load_logo(os.environ.get("LOGO", f"{PROJ}/logo/1.png"))
COVER = 1.2
FLASH = (235, 243, 255)
# SEGS: (out_ini, out_fim, src_ini, src_fim, zoom_ini, zoom_fim, transição_de_entrada[, foco=(fx, fy) 0..1 para zoom de detalhe])

def src_frame(ts):
    i = int(round(ts * SRC_FPS)) + 1; i = max(1, min(SRC_N, i))
    return Image.open(f"{PROJ}/src/{i:05d}.jpg").convert("RGB")

def fit_font(text, name, size, maxw):
    f = F(name, size)
    while tw(text, f) > maxw and size > 40: size -= 4; f = F(name, size)
    return size

# ---------------------------------------------------------------- vídeo base com transições
TR = 0.2
def base_frame(t):
    i = next(j for j, s in enumerate(SEGS) if s[0] <= t < s[1]); s = SEGS[i]
    o0, o1, s0, s1, z0, z1, tin = s[:7]; foc = s[7] if len(s) > 7 else (0.5, 0.5)
    k = (t - o0) / (o1 - o0); ts = s0 + (s1 - s0) * k; z = z0 + (z1 - z0) * eio(k)
    nxt = SEGS[i + 1][6] if i + 1 < len(SEGS) else "end"
    fx_amt, axis, zx, flash, split = 0, "x", 0, 0, 0
    dt_out, dt_in = o1 - t, t - o0
    if dt_out < TR:
        q = 1 - dt_out / TR
        if nxt in ("whip_x", "whip_y"): fx_amt = 260 * q ** 2; axis = nxt[-1]
        elif nxt == "zoom": zx = 0.35 * q ** 2; split = 14 * q
        elif nxt == "leak": flash = q ** 2 * 0.9; split = 10 * q
        elif nxt == "end": flash = q ** 2 * 0.6
    if tin and dt_in < TR:
        q = 1 - dt_in / TR
        if tin in ("whip_x", "whip_y"): fx_amt = 260 * q ** 2; axis = tin[-1]
        elif tin == "zoom": zx = -0.18 * q ** 2; split = 14 * q
        elif tin == "leak": flash = q ** 2 * 0.9; split = 10 * q
    shift = (fx_amt * 2.2) * (1 if dt_out < TR else -1) if fx_amt else 0
    zz = z + zx
    # foco: desloca o recorte para o ponto de interesse quando há zoom
    im = src_frame(ts); sw, sh = im.size
    sc = max(W / sw, H / sh) * zz
    dxf = -(foc[0] - 0.5) * sw * sc; dyf = -(foc[1] - 0.5) * sh * sc
    fr = fit(im, zz, dx=dxf + (shift if axis == "x" else 0), dy=dyf + (shift if axis == "y" else 0))
    if fx_amt: fr = motion_blur(fr, fx_amt, axis)
    if zx > 0.05: fr = fr.filter(ImageFilter.GaussianBlur(zx * 14))
    if split: fr = rgb_split(fr, split)
    fr = grade_bottom(fr)
    if flash: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 236, 200)), min(0.95, flash))
    return fr

def cap_layer(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for ws, te in PHRASES:
        if ws[0][0] - 0.1 <= t < te + 0.02:
            caption2(L, ws, t, W / 2, 1470, PAL, size_small=50, size_big=78, t_end=te)
    return L

def feature_chips(L, t):
    """Destaques do produto: cartões empilhados com ✓ azul-céu (uma ideia por vez, ~0,7 s entre eles)."""
    t0s = [c[0] for c in FEATURES]; t1 = FEATURES_END
    for j, (ta, title, sub) in enumerate(FEATURES):
        if not (ta <= t < t1 + 0.3): continue
        k = back(pr(t, ta, 0.3), 1.4); ko = eio(pr(t, t1 + j * 0.06, 0.25))
        w, h = 620, 118; im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 28, w + 20, h + 28], radius=24, fill=(0, 0, 0, 120)); im = im.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 20, w + 20, h + 20], radius=24, fill=(16, 26, 46, 232), outline=(255, 255, 255, 46), width=2)
        d.ellipse([44, 44, 114, 114], fill=SKY + (255,))
        d.line([(62, 80), (75, 94), (98, 64)], fill=NAVY + (255,), width=9, joint="curve")
        d.text((136, 38), title, font=F("InterDisplay-ExtraBold", 38), fill=(255, 255, 255, 255))
        d.text((136, 86), sub, font=F("Inter-Medium", 26), fill=PAL["muted"] + (255,))
        x = 60 - 500 * (1 - eo(pr(t, ta, 0.35))) - 700 * ko
        L.alpha_composite(with_alpha(im, cl(k) * (1 - ko)), (int(x), int(560 + j * 150)))

# ---------------------------------------------------------------- cartão final (CTA)
def cta_comment(L, t, te):
    """CTA "comenta PALAVRA": título + comentário simulado sendo digitado."""
    kinetic_title(L, CTA_KICKER, CTA_TITLE, t, END0 + 0.8, W / 2, 1010, PAL, size=fit_font(CTA_TITLE, "InterDisplay-Black", 150, 960), per_letter=0.05, color=SKY)
    # comentário simulado com a palavra do CTA
    if te > 2.0:
        kc = eo(pr(te, 2.0, 0.35)); w, h = 760, 150
        im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 28, w + 20, h + 28], radius=28, fill=(0, 0, 0, 120)); im = im.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 20, w + 20, h + 20], radius=28, fill=(255, 255, 255, 245))
        d.ellipse([44, 46, 116, 118], fill=SKY + (255,)); d.text((64, 56), "V", font=F("InterDisplay-Black", 44), fill=NAVY + (255,))
        d.text((140, 46), "você", font=F("Inter-Bold", 28), fill=(40, 48, 64, 255)); d.text((140 + tw("você", F("Inter-Bold", 28)) + 14, 49), "agora", font=F("Inter-Medium", 24), fill=(130, 140, 160, 255))
        typed = CTA_WORD[: int(len(CTA_WORD) * cl((te - 2.3) / 0.6)) ]
        d.text((140, 90), typed + ("|" if te < 3.1 and int(te * 6) % 2 else ""), font=F("InterDisplay-ExtraBold", 40), fill=NAVY + (255,))
        hk = back(pr(te, 3.1, 0.3), 2.0)
        if te > 3.1:  # coração pulsa quando o comentário é "enviado"
            hs = int(36 * hk); cx, cy = w - 40, 95
            d.ellipse([cx - hs, cy - hs * 0.9, cx, cy + hs * 0.1], fill=(235, 72, 88, 255)); d.ellipse([cx - hs * 0.1, cy - hs * 0.9, cx + hs * 0.9, cy + hs * 0.1], fill=(235, 72, 88, 255))
            d.polygon([(cx - hs, cy - hs * 0.3), (cx + hs * 0.9, cy - hs * 0.3), (cx - hs * 0.05, cy + hs)], fill=(235, 72, 88, 255))
        L.alpha_composite(with_alpha(im, kc), (int(W / 2 - (w + 40) / 2), int(1250 + 30 * (1 - kc))))
    if te > 3.4:
        k3 = eo(pr(te, 3.4, 0.35)); spr, pad = text_sprite(CTA_SUB, F("Inter-SemiBold", 36), (225, 232, 245, 255)); spr = blur_reveal(spr, k3)
        L.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(1500 - pad + 14 * (1 - k3))))

def contact_block(L, t, te):
    """CTA com contatos: título, frase de orçamento, telefones (WhatsApp) e região de atendimento."""
    kinetic_title(L, CTA_KICKER, CTA_TITLE, t, END0 + 0.6, W / 2, 790, PAL, size=fit_font(CTA_TITLE, "InterDisplay-Black", 130, 960), per_letter=0.04, color=SKY)
    for j, (line, font, col) in enumerate([(CTA_SUB, F("InterDisplay-Bold", 44), (255, 255, 255, 255)), (CTA_SUB2, F("Inter-Medium", 32), PAL["muted"] + (255,))]):
        kj = eo(pr(te, 1.5 + 0.2 * j, 0.35))
        if kj <= 0: continue
        spr, pad = text_sprite(line, font, col); spr = blur_reveal(spr, kj)
        L.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(960 + 66 * j - pad + 14 * (1 - kj))))
    for j, num in enumerate(CONTACTS):  # cartões de telefone com ícone de WhatsApp/celular
        kj = back(pr(te, 2.2 + 0.3 * j, 0.35), 1.6)
        if kj <= 0: continue
        w, h = 760, 112; im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 28, w + 20, h + 28], radius=56, fill=(0, 0, 0, 120)); im = im.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([20, 20, w + 20, h + 20], radius=56, fill=(255, 255, 255, 250))
        cx, cy = 20 + 62, 20 + h / 2
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(37, 211, 102, 255))          # verde WhatsApp
        d.rounded_rectangle([cx - 15, cy - 25, cx + 15, cy + 25], radius=6, outline=(255, 255, 255, 255), width=5)  # celular
        d.line([(cx - 5, cy + 17), (cx + 5, cy + 17)], fill=(255, 255, 255, 255), width=4)
        fn = F("InterDisplay-ExtraBold", 58); b = fn.getbbox(num)
        d.text((20 + 128, cy - (b[3] - b[1]) / 2 - b[1]), num, font=fn, fill=NAVY + (255,))
        L.alpha_composite(with_alpha(im, cl(kj)), (int(W / 2 - (w + 40) / 2), int(1110 + j * 140 + 30 * (1 - cl(kj)))))
    kl = eo(pr(te, 3.0, 0.35))
    if kl > 0:  # região de atendimento com pino
        f = F("InterDisplay-SemiBold", 40); txt = LOCATION; wt = tw(txt, f) + 64
        im = Image.new("RGBA", (wt + 20, 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse([4, 14, 40, 50], fill=SKY + (255,)); d.polygon([(8, 40), (36, 40), (22, 66)], fill=SKY + (255,)); d.ellipse([15, 25, 29, 39], fill=PAL["bg"] + (255,))
        d.text((60, 14), txt, font=f, fill=(240, 244, 252, 255))
        L.alpha_composite(blur_reveal(im, kl), (int(W / 2 - im.width / 2), int(1420 + 14 * (1 - kl))))

_end_bg = None
def end_card(t):
    global _end_bg
    if _end_bg is None:
        f = grade_bottom(fit(src_frame(END_BG_SRC), 1.0)).filter(ImageFilter.GaussianBlur(14)).convert("RGBA")
        f.alpha_composite(Image.new("RGBA", (W, H), (14, 23, 40, 175))); _end_bg = f
    te = t - END0; bg = _end_bg.copy(); L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    contacts = globals().get("CONTACTS")
    k = back(pr(te, 0.1, 0.55), 1.3); kb = eo(pr(te, 0.1, 0.4))
    lw = max(10, (440 if contacts else 560) * k); ly = 400 if contacts else 560
    lg = blur_reveal(logo_sz(lw), kb, 14)
    glow = with_alpha(logo_sz(lw).filter(ImageFilter.GaussianBlur(26)), 0.4 * kb)
    for im in (glow, lg): L.alpha_composite(im, (int(W / 2 - im.width / 2), int(ly - im.height / 2)))
    if contacts:
        contact_block(L, t, te)
    else:
        cta_comment(L, t, te)
    bg.alpha_composite(L)
    fo = pr(t, END1 - 0.5, 0.5)
    fr = bg.convert("RGB")
    return Image.blend(fr, Image.new("RGB", (W, H), PAL["bg"]), fo) if fo > 0 else fr

# ---------------------------------------------------------------- capa
_cover_bg = None
def cover(t, still=False):
    global _cover_bg
    if _cover_bg is None: _cover_bg = grade_bottom(fit(src_frame(COVER_SRC), 1.0)).filter(ImageFilter.GaussianBlur(4))
    z = 1.0 if still else 1.0 + 0.05 * t / COVER
    fr = _cover_bg.resize((int(W * z), int(H * z)), Image.LANCZOS)
    fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H)).convert("RGBA")
    fr.alpha_composite(Image.new("RGBA", (W, H), (14, 23, 40, 150)))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    lg = logo_sz(420); L.alpha_composite(lg, (int(W / 2 - lg.width / 2), 290))
    spr, pad = text_sprite(" ".join(COVER_KICKER.upper()), F("Inter-Bold", 40), (255, 255, 255, 255)); L.alpha_composite(spr, (int(W / 2 - spr.width / 2), 875 - pad))
    fe = F("InterDisplay-Black", 46); w1 = tw(COVER_PILL, fe) + 60
    d.rounded_rectangle([W / 2 - w1 / 2, 955, W / 2 + w1 / 2, 1035], radius=40, fill=SKY + (255,))
    b = fe.getbbox(COVER_PILL); d.text((W / 2 - (b[2] - b[0]) / 2 - b[0], 995 - (b[3] - b[1]) / 2 - b[1]), COVER_PILL, font=fe, fill=NAVY + (255,))
    y = 1080
    for line in COVER_TITLE:
        ft = F("InterDisplay-Black", fit_font(line, "InterDisplay-Black", 190, 980)); spr, pad = text_sprite(line, ft, (255, 255, 255, 255), ref="ÁÇO")
        L.alpha_composite(spr, (int(W / 2 - spr.width / 2), y - pad)); y += spr.height - 2 * pad + 10
    spr, pad = text_sprite(COVER_SUB, F("InterDisplay-SemiBold", 46), SKY + (255,)); L.alpha_composite(spr, (int(W / 2 - spr.width / 2), y + 40 - pad))
    fr.alpha_composite(L)
    return fr.convert("RGB")

# ---------------------------------------------------------------- frame
def render(t):
    if t < COVER:
        fr = cover(t)
        if t > COVER - 0.15: fr = Image.blend(fr, Image.new("RGB", (W, H), FLASH), (t - (COVER - 0.15)) / 0.15)
        return fr
    t -= COVER
    fr = render_main(t)
    return Image.blend(fr, Image.new("RGB", (W, H), FLASH), 1 - t / 0.12) if t < 0.12 else fr

def render_main(t):
    if t >= END0:
        fr = end_card(t)
        return Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 1 - (t - END0) / 0.18) if t - END0 < 0.18 else fr
    fr = base_frame(t).convert("RGBA"); L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kinetic_title(L, HOOK_KICKER, HOOK_TITLE, t, 0.05, W / 2, 520, PAL, size=fit_font(HOOK_TITLE, "InterDisplay-Black", 170, 980), exit_t=HOOK_EXIT, per_letter=0.06)
    if 0.25 <= t < END0:
        kl = eo(pr(t, 0.25, 0.4)) * (1 - pr(t, END0 - 0.4, 0.3)); L.alpha_composite(blur_reveal(logo_sz(170), kl, 10), (44, 52))
    section_tag(L, TAG_TXT, t, HOOK_EXIT + 0.1, END0 - 0.2, 236, 104, PAL, size=28)
    feature_chips(L, t)
    fr.alpha_composite(L); fr.alpha_composite(cap_layer(t))
    return fr.convert("RGB")

if __name__ == "__main__":
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    os.makedirs(out, exist_ok=True)
    N = int((END1 + COVER) * FPS)
    for f in range(a, min(b, N)):
        render(f / FPS).save(f"{out}/{f:05d}.png", compress_level=1)
