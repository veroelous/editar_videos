#!/bin/bash
# Renderiza vários planos em sequência (4 partes em paralelo cada) → áudio → entrega.
# Uso: lote.sh <pasta_planos> <pasta_saida> r1 r2 ...
S=/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad
source $S/wenv/bin/activate
P=/home/user/editar_videos/pipelines/reels_meet/reel_meet.py; PL=$1; OUT=$2; shift 2
n=0
for r in "$@"; do
  n=$((n+1)); slug=$(python3 -c "import json;print(json.load(open('$PL/$r.json'))['slug'])")
  for k in 0 1 2 3; do python $P $PL/$r.json render $k 4 & done; wait
  python $P $PL/$r.json audio
  python $P $PL/$r.json pack 4 "$OUT/$(printf %02d ${r#r})_$slug.mp4"
done
echo LOTE_OK
