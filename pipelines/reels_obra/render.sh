#!/usr/bin/env bash
# Render completo do reels "Diário da Reforma". Uso: PROJ=brutos/g2b EP=g2b_ep01 bash pipelines/reels_obra/render.sh
set -euo pipefail
PROJ=${PROJ:-brutos/g2b}; HERE=$(dirname "$0"); J=${J:-$(nproc)}
EP=${EP:-g2b_ep01}; export PROJ EP
# 1) ambiente do bruto remontado na linha do tempo (atempo por segmento)
python3 - <<'PY'
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.environ.get("HERE", "pipelines/reels_obra")))
from compose import SEGS
P = os.environ["PROJ"]; parts = []
for i, (o0, o1, s0, s1, *_ ) in enumerate(SEGS):
    sp = max(0.5, (s1 - s0) / (o1 - o0)); f = f"{P}/amb_{i}.wav"  # atempo aceita no mínimo 0,5
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-t", str(s1 - s0), "-i", f"{P}/raw.mp4", "-vn", "-ac", "1", "-ar", "48000",
                    "-af", f"atempo={sp:.4f},afade=t=in:d=0.03,afade=t=out:st={o1 - o0 - 0.04:.3f}:d=0.04,apad", "-t", str(o1 - o0), f], check=True)
    parts.append(f)
open(f"{P}/amb_list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{P}/amb_list.txt", f"{P}/amb.wav"], check=True)
PY
# 2) trilha + SFX
python3 "$HERE/audio.py"
# 3) frames em paralelo
NF=$(python3 -c "import sys; sys.path.insert(0,'$HERE'); from compose import END1,FPS,COVER; print(int((END1+COVER)*FPS))")
rm -rf "$PROJ/frames"; mkdir -p "$PROJ/frames"
CH=$(( (NF + J - 1) / J ))
for ((k=0; k<J; k++)); do python3 "$HERE/compose.py" $((k*CH)) $(((k+1)*CH)) "$PROJ/frames" & done; wait
# 4) encode + mux (loudnorm -14 LUFS)
ffmpeg -v error -y -framerate 30 -i "$PROJ/frames/%05d.png" -i "$PROJ/audio_mix.wav" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9" -c:a aac -b:a 192k -ar 48000 -shortest "$PROJ/final.mp4"
ls -l "$PROJ/final.mp4"
