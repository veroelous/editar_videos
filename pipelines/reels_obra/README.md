# Pipeline "Diário da Reforma" (reels de obra/antes e depois, vídeo SEM fala)

Usado no EP.01 da G2B Esquadrias e Vidros ("O antes"): passeio pela sede no início da reforma, com o objetivo de fazer os seguidores acompanharem a evolução.

| Ordem | Script | O que faz |
|---|---|---|
| 0 | `ffmpeg -i raw.mp4 -vf "eq=contrast=1.07:saturation=1.18:brightness=0.01,unsharp=5:5:0.6" -q:v 2 src/%05d.jpg` | Extrai os frames do bruto já gradeados (`PROJ/src/`) |
| 1 | `render.sh` | Ambiente remontado por segmento (atempo) → `audio.py` (trilha 120 bpm + SFX) → `compose.py` em paralelo → encode com loudnorm −14 LUFS |

Rodar (a partir da raiz): `PROJ=brutos/g2b EP=g2b_ep01 bash pipelines/reels_obra/render.sh`. Saída: `PROJ/final.mp4` (1080x1920, 30 fps).

## Episódios (`episodios/<EP>.py`)
Cada episódio é só um roteiro; o compositor é o mesmo. Para um episódio novo: copie o anterior, crie `brutos/<proj>/` com `raw.mp4`, `logo/1.png` (logo branco) e `src/` (passo 0), e ajuste:
- `SEGS` — trechos; um 8º item `dict(src=..., a=(ini, fim), wipe=(t, dur), ly=y)` vira **comparativo ANTES|AGORA** com divisória (o ANTES vem dos frames do episódio anterior, no mesmo ponto da sede);
- `PHRASES`, `HOOK_*`, `TOAST_TXT`, `TAG_TXT`, capa (`EP_LABEL`, `COVER_*`), `OUTRO_TXT`;
- `PILL` / `END_PCT` — a porcentagem da reforma **continua de onde o episódio anterior parou** (`END_PCT[1]`), e `END_NOTE` mostra o ganho ("+2% desde o EP. 01").

| EP | Tema | Reforma | Destaques |
|---|---|---|---|
| 01 | O antes | 0 → 5% | gancho "O ANTES", cartão ANTES/DEPOIS |
| 02 | A demolição | 5 → 7% | 2 comparativos (corredor e entrada da oficina), telhado e forro retirados |

## O que muda de um episódio para outro (`compose.py`)
- `SEGS`: trechos do bruto, com zoom (Ken Burns) e a transição de entrada (`whip_x`, `whip_y`, `zoom`, `leak`). Cortes nas batidas (múltiplos de 0,5 s).
- `PHRASES`: a copy das legendas (linha de ligação branca + linha forte amarela). Sem fala, o texto é escrito.
- Gancho (`kinetic_title` "O ANTES"), etiqueta `EP. 0X`, pílula de progresso `REFORMA x%`, fita "EM OBRAS" (`tape`) e o cartão final ANTES | DEPOIS com o "?" e o CTA "SIGA A G2B".
- Paleta: amarelo de obra #F5C542 + branco sobre azul-marinho.

## Cuidados
- Confira se o bruto mostra **marca de outra empresa** (no EP.01 havia uma placa "Vidraçaria Golfinho" logo depois do portão; o corte começa depois dela).
- Nos próximos episódios, suba o `REFORMA x%` e troque o painel DEPOIS pelo progresso real; o episódio final usa o mesmo cartão com o "?" revelado.

## Reels de portfólio (trabalho concluído) — `portfolio.py`
Mesma identidade (paleta, logo, legenda, transições), outra estrutura: **capa → gancho → destaques do produto (cartões com ✓) → detalhe (zoom com foco) → CTA "comenta EU QUERO"** com comentário simulado sendo digitado. Trilha em tom maior (`portfolio_audio.py`, C G Am F + sino de "vidro").
Roteiro em `trabalhos/<JOB>.py`. Rodar:
`PROJ=brutos/g2b_pergolado JOB=g2b_pergolado MOD=portfolio AUD=portfolio_audio bash pipelines/reels_obra/render.sh`

Módulos comuns: `visual.py` (paleta G2B, logo, enquadramento, transições, grade azul) e `synth.py` (instrumentos e SFX).
