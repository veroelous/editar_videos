"""Reel 9:16 a partir da pregação no palco (mesmo plano do longo_meet, layout "palco").
O 1º quadro é a capa: título grande (serif, destaque dourado), nome e um quadro escolhido do pregador.
Depois: palco em quadrado 1080x1080 acompanhando o pregador (zoom suave), título fixo no alto,
legenda palavra a palavra embaixo, CTA final. Fala em velocidade PLAN["speed"] (1,15x).
Uso: reel_palco.py <reel.json>    (antes: longo_meet.py <plano> dump)
reel.json: plan, blks, [from], [to], title[], kicker, cover_at (s do reel, 1x), cta[], out"""
import json, os, sys, math, re, subprocess, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/user/editar_videos/pipelines/reels_meet"); sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import estilo16 as st
from estilo import font
from fx import eo, eio, pr, tw

R = json.load(open(sys.argv[1])); PLAN = json.load(open(R["plan"]))
E = f"{PLAN['proj']}/edit"; WK = f"{E}/work_{PLAN['id']}"; D = json.load(open(f"{WK}/dump.json")); SRC = D["src"]
TRK = json.load(open(f"{WK}/track.json")); SPEED = PLAN.get("speed", 1.0); FPS = 30 / SPEED
W, H, VY, VS = 1080, 1920, 680, 1080
OUT = R["out"]; TMP = OUT + ".tmp"; os.makedirs(TMP, exist_ok=True)
def norm(s): return re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())

# ------------------------------------------------------------------ trecho: palavras dos blocos, recortadas por "from"/"to"
ws = [w for w in D["words"] if w["blk"] in R["blks"]]
def find(ph, last=False):
    n = norm(ph).split(); k = len(n)
    for i in range(len(ws) - k + 1):
        if [norm(w["text"]) for w in ws[i:i + k]] == n: return i + k - 1 if last else i
    raise KeyError(ph)
a = find(R["from"]) if R.get("from") else 0; b = find(R["to"], True) if R.get("to") else len(ws) - 1
drop = set()
for f_, t_ in R.get("skip", []): drop |= set(range(find(f_), find(t_, True) + 1))   # trechos removidos no meio
ws = [w for j, w in enumerate(ws) if a <= j <= b and j not in drop]
rg = D["ranges"]; segs = []   # (src_ini, src_fim, palavras)
for w in ws:
    r = rg[w["rk"]]; s0 = r["s"] + (w["start"] - r["o"]); s1 = r["s"] + (w["end"] - r["o"])
    if segs and segs[-1][3] == (w["rk"], w["i"] - 1): segs[-1][1] = s1; segs[-1][2].append((w, s0, s1)); segs[-1][3] = (w["rk"], w["i"])
    else: segs.append([s0, s1, [(w, s0, s1)], (w["rk"], w["i"])])
o = 0.0; SEG = []; WR = []
for s0, s1, lst, _ in segs:
    s0 -= 0.12; s1 += 0.25; SEG.append((s0, s1, o))
    for w, a_, b_ in lst: WR.append(dict(text=w["text"], start=o + a_ - s0, end=o + b_ - s0))
    o += s1 - s0
HOLD = R.get("cover_hold", 0.35); TAIL = 2.6; SPEECH = o; TOTAL = HOLD + o + TAIL
print("reel", round(TOTAL / SPEED, 1), "s finais;", len(SEG), "trechos")

# ------------------------------------------------------------------ áudio (voz limpa + whoosh/plim discretos)
inp, fl = [], []
for j, (s0, s1, _) in enumerate(SEG):
    inp += ["-ss", f"{s0:.3f}", "-t", f"{s1 - s0:.3f}", "-i", SRC]
    fl.append(f"[{j}:a]aresample=48000,afade=t=in:d=0.03,afade=t=out:st={s1 - s0 - 0.04:.3f}:d=0.04[a{j}]")
chain = (";".join(fl) + ";" + "".join(f"[a{j}]" for j in range(len(SEG))) + f"concat=n={len(SEG)}:v=0:a=1,adelay={int(HOLD * 1000)}|{int(HOLD * 1000)},apad=pad_dur={TAIL},"
         "highpass=f=90,afftdn=nf=-28:nr=10,acompressor=threshold=-22dB:ratio=3:attack=6:release=120:makeup=2,loudnorm=I=-14:TP=-1.5:LRA=7,"
         f"atempo={SPEED}[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inp + ["-filter_complex", chain, "-map", "[out]", "-ac", "2", f"{TMP}/voz.wav"], check=True)

# ------------------------------------------------------------------ vídeo
def person(ts):
    i = ts / TRK["dt"]; n = np.arange(len(TRK["x"])); return float(np.interp(i, n, TRK["x"])), float(np.interp(i, n, TRK["y"]))
def src_at(t):   # t no reel (1x) → tempo na fonte
    if t < HOLD: return None
    u = t - HOLD
    for s0, s1, oo in SEG:
        if u < oo + (s1 - s0): return s0 + (u - oo)
    return SEG[-1][1] - 0.05
_dec = {"p": None, "k": None, "f": None, "img": None}
def frame_at(ts, k):
    fi = int(round((ts - SEG[k][0]) * FPS))
    if _dec["k"] != k or _dec["f"] != fi:
        if _dec["p"]: _dec["p"].kill()
        _dec["p"] = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", SRC, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE); _dec["k"] = k
    b = _dec["p"].stdout.read(1920 * 1080 * 3); _dec["f"] = fi + 1
    if len(b) == 1920 * 1080 * 3: _dec["img"] = Image.frombytes("RGB", (1920, 1080), b)
    return _dec["img"] or Image.new("RGB", (1920, 1080))
def still(ts):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (1920, 1080), b[:1920 * 1080 * 3])
def auto_cover():
    """Quadro mais expressivo: maior abertura de braços (largura/altura da silhueta), pessoa longe das bordas."""
    import cv2, mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(
        model_asset_path="/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models/selfie_multiclass.tflite"), output_category_mask=True))
    best = (-1, 1.0)
    for u in np.arange(1.0, min(SPEECH - 1, 45.0), 0.75):
        im = np.asarray(still(src_at(HOLD + u)).resize((960, 540)))
        m = (np.squeeze(seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(im))).category_mask.numpy_view()) > 0).astype(np.uint8)
        n, lab, sts, cen = cv2.connectedComponentsWithStats(m)
        if n < 2: continue
        i = 1 + int(np.argmax(sts[1:, 4])); x, y, w, h, ar = sts[i]
        if ar < 1500 or x < 40 or x + w > 920: continue
        sc = w / h + 0.15 * (ar / 6000)
        if sc > best[0]: best = (sc, u)
    print("capa em", round(best[1], 2), "s"); return best[1]
CA = auto_cover() if R.get("cover_at", "auto") == "auto" else R["cover_at"]
COVER = still(src_at(HOLD + CA))
_m = np.ones((VS, VS), np.float32); r_ = np.arange(VS)
_m *= np.clip(r_ / 110, 0, 1)[:, None] * np.clip((VS - r_) / 170, 0, 1)[:, None]   # funde topo/base do quadro no fundo
MASK = Image.fromarray((_m * 255).astype(np.uint8), "L")

def zoom(t):
    P = 8.0; ZT = [1.0, 1.16, 1.06, 1.24]; tb = int(t // P); u = eio(pr(t, tb * P, 2.2))
    return ZT[(tb - 1) % 4] + (ZT[tb % 4] - ZT[(tb - 1) % 4]) * u
def stage_square(im, ts, z):
    px, py = person(ts); S = 1080 / z; x0 = min(max(px - S / 2, 0), 1920 - S); y0 = min(max(py - 0.16 * S, 0), 1080 - S)
    return im.resize((VS, VS), Image.LANCZOS if z > 1.01 else Image.BICUBIC, box=(x0, y0, x0 + S, y0 + S))
def bg_from(im):
    sm = im.resize((240, 135), Image.BILINEAR).crop((82, 0, 158, 135)).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    return Image.blend(sm, Image.new("RGB", (W, H), (8, 8, 10)), 0.66).convert("RGBA")

# legenda: frases curtas (≤ 4 palavras / 24 caracteres), palavra dita acende em dourado
PH, cur = [], []
for j, w in enumerate(WR):
    cur.append(w); nx = WR[j + 1] if j + 1 < len(WR) else None
    if w["text"][-1] in ".?!," or len(cur) >= 4 or sum(len(x["text"]) + 1 for x in cur) > 22 or not nx or nx["start"] - w["end"] > 0.4: PH.append(cur); cur = []
FC = font("sans_b", 66)
def caption(L, t):
    u = t - HOLD
    k = next((i for i, p in enumerate(PH) if p[0]["start"] - 0.08 <= u < (PH[i + 1][0]["start"] - 0.08 if i + 1 < len(PH) else p[-1]["end"] + 0.4)), None)
    if k is None: return
    p = PH[k]; sp = FC.getlength(" "); tot = sum(tw(w["text"], FC) for w in p) + sp * (len(p) - 1); x = W / 2 - tot / 2; y = 1745
    a = eo(pr(u, p[0]["start"] - 0.08, 0.18)); d = ImageDraw.Draw(L)
    for w in p:
        on = u >= w["start"] - 0.04
        d.text((x + 3, y + 4 + 10 * (1 - a)), w["text"], font=FC, fill=(0, 0, 0, int(140 * a)))
        d.text((x, y + 10 * (1 - a)), w["text"], font=FC, fill=(st.GOLD if on else st.INK) + (int(255 * a),)); x += tw(w["text"], FC) + sp

def header(L, t, cover):
    st.kicker(L, R.get("kicker", "Manoel Gonçalves · pregação"), W / 2, 290, 1.0, "center", size=26)
    y = 350; size = R.get("title_size", 112)
    for ln in R["title"]:
        size = st.line_rich(L, ln, W / 2, y, size, 1.0, align="center", maxw=960); y += size * 1.06
    d = ImageDraw.Draw(L); d.line([(W / 2 - 50, y + 26), (W / 2 + 50, y + 26)], fill=st.GOLD + (200,), width=3)

def cta(L, t):
    k = eo(pr(t, HOLD + SPEECH + 0.1, 0.6))
    if k <= 0: return
    y = 1690
    for ln in R.get("cta", ["Se essa palavra é pra você,", "comenta *AMÉM*."]):
        st.line_rich(L, ln, W / 2, y, 70, k, align="center", maxw=980); y += 80

def render(t):
    cover = t < HOLD; ts = src_at(t)
    if cover: im = COVER; z = R.get("cover_zoom", 1.3)
    else:
        k = next((j for j, (s0, s1, _) in enumerate(SEG) if s0 <= ts <= s1 + 0.01), len(SEG) - 1); im = frame_at(ts, k); z = zoom(t)
    out = bg_from(im); sq = stage_square(im, ts if ts else src_at(HOLD + CA), z)
    out.paste(sq, (0, VY), MASK)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); header(L, t, cover)
    if not cover:
        if t < HOLD + SPEECH + 0.3: caption(L, t)
        cta(L, t)
    out.alpha_composite(L); out = out.convert("RGB")
    if t > TOTAL - 0.5: out = Image.blend(Image.new("RGB", (W, H)), out, max(0.0, (TOTAL - t) / 0.5))
    return out

if len(sys.argv) > 2 and sys.argv[2] == "cover":
    render(0).save(OUT.replace(".mp4", "_capa.jpg"), quality=92); print("capa ok"); sys.exit()
NF = int(TOTAL * FPS)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{FPS}", "-i", "-", "-i", f"{TMP}/voz.wav",
                        "-map", "0:v", "-map", "1:a", "-vf", f"setpts=PTS/{SPEED},fps=30", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for fi in range(NF): enc.stdin.write(render(fi / FPS).tobytes())
enc.stdin.close(); enc.wait()
render(0).save(OUT.replace(".mp4", "_capa.jpg"), quality=92)
print("ok", OUT, round(os.path.getsize(OUT) / 2 ** 20, 1), "MiB")
