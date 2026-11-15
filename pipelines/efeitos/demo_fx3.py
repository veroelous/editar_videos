"""Demo dos efeitos da referência 3 sobre o reels do EBO. Saída: brutos/demo_fx/demo_fx3.mp4 (~12 s)."""
import json, subprocess, sys, os, math
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import fx
from fx import F, eo, pr, PAL_GOLD as P

E = "/home/user/editar_videos/brutos/edit"; OUT = "/home/user/editar_videos/brutos/demo_fx"; os.makedirs(OUT, exist_ok=True)
W, H, FPS, T0SRC, DUR = 1080, 1920, 30, 14.0, 12.0
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(T0SRC), "-i", f"{E}/mask.mkv", "-frames:v", str(int(DUR * FPS)), "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
MASKS = np.frombuffer(raw, np.uint8).reshape(-1, 640, 360)
def pmask(fi): return Image.fromarray(MASKS[min(fi, len(MASKS) - 1)]).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
# miniaturas: quadros do próprio vídeo (variadas)
thumbs = []
for s in np.linspace(0, 44, 14):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.2f}", "-i", f"{E}/base.mov", "-frames:v", "1", "-vf", "crop=1080:1080:0:300,scale=160:160", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    thumbs.append(Image.frombytes("RGB", (160, 160), b))
still = thumbs[3].resize((300, 300))
def bible_screen(verse_on):
    im = Image.new("RGB", (400, 820), (246, 243, 236)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 400, 110], fill=(43, 107, 251)); d.text((28, 50), "Gálatas 6", font=F("InterDisplay-Bold", 40), fill=(255, 255, 255))
    lines = ["7 Não vos enganeis:", "de Deus não se", "zomba; pois aquilo", "que o homem semear,", "isso também ceifará."] if verse_on else ["1 Irmãos, se alguém", "for surpreendido", "nalguma falta,", "vós, que sois", "espirituais…"]
    for i, l in enumerate(lines): d.text((28, 150 + i * 56), l, font=F("Inter-SemiBold", 32), fill=(30, 30, 35))
    return im
def ebo_screen():
    im = Image.new("RGB", (400, 820), (12, 12, 18)); d = ImageDraw.Draw(im)
    for r, (L, rest) in enumerate([("E", "studo"), ("B", "íblico"), ("O", "nline")]):
        y = 200 + r * 130; d.rounded_rectangle([40, y, 140, y + 100], radius=16, fill=(245, 197, 66)); d.text((70, y + 18), L, font=F("InterDisplay-Black", 60), fill=(20, 20, 20)); d.text((160, y + 22), rest, font=F("InterDisplay-ExtraBold", 54), fill=(255, 255, 255))
    d.text((40, 640), "quinta · 20h", font=F("Inter-Bold", 40), fill=(94, 230, 200)); return im

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(T0SRC), "-i", f"{E}/base.mov", "-t", str(DUR), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", f"{OUT}/v3.mp4"], stdin=subprocess.PIPE)
num_sprite, _ = fx.text_sprite("4 BILHÕES", F("InterDisplay-Black", 130), P["accent"] + (255,))
for fi in range(int(DUR * FPS)):
    t = fi / FPS; src = Image.frombytes("RGB", (W, H), dec.stdout.read(W * H * 3)); frame = src.convert("RGBA")
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 0–3.6 s: card que evolui (foto -> GIF -> 2x -> tira de filme)
    fx.evolving_card(ui, still, "a frase do versículo", [(0.8, "gif"), (1.6, "2x"), (2.5, "film")], t, 0.1, 3.6, 230, 1380, P)
    # 3.6–7.4 s: chuva de cartões -> esfera, com número; depois desintegra
    if 3.6 <= t < 7.4:
        sph = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fx.cards_to_sphere(sph, thumbs, t, 3.6, 4.6, W / 2, 1420, W, H, radius=230)
        if t >= 6.6:
            box = (W / 2 - 340, 1420 - 340, W / 2 + 340, 1420 + 340); piece = sph.crop(tuple(int(v) for v in box))
            d_ = fx.disintegrate(piece, pr(t, 6.6, 0.8), cell=8); sph = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sph.alpha_composite(d_, (int(box[0]), int(box[1] - 260)))
        ui.alpha_composite(sph)
        if t >= 5.0:
            k = eo(pr(t, 5.0, 0.3)); fx.kinetic_title(ui, "versículos lidos por semana", "4 BILHÕES", t, 5.0, W / 2, 150, P, size=120, exit_t=6.6)
    # 7.4–10.6 s: celular 3D com troca de tela girando no eixo Y + notificação
    if 7.4 <= t < 10.6:
        kf = pr(t, 8.6, 0.5); scr = bible_screen(kf < 0.5 or True) if kf < 0.5 else ebo_screen()
        ph = fx.phone_mockup(scr, w=330, tilt=-6 + 4 * math.sin(t))
        if 0 < kf < 1: ph = fx.y_flip(ph, kf)
        ke = eo(pr(t, 7.4, 0.4)); ko = pr(t, 10.3, 0.3)
        ui.alpha_composite(fx.with_alpha(ph, ke * (1 - ko)), (int(W - ph.width + 10 + 300 * (1 - ke)), 1050))
        fx.number_badge(ui, 1 if t < 8.85 else 2, t, 7.5, 10.3, 150, 300, P, color=P["accent"])
        fx.push_notification(ui, "EBO", "Novo estudo: Gálatas 6:7, quinta às 20h. Toque para participar.", t, 9.2, 10.5, W, P, icon_col=(43, 107, 251))
    # 10.6–12 s: ✕ riscando + órbita de recap atrás da pessoa
    if t >= 10.6:
        cards = [fx.phone_mockup(ebo_screen(), w=230), still.resize((240, 240)).convert("RGBA"), num_sprite.resize((440, 116))] + [th.resize((210, 210)).convert("RGBA") for th in thumbs[:5]]
        fx.orbit_recap(back, cards, t, 10.6, W / 2, 1150, W, H, rx=470, ry=330, front_layer=ui)
    frame.alpha_composite(back); frame = Image.composite(src.convert("RGBA"), frame, pmask(fi)) if t >= 10.6 else frame
    frame.alpha_composite(ui)
    enc.stdin.write(frame.convert("RGB").tobytes())
enc.stdin.close(); enc.wait(); dec.terminate()
v, sr = sf.read(f"{E}/voice_clean.wav", dtype="float32"); v = v[int(T0SRC * sr): int((T0SRC + DUR) * sr)].copy()
def add(sig, at, db):
    i = int(at * sr); s = sig[: len(v) - i] * 10 ** (db / 20); v[i:i + len(s)] += s[:, None]
for at in [0.8, 1.6, 5.0, 8.6, 9.2]: add(fx.chime(sr, f=1318.5 if at != 5.0 else 988), at, -26)
sf.write(f"{OUT}/a3.wav", v, sr)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/v3.mp4", "-i", f"{OUT}/a3.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", f"{OUT}/demo_fx3.mp4"], check=True)
print("ok", f"{OUT}/demo_fx3.mp4")
