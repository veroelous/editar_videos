"""Cortes verticais 1080x1920 a partir do EBO longo. Uso: shorts.py <n> (0..3)"""
import json, subprocess, sys, math
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
E = "/home/user/editar_videos/brutos/longo/edit"; OUTD = "/home/user/editar_videos/brutos/longo/entrega"
FPS, W, H, SW, SH = 24, 1080, 1920, 1280, 720
J = json.load(open(f"{E}/edl_out.json")); WD = {w["i"]: w for w in J["words"] if w["ch"] != "hook"}
CREAM = (242, 238, 230); INK = (17, 17, 17); BLUE = (43, 107, 251); GRAY = (110, 110, 115); WHITE = (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"; _fc = {}
def F(n, s):
    if (n, s) not in _fc: _fc[(n, s)] = ImageFont.truetype(FD + n + ".otf", s)
    return _fc[(n, s)]
def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def pr(t, a, d): return cl((t - a) / d)
def tw(s, f): b = f.getbbox(s); return b[2] - b[0]
def findw(txt, lo, hi):
    for i in range(lo, hi + 1):
        if i in WD and WD[i]["text"].lower().strip(".,?!").startswith(txt): return i
    raise KeyError(txt)
SH_DEF = [
    dict(slug="01_envelope_de_oferta", title=["Já vi esse versículo", "no envelope de oferta"],
         spans=[(601, 630), (findw("eu", 670, 690), 701)]),
    dict(slug="02_fazer_o_bem_cansa", title=["Por que fazer o bem", "cansa?"], spans=[(4297, 4455)]),
    dict(slug="03_a_carne_se_alimenta_sozinha", title=["A carne se alimenta", "sozinha."], spans=[(4592, 4767)]),
    dict(slug="04_continuaria_fazendo_o_bem", title=["Se você não recebesse nada,", "continuaria fazendo o bem?"], spans=[(5223, 5306)]),
]
n = int(sys.argv[1]); D = SH_DEF[n]
# ajusta o 2º span do short 1 para começar em "Eu vou confessar"
if n == 0:
    for i in range(647, 699):
        if i in WD and WD[i]["text"] == "Eu" and WD.get(i + 1, {}).get("text") == "vou" and WD.get(i + 2, {}).get("text") == "confessar":
            D["spans"][1] = (i, 701); break
segs = []  # (base_t0, base_t1, word ids)
for a, b in D["spans"]:
    ids = [i for i in range(a, b + 1) if i in WD]
    segs.append((WD[ids[0]]["start"] - 0.08, WD[ids[-1]]["end"] + 0.3, ids))
TAIL = 1.6
# linha do tempo do short
tl = []; off = 0.0
for t0, t1, ids in segs: tl.append((off, t0, t1, ids)); off += t1 - t0
TOT = off + TAIL
# legendas: blocos de até ~26 caracteres por linha, 2 linhas
words = []
for o, t0, t1, ids in tl:
    for i in ids: words.append((WD[i]["start"] - t0 + o, WD[i]["end"] - t0 + o, WD[i]["text"]))
blocks = []; cur = []
for w in words:
    txt = " ".join(x[2] for x in cur + [w])
    if cur and (len(txt) > 44 or w[0] - cur[-1][1] > 0.5 or cur[-1][2][-1] in ".?!"):
        blocks.append(cur); cur = []
    cur.append(w)
if cur: blocks.append(cur)
FC = F("InterDisplay-Bold", 58)
def lay(block):
    lines, c = [], []
    for w in block:
        if c and tw(" ".join(x[2] for x in c + [w]), FC) > 920: lines.append(c); c = []
        c.append(w)
    if c: lines.append(c)
    return lines
BL = [(b[0][0], (blocks[k + 1][0][0] if k + 1 < len(blocks) else b[-1][1] + 0.6), lay(b)) for k, b in enumerate(blocks)]

BGBASE = Image.new("RGB", (W, H), CREAM); g = ImageDraw.Draw(BGBASE, "RGBA")
for x in range(0, W, 120): g.line([(x, 0), (x, H)], fill=INK + (12,))
for y in range(0, H, 120): g.line([(0, y), (W, y)], fill=INK + (12,))
d0 = ImageDraw.Draw(BGBASE)
d0.ellipse([80, 170, 94, 184], fill=BLUE); d0.text((108, 158), "EBO · Gálatas 6:7-10", font=F("Inter-SemiBold", 34), fill=(80, 80, 85))
ft = F("InterDisplay-ExtraBold", 74)
for j, line in enumerate(D["title"]):
    while tw(line, ft) > 920: ft = F("InterDisplay-ExtraBold", ft.size - 4)
for j, line in enumerate(D["title"]):
    d0.text((80, 222 + j * 88), line, font=ft, fill=(BLUE if j == 1 else INK))
VX, VY, VW, VH = 60, 430, 960, 1080
MASK = Image.new("L", (VW, VH), 0); ImageDraw.Draw(MASK).rounded_rectangle([0, 0, VW - 1, VH - 1], radius=40, fill=255)
SHD = Image.new("RGBA", (VW + 120, VH + 120), (0, 0, 0, 0)); ImageDraw.Draw(SHD).rounded_rectangle([60, 74, VW + 60, VH + 74], radius=40, fill=(0, 0, 0, 90))
SHD = SHD.filter(ImageFilter.GaussianBlur(22)); BGBASE.paste(SHD, (VX - 60, VY - 60), SHD)

def video_area(im):
    arr = np.asarray(im); cm = arr.mean(axis=(0, 2))
    if cm[:200].mean() < 8 and cm[-200:].mean() < 8 and cm[500:780].mean() > 25:
        tile = im.crop((444, 0, 836, 680))
        bg = tile.resize((24, 27), Image.BILINEAR).resize((VW, VH), Image.BICUBIC)
        bg = Image.blend(bg, Image.new("RGB", (VW, VH)), 0.35)
        th = VH - 80; twd = int(392 * th / 680); t2 = tile.resize((twd, th), Image.BICUBIC)
        bg.paste(t2, ((VW - twd) // 2, 40)); return bg
    cw = SH * VW / VH; cx = 0.45 * SW; x0 = min(max(0, cx - cw / 2), SW - cw)
    return im.resize((VW, VH), Image.BICUBIC, box=(x0, 0, x0 + cw, SH - 14))

out_v = f"{E}/short_{n}_v.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out_v], stdin=subprocess.PIPE)
last = None
for o, t0, t1, ids in tl + [(off, None, None, None)]:
    if t0 is None:
        nfr = int(round(TAIL * FPS)); src = None
    else:
        nfr = int(round((t1 - t0) * FPS))
        src = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", f"{E}/base.mov", "-frames:v", str(nfr), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    for k in range(nfr):
        t = o + k / FPS
        if src:
            b = src.stdout.read(SW * SH * 3)
            if len(b) == SW * SH * 3: last = b
        fr = BGBASE.copy(); fr.paste(video_area(Image.frombytes("RGB", (SW, SH), last)), (VX, VY), MASK)
        d = ImageDraw.Draw(fr, "RGBA")
        for a, bnd, lines in BL:
            if a - 0.03 <= t < bnd:
                for li, line in enumerate(lines):
                    x = 80
                    for w in line:
                        if t >= w[0] - 0.03:
                            kk = pr(t, w[0] - 0.03, 0.1); act = w[0] - 0.03 <= t < w[1] + 0.05
                            col = (BLUE if act else INK) + (int(255 * (0.35 + 0.65 * kk)),)
                            d.text((x, 1560 + li * 70), w[2], font=FC, fill=col)
                        x += tw(w[2] + " ", FC)
        if t >= off:  # cartão final
            kb = eo(pr(t, off, 0.35)); txt = "estudo completo no YouTube  ↗"; fb = F("Inter-Bold", 44); bw = tw(txt, fb) + 70
            d.rounded_rectangle([(W - bw) // 2, 1700 - 10 * (1 - kb), (W + bw) // 2, 1790], radius=45, fill=BLUE + (int(255 * kb),))
            d.text(((W - bw) // 2 + 35, 1718), txt, font=fb, fill=WHITE + (int(255 * kb),))
        enc.stdin.write(fr.tobytes())
    if src: src.terminate()
enc.stdin.close(); enc.wait()
# áudio: trechos da voz limpa + cauda silenciosa, fades de 30 ms
v, sr = sf.read(f"{E}/voice_clean.wav", dtype="float32"); parts = []
for o, t0, t1, ids in tl:
    seg = v[int(t0 * sr):int(t1 * sr)].copy(); f = int(0.03 * sr)
    seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]; parts.append(seg)
parts.append(np.zeros((int(TAIL * sr), 2), np.float32))
sf.write(f"{E}/short_{n}_a.wav", np.concatenate(parts), sr)
final = f"{OUTD}/short_{D['slug']}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out_v, "-i", f"{E}/short_{n}_a.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
print("short ok", final, round(TOT, 1), "s")
