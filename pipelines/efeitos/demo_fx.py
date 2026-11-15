"""Demo da biblioteca fx.py sobre o reels do EBO (base.mov + mask.mkv + voice_clean.wav).
Saída: brutos/demo_fx/demo_fx.mp4 (vertical 1080x1920, ~14 s)."""
import json, subprocess, sys, os
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import fx
from fx import F, eo, pr, PAL_EBO as P

E = "/home/user/editar_videos/brutos/edit"; OUT = "/home/user/editar_videos/brutos/demo_fx"; os.makedirs(OUT, exist_ok=True)
W, H, FPS, DUR = 1080, 1920, 30, 14.0
J = json.load(open(f"{E}/edl_out.json")); WL = [w for w in J["words"] if w["start"] < DUR]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{E}/mask.mkv", "-frames:v", str(int(DUR * FPS)), "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
MASKS = np.frombuffer(raw, np.uint8).reshape(-1, 640, 360)
def mask_full(fi): return Image.fromarray(MASKS[min(fi, len(MASKS) - 1)]).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))

# frases da legenda: quebra em pontuação; palavras fortes = substantivos/verbos longos ou a última da frase
phr, cur = [], []
for w in WL:
    cur.append(w)
    if w["text"][-1] in ".?!," or len(cur) >= 5: phr.append(cur); cur = []
if cur: phr.append(cur)
CAPS = []
for k, ph in enumerate(phr):
    t_end = phr[k + 1][0]["start"] - 0.02 if k + 1 < len(phr) else ph[-1]["end"] + 0.4
    words = [(w["start"], w["end"], w["text"].strip(".,"), (i >= len(ph) - 2 and len(ph) > 1) or len(w["text"]) > 7) for i, w in enumerate(ph)]
    CAPS.append((ph[0]["start"], t_end, words))

T_SHRINK, T_EX, T_EX_END, T_EXP = 5.0, 5.5, 8.4, 8.9
T_CTA = 11.8
VERSE = "Não vos enganeis: de Deus não se zomba; pois aquilo que o homem semear, isso também ceifará."
def demo_card(t):
    img = Image.new("RGBA", (1000, 470), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 999, 469], radius=34, fill=(246, 243, 236, 255))
    d.ellipse([46, 52, 62, 68], fill=P["accent"] + (255,)); d.text((78, 40), "Gálatas 6:7", font=F("Inter-Bold", 36), fill=(20, 20, 25, 255))
    d.text((800, 46), "ARA", font=F("Inter-SemiBold", 28), fill=(140, 140, 145, 255))
    words = VERSE.split(); x, y = 50, 130; fnt = F("InterDisplay-Bold", 54)
    n = int(len(words) * eo(pr(t, T_EX + 0.3, 2.0)))
    for i, w_ in enumerate(words):
        ww = fx.tw(w_ + " ", fnt)
        if x + ww > 960: x, y = 50, y + 72
        col = P["accent"] if w_.strip(";.,") in ("semear", "ceifará") else (20, 20, 25)
        if i < n: d.text((x, y), w_, font=fnt, fill=col + (255,))
        x += ww
    return img
BG = fx.dark_bg(W, H, P)
HM = fx.HandMasker("/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models", video=True)
CARD = (40, int(H * 0.53), 470, int(H * 0.53) + 560)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{E}/base.mov", "-t", str(DUR), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", f"{OUT}/v.mp4"], stdin=subprocess.PIPE)
for fi in range(int(DUR * FPS)):
    t = fi / FPS; src = Image.frombytes("RGB", (W, H), dec.stdout.read(W * H * 3))
    if T_SHRINK <= t < T_EX:
        enc.stdin.write(fx.shrink_to_card(src, pr(t, T_SHRINK, T_EX - T_SHRINK), CARD, BG, W, H, glow=P["glow"]).tobytes()); continue
    if T_EX <= t < T_EX_END:
        cw = [(w[0], w[1], w[2], w[3]) for s0, s1, ws in CAPS if s0 <= t < s1 for w in ws]
        enc.stdin.write(fx.example_template(BG, src, demo_card(t), "Exemplo 1", "O versículo", cw, t, T_EX, P).tobytes()); continue
    if T_EX_END <= t < T_EXP:
        enc.stdin.write(fx.shrink_to_card(src, 1 - pr(t, T_EX_END, T_EXP - T_EX_END), CARD, BG, W, H, glow=P["glow"]).tobytes()); continue
    frame = src.convert("RGBA")
    # camada "no espaço" (atrás da pessoa): título do gancho, legenda em 2 camadas, título do CTA
    space = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < 2.4: fx.kinetic_title(space, "estudo bíblico online", "GÁLATAS 6:7", t, 0.0, W / 2, 96, P, size=118, exit_t=1.75)
    for s0, s1, ws in CAPS:
        if s0 - 0.05 <= t < s1 + 0.15 and not (t >= T_CTA + 0.6): fx.caption2(space, ws, t, W / 2, H * 0.68, P, t_end=s1)
    frame.alpha_composite(space)
    # só as MÃOS passam na frente da legenda (pele abaixo do queixo); o título do topo fica atrás da cabeça (máscara da pessoa só no topo)
    pm = mask_full(fi); top = Image.new("L", (W, H), 0); top.paste(pm.crop((0, 0, W, 330)), (0, 0))
    occ = Image.fromarray(np.maximum(np.asarray(top), np.asarray(HM(src, t))))
    frame = Image.composite(src.convert("RGBA"), frame, occ)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= T_CTA: fx.kinetic_title(ui, "comenta", "EBO", t, T_CTA, W / 2, 150, P, size=200)
    fx.number_badge(ui, 1, t, 2.3, 4.9, W - 130, 230, P)
    fx.toast(ui, "versículo mais usado fora de contexto", t, 2.8, 4.9, 120, 1560, P)
    fx.section_tag(ui, "ANTES DE TUDO", t, 9.0, 11.6, 60, 120, P)
    fx.chip_list(ui, [(9.2, "Leia o que vem antes", "Gálatas 5"), (9.8, "Leia o que vem depois", "Gálatas 6:8-10"), (10.4, "Pergunte o assunto", "não é dinheiro")], t, W - 440, 300, P, t1=11.6)
    if t >= T_CTA + 0.5:
        fx.comment_card(ui, "ebo.estudo", [(T_CTA + 0.6, "Link do próximo EBO", "quinta · 20h"), (T_CTA + 1.2, "Estudo completo", "youtube")], t, T_CTA + 0.5, 100, 1250, P)
    frame.alpha_composite(ui)
    enc.stdin.write(frame.convert("RGB").tobytes())
enc.stdin.close(); enc.wait(); dec.terminate()
# áudio: voz + plim nas revelações + whoosh nas transições
v, sr = sf.read(f"{E}/voice_clean.wav", dtype="float32"); v = v[: int(DUR * sr)].copy()
def add(sig, at, db):
    i = int(at * sr); s = sig[: len(v) - i] * 10 ** (db / 20); v[i:i + len(s)] += s[:, None]
for at in [0.15, 2.3, T_EX + 0.3, T_CTA]: add(fx.chime(sr), at, -24)
rng = np.random.default_rng(1)
def whoosh(d=0.35):
    n = int(d * sr); x = rng.standard_normal(n); X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / sr); X[(fr < 400) | (fr > 6000)] = 0
    s = np.fft.irfft(X, n) * np.sin(np.linspace(0, np.pi, n)) ** 2; return (s / np.abs(s).max()).astype(np.float32)
for at in [T_SHRINK - 0.1, T_EX_END - 0.05]: add(whoosh(), at, -22)
sf.write(f"{OUT}/a.wav", v, sr)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/v.mp4", "-i", f"{OUT}/a.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", f"{OUT}/demo_fx.mp4"], check=True)
print("ok", f"{OUT}/demo_fx.mp4"); os._exit(0)
