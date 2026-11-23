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
- **Antes de editar, leia `referencias/ACERVO.md`**: é o guia de decisão (qual efeito para cada momento da fala), com regras de bom gosto e paletas. Escolha os efeitos pelo que a fala pede, não por variedade.
- Biblioteca de efeitos: `pipelines/efeitos/fx.py` (ver o README da pasta). Reúne todas as referências.
- **Toda nova referência de vídeo:** analisar em `referencias/<nome>/ANALISE.md`, acrescentar as técnicas novas ao `ACERVO.md` (com status) e implementar no `fx.py` as que forem reaproveitáveis.
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
- **Vídeo-aula (YouTube, bruto já cortado):** pipeline `pipelines/youtube_aula/` — zoom por frase, painel de aula com ícones 3D, frases-chave, capítulos, inscreva-se/curtir animado, card final de 20 s.
- **Pregações (culto no palco), padrão do vídeo "O altar antes dos muros" (culto 18/01/2026):**
  - vídeo longo: `pipelines/youtube_meet/longo_meet.py` com `layout="stage"` (plano de exemplo: `pipelines/youtube_meet/exemplo_build_culto_audio.py`);
  - **não cortar silêncios** (`gap=999`): cortar só conteúdo (conversas paralelas, falas de terceiros, palavrões);
  - fala em **1,15x** (`speed=1.15`, `fps=600/23` → saída a 30 fps);
  - palco em tela cheia como base, zoom suave acompanhando o pregador, painel de vidro do lado oposto, frases e versículos sobre o palco desfocado, capítulos sobreposto, sem trilha (só efeitos), mesma identidade (grafite, Inter + Instrument Serif com itálico dourado);
  - **sincronia:** sempre transcrever o áudio do próprio vídeo-fonte. Se a transcrição veio de outro arquivo, realinhar com `pipelines/youtube_meet/alinha_transcricao.py`;
  - **reels/shorts:** `pipelines/youtube_meet/reel_palco.py` (no máximo 90 s, 1,15x, capa no 1º quadro, legenda sincronizada, CTA "Comenta PALAVRA");
    - escolher **só os trechos com mais potencial de engajamento**: gancho forte nos 3 primeiros segundos, ideia completa sozinha, frase de efeito, contraste, ilustração ou humor;
    - descartar trechos explicativos ou históricos sem aplicação, mesmo que sobrem poucos reels;
    - entregar também título de Shorts e descrição única (Reels e Shorts).
- Paletas: `PAL_EBO` (creme/preto/azul #2B6BFB) para o EBO; `PAL_TECH` (azul-marinho, laranja, creme) para conteúdo de tecnologia.

## Onde ficam as coisas
- `referencias/reels_claude/ANALISE.md`: estilo de edição de referência (reels).
- `referencias/nelmoricalde_meet/ANALISE.md`: estilo "tech premium" (vidro, desfoque, template Exemplo N, badges, CTA de comentário).
- `referencias/nelmoricalde_chatgpt/ANALISE.md`: estilo cinematográfico (objetos na mão, partículas, mockup 3D, card que evolui, bastidor no editor, recap).
- `referencias/ACERVO.md`: **acervo unificado + guia de decisão**.
- `pipelines/efeitos/`: biblioteca de efeitos reutilizável + demo.
- `pipelines/reels_claude_style/`: pipeline de reels vertical.
- `pipelines/youtube_longo/`: pipeline de vídeo longo 16:9 + cortes verticais.
- `pipelines/youtube_aula/`: vídeo-aula 16:9 sem cortes (ritmo, painéis didáticos, ícones).
- `pipelines/reels_meet/`: reel 9:16 a partir de Meet com câmera em miniatura (moldura + super-resolução, trilha e SFX).
- `.claude/skills/youtube/`: skill **claude-youtube** (MIT, AgriciDaniel) — `/youtube thumbnail`, `seo`, `metadata`, `script`, `hook`, `shorts`… Usar `/youtube thumbnail` (+ `references/thumbnail-ctr-guide.md`) para planejar thumbnails e `/youtube metadata` para título/descrição/tags.
- `brutos/`: vídeos brutos e saídas de edição (ignorado pelo git).
