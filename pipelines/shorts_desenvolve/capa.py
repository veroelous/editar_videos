"""Capa no 1º quadro dos Shorts (Desenvolve Mais).
Regra do usuário: o 1º quadro é a capa — ele olhando para a câmera, sério, olhos abertos, sem piscar, boca fechada e reta.

Uso (PROJ=<pasta do projeto>):
  capa.py scan                 → varre o vídeo a 3 fps com o MediaPipe Face Landmarker e grava edit/capa_scan.json
  capa.py pick <sid> [n]       → mostra os n melhores tempos dentro do trecho do Short (e no vídeo todo)
  capa.py sheet <sid> [n]      → folha de contato dos melhores quadros (edit/<sid>/capa_cands.jpg) para conferir a olho
  capa.py make <sid> [t]       → gera a capa (quadro t, ou o melhor do trecho) com o título e a coloca como 1º quadro do Short
"""
import json, os, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import fx

D = os.environ.get("PROJ", "/home/user/editar_videos/brutos/desenvolve"); E = f"{D}/edit"; SRC = f"{D}/bruto.mp4"
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
W, H = 1080, 1920
PAL = dict(bg=(12, 12, 20), ink=(255, 255, 255), accent=(43, 107, 251), cream=(255, 211, 77), glow=(43, 107, 251), muted=(160, 160, 170))
HOLD = 0.4   # duração da capa antes da fala (s)


def scan():
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    opt = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=f"{MODELS}/face_landmarker.task"),
                                       output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1)
    lm = vision.FaceLandmarker.create_from_options(opt)
    w, h, fps = 960, 540, 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out, k = [], 0
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3: break
        a = np.frombuffer(b, np.uint8).reshape(h, w, 3); t = k / fps; k += 1
        r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a)))
        if not r.face_blendshapes: continue
        bs = {c.category_name: c.score for c in r.face_blendshapes[0]}
        M = np.array(r.facial_transformation_matrixes[0])
        yaw = math.degrees(math.atan2(-M[2, 0], math.hypot(M[0, 0], M[1, 0]))); pitch = math.degrees(math.atan2(M[2, 1], M[2, 2]))
        pts = np.array([(q.x, q.y) for q in r.face_landmarks[0]])
        x0, y0 = (pts.min(0) * [w, h]).astype(int); x1, y1 = (pts.max(0) * [w, h]).astype(int)
        g = a[max(0, y0):y1, max(0, x0):x1].mean(2)
        sharp = float(np.var(np.diff(g, 2, 0)) + np.var(np.diff(g, 2, 1))) if g.size > 100 else 0
        # boca encoberta (microfone/mão): pixels de pouca saturação (grade do microfone) ou escuros nos lábios
        P = (pts * [w, h]).astype(int); mo = []
        for i in (0, 17, 13, 14, 61, 291, 39, 269, 181, 405):
            x, y = P[i]; mo.append(a[max(0, y - 3):y + 3, max(0, x - 3):x + 3].reshape(-1, 3))
        mo = np.vstack(mo).astype(float); mx, mn = mo.max(1), mo.min(1)
        sat = (mx - mn) / np.maximum(mx, 1); occ = float(((sat < 0.17) | (mx < 60)).mean())
        out.append(dict(t=round(t, 2), blink=max(bs["eyeBlinkLeft"], bs["eyeBlinkRight"]), jaw=bs["jawOpen"],
                        smile=(bs["mouthSmileLeft"] + bs["mouthSmileRight"]) / 2, tort=abs(bs["mouthSmileLeft"] - bs["mouthSmileRight"]) + abs(bs["mouthLeft"] - bs["mouthRight"]),
                        press=bs["mouthPressLeft"] + bs["mouthPressRight"], pucker=bs["mouthPucker"], funnel=bs["mouthFunnel"],
                        brow=bs["browInnerUp"], squint=max(bs["eyeSquintLeft"], bs["eyeSquintRight"]),
                        lookx=abs(bs["eyeLookOutLeft"] - bs["eyeLookInLeft"]) + abs(bs["eyeLookOutRight"] - bs["eyeLookInRight"]),
                        looky=max(bs["eyeLookUpLeft"], bs["eyeLookDownLeft"], bs["eyeLookUpRight"], bs["eyeLookDownRight"]),
                        yaw=round(yaw, 1), pitch=round(pitch, 1), sharp=round(sharp, 1), occ=round(occ, 2), cx=round(float(pts[:, 0].mean()), 3)))
    json.dump(out, open(f"{E}/capa_scan.json", "w"))
    print("scan", len(out), "quadros com rosto")


def score(f, sharp_ref):
    """Menor = melhor: olhos bem abertos, boca fechada e reta, cabeça de frente, olhar na lente, imagem nítida."""
    return (4 * f["blink"] + 6 * f["jaw"] + 3 * f["smile"] + 4 * f["tort"] + 2 * f["pucker"] + 2 * f["funnel"] + 1.5 * f["squint"]
            + 1.5 * f["lookx"] + 1.5 * f["looky"] + abs(f["yaw"]) / 12 + abs(f["pitch"] - 0) / 25 + 0.6 * max(0, 1 - f["sharp"] / sharp_ref) + 5 * f.get("occ", 0))


def ranked(sid, n):
    S = json.load(open(f"{E}/capa_scan.json")); WS = json.load(open(f"{E}/transcripts/bruto.json"))["words"]
    sp = json.load(open(f"{E}/shorts_plan.json"))[sid]["spans"]
    ref = float(np.percentile([f["sharp"] for f in S], 70))
    inside = lambda t: any(WS[a]["start"] - 1 <= t <= WS[b]["end"] + 1 for a, b in sp)
    S.sort(key=lambda f: score(f, ref))
    loc = [f for f in S if inside(f["t"])][:n]; glob = S[:n]
    return loc, glob


def frame_at(t):
    """Quadro da fonte recortado em 9:16, centrado no rosto daquele instante."""
    S = json.load(open(f"{E}/capa_scan.json")); f = min(S, key=lambda f: abs(f["t"] - t))
    x = int(min(max(f["cx"] * 1920 - 304, 0), 1920 - 608))
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1", "-vf", f"crop=608:1080:{x}:0,scale={W}:{H}:flags=lanczos",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), b)


def sheet(sid, n):
    loc, glob = ranked(sid, n)
    ims = []
    for f in loc + [g for g in glob if g not in loc][: max(0, 2 * n - len(loc))]:
        im = frame_at(f["t"]).resize((216, 384)); d = ImageDraw.Draw(im); d.rectangle((0, 0, 216, 22), fill=(0, 0, 0)); d.text((4, 4), f"{f['t']}", fill=(255, 220, 0)); ims.append(im)
    cols = min(len(ims), 8); rows = math.ceil(len(ims) / cols)
    out = Image.new("RGB", (216 * cols, 384 * rows))
    for i, im in enumerate(ims): out.paste(im, ((i % cols) * 216, (i // cols) * 384))
    os.makedirs(f"{E}/{sid}", exist_ok=True); out.save(f"{E}/{sid}/capa_cands.jpg", quality=85); print(f"{E}/{sid}/capa_cands.jpg")


def make(sid, t=None):
    P = json.load(open(f"{E}/shorts_plan.json"))[sid]
    if t is None: t = ranked(sid, 1)[0][0]["t"]
    bg = frame_at(t).convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    for y in range(520): d.line((0, y, W, y), fill=(0, 0, 0, int(150 * (1 - y / 520) ** 1.6)))   # leve sombra no topo para o título
    bg.alpha_composite(sh)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fx.kinetic_title(ui, P["kicker"], P["hero"], 2.0, 0.05, W / 2, 150, PAL, size=118 if len(P["hero"]) < 10 else 96, exit_t=99, kicker_scale=0.34)
    bg.alpha_composite(ui)
    cap = f"{D}/shorts/{sid}_{P['slug']}_capa.jpg"; bg.convert("RGB").save(cap, quality=93)
    vid = f"{D}/shorts/{sid}_{P['slug']}.mp4"; tmp = vid + ".capa.mp4"
    sr = "48000"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(HOLD), "-i", cap, "-f", "lavfi", "-t", str(HOLD), "-i", f"anullsrc=r={sr}:cl=stereo",
                    "-i", vid, "-filter_complex",
                    "[0:v]scale=1080:1920,setsar=1,format=yuv420p[c];[2:v]setsar=1,format=yuv420p[v];[2:a]aresample=48000[a2];[c][1:a][v][a2]concat=n=2:v=1:a=1[v][a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, vid); print("capa", sid, t, vid)


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "scan": scan()
    elif m == "pick":
        loc, glob = ranked(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
        print("trecho:", [f["t"] for f in loc]); print("vídeo:", [f["t"] for f in glob])
    elif m == "sheet": sheet(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
    elif m == "make": make(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None)
