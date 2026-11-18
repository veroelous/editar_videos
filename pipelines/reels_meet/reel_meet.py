"""Reel 9:16 viral a partir de gravação de Meet em que a câmera do autor é uma miniatura.
O rosto vai para uma MOLDURA grande (super-resolução x4, sr.py) sobre fundo animado; a parte de baixo
recebe gráficos que contam a história (pistas de corrida, cards, títulos cinéticos), com legenda em 2 camadas,
zooms por corte e por ênfase, efeitos sonoros e trilha sintetizada com ducking.
Uso:  reel_meet.py prep            (corte + base + voz)
      reel_meet.py render k n      (parte k de n, em paralelo)
      reel_meet.py frames t1 t2 …  (prévia em JPG)
      reel_meet.py audio           (voz + trilha + SFX)
      reel_meet.py pack            (junta e entrega ≤380 MiB)"""
import json, os, sys, math, subprocess, hashlib
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx
from fx import F, eo, eio, back, pr, tw, with_alpha, text_sprite, blur_reveal, cl

D = os.environ.get("PROJ", "/home/user/editar_videos/brutos/reel4"); E = f"{D}/edit"; SRC = f"{D}/dl/bruto.mp4"; WK = f"{E}/work"
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
os.makedirs(WK, exist_ok=True)
W, H, FPS = 1080, 1920, 30
PAL = dict(bg=(9, 10, 16), ink=(255, 255, 255), accent=(43, 107, 251), cream=(255, 211, 77), glow=(43, 107, 251), muted=(150, 155, 170))
GOLD, BLUE, INK, MUTED, RED = PAL["cream"], PAL["accent"], PAL["ink"], PAL["muted"], (235, 64, 52)
TILE = dict(x0=963, x1=1280, y=273, s=156)          # miniatura da câmera no quadro 1280x720 (sem a legenda do nome)
SEGS = {1: (f"{E}/transcripts/seg1.json", 1340.0), 2: (f"{E}/transcripts/seg2.json", 3190.0)}
GAP, PRE, POST, TAIL = 0.30, 0.05, 0.10, 3.0
# roteiro: (seg, palavra_ini, palavra_fim, bloco)
SPANS = [(1, 868, 876, "hook"), (1, 634, 645, "mito"),
         (1, 232, 242, "C"), (1, 268, 275, "C"), (1, 351, 361, "B"), (1, 378, 383, "B"),
         (1, 498, 510, "A"), (1, 511, 522, "A"), (1, 536, 546, "A"), (1, 554, 557, "justo"), (1, 565, 574, "justo"),
         (1, 1024, 1038, "reconhecer"), (1, 1130, 1141, "parar"), (2, 59, 83, "anda")]
FIX = {"esforce.": "esforce.", "ante.": "anda."}
EMPH = {"esforço.", "verdade", "particular,", "público.", "bomba,", "menos.", "justo,", "destino", "parar", "chamando.", "anda.", "injusto."}

# ------------------------------------------------------------------ corte (mapa palavra -> tempo de saída)
WSRC = {k: json.load(open(p))["words"] for k, (p, _) in SEGS.items()}
FT = json.load(open(f"{E}/faces_tile.json"))
ranges = []
for seg, a, b, blk in SPANS:
    ws = WSRC[seg]; off = SEGS[seg][1]; cur = dict(seg=seg, a=a, blk=blk)
    for i in range(a + 1, b + 1):
        if ws[i]["start"] - ws[i - 1]["end"] > GAP: cur["b"] = i - 1; ranges.append(cur); cur = dict(seg=seg, a=i, blk=blk)
    cur["b"] = b; ranges.append(cur)
o = 0.0; WORDS = []; WD = {}
for k, r in enumerate(ranges):
    ws = WSRC[r["seg"]]; off = SEGS[r["seg"]][1]; a, b = r["a"], r["b"]
    prev_end = ws[a - 1]["end"] if a > 0 else 0; nxt = ws[b + 1]["start"] if b + 1 < len(ws) else ws[b]["end"] + 1
    r["s"] = off + max(ws[a]["start"] - PRE, prev_end + 0.01); r["e"] = off + min(ws[b]["end"] + POST, nxt - 0.01)
    r["tail"] = TAIL if k == len(ranges) - 1 else 0
    fc = [f[1] for f in FT if r["s"] - 2 <= f[0] <= r["e"] + 2]
    cx = float(np.median(fc)) if fc else 1036.0
    r["x"] = int(min(max(cx - TILE["s"] / 2, TILE["x0"]), TILE["x1"] - TILE["s"]))
    d = r["e"] - r["s"] + r["tail"]; r["nf"] = max(1, round(d * FPS)); r["o"] = o; r["d"] = r["nf"] / FPS
    for i in range(a, b + 1):
        txt = FIX.get(ws[i]["text"], ws[i]["text"])
        w = dict(seg=r["seg"], i=i, text=txt, start=off + ws[i]["start"] - r["s"] + o, end=off + ws[i]["end"] - r["s"] + o, blk=r["blk"], rk=k)
        WORDS.append(w); WD[(r["seg"], i)] = w
    o += r["d"]
TOTAL = o; T_SPEECH = WORDS[-1]["end"]
def S(seg, i): return WD[(seg, i)]["start"]
def Ee(seg, i): return WD[(seg, i)]["end"]
def find(txt, seg, lo, hi):
    for i in range(lo, hi + 1):
        if (seg, i) in WD and WD[(seg, i)]["text"].lower().strip(".,?!").startswith(txt): return S(seg, i)
    raise KeyError(txt)
BLK = {}
for w in WORDS: BLK.setdefault(w["blk"], [w["start"], w["end"]]); BLK[w["blk"]][1] = w["end"]
BORDERS = [ranges[k]["o"] for k in range(1, len(ranges)) if ranges[k]["blk"] != ranges[k - 1]["blk"]]

# ------------------------------------------------------------------ PREP
if sys.argv[1] == "prep":
    lst = open(f"{WK}/list.txt", "w")
    for k, r in enumerate(ranges):
        od = r["d"]; out = f"{WK}/seg_{k:03d}.mkv"
        af = (f"aresample=48000,apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, od - 0.03):.4f}:d=0.03" if not r["tail"] else
              f"aresample=48000,apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={r['e'] - r['s']:.4f}:d=0.3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{od + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                        "-vf", f"crop={TILE['s']}:{TILE['s']}:{r['x']}:{TILE['y']},fps={FPS}", "-af", af,
                        "-c:v", "ffv1", "-c:a", "pcm_s16le", "-ac", "2", out], check=True)
        lst.write(f"file 'seg_{k:03d}.mkv'\n")
    lst.close()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/list.txt", "-c", "copy", f"{WK}/base.mkv"], check=True)
    chain = "highpass=f=90,afftdn=nf=-28:nr=10,acompressor=threshold=-22dB:ratio=3:attack=6:release=120:makeup=2"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/base.mkv", "-af", chain + ",loudnorm=I=-15:TP=-1.5:LRA=6:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    ln = (f"loudnorm=I=-15:TP=-1.5:LRA=6:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/base.mkv", "-af", chain + "," + ln, "-ar", "48000", "-ac", "2", f"{WK}/voice.wav"], check=True)
    print("prep ok", round(TOTAL, 2), "s,", len(ranges), "cortes; fala até", round(T_SPEECH, 2)); sys.exit()

# ------------------------------------------------------------------ roteiro gráfico (tempos de saída)
EV = []
def ev(kind, t0, t1, **kw): EV.append(dict(kind=kind, t0=t0, t1=t1, **kw))
hb = BLK["hook"]; ev("hook", 0.0, hb[1] + 0.35, lines=[(0.0, "NEM TODA DIFERENÇA"), (find("resultado", 1, 868, 876) - 0.1, "DE RESULTADO")], exit=hb[1] - 0.05)
ev("kinetic", find("é", 1, 868, 876) - 0.15, hb[1] + 0.35, kicker="", title="É ESFORÇO", exit=hb[1] - 0.05, y=1640, size=150)
mb = BLK["mito"]
ev("quote", mb[0] - 0.1, mb[1] + 0.3, lines=["“Todo mundo consegue,", "é só se esforçar.”"], x_at=find("não", 1, 642, 645))
lane_on = BLK["C"][0] - 0.1
ev("lanes", lane_on, BLK["justo"][1] + 0.4)
CHIPS = {"C": [(find("casal", 1, 232, 242), "money_bag", "classe B"), (find("particular", 1, 268, 275), "school", "escola particular")],
         "B": [(find("pai", 1, 351, 361), "broken_heart", "pai longe de casa"), (find("público", 1, 378, 383), "backpack", "escola pública")],
         "A": [(find("afeganistão", 1, 498, 510), "warning", "guerra"), (find("bomba", 1, 511, 522) - 0.3, "broken_heart", "sem pai"),
               (find("hospital", 1, 536, 546), "hospital", "sem escola nem hospital")]}
ACTIVE = [("C", BLK["C"][0] - 0.1), ("B", BLK["B"][0] - 0.1), ("A", BLK["A"][0] - 0.1), ("all", BLK["justo"][0] - 0.1)]
ev("kinetic", find("conquistar", 1, 565, 574) - 0.3, BLK["justo"][1] + 0.35, kicker="isso é", title="JUSTO?", exit=BLK["justo"][1] - 0.05, y=1560, size=170, dark=True)
rb = BLK["reconhecer"]
ev("statement", rb[0] - 0.1, rb[1] + 0.3, lines=[("reconhecer a injustiça da largada", "ink"), ("não me autoriza a entregar", "ink"), ("meu destino a ela", "gold")],
   line_t=[rb[0], find("não", 1, 1024, 1038), find("destino", 1, 1024, 1038) - 0.4])
pb = BLK["parar"]
ev("chip_big", pb[0] - 0.1, find("mas", 1, 1130, 1141) - 0.05, icon="check_mark_button", text="vamos reconhecer: é injusto")
ev("kinetic", find("mas", 1, 1130, 1141) - 0.1, pb[1] + 0.35, kicker="mas eu", title="NÃO VOU PARAR", exit=pb[1] - 0.05, y=1540, size=128)
ab = BLK["anda"]; t_lev = find("levanta", 2, 59, 83)
ev("duo", ab[0] - 0.1, t_lev - 0.15, rows=[(ab[0], "hourglass_not_done", "o passado", "explica"), (find("jesus", 2, 59, 83), "sparkles", "Jesus", "ainda chama")])
ev("hero", t_lev - 0.1, T_SPEECH + 0.45, kicker="", title="LEVANTA E ANDA", flash=t_lev)
ev("cta", T_SPEECH + 0.35, TOTAL + 1)
ev("tag", hb[1] + 0.3, T_SPEECH + 0.3, text="LARGADAS INJUSTAS")
ev("lower3", 0.6, 4.2, name="Manoel Gonçalves", role="Escola Bíblica · João 5")
PUNCH = [(w["start"], w["end"]) for w in WORDS if w["text"].lower() in EMPH]
IMPACT = [find("verdade", 1, 642, 645) - 0.2, t_lev]

# ------------------------------------------------------------------ desenho
_ic = {}
def icon(name, s):
    k = (name, s)
    if k not in _ic: _ic[k] = Image.open(f"{E}/icons/{name}.png").convert("RGBA").resize((s, s), Image.LANCZOS)
    return _ic[k]
rng = np.random.default_rng(7)
PART = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(20, 60), rng.uniform(0, 6.28)) for _ in range(46)]
yy, xx = np.mgrid[0:96, 0:54].astype(np.float32)
def background(t):
    """Fundo escuro com duas luzes que passeiam (azul e dourada) + partículas subindo."""
    img = np.zeros((96, 54, 3), np.float32) + np.array(PAL["bg"], np.float32)
    for (cx, cy, r, col, sp, ph) in [(27, 30, 26, BLUE, 0.35, 0), (27, 70, 22, GOLD, 0.27, 2.0), (10, 50, 18, (120, 70, 255), 0.21, 4.0)]:
        x = cx + 16 * math.sin(t * sp + ph); y = cy + 10 * math.cos(t * sp * 0.8 + ph)
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r))[..., None]
        img += g * np.array(col, np.float32) * (0.22 if col == GOLD else 0.32)
    bg = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert("RGBA")
    d = ImageDraw.Draw(bg)
    for (x0, y0, s, sp, ph) in PART:
        y = (y0 - t * sp) % H; x = x0 + 14 * math.sin(t * 0.6 + ph); a = int(70 + 60 * math.sin(t * 1.3 + ph))
        d.ellipse([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=(255, 255, 255, max(0, a)))
    return bg

FB = (100, 250, 980, 1130)   # moldura do rosto
_sr = None; _cache = {}
def cam_big(raw):
    global _sr
    key = hashlib.md5(raw).hexdigest()
    if key not in _cache:
        if _sr is None:
            from sr import Upscaler; _sr = Upscaler(MODELS, threads=int(os.environ.get("SR_THREADS", "1")))
        _cache.clear(); _cache[key] = Image.fromarray(_sr(np.frombuffer(raw, np.uint8).reshape(TILE["s"], TILE["s"], 3)))
    return _cache[key]
def zoom_at(t):
    k = max(0, min(len(ranges) - 1, next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1)))
    r = ranges[k]; base = 1.12 if k % 2 == 0 else 1.32
    z = base * (1 + 0.05 * pr(t, r["o"], r["d"]))
    for s0, s1 in PUNCH:
        if s0 - 0.12 <= t <= s1 + 0.6: z *= 1 + 0.16 * eo(pr(t, s0 - 0.12, 0.14)) * (1 - eio(pr(t, s1 + 0.3, 0.3)))
    return z
def shake(t):
    for t0 in IMPACT:
        if t0 <= t < t0 + 0.35:
            a = 14 * (1 - (t - t0) / 0.35); return a * math.sin(t * 90), a * math.cos(t * 77)
    return 0, 0
def frame_layer(img, t):
    """Moldura arredondada com o rosto + borda com brilho; entrada com pop; pulso nas trocas de bloco."""
    z = zoom_at(t); s = img.width
    cw = s / z; c0 = (s - cw) / 2; cy0 = s * 0.47 - cw / 2; cy0 = min(max(0, cy0), s - cw)
    fw, fh = FB[2] - FB[0], FB[3] - FB[1]
    pop = back(pr(t, 0.0, 0.5), 1.4); pulse = 0
    for b in BORDERS:
        if b - 0.06 <= t < b + 0.3: pulse = max(pulse, math.sin(math.pi * pr(t, b - 0.06, 0.36)))
    sc = (0.86 + 0.14 * pop) * (1 + 0.035 * pulse)
    piece = img.resize((fw, fh), Image.BICUBIC, box=(c0, cy0, c0 + cw, cy0 + cw))
    if pulse > 0.05: piece = piece.filter(ImageFilter.GaussianBlur(3 * pulse))
    pw, ph = int(fw * sc), int(fh * sc); piece = piece.resize((pw, ph), Image.BICUBIC)
    lay = Image.new("RGBA", (pw + 120, ph + 120), (0, 0, 0, 0))
    gl = Image.new("RGBA", lay.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    ga = 120 + int(60 * math.sin(t * 2.2))
    gd.rounded_rectangle([50, 50, pw + 70, ph + 70], radius=58, fill=BLUE + (ga,)); gl = gl.filter(ImageFilter.GaussianBlur(26))
    lay.alpha_composite(gl)
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=48, fill=255)
    lay.paste(piece.convert("RGBA"), (60, 60), m)
    ImageDraw.Draw(lay).rounded_rectangle([60, 60, 60 + pw - 1, 60 + ph - 1], radius=48, outline=(255, 255, 255, 120), width=4)
    return with_alpha(lay, min(1, pop * 1.4)), (FB[0] + fw / 2, FB[1] + fh / 2)

def pill(icon_name, text, fs=32, h=60, bgc=(255, 255, 255, 240), fg=(18, 20, 30, 255)):
    f = F("InterDisplay-Bold", fs); w = tw(text, f) + (h + 30 if icon_name else 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bgc)
    x = 20
    if icon_name: im.alpha_composite(icon(icon_name, h - 14), (10, 7)); x = h + 8
    b = f.getbbox(text); d.text((x, h / 2 - (b[3] + b[1]) / 2), text, font=f, fill=fg)
    return im

PANEL = (50, 1300, 1030, 1860)
LANES = {"A": (1430, 170), "B": (1600, 330), "C": (1770, 490)}   # y da pista, x de largada
FIN = 960
def draw_lanes(layer, t, e):
    k = eo(pr(t, e["t0"], 0.4)) * (1 - eo(pr(t, e["t1"] - 0.35, 0.35)))
    if k <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(PANEL, radius=40, fill=(14, 16, 26, 225), outline=(255, 255, 255, 40), width=2)
    fl = F("Inter-Bold", 24); d.text((PANEL[0] + 40, PANEL[1] + 26), " ".join("LARGADAS"), font=fl, fill=MUTED + (255,))
    d.text((FIN - tw(" ".join("CHEGADA"), fl) + 20, PANEL[1] + 26), " ".join("CHEGADA"), font=fl, fill=MUTED + (255,))
    for y in range(PANEL[1] + 70, PANEL[3] - 30, 22): d.line([(FIN, y), (FIN, y + 11)], fill=(255, 255, 255, 120), width=3)
    lay.alpha_composite(icon("chequered_flag", 64), (FIN - 10, PANEL[1] + 62))
    act = None
    for name, t0 in ACTIVE:
        if t >= t0: act = name
    for L, (y, x0) in LANES.items():
        on = act == L or act == "all"; seen = any(t >= t0 for n, t0 in ACTIVE if n == L) or act == "all"
        dim = 1.0 if on else (0.45 if seen else 0.25)
        d.line([(x0, y), (FIN, y)], fill=(255, 255, 255, int(50 * dim)), width=3)
        # progresso do corredor
        t_start = next(t0 for n, t0 in ACTIVE if n == L); t_all = next(t0 for n, t0 in ACTIVE if n == "all")
        p = 0.22 * eio(pr(t, t_start, 2.5)) + 0.35 * eio(pr(t, t_all, 3.5))
        xr = x0 + (FIN - 90 - x0) * p
        d.line([(x0, y), (xr + 20, y)], fill=(BLUE if on else MUTED) + (int(255 * dim),), width=8)
        d.ellipse([x0 - 7, y - 7, x0 + 7, y + 7], fill=INK + (int(255 * dim),))
        # letra
        kb = back(pr(t, t_start, 0.3), 2.2) if seen else 0.6
        r = 34 * max(0.4, kb); cx = PANEL[0] + 60
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=((GOLD if on else (70, 74, 90)) + (255,)))
        fL = F("InterDisplay-Black", int(40 * max(0.4, kb))); bb = fL.getbbox(L)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), L, font=fL, fill=(15, 15, 22, 255))
        bob = 6 * abs(math.sin(t * 9)) if on and p < 0.99 else 0
        ri = icon("person_running", 86)
        lay.alpha_composite(with_alpha(ri, dim), (int(xr - 20), int(y - 92 - bob)))
        # chips
        cx2 = x0
        for tc, ic, txt in CHIPS[L]:
            if t < tc - 0.05: continue
            kc = back(pr(t, tc - 0.05, 0.3), 2.0); pl = pill(ic, txt, fs=30, h=54)
            pl = pl.resize((max(1, int(pl.width * kc)), max(1, int(pl.height * kc))), Image.BICUBIC)
            lay.alpha_composite(with_alpha(pl, dim), (int(cx2), int(y + 18 + 26 * (1 - kc))))
            cx2 += pl.width + 10
    layer.alpha_composite(with_alpha(lay, k), (0, int(40 * (1 - k))))

def draw_quote(frame, layer, t, e):
    k = eo(pr(t, e["t0"], 0.35)) * (1 - eo(pr(t, e["t1"] - 0.3, 0.3)))
    if k <= 0: return frame
    box = (90, 1360, 990, 1640); tilt = -3
    card = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=36, fill=(250, 248, 242, 255))
    fq = F("InterDisplay-ExtraBold", 66)
    for j, l in enumerate(e["lines"]): cd.text((60, 52 + j * 88), l, font=fq, fill=(20, 20, 28, 255))
    xs = e["x_at"]
    if t >= xs:
        fx.strike_x(card, (40, 30, card.width - 40, card.height - 30), t, xs, color=RED, width=18)
    card = card.rotate(tilt, expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(with_alpha(card, k), (box[0] - 20, int(box[1] + 50 * (1 - k))))
    if t >= xs + 0.15:   # carimbo
        ks = pr(t, xs + 0.15, 0.22); s = 1.7 - 0.7 * eo(ks)
        st = pill(None, "NÃO É VERDADE", fs=64, h=110, bgc=RED + (255,), fg=(255, 255, 255, 255))
        st = st.rotate(6, expand=True, resample=Image.BICUBIC); st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        layer.alpha_composite(with_alpha(st, min(1, ks * 2) * k), (int(W / 2 - st.width / 2), int(1700 - st.height / 2)))
    return frame

def draw_statement(frame, layer, t, e):
    k = eo(pr(t, e["t0"], 0.35)) * (1 - eo(pr(t, e["t1"] - 0.3, 0.3)))
    if k <= 0: return frame
    box = (60, 1330, 1020, 1800)
    frame = fx.glass_panel(frame, box, t, e["t0"], e["t1"] - 0.3, tint=(14, 16, 26), alpha=0.62, blur=28)
    y = 1400
    for (txt, sty), tl in zip(e["lines"], e["line_t"]):
        f = F("InterDisplay-ExtraBold", 74 if sty == "gold" else 56)
        while tw(txt, f) > 880: f = F("InterDisplay-ExtraBold", f.size - 3)
        kj = eo(pr(t, tl - 0.05, 0.35)); spr, pad = text_sprite(txt, f, (GOLD if sty == "gold" else INK) + (255,))
        layer.alpha_composite(with_alpha(blur_reveal(spr, kj), k * min(1, kj * 3)), (int(W / 2 - spr.width / 2), int(y - pad + 20 * (1 - kj))))
        y += 120 if sty == "gold" else 96
    return frame

def draw_duo(layer, t, e):
    ko = eo(pr(t, e["t1"] - 0.25, 0.25))
    for j, (tr, ic, a, b) in enumerate(e["rows"]):
        if t < tr - 0.1: continue
        k = back(pr(t, tr - 0.1, 0.4), 1.6); y = 1390 + j * 220
        x = 90 + int(-300 * (1 - min(1, k)))
        layer.alpha_composite(with_alpha(icon(ic, 150), min(1, k) * (1 - ko)), (x, y))
        fa, fb = F("InterDisplay-SemiBold", 54), F("InterDisplay-ExtraBold", 92)
        s1, p1 = text_sprite(a, fa, INK + (255,)); s2, p2 = text_sprite(b, fb, (GOLD if j == 1 else INK) + (255,))
        layer.alpha_composite(with_alpha(s1, min(1, k) * (1 - ko)), (x + 180 - p1, y + 4 - p1))
        layer.alpha_composite(with_alpha(blur_reveal(s2, eo(pr(t, tr + 0.1, 0.3))), 1 - ko), (x + 180 - p2, y + 66 - p2))

def draw_hero(layer, t, e):
    tf = e["flash"]; k = pr(t, tf, 0.5)
    if t >= tf and t < tf + 0.35:
        a = int(200 * (1 - pr(t, tf, 0.35))); layer.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 220, a)))
    # raios de luz atrás do título
    if t >= tf:
        rays = Image.new("RGBA", (W, 900), (0, 0, 0, 0)); rd = ImageDraw.Draw(rays); cx, cy = W / 2, 450
        for j in range(14):
            ang = j / 14 * 2 * math.pi + t * 0.4
            rd.polygon([(cx, cy), (cx + 900 * math.cos(ang - 0.06), cy + 900 * math.sin(ang - 0.06)), (cx + 900 * math.cos(ang + 0.06), cy + 900 * math.sin(ang + 0.06))], fill=GOLD + (34,))
        rays = rays.filter(ImageFilter.GaussianBlur(10)); layer.alpha_composite(with_alpha(rays, eo(k)), (0, 1150))
        fx.kinetic_title(layer, "", "LEVANTA", t, tf - 0.15, W / 2, 1450, PAL, size=170, per_letter=0.04, color=INK)
        fx.kinetic_title(layer, "", "E ANDA.", t, tf + 0.25, W / 2, 1640, PAL, size=190, per_letter=0.05, color=GOLD)
        kf = back(pr(t, tf + 0.6, 0.4), 2.0)
        if kf > 0:
            s = int(130 * kf); layer.alpha_composite(icon("footprints", 130).resize((max(1, s), max(1, s))), (int(W - 200 - s / 2), int(1300 - s / 2 + 8 * math.sin(t * 4))))
        # partículas douradas explodindo
        rr = np.random.default_rng(11); d = ImageDraw.Draw(layer)
        for _ in range(60):
            ang = rr.uniform(0, 6.28); sp = rr.uniform(300, 900); s = rr.uniform(4, 11); dt = t - tf
            if dt > 1.6: break
            x = W / 2 + math.cos(ang) * sp * eo(dt / 1.6); y = 1560 + math.sin(ang) * sp * 0.7 * eo(dt / 1.6) + 200 * dt * dt
            a = int(255 * (1 - dt / 1.6)); d.ellipse([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=GOLD + (a,))

def draw_cta(layer, t, e):
    t0 = e["t0"]
    fx.kinetic_title(layer, "comenta", "ANDA", t, t0, W / 2, 1460, PAL, size=180, color=GOLD, kicker_scale=0.3)
    fx.comment_card(layer, "você", [(t0 + 0.6, "ANDA  —  eu me levanto hoje", None)], t, t0 + 0.4, 110, 1690, PAL, w=860, avatar_col=BLUE)
    kp = back(pr(t, t0 + 0.9, 0.3), 2.2)
    if kp > 0:
        s = int(110 * kp); layer.alpha_composite(icon("folded_hands", 110).resize((max(1, s), max(1, s))), (int(W - 170 - s / 2), int(1310 - s / 2)))

def draw_lower3(layer, t, e):
    k = eo(pr(t, e["t0"], 0.4)); ko = eo(pr(t, e["t1"] - 0.4, 0.4))
    fn, fr = F("InterDisplay-Bold", 40), F("Inter-Medium", 26)
    w = max(tw(e["name"], fn), tw(e["role"], fr)) + 70; h = 110
    x = FB[0] + 30 - int((w + 80) * (1 - k)) - int((w + 80) * ko); y = FB[3] - h - 30
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, w - 1, h - 1], radius=22, fill=(255, 255, 255, 240)); bd.rectangle([0, 16, 10, h - 16], fill=BLUE + (255,))
    bd.text((32, 14), e["name"], font=fn, fill=(18, 20, 30, 255)); bd.text((32, 66), e["role"], font=fr, fill=(90, 95, 110, 255))
    layer.alpha_composite(box, (x, y))

def draw_hook(layer, t, e):
    ko = pr(t, e["exit"], 0.3)
    for j, (tl, txt) in enumerate(e["lines"]):
        if t < tl: continue
        k = eo(pr(t, tl, 0.3)); f = F("InterDisplay-Black", 84)
        spr, pad = text_sprite(txt, f, INK + (255,)); spr = with_alpha(blur_reveal(spr, k, 12), 1 - ko)
        layer.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(1380 + j * 110 - pad + 30 * (1 - k) - 60 * eio(ko))))

def draw_chip_big(layer, t, e):
    k = back(pr(t, e["t0"], 0.35), 1.8); ko = eo(pr(t, e["t1"] - 0.2, 0.2))
    pl = pill(e["icon"], e["text"], fs=46, h=96)
    pl = pl.resize((max(1, int(pl.width * min(1.2, k))), max(1, int(pl.height * min(1.2, k)))), Image.BICUBIC)
    layer.alpha_composite(with_alpha(pl, min(1, k) * (1 - ko)), (int(W / 2 - pl.width / 2), int(1520 - pl.height / 2)))

# legenda: frases curtas
KEY = {"esforço.", "verdade", "justo,", "particular,", "público.", "bomba,", "destino", "parar", "chamando,", "chamando.", "anda.", "injusto.", "afeganistão.", "hospital", "consegue", "esforce."}
phrases, cur = [], []
for j, w in enumerate(WORDS):
    cur.append(w)
    nxt = WORDS[j + 1] if j + 1 < len(WORDS) else None
    if w["text"][-1] in ".?!," or len(cur) >= 4 or (nxt and (nxt["start"] - w["end"] > 0.25 or nxt["rk"] != w["rk"] and nxt["blk"] != w["blk"])):
        phrases.append(cur); cur = []
if cur: phrases.append(cur)
CAPS = []
for k, ph in enumerate(phrases):
    te = phrases[k + 1][0]["start"] - 0.02 if k + 1 < len(phrases) else ph[-1]["end"] + 0.4
    ws = [(w["start"], w["end"], w["text"].strip(".,"), w["text"].lower() in KEY or (i == len(ph) - 1 and len(ph) >= 3)) for i, w in enumerate(ph)]
    CAPS.append((ph[0]["start"], min(te, ph[-1]["end"] + 0.6), ws))

def render(raw, t):
    frame = background(t)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    act = [e for e in EV if e["t0"] <= t < e["t1"]]
    fl, (fcx, fcy) = frame_layer(cam_big(raw), t)
    dx, dy = shake(t)
    dy += 7 * math.sin(t * 1.7); dx += 4 * math.sin(t * 1.1)
    frame.alpha_composite(fl, (int(fcx - fl.width / 2 + dx), int(fcy - fl.height / 2 + dy)))
    # barra de progresso
    d = ImageDraw.Draw(frame); d.rectangle([0, 0, W * min(1, t / TOTAL), 10], fill=GOLD + (255,))
    for e in act:
        k = e["kind"]
        if k == "lanes": draw_lanes(ui, t, e)
        elif k == "quote": frame = draw_quote(frame, ui, t, e)
        elif k == "statement": frame = draw_statement(frame, ui, t, e)
        elif k == "duo": draw_duo(ui, t, e)
        elif k == "chip_big": draw_chip_big(ui, t, e)
        elif k == "lower3": draw_lower3(ui, t, e)
        elif k == "hook": draw_hook(ui, t, e)
        elif k == "tag": fx.section_tag(ui, e["text"], t, e["t0"], e["t1"], 60, 120, PAL, size=34)
    for e in act:   # títulos por cima dos painéis
        if e["kind"] == "kinetic":
            if e.get("dark"):
                kd = eo(pr(t, e["t0"], 0.3)) * (1 - pr(t, e["exit"], 0.3))
                ImageDraw.Draw(ui).rounded_rectangle(PANEL, radius=40, fill=(8, 9, 14, int(200 * kd)))
            fx.kinetic_title(ui, e["kicker"], e["title"], t, e["t0"], W / 2, e["y"], PAL, size=e["size"], exit_t=e["exit"], color=GOLD, kicker_scale=0.3)
        elif e["kind"] == "hero": draw_hero(ui, t, e)
        elif e["kind"] == "cta": draw_cta(ui, t, e)
    frame.alpha_composite(ui)
    if t < T_SPEECH + 0.3:
        cap = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        for s0, s1, ws in CAPS:
            if s0 - 0.05 <= t < s1 + 0.15: fx.caption2(cap, ws, t, W / 2, 150, PAL, size_small=50, size_big=72, maxw=960, t_end=s1)
        frame.alpha_composite(cap, (0, 1080))
    return frame

# ------------------------------------------------------------------ modos
mode = sys.argv[1]
RAW = TILE["s"] * TILE["s"] * 3
if mode == "frames":
    os.makedirs(f"{E}/prev", exist_ok=True)
    for ts in sys.argv[2:]:
        t = float(ts); fi = min(int(t * FPS), int(TOTAL * FPS) - 1)
        b = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mkv", "-vf", f"select=eq(n\\,{fi})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        render(b[:RAW], t).convert("RGB").save(f"{E}/prev/p_{t:06.2f}.jpg", quality=85)
    sys.exit()
if mode == "render":
    k, n = int(sys.argv[2]), int(sys.argv[3]); NF = int(round(TOTAL * FPS)); per = math.ceil(NF / n); f0, f1 = k * per, min(NF, (k + 1) * per)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mkv", "-vf", f"select=gte(n\\,{f0})", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", f"{WK}/part{k}.mp4"], stdin=subprocess.PIPE)
    last = bytes(RAW)
    for fi in range(f0, f1):
        b = dec.stdout.read(RAW)
        if len(b) == RAW: last = b
        enc.stdin.write(render(last, fi / FPS).convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); dec.terminate(); print("part", k, "ok", f1 - f0, flush=True); sys.exit()
if mode == "events":
    print("TOTAL", round(TOTAL, 2), "fala", round(T_SPEECH, 2))
    for b, (a, z) in BLK.items(): print(f"  {b:12s} {a:6.2f} – {z:6.2f}")
    for e in EV: print(f"{e['t0']:6.2f} {e['t1']:6.2f} {e['kind']}")
    sys.exit()
if mode == "audio":
    SR_ = 48000; N = int(TOTAL * SR_) + SR_
    r_ = np.random.default_rng(5)
    def tt(n): return np.arange(n) / SR_
    def env(n, a=0.005, dcy=8.0):
        t_ = tt(n); return np.minimum(1, t_ / a) * np.exp(-t_ * dcy)
    def lp(x, fc):   # passa-baixas de 1 polo
        a = math.exp(-2 * math.pi * fc / SR_); y = np.empty_like(x); acc = 0.0
        for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
        return y
    def noise(n): return r_.standard_normal(n)
    def hp(x):  return x - np.convolve(x, np.ones(8) / 8, "same")
    def put(buf, sig, at, g=1.0):
        i = int(at * SR_)
        if i < 0: sig = sig[-i:]; i = 0
        if i >= len(buf): return
        sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig * g
    # ---- trilha (100 bpm, Am F C G)
    BPM = 100; beat = 60 / BPM; bar = 4 * beat
    CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); clap = np.zeros(N); hat = np.zeros(N)
    t_brk0, t_brk1 = BLK["reconhecer"][0] - 0.2, BLK["parar"][0] - 0.1
    t_drop = t_lev; nb = int(TOTAL / bar) + 2
    kk = np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tt(int(0.4 * SR_)) * 30)) / SR_) * env(int(0.4 * SR_), 0.002, 9)
    cl_ = hp(noise(int(0.18 * SR_))) * env(int(0.18 * SR_), 0.001, 22)
    hh = hp(hp(noise(int(0.05 * SR_)))) * env(int(0.05 * SR_), 0.001, 60)
    for b in range(nb):
        t0 = b * bar; ch = CH[b % 4]
        n = int(bar * SR_) + int(0.6 * SR_); t_ = tt(n)
        sig = sum(np.sin(2 * np.pi * hz(m + 12) * t_) + 0.5 * np.sin(2 * np.pi * hz(m + 12) * 1.003 * t_) + 0.3 * np.sin(2 * np.pi * hz(m) * t_) for m in ch)
        put(pad, sig * np.minimum(1, t_ / 0.25) * np.exp(-np.maximum(0, t_ - bar) * 6) * 0.18, t0)
        for s in range(8):   # arpejo em colcheias
            m = ch[[0, 1, 2, 1, 0, 2, 1, 2][s]] + 24; nn = int(0.4 * SR_)
            put(arp, (np.sin(2 * np.pi * hz(m) * tt(nn)) + 0.25 * np.sin(4 * np.pi * hz(m) * tt(nn))) * env(nn, 0.003, 9) * 0.22, t0 + s * beat / 2)
        for q in range(4):
            tb = t0 + q * beat; brk = t_brk0 <= tb < t_brk1; drop = tb >= t_drop
            nn = int(beat * 0.9 * SR_); put(bass, np.tanh(2 * np.sin(2 * np.pi * hz(ch[0] - 12) * tt(nn))) * env(nn, 0.01, 3) * (0.0 if brk else 0.35), tb)
            if brk: continue
            if q in (0, 2) or drop: put(kick, kk, tb, 1.0)
            if q in (1, 3): put(clap, cl_, tb, 0.35)
            for h_ in (0, 0.5): put(hat, hh, tb + h_ * beat, 0.18 if h_ else 0.12)
    music = pad + arp + bass + kick * 0.9 + clap + hat
    music[: int(0.02 * SR_)] *= np.linspace(0, 1, int(0.02 * SR_))
    fo = int((TOTAL - 1.2) * SR_); music[fo:] *= np.linspace(1, 0, len(music) - fo)
    music /= np.abs(music).max() + 1e-9
    # ducking pela voz
    v, _ = sf.read(f"{WK}/voice.wav", dtype="float32"); v = v[:N]; vm = np.abs(v).mean(1)
    hop = int(0.05 * SR_); e_ = np.array([vm[i:i + hop].mean() for i in range(0, len(vm), hop)])
    act_ = (e_ > 0.02).astype(float); act_ = np.convolve(act_, np.ones(6) / 6, "same")
    duck = np.interp(np.arange(N), np.arange(len(act_)) * hop, act_, right=0)
    gm = 10 ** (-15 / 20) * (1 - 0.62 * duck)
    gm *= np.where((np.arange(N) / SR_ >= t_brk0) & (np.arange(N) / SR_ < t_brk1), 0.8, 1.0)
    gm *= np.where(np.arange(N) / SR_ >= T_SPEECH, 1.6, 1.0)
    mus = music * gm
    # ---- efeitos sonoros
    sfx = np.zeros(N)
    def whoosh(d=0.4):
        n = int(d * SR_); x = noise(n); y = np.zeros(n); seg = 12
        for k_ in range(seg):
            a, b = k_ * n // seg, (k_ + 1) * n // seg; y[a:b] = lp(x[a:b], 400 + 4000 * (k_ / seg) ** 1.5)
        return y * np.sin(np.linspace(0, np.pi, n)) ** 2 / (np.abs(y).max() + 1e-9)
    def pop(f=600):
        n = int(0.1 * SR_); t_ = tt(n); return np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-t_ * 60))) / SR_) * np.exp(-t_ * 40)
    def boom():
        n = int(1.2 * SR_); t_ = tt(n)
        return (np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t_ * 8)) / SR_) * np.exp(-t_ * 3) + 0.4 * lp(noise(n), 900) * np.exp(-t_ * 10))
    def riser(d=1.6):
        n = int(d * SR_); t_ = tt(n); x = noise(n); y = np.zeros(n); seg = 24
        for k_ in range(seg):
            a, b = k_ * n // seg, (k_ + 1) * n // seg; y[a:b] = lp(x[a:b], 300 + 7000 * (k_ / seg) ** 2)
        y /= np.abs(y).max() + 1e-9; return y * (t_ / d) ** 2 + 0.3 * np.sin(2 * np.pi * np.cumsum(200 + 800 * (t_ / d) ** 2) / SR_) * (t_ / d) ** 3
    chime_ = fx.chime(SR_)
    put(sfx, boom(), 0.0, 0.5)
    for b in BORDERS: put(sfx, whoosh(), b - 0.2, 0.35)
    for name, t0 in ACTIVE[:3]: put(sfx, pop(520), t0 + 0.05, 0.4)
    for L in CHIPS:
        for tc, _, _ in CHIPS[L]: put(sfx, pop(760), tc, 0.3)
    for e in EV:
        if e["kind"] == "kinetic": put(sfx, whoosh(0.35), e["t0"] - 0.1, 0.3); put(sfx, chime_, e["t0"] + 0.25, 0.22)
        if e["kind"] == "quote": put(sfx, pop(480), e["t0"], 0.35)
        if e["kind"] == "statement":
            for tl in e["line_t"]: put(sfx, pop(640), tl, 0.25)
            put(sfx, chime_, e["line_t"][-1] + 0.1, 0.28)
        if e["kind"] == "chip_big": put(sfx, pop(700), e["t0"], 0.4)
        if e["kind"] == "duo":
            for tr, *_ in e["rows"]: put(sfx, whoosh(0.3), tr - 0.15, 0.25); put(sfx, pop(560), tr + 0.1, 0.3)
        if e["kind"] == "cta": put(sfx, pop(880), e["t0"] + 0.4, 0.4); put(sfx, chime_, e["t0"] + 0.6, 0.3)
    xs = next(e for e in EV if e["kind"] == "quote")["x_at"]
    put(sfx, whoosh(0.2), xs - 0.05, 0.4); put(sfx, boom(), xs + 0.15, 0.55)
    put(sfx, riser(1.6), t_lev - 1.6, 0.4); put(sfx, boom(), t_lev, 0.75); put(sfx, chime_, t_lev + 0.3, 0.35)
    mix = v[:N] * 1.0 + (mus + sfx * 0.5)[:, None][: len(v[:N])]
    mix = mix[: int(TOTAL * SR_)]
    sf.write(f"{WK}/mix_raw.wav", mix.astype(np.float32), SR_)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1:LRA=8:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/mix_raw.wav", "-af",
                    f"loudnorm=I=-14:TP=-1:LRA=8:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true",
                    "-ar", "48000", f"{WK}/mix.wav"], check=True)
    print("audio ok", js["input_i"]); sys.exit()
if mode == "pack":
    n = int(sys.argv[2]); out = sys.argv[3]
    open(f"{WK}/parts.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(n)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/parts.txt", "-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("ok", out, round(os.path.getsize(out) / 2 ** 20, 1), "MiB"); sys.exit()
