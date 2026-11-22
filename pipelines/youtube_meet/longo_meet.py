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
D = PLAN.get("proj", "/home/user/editar_videos/brutos/reel4"); E = f"{D}/edit"; SRC = PLAN.get("src", f"{D}/dl/bruto.mp4"); WK = f"{E}/work_{PLAN['id']}"
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
os.makedirs(WK, exist_ok=True)
W, H, CS = 1920, 1080, 624; FPS = PLAN.get("fps", 24); SPEED = PLAN.get("speed", 1.0)
STAGE = PLAN.get("layout") == "stage"   # palco em tela cheia como base; gráficos por cima
TILE = PLAN.get("tile", dict(x0=963, x1=1280, y=273, s=156))
GAP, PRE, POST = PLAN.get("gap", 0.35), 0.05, 0.12
FIX = PLAN.get("fix", {})

# ------------------------------------------------------------------ corte
WSRC = {int(k): json.load(open(f"{E}/transcripts/" + PLAN.get("tfile", {}).get(k, f"seg{k}.json")))["words"] for k in PLAN["segs"]}
AUDIO_ONLY = PLAN.get("audio_only", False)
if AUDIO_ONLY: st.set_audio_only()
OFF = {int(k): float(v) for k, v in PLAN["segs"].items()}
FT = json.load(open(f"{E}/faces_tile.json")) if os.path.exists(f"{E}/faces_tile.json") else []
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

def rkey(r):
    return f"card_{r['blk']}_{r['nf']}" if r.get("card") else f"{r['seg']}_{r['a']}_{r['b']}_{r['mode']}_{r['x']}_{r['nf']}"
def tile_face(r, side="largest"):
    """Rosto dentro da miniatura (outra pessoa lendo, ou a Ester na mesma câmera)."""
    import cv2
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); pts = []
    for tt in np.linspace(r["s"], r["e"], 6):
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tt:.2f}", "-i", SRC, "-frames:v", "1", "-vf", "crop=318:178:962:272,scale=954:534", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(b) < 954 * 534: continue
        fs = cas.detectMultiScale(np.frombuffer(b, np.uint8).reshape(534, 954), 1.1, 5, minSize=(60, 60))
        if len(fs):
            x, y, w, h = (max(fs, key=lambda f: f[0]) if side == "right" else max(fs, key=lambda f: f[2])); pts.append((962 + (x + w / 2) / 3, 272 + (y + h / 2) / 3))
    return np.median(np.array(pts), 0) if pts else (1121, 360)

_seg = None
def stage_person(r):
    """Posição da pessoa no palco: x = maior blob da segmentação de pessoa (MediaPipe), y = rosto (Haar);
    mediana de 3 quadros do trecho. Retorna (cx, y_do_rosto)."""
    global _seg
    import cv2, mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    if _seg is None:
        _seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=f"{MODELS}/selfie_multiclass.tflite"), output_category_mask=True))
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); xs, ys = [], []
    for tt in np.linspace(r["s"] + 0.2, max(r["s"] + 0.3, r["e"] - 0.2), 3):
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tt:.2f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(b) < 1920 * 1080 * 3: continue
        im = np.frombuffer(b, np.uint8).reshape(1080, 1920, 3); sm = np.ascontiguousarray(cv2.resize(im, (960, 540)))
        m = (np.squeeze(_seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=sm)).category_mask.numpy_view()) > 0).astype(np.uint8)
        n, lab, st_, cen = cv2.connectedComponentsWithStats(m)
        if n > 1:
            i = 1 + int(np.argmax(st_[1:, 4]))
            if st_[i, 4] > 1500: xs.append(2 * cen[i, 0])
        fs = cas.detectMultiScale(cv2.cvtColor(im, cv2.COLOR_RGB2GRAY), 1.1, 6, minSize=(36, 36), maxSize=(140, 140))
        if len(fs) and xs:
            x, y, w, h = min(fs, key=lambda f: abs(f[0] + f[2] / 2 - xs[-1])); ys.append(y + h / 2)
    d0 = PLAN.get("stage_default", (960, 300))
    return (float(np.median(xs)) if xs else d0[0], float(np.median(ys)) if ys else d0[1])

def prep_range(k):
    r = ranges[k]; out = f"{WK}/cam_{rkey(r)}.mp4"; aud = f"{WK}/aud_{rkey(r)}.wav"
    if os.path.exists(out) and os.path.exists(aud): return k
    enc = ["-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if r.get("card") or AUDIO_ONLY or STAGE:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={CS}x{CS}:r={FPS}", "-frames:v", str(r["nf"])] + enc + [out], check=True)
    if r.get("card"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{r['d']:.6f}", "-c:a", "pcm_s16le", aud], check=True)
        return k
    d = r["d"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-vn",
                    "-af", f"aresample=48000,apad,atrim=0:{d:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, d - 0.03):.4f}:d=0.03",
                    "-c:a", "pcm_s16le", "-ac", "2", aud], check=True)
    if AUDIO_ONLY or STAGE: return k
    if r["mode"] == "stage":   # palco (câmera fixa larga): recorte quadrado acompanhando a pessoa (HOG) no trecho
        cx, cy = stage_person(r); S = PLAN.get("stage_crop", 720); H0 = PLAN.get("src_h", 1080); W0 = PLAN.get("src_w", 1920)
        x = int(min(max(cx - S / 2, 0), W0 - S)); y = int(min(max(cy - S * 0.27, 0), H0 - S))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                        "-vf", f"crop={S}:{S}:{x}:{y},scale={CS}:{CS}:flags=lanczos,unsharp=5:5:0.6,fps={FPS}", "-an"] + enc + [out], check=True)
        return k
    if r["mode"] == "full":
        cx, cy = face_full(r); S = 600; x = int(min(max(cx - S / 2, 0), 1280 - S)); y = int(min(max(cy - S * 0.42, 0), 720 - S))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                        "-vf", f"crop={S}:{S}:{x}:{y},scale={CS}:{CS}:flags=lanczos,fps={FPS}", "-an"] + enc + [out], check=True)
        return k
    from sr import Upscaler
    up = Upscaler(MODELS, threads=1); s_ = TILE["s"]; RAW = s_ * s_ * 3; cx_, cy_ = r["x"], TILE["y"]
    if r["mode"] in ("ester", "other"):    # quem lê aparece: posição fixa medida (mesma câmera) ou o rosto da miniatura
        fx_, fy_ = PLAN["fixed_face"][r["mode"]] if r["mode"] in PLAN.get("fixed_face", {}) else tile_face(r)
        cx_ = int(min(max(fx_ - s_ / 2, 962), 1280 - s_)); cy_ = int(min(max(fy_ - s_ * 0.45, 272), 449 - s_))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{r['s']:.3f}", "-t", f"{d + 0.2:.3f}", "-i", SRC, "-frames:v", str(r["nf"]),
                            "-vf", f"crop={s_}:{s_}:{cx_}:{cy_},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
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

def stage_track():
    """Posição da pessoa no palco ao longo da fonte (1 amostra a cada 2 s): x do centro e topo da cabeça, suavizados."""
    import cv2, mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    from scipy.ndimage import median_filter, gaussian_filter1d
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=f"{MODELS}/selfie_multiclass.tflite"), output_category_mask=True))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", "fps=0.5,scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    xs, ys = [], []
    while True:
        b = p.stdout.read(960 * 540 * 3)
        if len(b) < 960 * 540 * 3: break
        im = np.frombuffer(b, np.uint8).reshape(540, 960, 3)
        m = (np.squeeze(seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(im))).category_mask.numpy_view()) > 0).astype(np.uint8)
        n, lab, st_, cen = cv2.connectedComponentsWithStats(m)
        i = 1 + int(np.argmax(st_[1:, 4])) if n > 1 else 0
        if i and st_[i, 4] > 600: xs.append(2 * cen[i, 0]); ys.append(2 * st_[i, 1])
        else: xs.append(np.nan); ys.append(np.nan)
    xs, ys = np.array(xs), np.array(ys); ok = ~np.isnan(xs); idx = np.arange(len(xs))
    xs = np.interp(idx, idx[ok], xs[ok]); ys = np.interp(idx, idx[ok], ys[ok])
    xs = gaussian_filter1d(median_filter(xs, 5), 1.5); ys = gaussian_filter1d(median_filter(ys, 5), 1.5)
    json.dump({"dt": 2.0, "x": xs.round(1).tolist(), "y": ys.round(1).tolist()}, open(f"{WK}/track.json", "w")); print("track", len(xs))

if MODE == "track": stage_track(); sys.exit()
if MODE == "keys":
    for k, r in enumerate(ranges): print(k, rkey(r))
    sys.exit()
if MODE == "prep":
    from multiprocessing import Pool
    with Pool(4) as p:
        for i, k in enumerate(p.imap_unordered(prep_range, range(len(ranges)))):
            if i % 40 == 0: print("prep", i, "/", len(ranges), flush=True)
    open(f"{WK}/cams.txt", "w").write("".join(f"file 'cam_{rkey(r)}.mp4'\n" for r in ranges))
    open(f"{WK}/auds.txt", "w").write("".join(f"file 'aud_{rkey(r)}.wav'\n" for r in ranges))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/cams.txt", "-c", "copy", f"{WK}/cam.mp4"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/auds.txt", "-c", "copy", f"{WK}/aud_raw.wav"], check=True)
    chain = "highpass=f=90,afftdn=nf=-28:nr=10,acompressor=threshold=-22dB:ratio=3:attack=6:release=120:makeup=2"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{WK}/aud_raw.wav", "-af", chain + ",loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WK}/aud_raw.wav", "-af", chain + "," + ln, "-ar", "48000", "-ac", "2", f"{WK}/voice.wav"], check=True)
    if STAGE and not os.path.exists(f"{WK}/track.json"): stage_track()
    if AUDIO_ONLY:   # envelope da voz por quadro (onda sonora) em vez de corrigir câmera
        a_, sr_ = sf.read(f"{WK}/voice.wav", dtype="float32"); a_ = np.abs(a_).mean(1); hop = sr_ // FPS
        envv = np.add.reduceat(a_, np.arange(0, len(a_), hop)) / hop; np.save(f"{WK}/env.npy", envv / (np.percentile(envv, 98) + 1e-9))
        json.dump({}, open(f"{WK}/fix.json", "w"))
    else: fixmap()
    print("prep ok", round(TOTAL, 1), "s", len(ranges), "trechos"); sys.exit()

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
# palco aberto ("wide"): 1 a cada N trechos sem gráfico vira tela cheia com o palco inteiro (corte seco)
WIDE = []
if PLAN.get("wide_every") and not AUDIO_ONLY:
    ivs = [(CHG[j][0], CHG[j + 1][0] if j + 1 < len(CHG) else TOTAL) for j in range(len(CHG)) if CHG[j][1] == "center"]
    ivs = [(a, b) for a, b in ivs if b - a >= PLAN.get("wide_min", 6.0)]
    for n_, (a, b) in enumerate(ivs):
        if n_ % PLAN["wide_every"] == PLAN.get("wide_phase", 1) % PLAN["wide_every"]: WIDE.append((a + 0.8, min(b - 0.3, a + 0.8 + PLAN.get("wide_max", 10.0))))
WF = PLAN.get("wide_fade", 0.9)   # duração da fusão (fade) na entrada e na saída do palco aberto
def wide_alpha(t):
    for a, b in WIDE:
        if a - WF / 2 <= t <= b + WF / 2: return eio(pr(t, a - WF / 2, WF)) * (1 - eio(pr(t, b - WF / 2, WF)))
    return 0.0
CHT = [c[0] for c in CHG]
def layout(t):
    import bisect
    j = max(0, bisect.bisect_right(CHT, t) - 1); t0, s1 = CHG[j]; s0 = CHG[j - 1][1] if j > 0 else s1
    if s1 == "wide": return st.BOX["center"], 1.0, "wide"
    if s0 == "wide": return st.BOX[s1], 1.0, s1
    k = eio(pr(t, t0, 0.7)); b0, b1 = st.BOX[s0], st.BOX[s1]
    a0 = 0.0 if s0 == "card" else 1.0; a1 = 0.0 if s1 == "card" else 1.0
    return tuple(b0[i] + (b1[i] - b0[i]) * k for i in range(4)), a0 + (a1 - a0) * k, s1
ZS = PLAN.get("zoom_smooth", 0)   # >0: zoom aproxima/afasta suavemente entre trechos (sem salto no corte)
def zoom_at(t):
    k = next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1)
    r = ranges[k]; zb = lambda j: (1.10 if j % 2 == 0 else 1.26)
    if ZS:   # alvo muda a cada ~ZS s de fala; transição de 1,6 s com easing
        tb = int(t // ZS); u = eio(pr(t, tb * ZS, 1.6)); base = zb(tb - 1) + (zb(tb) - zb(tb - 1)) * u
        z = PLAN.get("zoom_mult", 1.0) * base
        for s0, s1 in PUNCH:
            if s0 - 0.8 <= t <= s1 + 1.6: z *= 1 + 0.06 * eio(pr(t, s0 - 0.8, 0.9)) * (1 - eio(pr(t, s1 + 0.4, 1.2)))
        return z
    z = PLAN.get("zoom_mult", 1.0) * zb(k) * (1 + 0.04 * pr(t, r["o"], r["d"]))
    for s0, s1 in PUNCH:
        if s0 - 0.2 <= t <= s1 + 0.8: z *= 1 + 0.08 * eio(pr(t, s0 - 0.2, 0.3)) * (1 - eio(pr(t, s1 + 0.35, 0.45)))
    return z

ENV = np.load(f"{WK}/env.npy") if AUDIO_ONLY and os.path.exists(f"{WK}/env.npy") else None
PHR = []
if AUDIO_ONLY:
    cur = []
    for j, w in enumerate(WORDS):
        cur.append(w); nxt = WORDS[j + 1] if j + 1 < len(WORDS) else None
        if w["text"][-1] in ".?!" or sum(len(x["text"]) + 1 for x in cur) > 58 or (nxt and nxt["start"] - w["end"] > 0.45) or not nxt:
            PHR.append(cur); cur = []
PHT = [p[0]["start"] for p in PHR]
def audio_layer(L, t, state, chap, alpha):
    """Sem câmera: título do capítulo ao centro quando não há bloco, onda sonora dourada e legenda."""
    import bisect
    from estilo import font
    from fx import tw as tw_
    d = ImageDraw.Draw(L); fi = int(t * FPS); a = 0.0 if state == "card" else 1.0
    if a > 0 and ENV is not None:      # onda: 120 barras finas, espelhadas, com o envelope recente
        n = 120; cy = 1010 if state != "center" else 640; x0 = W / 2 - n * 7
        for k in range(n):
            j = fi - abs(k - n // 2) // 2; v = float(ENV[j]) if 0 <= j < len(ENV) else 0
            h = 3 + min(1.0, v) * (60 if state == "center" else 26) * (0.6 + 0.4 * math.sin(k * 0.7 + t * 3))
            d.line([(x0 + k * 14, cy - h / 2), (x0 + k * 14, cy + h / 2)], fill=st.GOLD + (int((150 if state == "center" else 90) * a),), width=4)
    if state == "center" and chap:     # título do capítulo como "capa" do trecho
        st.kicker(L, "estudo · Zorobabel e a videira", W / 2, 330, 1.0, "center", col=st.MUTED)
        st.line_rich(L, chap, W / 2, 380, 110, 1.0, align="center", maxw=1500)
    if state not in ("card", "full"):   # legenda: frase atual, palavras acendem ao serem ditas
        k = bisect.bisect_right(PHT, t + 0.1) - 1
        if 0 <= k < len(PHR) and t < PHR[k][-1]["end"] + 0.6:
            ws = PHR[k]; f = font("sans", 44); sp = f.getlength(" ")
            tot = sum(tw_(w["text"], f) for w in ws) + sp * (len(ws) - 1); x = W / 2 - tot / 2; y = 905 if state == "center" else 940
            for w in ws:
                on = t >= w["start"] - 0.05
                d.text((x, y), w["text"], font=f, fill=(st.INK if on else st.MUTED) + (255 if on else 120,)); x += tw_(w["text"], f) + sp

_wd = {"p": None, "k": None, "f": None}
def wide_frame(t):
    """Quadro do palco inteiro direto da fonte (decodificador sequencial por trecho), com aproximação lenta."""
    k = next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1); r = ranges[k]
    fi = int(round((t - r["o"]) * FPS))
    if _wd["k"] != k or _wd["f"] != fi:
        if _wd["p"]: _wd["p"].kill()
        _wd["p"] = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{r['s'] + fi / FPS:.3f}", "-i", SRC, "-vf", f"fps={FPS},scale={W}:{H}",
                                     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE); _wd["k"] = k
    b = _wd["p"].stdout.read(W * H * 3); _wd["f"] = fi + 1
    im = Image.frombytes("RGB", (W, H), b) if len(b) == W * H * 3 else Image.new("RGB", (W, H))
    a = next((a - WF / 2 for a, b_ in WIDE if a - WF / 2 <= t <= b_ + WF / 2), t); z = 1 + 0.06 * eio(min(1.0, (t - a) / 11.0))
    if z > 1.001:
        cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) * 0.4
        im = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    return im.convert("RGBA")
# ------------------------------------------------------------------ layout "palco": tela cheia + gráficos por cima
if STAGE:
    st.FX = 960
    TRK = json.load(open(f"{WK}/track.json")) if os.path.exists(f"{WK}/track.json") else None
    def frac(t, f, dur=0.9):
        import bisect
        j = max(0, bisect.bisect_right(CHT, t) - 1); t0, s1 = CHG[j]; s0 = CHG[j - 1][1] if j > 0 else s1
        k = eio(pr(t, t0, dur)); return f(s0) * (1 - k) + f(s1) * k
    def rng_at(t): return next((j for j, r in enumerate(ranges) if r["o"] <= t < r["o"] + r["d"]), len(ranges) - 1)
    def src_at(t):
        k = rng_at(t); r = ranges[k]
        if r.get("card"):
            if k == 0: return ranges[1]["s"] + 0.5
            return ranges[k - 1]["e"] - 0.2
        return r["s"] + (t - r["o"])
    def person(ts):
        if TRK is None: return 960.0, 300.0
        i = ts / TRK["dt"]; return float(np.interp(i, np.arange(len(TRK["x"])), TRK["x"])), float(np.interp(i, np.arange(len(TRK["y"])), TRK["y"]))
    SIDE = {}   # lado do painel de cada bloco de coluna: oposto ao pregador
    for e in EV:
        if e["k"].startswith("c_"): SIDE[e["t0"]] = "L" if person(src_at(e["t0"] + 0.1))[0] > 1060 else "R"
    def side_at(t):
        act = [e["t0"] for e in EV if e["k"].startswith("c_") and e["t0"] - 0.05 <= t < e["t1"] + 0.9]
        return SIDE[max(act)] if act else "R"
    _g = np.clip((np.arange(W) - 760) / 520, 0, 1) ** 1.4
    GR = Image.fromarray((np.tile(_g, (H, 1)) * 225).astype(np.uint8), "L"); GL = GR.transpose(Image.FLIP_LEFT_RIGHT)
    _yy, _xx = np.mgrid[0:H, 0:W]; _v = np.clip(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2, 0, 1) ** 1.6 * 150
    _v = np.maximum(_v, np.clip(1 - _yy / 150, 0, 1) * 150)   # vinheta + topo escuro (rótulos)
    VIG = Image.new("RGBA", (W, H)); VIG.putalpha(Image.fromarray(_v.astype(np.uint8), "L"))
    _sd = {"p": None, "k": None, "f": None, "prev": None, "img": None, "freeze": {}}
    def src_frame(t):
        k = rng_at(t); r = ranges[k]
        if r.get("card"):
            ts = src_at(t)
            if k not in _sd["freeze"]:
                b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.2f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
                _sd["freeze"][k] = Image.frombytes("RGB", (W, H), b[:W * H * 3]) if len(b) >= W * H * 3 else Image.new("RGB", (W, H))
            return _sd["freeze"][k]
        fi = int(round((t - r["o"]) * FPS))
        if _sd["k"] != k or _sd["f"] != fi:
            if _sd["p"]: _sd["p"].kill()
            if _sd["k"] is not None and _sd["k"] != k and _sd["img"] is not None: _sd["prev"] = (_sd["img"], r["o"])
            _sd["p"] = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{r['s'] + fi / FPS:.3f}", "-i", SRC, "-vf", f"fps={FPS}",
                                         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE); _sd["k"] = k
        b = _sd["p"].stdout.read(W * H * 3); _sd["f"] = fi + 1
        im = Image.frombytes("RGB", (W, H), b) if len(b) == W * H * 3 else (_sd["img"] or Image.new("RGB", (W, H)))
        _sd["img"] = im
        pv = _sd["prev"]   # fusão de 0,5 s nos cortes de conteúdo
        if pv and 0 <= t - pv[1] < 0.5: im = Image.blend(pv[0], im, eio((t - pv[1]) / 0.5))
        return im
    ZT = PLAN.get("stage_zooms", [1.0, 1.22, 1.0, 1.38]); ZP = PLAN.get("stage_zoom_period", 11.0)
    def stage_zoom(t):
        tb = int(t // ZP); u = eio(pr(t, tb * ZP, 2.4)); z = ZT[(tb - 1) % len(ZT)] + (ZT[tb % len(ZT)] - ZT[(tb - 1) % len(ZT)]) * u
        for s0, s1 in PUNCH:
            if s0 - 0.8 <= t <= s1 + 1.6: z *= 1 + 0.07 * eio(pr(t, s0 - 0.8, 0.9)) * (1 - eio(pr(t, s1 + 0.4, 1.2)))
        return z
    def render_stage(t):
        box, alpha, s1 = layout(t)
        cf = frac(t, lambda s: 1.0 if s == "col" else 0.0); df = frac(t, lambda s: 1.0 if s in ("full", "card") else 0.0)
        sd = side_at(t); px, py = person(src_at(t))
        z = stage_zoom(t); z = z + (max(z, 1.42) - z) * cf
        xs_t = W / 2 + ((0.27 if sd == "R" else 0.73) * W - W / 2) * cf
        cw, ch = W / z, H / z; x0 = min(max(px - xs_t / z, 0), W - cw); y0 = min(max(py - 0.20 * H / z, 0), H - ch)
        im = src_frame(t)
        if z > 1.001: im = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        if df > 0.01:
            from PIL import ImageFilter
            bl = im.resize((384, 216), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
            im = Image.blend(im, Image.blend(bl, Image.new("RGB", (W, H)), 0.55), df)
        out = im.convert("RGBA"); out.alpha_composite(VIG)
        if cf > 0.01:
            st.CX0, st.CX1 = (1030, 1810) if sd == "R" else (110, 890); st.CMID = (st.CX0 + st.CX1) / 2
            g = (GR if sd == "R" else GL).point(lambda v: int(v * cf)); sh = Image.new("RGBA", (W, H), (8, 8, 10, 0)); sh.putalpha(g); out.alpha_composite(sh)
        ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); chap = next((c for tc, c in reversed(CHAPS) if t >= tc), "")
        st.topbar(ui, t, TOTAL, PLAN.get("tag", ""), chap, a=0 if s1 == "card" else 1)
        lastc = max((e["t0"] for e in EV if e["k"].startswith("c_") and e["t0"] <= t < e["t1"]), default=None)
        for e in EV:
            if e["k"].startswith("c_") and (s1 in ("full", "card") or (lastc is not None and e["t0"] < lastc and e["t0"] <= t < e["t1"])): continue
            if e["t0"] - 0.05 <= t < e["t1"] + 0.05: st.BLOCKS[e["k"]](ui, t, e)
        out.alpha_composite(ui); return out.convert("RGB")

def render(cam_img, t):
    wa = wide_alpha(t)
    out = render_stage(t) if STAGE else (wide_frame(t) if wa >= 0.999 else render_main(cam_img, t))
    if 0.001 < wa < 0.999: out = Image.blend(out, wide_frame(t).convert("RGB"), wa)
    fi_ = PLAN.get("fade_in", 0.0); fo_ = PLAN.get("fade_out", 0.0)   # abre do preto e fecha no preto
    k = min(1.0, t / fi_ if fi_ else 1.0, (TOTAL - t) / fo_ if fo_ else 1.0)
    if k < 1: out = Image.blend(Image.new("RGB", out.size), out.convert("RGB"), max(0.0, eio(k)))
    return out.convert("RGB")
def render_main(cam_img, t):
    box, alpha, s1 = layout(t)
    out = st.background(t)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    chap = next((c for tc, c in reversed(CHAPS) if t >= tc), "")
    if AUDIO_ONLY:
        audio_layer(ui, t, s1, chap, alpha)
    elif s1 != "wide":
        lay, pos = st.cam(cam_img, box, zoom_at(t), alpha)
        if lay is not None: out.alpha_composite(lay, pos)
    if s1 != "wide": st.topbar(ui, t, TOTAL, PLAN.get("tag", ""), chap, a=0 if s1 == "card" else 1)
    lastc = max((e["t0"] for e in EV if e["k"].startswith("c_") and e["t0"] <= t < e["t1"]), default=None)
    for e in EV:   # tela cheia/vinheta esconde os blocos de coluna; com dois blocos de coluna, só o mais recente
        if e["k"].startswith("c_") and (s1 in ("full", "card") or (lastc is not None and e["t0"] < lastc and e["t0"] <= t < e["t1"])): continue
        if e["t0"] - 0.05 <= t < e["t1"] + 0.05: st.BLOCKS[e["k"]](ui, t, e)
    out.alpha_composite(ui)
    return out.convert("RGB")

RAWC = CS * CS * 3
def fixes(): return {int(k): v for k, v in json.load(open(f"{WK}/fix.json")).items()}
if MODE == "events":
    print("TOTAL", round(TOTAL, 1), "s; fala até", round(T_SPEECH, 1))
    for b, (a, z) in BLK.items(): print(f"  {b:6s} {a:7.1f} – {z:7.1f}  " + " ".join(w["text"] for w in WORDS if w["blk"] == b)[:120])
    for e in EV: print(f"{e['t0']:7.1f} {e['t1']:7.1f} {e['k']}")
    for a, b in WIDE: print(f"{a:7.1f} {b:7.1f} WIDE")
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
if MODE == "clip":   # prévia: clip t0 t1 saida.mp4 (vídeo + mix.wav do trecho, sem reposição de quadros)
    a_, b_, outp = float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]; f0, f1 = int(a_ * FPS), int(b_ * FPS); dec = read_cam_frames(f0)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-ss", f"{a_:.3f}", "-t", f"{b_ - a_:.3f}", "-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", outp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        b = dec.stdout.read(RAWC); enc.stdin.write(render(Image.frombytes("RGB", (CS, CS), b if len(b) == RAWC else bytes(RAWC)), fi / FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.terminate(); print("clip ok"); sys.exit()
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
    OFF = bool(M.get("off"))
    if not OFF:
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
        if M.get("off"): music[:] = 0      # sem trilha de fundo: só voz + efeitos sonoros
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
    else:
        v, _ = sf.read(f"{WK}/voice.wav", dtype="float32"); v = v[:N]; mus = 0.0
    sfx = np.zeros(N, np.float32)
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
    mix = v[:N] + ((mus + sfx)[:, None])[: len(v[:N])].astype(np.float32); mix = mix[: int(TOTAL * SR_)]
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
    def ts(t): t = t / SPEED; h, r_ = divmod(t, 3600); m, s = divmod(r_, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    with open(out, "w") as f:
        for n, c in enumerate(cues, 1):
            txt = " ".join(x["text"] for x in c)
            if len(txt) > 42:
                ws = txt.split(); bk = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(txt) / 2)); txt = " ".join(ws[:bk]) + "\n" + " ".join(ws[bk:])
            end = min(c[-1]["end"] + 0.3, cues[n][0]["start"] - 0.02) if n < len(cues) else c[-1]["end"] + 0.3
            f.write(f"{n}\n{ts(c[0]['start'])} --> {ts(end)}\n{txt}\n\n")
    for tc, title in [(0, PLAN.get("cold_title", "Abertura"))] + CHAPS: tc = tc / SPEED; print(f"{int(tc // 60)}:{int(tc % 60):02d} {title.replace("*", "")}")
    sys.exit()
if MODE == "pack":
    n = int(sys.argv[3]); out = sys.argv[4]
    open(f"{WK}/parts.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(n)))
    vk = int((380 * 8388.608 / (TOTAL / SPEED) - 128) * 0.96)
    vf = ["-vf", f"setpts=PTS/{SPEED},fps={round(FPS * SPEED, 3)}"] if SPEED != 1 else []; af = ["-af", f"atempo={SPEED}"] if SPEED != 1 else []
    base = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/parts.txt"]
    vopt = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{vk}k", "-maxrate", f"{2 * vk}k", "-bufsize", f"{4 * vk}k", "-pix_fmt", "yuv420p", "-passlogfile", f"{WK}/pl"]
    subprocess.run(base + vf + vopt + ["-pass", "1", "-an", "-f", "null", "/dev/null"], check=True)
    subprocess.run(base + ["-i", f"{WK}/mix.wav", "-map", "0:v", "-map", "1:a"] + vf + af + vopt + ["-pass", "2", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", out], check=True)
    print("ok", out, round(os.path.getsize(out) / 2 ** 20, 1), "MiB", vk, "kbps"); sys.exit()
