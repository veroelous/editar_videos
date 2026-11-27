"""Centro da cabeça (cabelo + pele do rosto, MediaPipe selfie_multiclass) a 2 fps num vídeo vertical → [[t, cx, cy, h]] em px da fonte."""
import json, sys, subprocess, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
src, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
w, h = 270, 480; SW, SH = 1080, 1920
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=model), output_category_mask=True))
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=2,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
res = []; k = 0; last = [SW / 2, SH * 0.35, 400]
while True:
    b = p.stdout.read(w * h * 3)
    if len(b) < w * h * 3: break
    a = np.frombuffer(b, np.uint8).reshape(h, w, 3)
    m = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a))).category_mask.numpy_view()
    ys, xs = np.where((m == 1) | (m == 3))
    if len(xs) > 200:
        last = [float(np.median(xs)) * SW / w, float(np.median(ys)) * SH / h, float(np.percentile(ys, 97) - np.percentile(ys, 3)) * SH / h]
    res.append([k / 2] + [round(v, 1) for v in last]); k += 1
json.dump(res, open(out, "w")); print("head", len(res))
