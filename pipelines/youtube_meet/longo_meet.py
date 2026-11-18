"""Vídeo longo 16:9 para YouTube a partir de gravação de Meet (estudo/aula), estilo elegante (estilo16.py).
Corta conversas, orações e falas de terceiros (pelo plano), comprime pausas, insere vinhetas (abertura, capítulos,
versículos lidos por outros) e anima a fala com blocos de texto, versículos, palavras-chave em tela cheia e desenhos.
Câmera do autor: miniatura do Meet ampliada x4 (Real-ESRGAN, ../reels_meet/sr.py) ou recorte da câmera cheia.
Uso: longo_meet.py <plano.json> prep | events | frames t… | render k n | audio | srt | pack n saida.mp4
Tempos no plano: "w:SEG.I", "e:SEG.I", "b:bloco", "B:bloco", "f:texto@bloco", "F:texto@bloco", "end" (+/-seg)."""
import json, os, sys, math, re, subprocess, hashlib
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/user/editar_videos/pipelines/reels_meet"); sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import estilo16 as st
from fx import eo, eio, pr

PLAN = json.load(open(sys.argv[1])); MODE = sys.argv[2]
D = PLAN.get("proj", "/home/user/editar_videos/brutos/reel4"); E = f"{D}/edit"; SRC = f"{D}/dl/bruto.mp4"; WK = f"{E}/work_{PLAN['id']}"
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
os.makedirs(WK, exist_ok=True)
W, H, FPS, CS = 1920, 1080, 24, 624
TILE = PLAN.get("tile", dict(x0=963, x1=1280, y=273, s=156))
GAP, PRE, POST = PLAN.get("gap", 0.35), 0.05, 0.12
FIX = PLAN.get("fix", {})

# ------------------------------------------------------------------ corte
WSRC = {int(k): json.load(open(f"{E}/transcripts/seg{k}.json"))["words"] for k in PLAN["segs"]}
OFF = {int(k): float(v) for k, v in PLAN["segs"].items()}
FT = json.load(open(f"{E}/faces_tile.json"))
ranges = []
for sp in PLAN["spans"]:
    if sp[0] == "card": ranges.append(dict(card=True, dur=float(sp[1]), blk=sp[2])); continue
    seg, a, b, blk = sp[:4]; mode = sp[4] if len(sp) > 4 else "tile"
    ws = WSRC[seg]; cur = dict(seg=seg, a=a, blk=blk, mode=mode)
    for i in range(a + 1, b + 1):
        if ws[i]["start"] - ws[i - 1]["end"] > GAP: cur["b"] = i - 1; ranges.append(cur); cur = dict(seg=seg, a=i, blk=blk, mode=mode)
    cur["b"] = b; ranges.append(cur)
o = 0.0; WORDS = []; WD = {}; BLK = {}
for k, r in enumerate(ranges):
    if r.get("card"):
        r["nf"] = round(r["dur"] * FPS); r["d"] = r["nf"] / FPS; r["o"] = o; BLK[r["blk"]] = [o, o + r["d"]]; o += r["d"]; continue
    ws = WSRC[r["seg"]]; off = OFF[r["seg"]]; a, b = r["a"], r["b"]
    prev_end = ws[a - 1]["end"] if a > 0 else 0; nxt = ws[b + 1]["start"] if b + 1 < len(ws) else ws[b]["end"] + 1
    r["s"] = off + max(ws[a]["start"] - PRE, prev_end + 0.01); r["e"] = off + min(ws[b]["end"] + POST, nxt - 0.01)
    fc = [f[1] for f in FT if r["s"] - 4 <= f[0] <= r["e"] + 4]
    r["x"] = int(min(max((float(np.median(fc)) if fc else 1036.0) - TILE["s"] / 2, TILE["x0"]), TILE["x1"] - TILE["s"]))
    d = r["e"] - r["s"]; r["nf"] = max(1, round(d * FPS)); r["o"] = o; r["d"] = r["nf"] / FPS
    for i in range(a, b + 1):
        w = dict(seg=r["seg"], i=i, text=FIX.get(ws[i]["text"], ws[i]["text"]), start=off + ws[i]["start"] - r["s"] + o, end=off + ws[i]["end"] - r["s"] + o, blk=r["blk"], rk=k)
        WORDS.append(w); WD[(r["seg"], i)] = w
        BLK.setdefault(r["blk"], [w["start"], w["end"]]); BLK[r["blk"]][1] = w["end"]
    o += r["d"]
TOTAL = o; T_SPEECH = WORDS[-1]["end"]
CARDS = [(r["o"], r["o"] + r["d"]) for r in ranges if r.get("card")]
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
    raise KeyError(f"âncora não encontrada: {v}")
def resolve(x):
    if isinstance(x, dict): return {k: resolve(v) for k, v in x.items()}
    if isinstance(x, list): return [resolve(v) for v in x]
    return T(x)

# ------------------------------------------------------------------ PREP (câmera 624x624 a 24 fps + áudio, em paralelo)
def face_full(r):
    import cv2
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); pts = []
    for tt in np.linspace(r["s"], r["e"], 5):
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tt:.2f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(b) < 1280 * 720: continue
        fs = cas.detectMultiScale(np.frombuffer(b, np.uint8).reshape(720, 1280), 1.1, 6, minSize=(90, 90))
        if len(fs): x, y, w, h = max(fs, key=lambda f: f[2]); pts.append((x + w / 2, y + h / 2))
    return np.median(np.array(pts), 0) if pts else (430, 300)

def prep_range(k):
    r = ranges[k]; out = f"{WK}/cam_{k:04d}.mp4"; aud = f"{WK}/aud_{k:04d}.wav"
    if os.path.exists(out) and os.path.exists(aud): return k
    enc = ["-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if r.get("card"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={CS}x{CS}:r={FPS}", "-frames:v", str(r["nf"])] + enc + [out], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{r['d']:.6f}", "-c:a", "pcm_s16le", aud], check=True)
        return k
    d = r["d"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-vn",
                    "-af", f"aresample=48000,apad,atrim=0:{d:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, d - 0.03):.4f}:d=0.03",
                    "-c:a", "pcm_s16le", "-ac", "2", aud], check=True)
    if r["mode"] == "full":
        cx, cy = face_full(r); S = 600; x = int(min(max(cx - S / 2, 0), 1280 - S)); y = int(min(max(cy - S * 0.42, 0), 720 - S))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                        "-vf", f"crop={S}:{S}:{x}:{y},scale={CS}:{CS}:flags=lanczos,fps={FPS}", "-an"] + enc + [out], check=True)
        return k
    from sr import Upscaler
    up = Upscaler(MODELS, threads=1); s_ = TILE["s"]; RAW = s_ * s_ * 3
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                            "-vf", f"crop={s_}:{s_}:{r['x']}:{TILE['y']},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    e = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{CS}x{CS}", "-r", str(FPS), "-i", "-"] + enc + [out], stdin=subprocess.PIPE)
    last = None; lastk = None; n = 0
    while n < r["nf"]:
        b = dec.stdout.read(RAW)
        if len(b) < RAW: b = last if last is not None else bytes(RAW)
        if b != lastk: lastk = b; last_up = up(np.frombuffer(b, np.uint8).reshape(s_, s_, 3)).tobytes()
        last = b; e.stdin.write(last_up); n += 1
    e.stdin.close(); e.wait(); dec.terminate()
    return k

def fixmap():
    """Quadros em que a miniatura mostra outra pessoa → último quadro bom (só em trechos 'tile')."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WK}/cam.mp4", "-vf", "scale=24:24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    th = np.frombuffer(out, np.uint8).reshape(-1, 24, 24, 3).astype(np.float32)
    tile_mask = np.zeros(len(th), bool)
    for r in ranges:
        if not r.get("card") and r["mode"] == "tile": tile_mask[int(round(r["o"] * FPS)):int(round((r["o"] + r["d"]) * FPS))] = True
    ref = np.median(th[tile_mask], 0); dd = np.abs(th - ref).mean((1, 2, 3)); bad = (dd > 42) & tile_mask
    rep = {}; lastgood = None
    for i in range(len(th)):
        if not tile_mask[i]: lastgood = None; continue
        if bad[i]:
            if lastgood is not None: rep[i] = lastgood
        else: lastgood = i
    json.dump(rep, open(f"{WK}/fix.json", "w")); print("quadros trocados:", len(rep))

if MODE == "prep":
    from multiprocessing import Pool
    with Pool(4) as p:
        for i, k in enumerate(p.imap_unordered(prep_range, range(len(ranges)))):
            if i % 40 == 0: print("prep", i, "/", len(ranges), flush=True)
    open(f"{WK}/cams.txt", "w").write("".join(f"file 'cam_{k:04d}.mp4'\n" for k in range(len(ranges))))
    open(f"{WK}/auds.txt", "w").write("".join(f"file 'aud_{k:04d}.wav'\n" for k in range(len(ranges))))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/cams.txt", "-c", "copy", f"{WK}/cam.mp4"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/auds.txt", "-c", "copy", f"{WK}/aud_raw.wav"], check=True)
    chain = "highpass=f=90,afftdn=nf=-28:nr=10,acompressor=threshold=-22dB:ratio=3:attack=6:release=120:makeup=2"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/aud_raw.wav", "-af", chain + ",loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/aud_raw.wav", "-af", chain + "," + ln, "-ar", "48000", "-ac", "2", f"{WK}/voice.wav"], check=True)
    fixmap(); print("prep ok", round(TOTAL, 1), "s", len(ranges), "trechos"); sys.exit()

# ------------------------------------------------------------------ roteiro e layout
EV = [dict(resolve(e)) for e in PLAN["events"]]
for e in EV: e.setdefault("t0", 0.0)
FULLS = [(e["t0"], e["t1"]) for e in EV if st.STATE.get(e["k"]) in ("full", "card")]
for e in EV:   # bloco de coluna não entra por cima de uma tela cheia: espera ela sair
    if e["k"].startswith("c_"):
        for a_, b_ in FULLS:
            if a_ <= e["t0"] < b_ and b_ < e["t1"] - 1.0: e["t0"] = b_ - 0.1
CHAPS = sorted([(e["t0"], e["title"]) for e in EV if e["k"] == "chapter"])
EMPH = {norm(x) for x in PLAN.get("punch", [])}
PUNCH = [(w["start"], w["end"]) for w in WORDS if norm(w["text"]) in EMPH]
def state_at(t):
    if any(a <= t < b for a, b in CARDS): return "card"
    act = [e["k"] for e in EV if e["t0"] <= t < e["t1"]]
    for k in act:
        if st.STATE.get(k) == "card": return "card"
    if any(st.STATE.get(k) == "full" for k in act): return "full"
    if any(k.startswith("c_") for k in act): return "col"
    return "center"
CHG = []; prev = None
for i in range(int(TOTAL * 20) + 1):
    s_ = state_at(i / 20)
    if s_ != prev: CHG.append((i / 20, s_)); prev = s_
CHT = [c[0] for c in CHG]
def layout(t):
    import bisect
    j = max(0, bisect.bisect_right(CHT, t) - 1); t0, s1 = CHG[j]; s0 = CHG[j - 1][1] if j > 0 else s1
    k = eio(pr(t, t0, 0.7)); b0, b1 = st.BOX[s0], st.BOX[s1]
    a0 = 0.0 if s0 == "card" else 1.0; a1 = 0.0 if s1 == "card" else 1.0
    return tuple(b0[i] + (b1[i] - b0[i]) * k for i in range(4)), a0 + (a1 - a0) * k, s1
def zoom_at(t):
    k = next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1)
    r = ranges[k]; z = (1.10 if k % 2 == 0 else 1.26) * (1 + 0.04 * pr(t, r["o"], r["d"]))
    for s0, s1 in PUNCH:
        if s0 - 0.2 <= t <= s1 + 0.8: z *= 1 + 0.08 * eio(pr(t, s0 - 0.2, 0.3)) * (1 - eio(pr(t, s1 + 0.35, 0.45)))
    return z

def render(cam_img, t):
    out = st.background(t)
    box, alpha, s1 = layout(t)
    lay, pos = st.cam(cam_img, box, zoom_at(t), alpha)
    if lay is not None: out.alpha_composite(lay, pos)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    chap = next((c for tc, c in reversed(CHAPS) if t >= tc), "")
    st.topbar(ui, t, TOTAL, PLAN.get("tag", ""), chap, a=0 if s1 == "card" else 1)
    for e in EV:
        if e["t0"] - 0.05 <= t < e["t1"] + 0.05: st.BLOCKS[e["k"]](ui, t, e)
    out.alpha_composite(ui)
    return out.convert("RGB")

RAWC = CS * CS * 3
def fixes(): return {int(k): v for k, v in json.load(open(f"{WK}/fix.json")).items()}
if MODE == "events":
    print("TOTAL", round(TOTAL, 1), "s; fala até", round(T_SPEECH, 1))
    for b, (a, z) in BLK.items(): print(f"  {b:6s} {a:7.1f} – {z:7.1f}  " + " ".join(w["text"] for w in WORDS if w["blk"] == b)[:120])
    for e in EV: print(f"{e['t0']:7.1f} {e['t1']:7.1f} {e['k']}")
    sys.exit()
def read_cam_frames(f0):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WK}/cam.mp4", "-vf", f"select=gte(n\\,{f0})", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
if MODE == "frames":
    os.makedirs(f"{WK}/prev", exist_ok=True); FX = fixes()
    for ts in sys.argv[3:]:
        t = float(ts); fi = min(int(t * FPS), int(TOTAL * FPS) - 1); fi2 = FX.get(fi, fi)
        b = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{WK}/cam.mp4", "-vf", f"select=eq(n\\,{fi2})", "-fps_mode", "passthrough", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        render(Image.frombytes("RGB", (CS, CS), b[:RAWC]), t).save(f"{WK}/prev/p_{t:07.1f}.jpg", quality=86)
    sys.exit()
if MODE == "render":
    k, n = int(sys.argv[3]), int(sys.argv[4]); NF = int(round(TOTAL * FPS)); per = math.ceil(NF / n); f0, f1 = k * per, min(NF, (k + 1) * per)
    FX = fixes(); need = {v for i, v in FX.items() if f0 <= i < f1}; store = {}
    dec = read_cam_frames(f0)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", f"{WK}/part{k}.mp4"], stdin=subprocess.PIPE)
    # quadros de reposição anteriores ao início da parte
    pre = sorted(v for v in need if v < f0)
    if pre:
        d2 = read_cam_frames(pre[0]); i = pre[0]
        while i <= pre[-1]:
            b = d2.stdout.read(RAWC)
            if i in need: store[i] = b
            i += 1
        d2.terminate()
    last = bytes(RAWC)
    for fi in range(f0, f1):
        b = dec.stdout.read(RAWC)
        if len(b) == RAWC: last = b
        if fi in need: store[fi] = last
        cur = store.get(FX[fi], last) if fi in FX else last
        enc.stdin.write(render(Image.frombytes("RGB", (CS, CS), cur), fi / FPS).tobytes())
        if (fi - f0) % 2400 == 0: print("part", k, fi - f0, "/", f1 - f0, flush=True)
    enc.stdin.close(); enc.wait(); dec.terminate(); print("part", k, "ok", flush=True); sys.exit()

# ------------------------------------------------------------------ áudio: voz + trilha (piano/pad) com ducking + SFX
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
    PROG = [chord(c) for c in M.get("prog", "C Am F G").split()]
    BPM = M.get("bpm", 76); beat = 60 / BPM; bar = 4 * beat
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    _pc = {}
    def piano(m):
        if m not in _pc:
            n = int(1.6 * SR_); t_ = tt(n); f = hz(m)
            _pc[m] = sum(a * np.sin(2 * np.pi * f * h * t_) * np.exp(-t_ * (2.2 + h * 1.4)) for h, a in ((1, 1), (2, .45), (3, .22), (4, .1))) * np.minimum(1, t_ / 0.004)
        return _pc[m]
    pad = np.zeros(N); pno = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); shk = np.zeros(N)
    kk = np.sin(2 * np.pi * np.cumsum(48 + 60 * np.exp(-tt(int(.35 * SR_)) * 25)) / SR_) * np.exp(-tt(int(.35 * SR_)) * 10)
    sh = filt(rng.standard_normal(int(.06 * SR_)), 5000, "high") * np.exp(-tt(int(.06 * SR_)) * 70)
    quiet = [(a, b) for a, b in CARDS]
    for b in range(int(TOTAL / bar) + 2):
        t0 = b * bar; ch = PROG[b % len(PROG)]; n = int((bar + 1.5) * SR_); t_ = tt(n)
        sig = sum(np.sin(2 * np.pi * hz(m + 12) * t_) + 0.4 * np.sin(2 * np.pi * hz(m + 12) * 1.004 * t_) + 0.25 * np.sin(2 * np.pi * hz(m + 24) * 0.998 * t_) for m in ch)
        put(pad, sig * np.minimum(1, t_ / 0.8) * np.exp(-np.maximum(0, t_ - bar) * 3) * 0.10, t0)
        sparse = (b // 16) % 3 == 2
        pat = [0, 2, 1, 2, 0, 2, 1, 2] if not sparse else [0, None, 2, None, 1, None, None, None]
        for s_, ix in enumerate(pat):
            if ix is not None: put(pno, piano(ch[ix] + 24) * (0.20 if s_ % 2 == 0 else 0.13), t0 + s_ * beat / 2)
        for q in range(4):
            tb = t0 + q * beat
            if q in (0, 2): put(bass, np.sin(2 * np.pi * hz(ch[0] - 12) * tt(int(beat * 1.8 * SR_))) * np.exp(-tt(int(beat * 1.8 * SR_)) * 1.6) * 0.22, tb)
            if sparse: continue
            if q in (0, 2): put(kick, kk, tb, 0.45)
            put(shk, sh, tb, 0.08); put(shk, sh, tb + beat / 2, 0.05)
    music = pad + pno + bass + kick + shk; music /= np.abs(music).max() + 1e-9
    fo = int((TOTAL - 2.5) * SR_); music[fo:] *= np.linspace(1, 0, len(music) - fo)
    v, _ = sf.read(f"{WK}/voice.wav", dtype="float32"); v = v[:N]; vm = np.abs(v).mean(1)
    hop = int(0.05 * SR_); e_ = np.add.reduceat(vm, np.arange(0, len(vm), hop)) / hop
    act_ = np.convolve((e_ > 0.02).astype(float), np.ones(10) / 10, "same")
    duck = np.interp(np.arange(N), np.arange(len(act_)) * hop, act_, right=0)
    tN = np.arange(N) / SR_
    card_boost = np.zeros(N)
    for a, b in CARDS: card_boost[int(a * SR_):int(b * SR_)] = 1
    card_boost = np.convolve(card_boost, np.ones(SR_ // 2) / (SR_ // 2), "same")
    gm = 10 ** (-17 / 20) * (1 - 0.55 * duck) * (1 + 1.2 * card_boost)
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
        n = int(d * SR_); t_ = tt(n); return sum(a * np.sin(2 * np.pi * f * h * t_) * np.exp(-t_ * (2 + h)) for h, a in ((1, 1), (2.76, .35), (5.4, .12)))
    for e in EV:
        k = e["k"]
        if k in ("chapter", "intro"): put(sfx, whoosh(0.7), e["t0"] - 0.3, 0.25); put(sfx, bell(523, 2.2), e["t0"] + 0.2, 0.16)
        elif k in ("f_word", "f_verse"): put(sfx, whoosh(0.5), e["t0"] - 0.2, 0.18); put(sfx, bell(784 if k == "f_word" else 660, 1.6), e["t0"] + 0.15, 0.10)
        elif k.startswith("c_"): put(sfx, whoosh(0.4), e["t0"] - 0.15, 0.10)
        if k == "c_list":
            for it in e["items"]: put(sfx, tick(), it[0], 0.08)
        if k in ("c_flow",):
            for ti, _ in e["steps"]: put(sfx, tick(1500), ti, 0.08)
        if k == "c_counter":
            for ti, *_ in e["rows"]: put(sfx, tick(1300), ti, 0.10)
    mix = v[:N] + (mus + sfx)[:, None][: len(v[:N])]; mix = mix[: int(TOTAL * SR_)]
    sf.write(f"{WK}/mix_raw.wav", mix.astype(np.float32), SR_)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/mix_raw.wav", "-af",
                    f"loudnorm=I=-14:TP=-1:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true",
                    "-ar", "48000", f"{WK}/mix.wav"], check=True)
    print("audio ok"); sys.exit()
if MODE == "srt":
    out = sys.argv[3]; cues = []; cur = []
    for j, w in enumerate(WORDS):
        cur.append(w); nxt = WORDS[j + 1] if j + 1 < len(WORDS) else None
        if w["text"][-1] in ".?!" and len(" ".join(x["text"] for x in cur)) > 20 or len(" ".join(x["text"] for x in cur)) > 70 or (nxt and nxt["start"] - w["end"] > 0.8) or not nxt:
            cues.append(cur); cur = []
    def ts(t): h, r_ = divmod(t, 3600); m, s = divmod(r_, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    with open(out, "w") as f:
        for n, c in enumerate(cues, 1):
            txt = " ".join(x["text"] for x in c)
            if len(txt) > 42:
                ws = txt.split(); bk = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(txt) / 2)); txt = " ".join(ws[:bk]) + "\n" + " ".join(ws[bk:])
            end = min(c[-1]["end"] + 0.3, cues[n][0]["start"] - 0.02) if n < len(cues) else c[-1]["end"] + 0.3
            f.write(f"{n}\n{ts(c[0]['start'])} --> {ts(end)}\n{txt}\n\n")
    for tc, title in [(0, PLAN.get("cold_title", "Abertura"))] + CHAPS: print(f"{int(tc // 60)}:{int(tc % 60):02d} {title.replace("*", "")}")
    sys.exit()
if MODE == "pack":
    n = int(sys.argv[3]); out = sys.argv[4]
    open(f"{WK}/parts.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(n)))
    vk = int((380 * 8388.608 / TOTAL - 128) * 0.96)
    base = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/parts.txt"]
    vopt = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{vk}k", "-maxrate", f"{2 * vk}k", "-bufsize", f"{4 * vk}k", "-pix_fmt", "yuv420p", "-passlogfile", f"{WK}/pl"]
    subprocess.run(base + vopt + ["-pass", "1", "-an", "-f", "null", "/dev/null"], check=True)
    subprocess.run(base + ["-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a"] + vopt + ["-pass", "2", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", out], check=True)
    print("ok", out, round(os.path.getsize(out) / 2 ** 20, 1), "MiB", vk, "kbps"); sys.exit()
