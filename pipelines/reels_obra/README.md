# Pipeline "Diário da Reforma" (reels de obra/antes e depois, vídeo SEM fala)

Usado no EP.01 da G2B Esquadrias e Vidros ("O antes"): passeio pela sede no início da reforma, com o objetivo de fazer os seguidores acompanharem a evolução.

| Ordem | Script | O que faz |
|---|---|---|
| 0 | `ffmpeg -i raw.mp4 -vf "eq=contrast=1.07:saturation=1.18:brightness=0.01,unsharp=5:5:0.6" -q:v 2 src/%05d.jpg` | Extrai os frames do bruto já gradeados (`PROJ/src/`) |
| 1 | `render.sh` | Ambiente remontado por segmento (atempo) → `audio.py` (trilha 120 bpm + SFX) → `compose.py` em paralelo → encode com loudnorm −14 LUFS |

Rodar: `PROJ=brutos/g2b bash pipelines/reels_obra/render.sh` (a partir da raiz). Saída: `PROJ/final.mp4` (1080x1920, 30 fps).

## O que muda de um episódio para outro (`compose.py`)
- `SEGS`: trechos do bruto, com zoom (Ken Burns) e a transição de entrada (`whip_x`, `whip_y`, `zoom`, `leak`). Cortes nas batidas (múltiplos de 0,5 s).
- `PHRASES`: a copy das legendas (linha de ligação branca + linha forte amarela). Sem fala, o texto é escrito.
- Gancho (`kinetic_title` "O ANTES"), etiqueta `EP. 0X`, pílula de progresso `REFORMA x%`, fita "EM OBRAS" (`tape`) e o cartão final ANTES | DEPOIS com o "?" e o CTA "SIGA A G2B".
- Paleta: amarelo de obra #F5C542 + branco sobre azul-marinho.

## Cuidados
- Confira se o bruto mostra **marca de outra empresa** (no EP.01 havia uma placa "Vidraçaria Golfinho" logo depois do portão; o corte começa depois dela).
- Nos próximos episódios, suba o `REFORMA x%` e troque o painel DEPOIS pelo progresso real; o episódio final usa o mesmo cartão com o "?" revelado.
