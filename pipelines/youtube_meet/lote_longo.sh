#!/bin/bash
# Render completo do vídeo longo: 4 partes em paralelo → áudio → SRT/capítulos → entrega em 2 passes (≤380 MiB).
# Uso: lote_longo.sh <plano.json> <saida.mp4> <saida.srt>
S=/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad
source $S/wenv/bin/activate
P=/home/user/editar_videos/pipelines/youtube_meet/longo_meet.py
for k in 0 1 2 3; do python $P $1 render $k 4 & done; wait
python $P $1 audio
python $P $1 srt $3 > "${3%.srt}_capitulos.txt"
python $P $1 pack 4 $2
echo LOTE_OK
