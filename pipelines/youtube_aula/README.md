# Vídeo-aula 16:9 para YouTube (sem cortes, com "cara de aula")

Para brutos que o próprio autor já cortou: não corta nada, só dá ritmo e didática.

## Passos
1. Transcrição com tempos por palavra → `edit/transcripts/bruto.json` (pipeline `reels_claude_style/asr.py` + `refine.py`).
2. Rosto a 2 fps → `edit/faces.json` (`[t, cx, cy, w, top]`, normalizado).
3. Ícones (Fluent 3D Emoji, MIT, 256 px) → `edit/icons/<nome>.png`.
4. Base acelerada (fala 1,15x):
   `ffmpeg -i bruto.mp4 -vf "setpts=PTS/1.15,fps=30" -af atempo=1.15 -c:v libx264 -crf 15 -g 30 -c:a pcm_s16le edit/base_fast.mov`
5. Roteiro gráfico: editar a seção "roteiro gráfico" de `aula.py` (eventos ancorados em palavras com `find(texto, i_min, i_max)`).
6. Prévia: `aula.py frames <pasta> t1 t2 ...` (JPGs) · lista: `aula.py events` (também grava `edit/events.json`).
7. Render em 4 partes: `aula.py <k> 4 parts/p<k>.mp4` (k = 0..3, em paralelo; ~3,5 s de CPU por s de vídeo).
8. Áudio: `audio_aula.py` (voz -14 LUFS + SFX nos eventos + pad no card final).
9. Legendas e capítulos: `srt_aula.py`.
10. Entrega ≤ 380 MiB: concat das partes + áudio, x264 2 passes (taxa pela regra do CLAUDE.md).

## Linguagem visual
- **Zoom por frase (ritmo):** alterna plano aberto (1,0) e médio (1,14) a cada ~7 s de fala, transição suave de 0,7 s;
  *punch-in* rápido (1,30 em 0,22 s) em frases curtas e enfáticas (pergunta, "grava isso", "presta atenção"…), e volta.
  O enquadramento segue o rosto suavizado.
- **Painel de aula (split):** a pessoa encolhe para um card arredondado à direita; à esquerda, painel escuro de vidro
  com título + itens que entram sincronizados com a fala (linhas com ícone, numeradas, chips, balões de conversa, diagrama A→B).
  Painéis seguidos se emendam sem voltar à tela cheia.
- **Capítulo:** tela desfoca, número grande azul + "CAPÍTULO" + título; etiqueta de seção persistente no canto.
- **Frase-chave:** card de vidro embaixo, linha branca + linha dourada, com plim.
- **Ícone pop:** emoji 3D com brilho e rótulo, ao lado do rosto, em metáforas ("apagando incêndio", "cabeça de dono").
- **Títulos cinéticos** (gancho, virada, fechamento) na parte de baixo sobre degradê, para não cobrir o rosto.
- **Inscreva-se:** botão vermelho com cursor que clica → "Inscrito ✓" + sino balançando + joia. Pequeno no início, grande no pedido.
- **Comentário** fixado simulado (CTA de pergunta) e **card final** de 20 s com o lado direito livre para a tela final do YouTube.
