# Regras deste repositório

## Tamanho dos vídeos entregues (regra do usuário, vale para qualquer projeto)
- **Todo vídeo final entregue deve ter no máximo 380 MiB.** O envio de arquivos para o usuário tem limite (já recusou 466 MiB com limite de 400 MiB, e outra vez com 500 MiB). Use 380 MiB como teto, com folga.
- Calcule a taxa de bits **antes** de codificar o produto final, a partir da duração:
  `vídeo_kbps = (380 * 8388.608 / duração_s) - áudio_kbps` (áudio AAC 128 kbps).
  Ex.: 30 min → ~1.600 kbps de vídeo; 10 min → ~5.100 kbps; até ~3 min, CRF 18–20 normalmente já fica abaixo.
- Para vídeos longos use x264 em 2 passes (`-pass 1` / `-pass 2`, `-preset medium`), com `-maxrate` ≈ 2× a taxa e `-bufsize` ≈ 4×.
- Masters intermediários podem ser maiores, mas ficam só em `brutos/` (fora do git) e nunca são o arquivo entregue.
- Confira o tamanho (`ls -l`) antes de enviar. Se passar de 380 MiB, recodifique; não tente enviar.

## Padrões de edição (usar por padrão nas próximas edições)
- Biblioteca de efeitos: `pipelines/efeitos/fx.py` (ver o README da pasta). Combina as duas referências.
- **Reels:**
  - legenda `caption2` (duas camadas, entrada com desfoque), no peito, com as **mãos passando na frente** (`HandMasker`);
  - título do gancho com `kinetic_title`;
  - listas com `number_badge`, seções com `example_template` + `shrink_to_card`;
  - CTA "Comenta PALAVRA" com `kinetic_title` + `comment_card`;
  - "plim" (`chime`) nas revelações.
- **YouTube longo:**
  - painéis laterais podem usar `glass_panel` (vidro) no lugar do painel creme opaco;
  - versículos e demonstrações no layout `example_template` (16:9 adaptado);
  - etiqueta de seção persistente (`section_tag`).
- Paletas: `PAL_EBO` (creme/preto/azul #2B6BFB) para o EBO; `PAL_TECH` (azul-marinho, laranja, creme) para conteúdo de tecnologia.

## Onde ficam as coisas
- `referencias/reels_claude/ANALISE.md`: estilo de edição de referência (reels).
- `referencias/nelmoricalde_meet/ANALISE.md`: estilo "tech premium" (vidro, desfoque, template Exemplo N, badges, CTA de comentário).
- `pipelines/efeitos/`: biblioteca de efeitos reutilizável + demo.
- `pipelines/reels_claude_style/`: pipeline de reels vertical.
- `pipelines/youtube_longo/`: pipeline de vídeo longo 16:9 + cortes verticais.
- `brutos/`: vídeos brutos e saídas de edição (ignorado pelo git).
