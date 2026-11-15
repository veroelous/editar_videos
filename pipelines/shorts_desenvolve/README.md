# Shorts verticais a partir de vídeo longo 16:9 (talking head)

Usado no vídeo "Por que você diz SIM quando queria dizer NÃO?" (Desenvolve Mais, 27 min → 6 Shorts de 30–55 s).

## Fluxo
1. **Transcrição** palavra por palavra: `../reels_claude_style/asr.py` + `refine.py` → `edit/transcripts/bruto.json`.
2. **Rosto a 2 fps** (OpenCV Haar, `opencv-python-headless<5`) → `edit/faces.json`. O recorte 9:16 (608×1080 → 1080×1920) de cada segmento é centrado na mediana do rosto daquele trecho.
3. **Escolha dos trechos:** ler `takes_packed.md` e montar `shorts_plan.json` (ver `exemplo_shorts_plan.json`):
   - `spans`: intervalos de índices de palavras (podem vir de partes diferentes do vídeo, na ordem que contar melhor a história);
   - `kicker`/`hero`: título do gancho; `tag`: etiqueta persistente do tema;
   - `cards`: frase-chave num card de vidro (`at`/`ate` = índices de palavra, ou `dur`);
   - `badges`: números 1-2-3 sincronizados com a contagem.
4. `shorts.py <id>` corta (pausas > 0,35 s comprimidas), trata o áudio (−14 LUFS), compõe com `fx.py` e entrega em `brutos/desenvolve/shorts/`.

## Critérios para escolher trechos (o que funcionou)
- **Começar com um gancho que se sustenta sozinho:** pergunta ("Restaurante vazio ou cheio?"), história curta (síndico, degustação, festa de aniversário) ou frase forte.
- **Uma ideia por Short**, fechando com a frase-chave ou uma pergunta prática.
- **Remontar fora de ordem** é válido: história → lição → pergunta (Short do síndico).
- Duração-alvo de 40–55 s (limite de 59 s), com 2,4 s de CTA no fim.

## Desempenho
~19 min por Short de 40 s num núcleo (MediaPipe + desfoques). Rode os Shorts em paralelo (um processo por Short). A detecção das mãos em meia resolução acelera bastante.
