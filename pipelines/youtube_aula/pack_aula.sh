#!/bin/bash
# Junta as partes + áudio e codifica em 2 passes abaixo de 380 MiB. Uso: pack_aula.sh <pasta_partes> <saida.mp4>
set -e
P=$1; OUT=$2; A=${PROJ:-/home/user/editar_videos/brutos/aula}/edit/audio_mix.wav
cd "$P"; printf "file 'p%d.mp4'\n" 0 1 2 3 > list.txt
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$A")
VK=$(python3 -c "print(int((380*8388.608/$DUR - 128)*0.96))")
echo "dur $DUR  video ${VK}k"
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c:v libx264 -preset medium -b:v ${VK}k -maxrate $((VK*2))k -bufsize $((VK*4))k -pass 1 -passlogfile pl -an -f null /dev/null
ffmpeg -v error -y -f concat -safe 0 -i list.txt -i "$A" -map 0:v -map 1:a -c:v libx264 -preset medium -b:v ${VK}k -maxrate $((VK*2))k -bufsize $((VK*4))k -pass 2 -passlogfile pl -pix_fmt yuv420p -c:a aac -b:a 128k -ar 48000 -movflags +faststart -shortest "$OUT"
ls -l "$OUT"
