"""Reel 9:16 elegante a partir de gravação de Meet em que a câmera do autor é uma miniatura.
Rosto em moldura (super-resolução x4, sr.py), fundo grafite com grão, tipografia editorial (estilo.py),
blocos gráficos sincronizados às palavras, zooms por corte/ênfase, trilha sintetizada (piano/pad) com ducking e SFX discretos.
O QUADRO 0 JÁ É A CAPA (bloco "cover" totalmente desenhado em t=0).
Uso: reel_meet.py <plano.json> prep | events | frames t… | render k n | audio | pack n saida.mp4
Plano: ver planos/exemplo.json e README.md. Tempos: "w:SEG.I" início da palavra, "e:SEG.I" fim, "b:bloco"/"B:bloco",
"f:texto@bloco" (início da 1ª palavra do bloco que começa com texto), "F:texto@bloco" (fim), "end" (fim da fala); aceita +/-seg."""
import json, os, sys, math, re, subprocess, hashlib
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import fx, estilo as st
from fx import eo, eio, pr

PLAN = json.load(open(sys.argv[1])); MODE = sys.argv[2]
D = PLAN.get("proj", "/home/user/editar_videos/brutos/reel4"); E = f"{D}/edit"; SRC = PLAN.get("src", f"{D}/dl/bruto.mp4"); WK = f"{E}/work_{PLAN['id']}"
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
os.makedirs(WK, exist_ok=True)
W, H, FPS = 1080, 1920, 30
TILE = PLAN.get("tile", dict(x0=963, x1=1280, y=273, s=156))
GAP, PRE, POST, TAIL = PLAN.get("gap", 0.32), 0.05, 0.12, PLAN.get("tail", 3.2)
FIX = PLAN.get("fix", {})

# ------------------------------------------------------------------ corte
WSRC = {int(k): json.load(open(f"{E}/transcripts/seg{k}.json"))["words"] for k in PLAN["segs"]}
OFF = {int(k): float(v) for k, v in PLAN["segs"].items()}
FT = json.load(open(f"{E}/faces_tile.json"))
ranges = []
for seg, a, b, blk in PLAN["spans"]:
    ws = WSRC[seg]; cur = dict(seg=seg, a=a, blk=blk)
    for i in range(a + 1, b + 1):
        if ws[i]["start"] - ws[i - 1]["end"] > GAP: cur["b"] = i - 1; ranges.append(cur); cur = dict(seg=seg, a=i, blk=blk)
    cur["b"] = b; ranges.append(cur)
o = 0.0; WORDS = []; WD = {}
for k, r in enumerate(ranges):
    ws = WSRC[r["seg"]]; off = OFF[r["seg"]]; a, b = r["a"], r["b"]
    prev_end = ws[a - 1]["end"] if a > 0 else 0; nxt = ws[b + 1]["start"] if b + 1 < len(ws) else ws[b]["end"] + 1
    r["s"] = off + max(ws[a]["start"] - PRE, prev_end + 0.01); r["e"] = off + min(ws[b]["end"] + POST, nxt - 0.01)
    r["tail"] = TAIL if k == len(ranges) - 1 else 0
    fc = [f[1] for f in FT if r["s"] - 3 <= f[0] <= r["e"] + 3]
    cx = float(np.median(fc)) if fc else 1036.0
    r["x"] = int(min(max(cx - TILE["s"] / 2, TILE["x0"]), TILE["x1"] - TILE["s"]))
    d = r["e"] - r["s"] + r["tail"]; r["nf"] = max(1, round(d * FPS)); r["o"] = o; r["d"] = r["nf"] / FPS
    for i in range(a, b + 1):
        txt = FIX.get(ws[i]["text"], ws[i]["text"])
        w = dict(seg=r["seg"], i=i, text=txt, start=off + ws[i]["start"] - r["s"] + o, end=off + ws[i]["end"] - r["s"] + o, blk=r["blk"], rk=k)
        WORDS.append(w); WD[(r["seg"], i)] = w
    o += r["d"]
TOTAL = o; T_SPEECH = WORDS[-1]["end"]
BLK = {}
for w in WORDS: BLK.setdefault(w["blk"], [w["start"], w["end"]]); BLK[w["blk"]][1] = w["end"]
BORDERS = [ranges[k]["o"] for k in range(1, len(ranges)) if ranges[k]["blk"] != ranges[k - 1]["blk"]]
def norm(s): return s.lower().strip(".,?!:;“”\"")

SPEC = re.compile(r"^(w|e|b|B|f|F):(.+?)([+-]\d+(?:\.\d+)?)?$|^end([+-]\d+(?:\.\d+)?)?$")
def T(v):
    if not isinstance(v, str): return v
    m = SPEC.match(v)
    if not m: return v
    if v.startswith("end"): return T_SPEECH + float(m.group(4) or 0)
    c, arg, offs = m.group(1), m.group(2), float(m.group(3) or 0)
    if c in "we":
        seg, i = arg.split("."); w = WD[(int(seg), int(i))]; return (w["start"] if c == "w" else w["end"]) + offs
    if c in "bB": return BLK[arg][0 if c == "b" else 1] + offs
    txt, blk = arg.split("@")
    for w in WORDS:
        if w["blk"] == blk and norm(w["text"]).startswith(norm(txt)): return (w["start"] if c == "f" else w["end"]) + offs
    raise KeyError(v)
def resolve(x):
    if isinstance(x, dict): return {k: resolve(v) for k, v in x.items()}
    if isinstance(x, list): return [resolve(v) for v in x]
    return T(x)

# ------------------------------------------------------------------ PREP
def fixmap():
    """O Meet troca a miniatura para quem faz barulho: quadros que não são o autor são trocados pelo último bom."""
    s_ = TILE["s"]; out = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mkv", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(out, np.uint8).reshape(-1, s_, s_, 3)
    th = fr.reshape(-1, 12, 13, 12, 13, 3).mean((2, 4)); dd = np.abs(th - np.median(th, 0)).mean((1, 2, 3)); bad = dd > 40
    good = np.where(~bad)[0]; idx = []; raws = []
    for i in np.where(bad)[0]:
        prv = good[good < i]; j = prv[-1] if len(prv) else good[good > i][0]; idx.append(int(i)); raws.append(fr[j])
    np.savez(f"{WK}/fix.npz", idx=np.array(idx, np.int64), raw=np.array(raws, np.uint8).reshape(-1, s_, s_, 3))
    runs = []; i = 0
    while i < len(bad):
        if bad[i]:
            j = i
            while j < len(bad) and bad[j]: j += 1
            runs.append(f"{i / FPS:.1f}s+{(j - i) / FPS:.1f}"); i = j
        else: i += 1
    print("quadros trocados:", len(idx), runs)

if MODE == "prep":
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
    if PLAN.get("fixmap", True): fixmap()
    print(PLAN["id"], "prep ok", round(TOTAL, 2), "s,", len(ranges), "cortes"); sys.exit()

# ------------------------------------------------------------------ roteiro
EV = []
for e in PLAN["events"]:
    e = resolve(e); e.setdefault("t0", 0.0); EV.append(e)
if "cta" in PLAN: EV.append(dict(k="cta", t0=T_SPEECH + 0.3, t1=TOTAL + 1, **PLAN["cta"]))
COVER_END = next((e["t1"] for e in EV if e["k"] == "cover"), 0)
NOCAP = [(e["t0"], e["t1"]) for e in EV if e["k"] in ("cover", "hero", "cta")]
EMPH = {norm(x) for x in PLAN.get("punch", [])}; KEY = {norm(x) for x in PLAN.get("key", [])}
PUNCH = [(w["start"], w["end"]) for w in WORDS if norm(w["text"]) in EMPH]

phrases, cur = [], []
for j, w in enumerate(WORDS):
    cur.append(w); nxt = WORDS[j + 1] if j + 1 < len(WORDS) else None
    chars = sum(len(x["text"]) + 1 for x in cur)
    if w["text"][-1] in ".?!" or (w["text"][-1] in ",:" and len(cur) >= 3) or chars > 30 or (nxt and nxt["start"] - w["end"] > 0.3):
        phrases.append(cur); cur = []
if cur: phrases.append(cur)
CAPS = []
for k, ph in enumerate(phrases):
    te = phrases[k + 1][0]["start"] - 0.02 if k + 1 < len(phrases) else ph[-1]["end"] + 0.4
    CAPS.append((ph[0]["start"], min(te, ph[-1]["end"] + 0.7), [(w["start"], w["end"], w["text"].rstrip(","), norm(w["text"]) in KEY) for w in ph]))

def zoom_at(t):
    k = next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1)
    r = ranges[k]; z = (1.16 if k % 2 == 0 else 1.34) * (1 + 0.04 * pr(t, r["o"], r["d"]))
    for s0, s1 in PUNCH:
        if s0 - 0.2 <= t <= s1 + 0.8: z *= 1 + 0.10 * eio(pr(t, s0 - 0.2, 0.3)) * (1 - eio(pr(t, s1 + 0.35, 0.45)))
    return z

_sr = None; _cache = {}
def cam_big(raw):
    global _sr
    if not PLAN.get("sr", True):   # câmera boa (celular): sem super-resolução, só redimensiona
        return Image.frombytes("RGB", (TILE["s"], TILE["s"]), raw).resize((TILE.get("out", 900),) * 2, Image.LANCZOS)
    key = hashlib.md5(raw).hexdigest()
    if key not in _cache:
        if _sr is None:
            from sr import Upscaler; _sr = Upscaler(MODELS, threads=int(os.environ.get("SR_THREADS", "1")))
        _cache.clear(); _cache[key] = Image.fromarray(_sr(np.frombuffer(raw, np.uint8).reshape(TILE["s"], TILE["s"], 3)))
    return _cache[key]

PIP = PLAN.get("layout", "frame") == "pip"
PIP_BOX = (770, 170, 1010, 410)     # seu quadro pequeno no canto (layout pip)
ZS = 1.12                           # escala da zona gráfica no layout pip
if PIP: st.FS = 1.15
def render(raw, t):
    out = st.background(t)
    pulse = 0
    for b in BORDERS:
        if b - 0.1 <= t < b + 0.35: pulse = max(pulse, math.sin(math.pi * pr(t, b - 0.1, 0.45)))
    fl, (fcx, fcy) = st.frame(cam_big(raw), t, zoom_at(t), pulse, box=PIP_BOX if PIP else None)
    out.alpha_composite(fl, (int(fcx - fl.width / 2 + 2 * math.sin(t * 0.9)), int(fcy - fl.height / 2 + 4 * math.sin(t * 0.7))))
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    st.topbar(ui, t, TOTAL, PLAN.get("tag", ""), "" if PIP else PLAN.get("name", ""))
    zl = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if PIP else ui
    for e in EV:
        if e["k"] == "cover" or (e["t0"] - 0.05 <= t < e["t1"] + 0.05): st.BLOCKS[e["k"]](zl, t, e)
    if PIP:   # zona gráfica ampliada (ZS) e centralizada; a borda de baixo some antes do rodapé do Instagram
        zc = zl.crop((0, 1250, W, H)); zc = zc.resize((int(W * ZS), int(zc.height * ZS)), Image.LANCZOS)
        ui.alpha_composite(zc, (int((W - zc.width) / 2), int(600 - 80 * ZS)))
    if not any(a <= t < b for a, b in NOCAP) and t < T_SPEECH + 0.3:
        cur = None
        for s0, s1, ws in CAPS:
            if s0 - 0.15 <= t < s1 + 0.05: cur = (s0, s1, ws)
        if cur: st.caption(ui, cur[2], t, cy=1430 if PIP else 1232, size=52, t_end=cur[1])
    out.alpha_composite(ui)
    return out

RAW = TILE["s"] * TILE["s"] * 3
def fixes():
    if not os.path.exists(f"{WK}/fix.npz"): return {}
    FX_ = np.load(f"{WK}/fix.npz"); return {int(i): r.tobytes() for i, r in zip(FX_["idx"], FX_["raw"])}
if MODE == "events":
    print(PLAN["id"], "TOTAL", round(TOTAL, 2), "fala", round(T_SPEECH, 2), "cortes", len(ranges))
    for b, (a, z) in BLK.items(): print(f"  {b:12s} {a:6.2f} – {z:6.2f}  " + " ".join(w["text"] for w in WORDS if w["blk"] == b)[:110])
    for e in EV: print(f"{e['t0']:6.2f} {e['t1']:6.2f} {e['k']}")
    sys.exit()
if MODE == "frames":
    os.makedirs(f"{WK}/prev", exist_ok=True); FIXR = fixes()
    for ts in sys.argv[3:]:
        t = float(ts); fi = min(int(t * FPS), int(TOTAL * FPS) - 1)
        b = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mkv", "-vf", f"select=eq(n\\,{fi})", "-fps_mode", "passthrough", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        render(FIXR.get(fi, b[:RAW]), t).convert("RGB").save(f"{WK}/prev/p_{t:06.2f}.jpg", quality=88)
    sys.exit()
if MODE == "render":
    k, n = int(sys.argv[3]), int(sys.argv[4]); NF = int(round(TOTAL * FPS)); per = math.ceil(NF / n); f0, f1 = k * per, min(NF, (k + 1) * per)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WK}/base.mkv", "-vf", f"select=gte(n\\,{f0})", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", f"{WK}/part{k}.mp4"], stdin=subprocess.PIPE)
    last = bytes(RAW); FIXR = fixes()
    for fi in range(f0, f1):
        b = dec.stdout.read(RAW)
        if len(b) == RAW: last = b
        enc.stdin.write(render(FIXR.get(fi, last), fi / FPS).convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); dec.terminate(); print(PLAN["id"], "part", k, "ok", f1 - f0, flush=True); sys.exit()

# ------------------------------------------------------------------ áudio
if MODE == "audio":
    from scipy.signal import butter, sosfilt
    SR_ = 48000; N = int(TOTAL * SR_) + SR_; rng = np.random.default_rng(5); M = PLAN.get("music", {})
    def tt(n): return np.arange(n) / SR_
    def put(buf, sig, at, g=1.0):
        i = int(at * SR_)
        if i < 0: sig = sig[-i:]; i = 0
        if i >= len(buf): return
        sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig * g
    def filt(x, f, kind="low"): return sosfilt(butter(2, f, kind, fs=SR_, output="sos"), x)
    NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    def chord(name):
        root = NOTE[name[0]] + (1 if "#" in name else -1 if "b" in name[1:2] else 0); minor = "m" in name[1:]
        return [48 + root, 48 + root + (3 if minor else 4), 48 + root + 7]
    PROG = [chord(c) for c in M.get("prog", "Am F C G").split()]
    BPM = M.get("bpm", 80); beat = 60 / BPM; bar = 4 * beat
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    def piano(f, d=1.6):
        n = int(d * SR_); t_ = tt(n); s = sum(a * np.sin(2 * np.pi * f * h * t_) * np.exp(-t_ * (2.2 + h * 1.4)) for h, a in ((1, 1), (2, .45), (3, .22), (4, .1)))
        return s * np.minimum(1, t_ / 0.004)
    brk0, brk1 = (T(M["break"][0]), T(M["break"][1])) if "break" in M else (1e9, 1e9)
    swell = T(M["swell"]) if "swell" in M else T_SPEECH - 4
    pad = np.zeros(N); pno = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); shk = np.zeros(N)
    kk = np.sin(2 * np.pi * np.cumsum(48 + 60 * np.exp(-tt(int(.35 * SR_)) * 25)) / SR_) * np.exp(-tt(int(.35 * SR_)) * 10)
    sh = filt(rng.standard_normal(int(.06 * SR_)), 5000, "high") * np.exp(-tt(int(.06 * SR_)) * 70)
    for b in range(int(TOTAL / bar) + 2):
        t0 = b * bar; ch = PROG[b % len(PROG)]; n = int((bar + 1.5) * SR_); t_ = tt(n)
        sig = sum(np.sin(2 * np.pi * hz(m + 12) * t_) + 0.4 * np.sin(2 * np.pi * hz(m + 12) * 1.004 * t_) + 0.25 * np.sin(2 * np.pi * hz(m + 24) * 0.998 * t_) for m in ch)
        envp = np.minimum(1, t_ / 0.8) * np.exp(-np.maximum(0, t_ - bar) * 3)
        lift = 1.6 if t0 >= swell else 1.0
        put(pad, sig * envp * 0.10 * lift, t0)
        pat = [0, 2, 1, 2, 0, 2, 1, 2] if t0 < brk0 or t0 >= brk1 else [0, None, 2, None, 1, None, None, None]
        for s_, ix in enumerate(pat):
            if ix is None: continue
            m = ch[ix] + 24 + (12 if s_ in (3, 7) and t0 >= swell else 0)
            put(pno, piano(hz(m)) * (0.20 if s_ % 2 == 0 else 0.13), t0 + s_ * beat / 2)
        for q in range(4):
            tb = t0 + q * beat; quiet = brk0 <= tb < brk1
            if q in (0, 2): put(bass, np.sin(2 * np.pi * hz(ch[0] - 12) * tt(int(beat * 1.8 * SR_))) * np.exp(-tt(int(beat * 1.8 * SR_)) * 1.6) * (0.10 if quiet else 0.28), tb)
            if quiet: continue
            if q in (0, 2): put(kick, kk, tb, 0.55)
            put(shk, sh, tb, 0.10); put(shk, sh, tb + beat / 2, 0.06)
    music = pad + pno + bass + kick + shk
    music[: int(0.6 * SR_)] *= np.linspace(0.4, 1, int(0.6 * SR_))
    fo = int((TOTAL - 1.5) * SR_); music[fo:] *= np.linspace(1, 0, len(music) - fo)
    music /= np.abs(music).max() + 1e-9
    v, _ = sf.read(f"{WK}/voice.wav", dtype="float32"); v = v[:N]; vm = np.abs(v).mean(1)
    hop = int(0.05 * SR_); e_ = np.array([vm[i:i + hop].mean() for i in range(0, len(vm), hop)])
    act_ = np.convolve((e_ > 0.02).astype(float), np.ones(8) / 8, "same")
    duck = np.interp(np.arange(N), np.arange(len(act_)) * hop, act_, right=0)
    tN = np.arange(N) / SR_
    gm = 10 ** (-14 / 20) * (1 - 0.6 * duck) * np.where(tN >= T_SPEECH, 1.5, 1.0)
    mus = music * gm
    sfx = np.zeros(N)
    def whoosh(d=0.5):
        n = int(d * SR_); x = rng.standard_normal(n); y = np.zeros(n); seg = 10
        for k_ in range(seg):
            a, b = k_ * n // seg, (k_ + 1) * n // seg; y[a:b] = filt(x[a:b], 300 + 2600 * (k_ / seg) ** 1.4)
        return y * np.sin(np.linspace(0, np.pi, n)) ** 2 / (np.abs(y).max() + 1e-9)
    def tick(f=1800):
        n = int(0.05 * SR_); t_ = tt(n); return np.sin(2 * np.pi * f * t_) * np.exp(-t_ * 90)
    def bell(f=880, d=1.6):
        n = int(d * SR_); t_ = tt(n)
        return sum(a * np.sin(2 * np.pi * f * h * t_) * np.exp(-t_ * (2 + h)) for h, a in ((1, 1), (2.76, .35), (5.4, .12)))
    def swell_snd(d=2.0):
        n = int(d * SR_); t_ = tt(n); x = filt(rng.standard_normal(n), 1800); return x / (np.abs(x).max() + 1e-9) * (t_ / d) ** 2
    for b in BORDERS: put(sfx, whoosh(), b - 0.25, 0.22)
    for e in EV:
        k = e["k"]
        if k in ("title", "statement", "versus", "counter", "flow", "dots", "lanes", "list", "verse"): put(sfx, whoosh(0.4), e["t0"] - 0.15, 0.16)
        if k == "verse": put(sfx, bell(660), e["t0"] + 0.2, 0.14)
        if k == "list":
            for it in e["items"]: put(sfx, tick(), it[0], 0.12)
            if e.get("strike") is not None: put(sfx, whoosh(0.3), e["strike"], 0.2)
        if k == "flow":
            for ti, _ in e["steps"]: put(sfx, tick(1500), ti, 0.12)
        if k == "counter":
            for ti, *_ in e["rows"]: put(sfx, tick(1300), ti, 0.14)
        if k == "statement":
            for _, tl in e["lines"]: put(sfx, tick(2000), tl, 0.08)
        if k == "title": put(sfx, bell(990, 1.2), e["t0"] + 0.2, 0.10)
        if k == "hero": put(sfx, swell_snd(), e["t0"] - 2.0, 0.22); put(sfx, bell(523, 2.4), e["t0"], 0.22); put(sfx, bell(784, 2.0), e["t0"] + 0.35, 0.14)
        if k == "cta": put(sfx, bell(1046, 1.4), e["t0"] + 0.1, 0.14)
    mix = v[:N] + (mus + sfx)[:, None][: len(v[:N])]
    mix = mix[: int(TOTAL * SR_)]
    sf.write(f"{WK}/mix_raw.wav", mix.astype(np.float32), SR_)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1:LRA=8:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/mix_raw.wav", "-af",
                    f"loudnorm=I=-14:TP=-1:LRA=8:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true",
                    "-ar", "48000", f"{WK}/mix.wav"], check=True)
    print(PLAN["id"], "audio ok"); sys.exit()
if MODE == "pack":
    n = int(sys.argv[3]); out = sys.argv[4]
    open(f"{WK}/parts.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(n)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/parts.txt", "-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("ok", out, round(os.path.getsize(out) / 2 ** 20, 1), "MiB"); sys.exit()
