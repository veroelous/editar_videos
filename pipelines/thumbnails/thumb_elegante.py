"""Thumbnail 1920x1080 no estilo elegante (grafite + grão, Instrument Serif com itálico dourado), com o rosto REAL
do apresentador recortado do vídeo (segmentação MediaPipe), ampliado por super-resolução e com luz de contorno.
Regras (skill /youtube thumbnail): rosto com emoção, ≤3 palavras grandes, 30–40% de área livre, não repetir o título,
legível a 168x94 px, JPG < 2 MB.
Uso: thumb_elegante.py <video> <t_segundos> <crop x,y,w,h> <saida.jpg> "<linha1>" "<linha2 com *destaque*>" [kicker]"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
sys.path.insert(0, "/home/user/editar_videos/pipelines/youtube_meet"); sys.path.insert(0, "/home/user/editar_videos/pipelines/reels_meet")
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import estilo16 as st
from estilo import font, GOLD, INK, MUTED
from fx import tw
MODELS = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/models"
W, H = 1920, 1080

def frame_at(video, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    import io; return Image.open(io.BytesIO(b)).convert("RGB")

def person_cutout(img):
    """Máscara da pessoa (cabelo+pele+roupa) com o selfie_multiclass do MediaPipe, suavizada."""
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=f"{MODELS}/selfie_multiclass.tflite"), output_category_mask=True))
    r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(img)))
    cat = np.squeeze(r.category_mask.numpy_view()).copy(); seg.close()
    m = (cat > 0).astype(np.float32)
    h, w = m.shape   # o corpo se dissolve nas bordas do recorte (esquerda e base) em vez de um corte reto
    m *= np.clip(np.arange(w) / (0.16 * w), 0, 1)[None, :] ** 1.5
    m *= np.clip((h - np.arange(h)) / (0.05 * h), 0, 1)[:, None]
    return Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))

def build(video, t, crop, out, l1, l2, kicker="João 5 · estudo bíblico", person_h=1120, head_x=1480):
    src = frame_at(video, t).crop(crop)
    mask = person_cutout(src)
    from sr import Upscaler
    big = Image.fromarray(Upscaler(MODELS, threads=4)(np.asarray(src)))
    s = person_h / big.height; size = (int(big.width * s), person_h)
    big = big.resize(size, Image.LANCZOS); mask = mask.resize(size, Image.LANCZOS)
    mk = np.asarray(mask).astype(np.float32); top = mk[: int(size[1] * 0.35)]
    hx = (top.sum(0) * np.arange(size[0])).sum() / max(1, top.sum())     # centro da cabeça (topo da máscara)
    person_x = int(head_x - hx)
    # camiseta branca: escurece suavemente a parte de baixo para o olhar ficar no rosto
    sh_ = np.clip((np.arange(size[1]) - size[1] * 0.55) / (size[1] * 0.45), 0, 1)[:, None, None] * 0.38
    big = Image.fromarray((np.asarray(big).astype(np.float32) * (1 - sh_)).astype(np.uint8))
    big = ImageEnhance.Contrast(ImageEnhance.Color(big).enhance(0.92)).enhance(1.06)
    # leve aquecimento para casar com o dourado
    a = np.asarray(big).astype(np.float32); a[..., 0] *= 1.03; a[..., 2] *= 0.96; big = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    bg = st.background(3.0).convert("RGBA")
    # halo dourado atrás da cabeça
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    cx, cy = person_x + size[0] * 0.48, 380
    gd.ellipse([cx - 520, cy - 460, cx + 520, cy + 560], fill=GOLD + (60,)); bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(140)))
    # luz de contorno: borda da máscara, dourada, por trás
    edge = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10))
    rim = Image.new("RGBA", size, GOLD + (0,)); rim.putalpha(edge.point(lambda v: int(v * 0.55)))
    py = H - person_h + 40
    bg.alpha_composite(rim, (person_x - 6, py - 4))
    person = big.convert("RGBA"); person.putalpha(mask)
    # sombra suave à esquerda da pessoa
    sh = Image.new("RGBA", size, (0, 0, 0, 0)); sh.putalpha(mask.point(lambda v: int(v * 0.5)))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)), (person_x - 30, py + 10))
    bg.alpha_composite(person, (person_x, py))
    # vinheta para o texto respirar
    vg = np.zeros((H, W, 4), np.uint8); xs = np.linspace(1, 0, W)[None, :] ** 2.2
    vg[..., 3] = (np.clip(xs * 1.25, 0, 1) * 150).astype(np.uint8); vg[..., :3] = 8
    bg.alpha_composite(Image.fromarray(vg, "RGBA"))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x0 = 110
    st.kicker(L, kicker, x0, 250, 1.0, size=34)
    ImageDraw.Draw(L).line([(x0, 300), (x0 + 120, 300)], fill=GOLD + (230,), width=3)
    y = 340; size_t = 230
    for ln in (l1, l2):
        size_t = st.line_rich(L, ln, x0, y, size_t, 1.0, maxw=790); y += size_t * 1.0
    # detalhe: três linhas de largada (A, B, C) em traço fino
    d = ImageDraw.Draw(L); yb = y + 60
    for j, (xs_, col) in enumerate(((0, MUTED), (90, MUTED), (190, GOLD))):
        yy = yb + j * 34; d.line([(x0 + xs_, yy), (x0 + 560, yy)], fill=col + (150 if col == MUTED else 230,), width=3)
        d.ellipse([x0 + xs_ - 7, yy - 7, x0 + xs_ + 7, yy + 7], fill=col + (255,))
    bg.alpha_composite(L)
    bg.convert("RGB").save(out, quality=90, optimize=True)
    print(out, round(os.path.getsize(out) / 1024), "KB")

if __name__ == "__main__":
    v, t, crop, out, l1, l2 = sys.argv[1:7]
    build(v, float(t), tuple(int(c) for c in crop.split(",")), out, l1, l2, *(sys.argv[7:8] or []))
