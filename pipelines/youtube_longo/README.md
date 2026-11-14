# Pipeline YouTube longo (16:9) + cortes verticais

Usado no EBO de Gálatas 6:7-10 (gravação do Google Meet, 62 min → 30:32 min). Caminhos fixos no topo de cada script (`brutos/longo/edit`).

| Ordem | Script | O que faz |
|---|---|---|
| 1 | `../reels_claude_style/asr.py` + `refine.py` | Transcrição local palavra por palavra (Parakeet v3) e refino por energia |
| 2 | `pack_long.py` | Frases com índice das palavras e nome de quem fala (tirado da faixa de legenda do Meet) → `takes_packed.md` |
| 3 | `cut_long.py` | Seleção por capítulo (índices de palavras), pausas ≥0,6 s encurtadas, segmentos com áudio e vídeo do mesmo tamanho → `base.mov` + `edl_out.json` |
| 4 | `compose_long.py <i> <n> <out>` | Compositor 1920×1080 em n partes paralelas: reenquadramento (zoom alternado e participante de celular com fundo desfocado), painéis de versículo, frases de destaque, lower-thirds, cartões de título/capítulo/final inseridos |
| 5 | `audio_long.py` | Voz nivelada (dynaudnorm + loudnorm −14 LUFS) com as mesmas inserções (whoosh/chime/pad) |
| 6 | ffmpeg concat + mux | junta as partes e o `audio_mix.wav` |
| 7 | `shorts.py <n>` | Cortes verticais 1080×1920: título, vídeo recortado no rosto, legenda progressiva e cartão "estudo completo no YouTube" |

A detecção de layout do Meet (`layout4fps.json`) é gerada a 4 fps a partir das faixas pretas laterais. Os textos dos versículos (ARA) ficam no dicionário `V` do `compose_long.py`.

## Limite de entrega
O arquivo entregue deve ter no máximo 380 MiB (ver `CLAUDE.md`). Depois do concat, gere a versão final com 2 passes:
```
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 master.mp4)
VK=$(python3 -c "print(int(380*8388.608/$DUR - 128))")
ffmpeg -y -i master.mp4 -c:v libx264 -preset medium -b:v ${VK}k -pass 1 -an -f null /dev/null
ffmpeg -y -i master.mp4 -c:v libx264 -preset medium -b:v ${VK}k -maxrate $((VK*2))k -bufsize $((VK*4))k -pass 2 -c:a aac -b:a 128k -movflags +faststart final.mp4
```
