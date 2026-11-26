"""Reels "Diário da Reforma" — vídeo de passeio SEM fala (cliente G2B Esquadrias e Vidros).
Texto (headlines + legendas) é copy escrita, não transcrição. O roteiro de cada episódio fica em
episodios/<EP>.py (trechos, legendas, títulos, porcentagens, comparativos ANTES|AGORA). Uso:
  PROJ=brutos/g2b EP=g2b_ep01 python3 compose.py <frame_ini> <frame_fim> <saida_dir>
Lê PROJ/src/%05d.jpg (frames do bruto já gradeados, 30 fps) e escreve PNGs 1080x1920.
"""
import os, sys, math, importlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "efeitos"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx import *  # noqa
from visual import *  # noqa

PROJ = os.environ.get("PROJ", "brutos/g2b")
SRC_FPS, SRC_N = 30, len(os.listdir(f"{PROJ}/src"))
Y = PAL["accent"]
LOGO_PATH = os.environ.get("LOGO", f"{PROJ}/logo/1.png")  # versão branca do logo (PNG transparente)
_logo = Image.open(LOGO_PATH).convert("RGBA"); LOGO = _logo.crop(_logo.getbbox())
def logo_sz(w):
    return LOGO.resize((int(w), int(LOGO.height * w / LOGO.width)), Image.LANCZOS)

# ---------------------------------------------------------------- roteiro do episódio
from compose_helpers import ph  # noqa

EP = os.environ.get("EP", "g2b_ep01")
sys.path.insert(0, os.path.dirname(__file__))
_ep = importlib.import_module(f"episodios.{EP}")
globals().update({k: v for k, v in vars(_ep).items() if k.isupper()})
# SEGS: (out_ini, out_fim, src_ini, src_fim, zoom_ini, zoom_fim, transição_de_entrada[, comparativo])
# comparativo = dict(src=<pasta de frames do episódio anterior>, a=(ts_ini, ts_fim), wipe=(t_ini, dur) relativo ao trecho)
OUTRO = END0 + 5.4  # vinheta final com o logo grande

def src_frame(ts, d=None):
    d = d or f"{PROJ}/src"; n = SRC_N if d == f"{PROJ}/src" else len(os.listdir(d))
    i = int(round(ts * SRC_FPS)) + 1; i = max(1, min(n, i))
    return Image.open(f"{d}/{i:05d}.jpg").convert("RGB")

def fit_font(text, name, size, maxw):
    f = F(name, size)
    while tw(text, f) > maxw and size > 40: size -= 4; f = F(name, size)
    return size


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
    bd.rectangle([0, 0, 2600, 230], fill=(255, 255, 255, 255))
    for x in range(-300, 2900, 120): bd.polygon([(x, 0), (x + 60, 0), (x - 60, 230), (x - 120, 230)], fill=NAVY + (255,))
    bd.rectangle([0, 60, 2600, 170], fill=NAVY + (255,))
    f = F("InterDisplay-Black", 70); txt = "EM OBRAS  •  EM OBRAS  •  EM OBRAS  •  EM OBRAS  •  EM OBRAS"
    bd.text((40 - 400 * k, 72), txt, font=f, fill=(255, 255, 255, 255))
    for j in range(n_strips):
        b = band.rotate(angle + 26 * j, expand=True, resample=Image.BICUBIC)
        off = (1 - 2 * k) * 1800 * (1 if j == 0 else -1)
        L.alpha_composite(b, (int(W / 2 - b.width / 2 + off), int((700 if j == 0 else 1250) - b.height / 2)))

def rec_dot(L, t, t0, t1):
    toast(L, TOAST_TXT, t, t0, t1, 236, 300, PAL, dot=(235, 52, 52), size=26)

# ---------------------------------------------------------------- cartão final (ANTES | DEPOIS)
FREEZE = None
def end_card(t):
    global FREEZE
    if FREEZE is None: FREEZE = fit(src_frame(ANTES_FREEZE[1], ANTES_FREEZE[0]), 1.0)
    te = t - END0
    bg = dark_bg(W, H, PAL).convert("RGBA")
    # painel ANTES (P&B) desce de cima; painel DEPOIS (escuro) sobe de baixo
    k1 = eo(pr(te, 0.0, 0.45)); k2 = eo(pr(te, 0.25, 0.45))
    pw, phh = 900, 640; px = (W - pw) // 2
    antes = ImageOps.colorize(ImageOps.grayscale(FREEZE), black=(10, 18, 34), white=(232, 240, 252)).resize((pw, int(pw * H / W)), Image.LANCZOS)
    antes = antes.crop((0, (antes.height - phh) // 2, pw, (antes.height - phh) // 2 + phh))
    m = Image.new("L", (pw, phh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, phh - 1], radius=34, fill=255)
    ya = int(170 - 900 * (1 - k1)); bg.paste(antes, (px, ya), m)
    d = ImageDraw.Draw(bg)
    # selo ANTES
    f = F("InterDisplay-Black", 64); s = "ANTES"; sw = tw(s, f)
    d.rounded_rectangle([px + 30, ya + 30, px + 30 + sw + 44, ya + 30 + 92], radius=14, fill=(255, 255, 255, 255))
    d.text((px + 52, ya + 38), s, font=f, fill=NAVY + (255,))
    # DEPOIS
    yd = int(860 + 900 * (1 - k2))
    dep = Image.new("RGBA", (pw, phh), (0, 0, 0, 0)); dd = ImageDraw.Draw(dep)
    dd.rounded_rectangle([0, 0, pw - 1, phh - 1], radius=34, fill=NAVY + (255,), outline=Y + (255,), width=4)
    # listras de obra no topo do card
    for x in range(-40, pw + 40, 56): dd.polygon([(x, 0), (x + 28, 0), (x + 8, 22), (x - 20, 22)], fill=(255, 255, 255, 170))
    q = F("InterDisplay-Black", 300); pulse = 1 + 0.06 * math.sin(te * 7)
    qs, qp = text_sprite("?", q, Y + (255,)); qs = qs.resize((int(qs.width * pulse), int(qs.height * pulse)), Image.BICUBIC)
    dep.alpha_composite(qs, (int(pw / 2 - qs.width / 2), int(phh / 2 - qs.height / 2 - 30)))
    f2 = F("InterDisplay-Black", 64); s2 = "DEPOIS"; s2w = tw(s2, f2)
    dd.rounded_rectangle([30, 30 + 14, 30 + s2w + 44, 30 + 14 + 92], radius=14, fill=Y + (255,))
    dd.text((52, 38 + 14), s2, font=f2, fill=NAVY + (255,))
    # barra "carregando"
    lk = pr(te, 0.8, 3.6); bx0, bx1, by = 60, pw - 60, phh - 70
    dd.rounded_rectangle([bx0, by, bx1, by + 18], radius=9, fill=(255, 255, 255, 40))
    pv = END_PCT[0] + (END_PCT[1] - END_PCT[0]) * eo(lk)
    dd.rounded_rectangle([bx0, by, bx0 + max(18, (bx1 - bx0) * pv / 100), by + 18], radius=9, fill=Y + (255,))
    dd.text((bx0, by - 44), "EM CONSTRUÇÃO…", font=F("Inter-Bold", 26), fill=(210, 215, 225, 255))
    pct = f"{pv:.0f}%"; fp = F("InterDisplay-Black", 30); dd.text((bx1 - tw(pct, fp), by - 48), pct, font=fp, fill=Y + (255,))
    if END_NOTE and te > 1.2:  # ex.: "+2% desde o EP. 01"
        kn = back(pr(te, 1.2, 0.3)); fn = F("InterDisplay-ExtraBold", 30); wn = tw(END_NOTE, fn) + 40
        dd.rounded_rectangle([pw - 30 - wn, 44, pw - 30, 44 + 56], radius=28, fill=(255, 255, 255, int(255 * cl(kn))))
        dd.text((pw - 30 - wn + 20, 54), END_NOTE, font=fn, fill=NAVY + (int(255 * cl(kn)),))
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
    if t >= OUTRO - 0.35:  # painéis recolhem e o logo cresce no centro
        ko = eio(pr(t, OUTRO - 0.35, 0.35))
        bg = Image.blend(bg, dark_bg(W, H, PAL).convert("RGBA"), ko)
        if t >= OUTRO:
            k = back(pr(t, OUTRO, 0.55), 1.4); kb = eo(pr(t, OUTRO, 0.4))
            lg = logo_sz(max(10, 760 * k)); lg = blur_reveal(lg, kb, 14)
            glow = logo_sz(max(10, 760 * k)).filter(ImageFilter.GaussianBlur(28)); glow = with_alpha(glow, 0.45 * kb)
            for im in (glow, lg): bg.alpha_composite(im, (int(W / 2 - im.width / 2), int(820 - im.height / 2)))
            if t >= OUTRO + 0.6:
                k2 = eo(pr(t, OUTRO + 0.6, 0.35)); f = F("InterDisplay-SemiBold", 40)
                spr, pad = text_sprite(OUTRO_TXT, f, SKY + (255,)); spr = blur_reveal(spr, k2)
                bg.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(1330 - pad + 16 * (1 - k2))))
    return bg.convert("RGB")

# ---------------------------------------------------------------- frame
TR = 0.2  # meia-duração das transições
def seg_at(t):
    for i, s in enumerate(SEGS):
        if s[0] <= t < s[1]: return i, s
    return None, None

def base_frame(t):
    i, s = seg_at(t)
    o0, o1, s0, s1, z0, z1 = s[:6]
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
    cmp = s[7] if len(s) > 7 else None
    if cmp:  # comparativo: quadro do episódio anterior (ANTES) é revelado como AGORA por uma divisória
        w0, wd = cmp["wipe"]; kw = eio(pr(t - o0, w0, wd))
        if kw < 1:
            ta = cmp["a"][0] + (cmp["a"][1] - cmp["a"][0]) * k
            fa = fit(src_frame(ta, cmp["src"]), z + zoom_extra)
            xd = int(W * (1 - kw))
            fr = fr.copy(); fr.paste(fa.crop((0, 0, xd, H)), (0, 0))
    if fx_amt: fr = motion_blur(fr, fx_amt, axis)
    if zoom_extra > 0.05: fr = fr.filter(ImageFilter.GaussianBlur(zoom_extra * 14))
    if split: fr = rgb_split(fr, split)
    fr = grade_bottom(fr)
    if flash:
        warm = Image.new("RGB", (W, H), (255, 236, 200)); fr = Image.blend(fr, warm, min(0.95, flash))
    return fr

def compare_labels(L, t):
    """Divisória + selos ANTES (EP anterior) e AGORA durante os comparativos."""
    for s in SEGS:
        if len(s) < 8 or not (s[0] <= t < s[1]): continue
        cmp = s[7]; w0, wd = cmp["wipe"]; tl = t - s[0]
        kw = eio(pr(tl, w0, wd)); kin = eo(pr(tl, 0.15, 0.3)); kout = pr(t, s[1] - 0.25, 0.2)
        f = F("InterDisplay-Black", 46)
        def pill(txt, sub, x, y, fill, ink, a):
            if a <= 0: return
            fs = F("Inter-Bold", 24); wv = tw(txt, f) + 48; wt = max(wv, tw(sub, fs) + 12 if sub else 0)
            im = Image.new("RGBA", (wt, 124), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([0, 0, wv, 72], radius=16, fill=fill + (255,)); d.text((24, 8), txt, font=f, fill=ink + (255,))
            if sub:
                sp, pd = text_sprite(sub, fs, (240, 244, 252, 255), pad=6); im.alpha_composite(sp, (0, 80))
            L.alpha_composite(with_alpha(im, a), (int(x if x >= 0 else W + x - wt), int(y)))
        pill("ANTES", cmp.get("a_sub", ""), 60, cmp.get("ly", 330), (255, 255, 255), NAVY, kin * (1 - kw) * (1 - kout) if kw < 1 else 0)
        pill("AGORA", cmp.get("b_sub", ""), -60, cmp.get("ly", 330), SKY, NAVY, eo(pr(tl, w0 + wd * 0.5, 0.25)) * (1 - kout))
        if 0 < kw < 1:  # linha da divisória com puxador
            xd = int(W * (1 - kw)); d = ImageDraw.Draw(L)
            d.rectangle([xd - 3, 0, xd + 3, H], fill=(255, 255, 255, 235))
            d.ellipse([xd - 44, H / 2 - 44, xd + 44, H / 2 + 44], fill=(255, 255, 255, 255))
            fa = F("InterDisplay-Black", 40); d.text((xd - 30, H / 2 - 26), "‹ ›", font=fa, fill=NAVY + (255,))

# ---------------------------------------------------------------- capa (primeiro quadro / capa do Instagram)
COVER = 1.2  # segundos de capa antes do gancho (todo o resto é deslocado por isso)
_cover_bg = None
def cover(t, still=False):
    global _cover_bg
    if _cover_bg is None: _cover_bg = grade_bottom(fit(src_frame(COVER_SRC), 1.0)).filter(ImageFilter.GaussianBlur(5))
    z = 1.0 if still else 1.0 + 0.05 * t / COVER
    fr = _cover_bg.resize((int(W * z), int(H * z)), Image.LANCZOS)
    fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H)).convert("RGBA")
    veil = Image.new("RGBA", (W, H), (14, 23, 40, 150)); fr.alpha_composite(veil)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lg = logo_sz(420); L.alpha_composite(lg, (int(W / 2 - lg.width / 2), 290))
    fk = F("Inter-Bold", 40); spr, pad = text_sprite(" ".join("DIÁRIO DA REFORMA"), fk, (255, 255, 255, 255))
    L.alpha_composite(spr, (int(W / 2 - spr.width / 2), 875 - pad))
    # EP. 01 em pílula azul-céu
    fe = F("InterDisplay-Black", 54); s1 = EP_LABEL; w1 = tw(s1, fe) + 60
    d = ImageDraw.Draw(L); d.rounded_rectangle([W / 2 - w1 / 2, 955, W / 2 + w1 / 2, 1045], radius=45, fill=SKY + (255,))
    b = fe.getbbox(s1); d.text((W / 2 - (b[2] - b[0]) / 2 - b[0], 1000 - (b[3] - b[1]) / 2 - b[1]), s1, font=fe, fill=NAVY + (255,))
    ft = F("InterDisplay-Black", fit_font(COVER_TITLE, "InterDisplay-Black", 210, 980)); spr, pad = text_sprite(COVER_TITLE, ft, (255, 255, 255, 255), ref="ÁO")
    L.alpha_composite(spr, (int(W / 2 - spr.width / 2), 1090 - pad))
    fs = F("InterDisplay-SemiBold", 46); spr, pad = text_sprite(COVER_SUB, fs, SKY + (255,))
    L.alpha_composite(spr, (int(W / 2 - spr.width / 2), 1375 - pad))
    fs2 = F("Inter-SemiBold", 34); spr, pad = text_sprite("Acompanhe cada etapa  →", fs2, (225, 232, 245, 255))
    L.alpha_composite(spr, (int(W / 2 - spr.width / 2), 1465 - pad))
    fr.alpha_composite(L)
    return fr.convert("RGB")

def render(t):
    if t < COVER:
        fr = cover(t)
        if t > COVER - 0.15:  # flash para o gancho
            fr = Image.blend(fr, Image.new("RGB", (W, H), (235, 243, 255)), (t - (COVER - 0.15)) / 0.15)
        return fr
    t -= COVER
    if t < 0.12: return Image.blend(render_main(t), Image.new("RGB", (W, H), (235, 243, 255)), 1 - t / 0.12)
    return render_main(t)

def render_main(t):
    if t >= END0:
        fr = end_card(t)
        if t - END0 < 0.18: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 1 - (t - END0) / 0.18)
        return fr
    fr = base_frame(t).convert("RGBA")
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # gancho
    kinetic_title(L, HOOK_KICKER, HOOK_TITLE, t, 0.05, W / 2, 520, PAL, size=fit_font(HOOK_TITLE, "InterDisplay-Black", 190, 980), exit_t=3.6, per_letter=0.07)
    rec_dot(L, t, 0.6, 3.6)
    if 0.25 <= t < END0:
        kl = eo(pr(t, 0.25, 0.4)) * (1 - pr(t, END0 - 0.4, 0.3)); lg = blur_reveal(logo_sz(170), kl, 10)
        L.alpha_composite(lg, (44, 52))
    # persistentes
    section_tag(L, TAG_TXT, t, 4.15, END0 - 0.2, 236, 104, PAL, size=28)
    progress_pill(L, t, 4.35, END0 - 0.2, PILL[0], PILL[1], W - 50 - 330, 96)
    compare_labels(L, t)
    tape(L, t, END0 - 0.55, d=0.6)
    fr.alpha_composite(L); fr.alpha_composite(cap_layer(t))
    return fr.convert("RGB")

if __name__ == "__main__":
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    os.makedirs(out, exist_ok=True)
    N = int((END1 + COVER) * FPS)
    for f in range(a, min(b, N)):
        render(f / FPS).save(f"{out}/{f:05d}.png", compress_level=1)
