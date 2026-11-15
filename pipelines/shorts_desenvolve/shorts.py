"""Shorts verticais (≤59 s) a partir de um vídeo 16:9 de talking head — canal Desenvolve Mais.
Uso: shorts.py <id_do_short>   (lê brutos/desenvolve/edit/shorts_plan.json)
Etapas: corte por palavras (pausas comprimidas) com recorte 9:16 centrado no rosto → áudio −14 LUFS →
compositor com fx.py (legenda em 2 camadas com mãos na frente, título cinético, etiqueta do mecanismo,
card de vidro com a frase-chave, badges numéricos, CTA final)."""
import json, subprocess, sys, os, statistics, math
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import fx
from fx import F, eo, pr, back

SID = sys.argv[1]
D = "/home/user/editar_videos/brutos/desenvolve"; E = f"{D}/edit"; SRC = f"{D}/bruto.mp4"
OUTD = f"{D}/shorts"; os.makedirs(OUTD, exist_ok=True); WK = f"{E}/{SID}"; os.makedirs(WK, exist_ok=True)
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
W, H, FPS = 1080, 1920, 30
PAL = dict(bg=(12, 12, 20), ink=(255, 255, 255), accent=(43, 107, 251), cream=(255, 211, 77), glow=(43, 107, 251), muted=(160, 160, 170))
P = json.load(open(f"{E}/shorts_plan.json"))[SID]
WS = json.load(open(f"{E}/transcripts/bruto.json"))["words"]
FACES = json.load(open(f"{E}/faces.json"))
GAP, PRE, POST, TAIL = 0.35, 0.06, 0.10, 2.4

# ------------------------------------------------------------------ 1. corte
ranges = []
for a, b in P["spans"]:
    cur = {"a": a}
    for i in range(a + 1, b + 1):
        if WS[i]["start"] - WS[i - 1]["end"] > GAP:
            cur["b"] = i - 1; ranges.append(cur); cur = {"a": i}
    cur["b"] = b; ranges.append(cur)
for r in ranges:
    a, b = r["a"], r["b"]
    prev_end = WS[a - 1]["end"] if a > 0 else 0; nxt = WS[b + 1]["start"] if b + 1 < len(WS) else WS[b]["end"] + 1
    r["s"] = max(WS[a]["start"] - PRE, prev_end + 0.01); r["e"] = min(WS[b]["end"] + POST, nxt - 0.01)
    fc = [f[1] for f in FACES if r["s"] - 1 <= f[0] <= r["e"] + 1]
    cx = statistics.median(fc) if fc else 0.52
    r["x"] = int(min(max(cx * 1920 - 304, 0), 1920 - 608))
# última faixa ganha cauda para o CTA (silêncio vira "respiro" com o vídeo correndo)
ranges[-1]["tail"] = TAIL
lst = open(f"{WK}/list.txt", "w"); off = 0.0; words = []
for k, r in enumerate(ranges):
    d = r["e"] - r["s"] + r.get("tail", 0); NF = max(1, round(d * FPS)); od = NF / FPS
    out = f"{WK}/seg_{k:03d}.mov"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                    "-frames:v", str(NF), "-vf", f"crop=608:1080:{r['x']}:0,scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p",
                    "-af", (f"aresample=48000,apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, od - 0.03):.4f}:d=0.03"
                            if not r.get("tail") else
                            f"aresample=48000,apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={r['e'] - r['s']:.4f}:d=0.25"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "pcm_s16le", "-ac", "2", out], check=True)
    for i in range(r["a"], r["b"] + 1):
        words.append({"i": i, "text": WS[i]["text"], "start": WS[i]["start"] - r["s"] + off, "end": WS[i]["end"] - r["s"] + off})
    r["o"] = off; off += od; lst.write(f"file 'seg_{k:03d}.mov'\n")
lst.close(); TOTAL = off; T_SPEECH = words[-1]["end"]
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/list.txt", "-c", "copy", f"{WK}/base.mov"], check=True)
WD = {w["i"]: w for w in words}
def S(i): return WD[i]["start"]
print(SID, "duração", round(TOTAL, 2), "s,", len(ranges), "segmentos", flush=True)

# ------------------------------------------------------------------ 2. áudio
chain = "highpass=f=80,afftdn=nf=-30:nr=8,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1.5"
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/base.mov", "-af", chain + ",loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/base.mov", "-af", chain + "," + ln, "-ar", "48000", "-ac", "2", f"{WK}/voice.wav"], check=True)

# ------------------------------------------------------------------ 3. roteiro gráfico
KEY = set(P.get("fortes", [])) | {"sim", "não", "sim,", "não.", "escolher", "influenciado", "gratidão", "obrigação", "coerente", "síndico", "cheio", "vazio",
                                   "degustação", "dívida", "quero", "sentido", "escolhendo", "certo", "errado", "maioria", "critério", "pista", "melhor"}
phrases, cur = [], []
for w in words:
    cur.append(w)
    if w["text"][-1] in ".?!," or len(cur) >= 5 or (len(cur) >= 3 and w is not words[-1] and words[words.index(w) + 1]["start"] - w["end"] > 0.3):
        phrases.append(cur); cur = []
if cur: phrases.append(cur)
CAPS = []
for k, ph in enumerate(phrases):
    t_end = phrases[k + 1][0]["start"] - 0.02 if k + 1 < len(phrases) else min(ph[-1]["end"] + 0.5, TOTAL)
    ws = [(w["start"], w["end"], w["text"].strip(".,"), w["text"].lower().strip(".,?!") in KEY or (i == len(ph) - 1 and len(ph) >= 3)) for i, w in enumerate(ph)]
    CAPS.append((ph[0]["start"], t_end, ws))
CARDS = [(S(c["at"]) - 0.1, min(T_SPEECH - 0.15, (S(c["ate"]) if "ate" in c else S(c["at"]) + c.get("dur", 4.0))), c["linhas"]) for c in P.get("cards", []) if c["at"] in WD]
BADGES = [(S(b["at"]) - 0.05, min(T_SPEECH - 0.15, (S(b["ate"]) if "ate" in b else T_SPEECH)), b["n"]) for b in P.get("badges", []) if b["at"] in WD]
T_TITLE_OUT = min(2.6, S(phrases[min(2, len(phrases) - 1)][0]["i"]) + 0.5)

def draw_card(frame, layer, t, t0, t1, lines):
    """Card de vidro na parte de baixo com a frase-chave (linhas: [(texto, estilo)])."""
    box = (50, 1400, W - 50, 1400 + 100 + 100 * len(lines))
    frame = fx.glass_panel(frame, box, t, t0, t1, tint=(15, 15, 25), alpha=0.55, blur=26)
    k = eo(pr(t, t0, 0.3)) * (1 - pr(t, t1, 0.3))
    for j, (txt, sty) in enumerate(lines):
        kj = eo(pr(t, t0 + 0.15 + 0.18 * j, 0.3))
        f = F("InterDisplay-ExtraBold", 80) if sty != "small" else F("Inter-SemiBold", 40)
        while sty != "small" and fx.tw(txt, f) > W - 160: f = F("InterDisplay-ExtraBold", f.size - 4)
        col = PAL["cream"] if sty == "gold" else (PAL["muted"] if sty == "small" else PAL["ink"])
        spr, pad = fx.text_sprite(txt, f, col + (255,))
        spr = fx.with_alpha(fx.blur_reveal(spr, kj), k)
        layer.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(box[1] + 46 + 100 * j - pad + 30 * (1 - k))))
    return frame

# ------------------------------------------------------------------ 4. render
HM = fx.HandMasker(MODELS, video=True)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"{WK}/video.mp4"], stdin=subprocess.PIPE)
NFR = int(round(TOTAL * FPS))
for fi in range(NFR):
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    t = fi / FPS; src = Image.frombytes("RGB", (W, H), b); frame = src.convert("RGBA")
    # camada no espaço: legenda em 2 camadas no peito (as mãos passam na frente)
    in_card = any(c0 <= t < c1 + 0.3 for c0, c1, _ in CARDS)
    space = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_SPEECH + 0.4:
        for s0, s1, ws in CAPS:
            if s0 - 0.05 <= t < s1 + 0.15: fx.caption2(space, ws, t, W / 2, H * (0.60 if in_card else 0.68), PAL, size_small=52, size_big=74, t_end=s1)
    frame.alpha_composite(space)
    hm = HM(src.resize((540, 960), Image.BILINEAR), t).resize((W, H), Image.BILINEAR)
    frame = Image.composite(src.convert("RGBA"), frame, hm)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # gancho: título cinético no topo
    if t < T_TITLE_OUT + 0.6: fx.kinetic_title(ui, P["kicker"], P["hero"], t, 0.05, W / 2, 150, PAL, size=118 if len(P["hero"]) < 10 else 96, exit_t=T_TITLE_OUT, kicker_scale=0.34)
    # etiqueta do mecanismo (persistente) depois do título
    fx.section_tag(ui, P["tag"].upper(), t, T_TITLE_OUT + 0.4, T_SPEECH - 0.2, 50, 70, PAL, size=30)
    for b0, b1, n in BADGES: fx.number_badge(ui, n, t, b0, b1, W - 120, 160, PAL)
    for c0, c1, lines in CARDS: frame = draw_card(frame, ui, t, c0, c1, lines)
    # CTA final
    if t >= T_SPEECH - 0.1:
        fx.kinetic_title(ui, "assista o vídeo", "COMPLETO", t, T_SPEECH - 0.1, W / 2, 170, PAL, size=120, color=PAL["cream"], kicker_scale=0.34)
        fx.comment_card(ui, "desenvolvemais", [(T_SPEECH + 0.5, "Por que você diz SIM quando queria dizer NÃO?", None)], t, T_SPEECH + 0.3, 110, 1480, PAL, w=860, avatar_col=PAL["accent"])
    frame.alpha_composite(ui)
    enc.stdin.write(frame.convert("RGB").tobytes())
enc.stdin.close(); enc.wait(); dec.terminate()
# áudio: voz + plim nos cards/badges
v, sr = sf.read(f"{WK}/voice.wav", dtype="float32")
def add(sig, at, db):
    i = int(at * sr)
    if i >= len(v): return
    s = sig[: len(v) - i] * 10 ** (db / 20); v[i:i + len(s)] += s[:, None]
for c0, _, _ in CARDS: add(fx.chime(sr), c0 + 0.1, -27)
for b0, _, _ in BADGES: add(fx.chime(sr, f=988), b0, -27)
add(fx.chime(sr, f=1568), T_SPEECH, -25)
sf.write(f"{WK}/mix.wav", v, sr)
final = f"{OUTD}/{SID}_{P['slug']}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/video.mp4", "-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", final], check=True)
print("ok", final, round(TOTAL, 2), "s", flush=True)
os._exit(0)
