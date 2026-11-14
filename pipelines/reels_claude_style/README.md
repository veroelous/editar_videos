# Pipeline "estilo reels_claude"

Scripts usados para editar o reels do EBO aplicando o estilo descrito em `referencias/reels_claude/ANALISE.md`.
Eles rodam em sequência sobre `brutos/edit/` (os caminhos estão fixos no topo de cada script; ajuste para outro vídeo).

| Ordem | Script | O que faz |
|---|---|---|
| 1 | `asr.py <modelo> <audio16k.wav> <out.json>` | Transcrição local, palavra por palavra (sherpa-onnx + Parakeet TDT 0.6B v3 int8, baixado dos releases do GitHub do k2-fsa/sherpa-onnx) |
| 2 | `refine.py <json> <audio16k.wav>` | Ajusta início e fim de cada palavra pela energia do áudio (−38 dB) |
| 3 | `cut.py` | Monta a lista de trechos (remove pausas ≥0,15 s e frases de `DROP`, punch-in em `PUNCH`, acelera com `SPD`), extrai os segmentos com áudio e vídeo do mesmo tamanho e gera `base.mov` + `edl_out.json` (tempos das palavras na linha do tempo final) |
| 4 | `masks.py` | Máscara da pessoa por frame (rembg `u2net_human_seg`) → `mask.mkv` |
| 5 | `audio.py` | Limpa a voz (highpass, afftdn, compressor, loudnorm −14 LUFS) e adiciona SFX sintetizados → `audio_mix.wav` |
| 6 | `compose.py 0 99 <saida.mp4>` | Compositor frame a frame: palavra-herói atrás da pessoa, cartões em tela cheia, UI falsa, legenda progressiva (sempre a última camada) |
| 7 | ffmpeg mux | `ffmpeg -i video_gfx.mp4 -i audio_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest final.mp4` |

Para outro vídeo, o que muda é o roteiro gráfico em `compose.py` (`CARDS`, `PHRASES`, `HEROES`, funções `card_*` e `ui_*`) e as listas `DROP`/`PUNCH` em `cut.py`. Todos os tempos saem dos índices das palavras (`S(i)`, `SS(i)`, `SE(i)`), então um recorte novo não quebra a sincronia.

Dependências: ffmpeg, Python 3 com `sherpa-onnx soundfile rembg[cpu] pillow numpy`, e a fonte Inter / Inter Display.
