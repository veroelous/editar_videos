## Session 1 — 2026-11-14

**Strategy:** Aplicar o estilo do `referencias/reels_claude` (ver ANALISE.md) no bruto "reels claude 2.mp4" (selfie no carro, 72 s, convite para o EBO, Estudo Bíblico Online). Versão enxuta (~46 s) com a paleta da referência: creme #F2EEE6, preto #111 e azul #2B6BFB.

**Decisions:**
- Transcrição local com Parakeet TDT 0.6B v3 (sherpa-onnx; o modelo veio do GitHub porque o Hugging Face está bloqueado) com timestamps por token. Inícios e fins das palavras refinados por energia (−38 dB), porque o ASR adianta até 0,35 s a primeira palavra depois de uma pausa.
- Removidos: "Pois é, eu também", o tropeço "tá? / e nem", "Não importa se você é de alguma igreja", "Fica aí o convite", "Bora? … É só digitar EBO", "Vamos lá,".
- Voz acelerada 1,1× (atempo) para chegar a ~45 s. Pausas ≥0,15 s removidas, padding de 50/70 ms e fades de 30 ms.
- Punch-in de 115 % em "o assunto é bem mais profundo" e "Quer participar?".
- Palavra-herói atrás da cabeça (máscara rembg u2net_human_seg por frame), posicionada pela oclusão real (≤30 % da palavra coberta). Quando não cabe, a legenda sai e a palavra assume o topo. Se ainda não couber, a palavra vai para o peito, na frente.
- Cartões em tela cheia: versículo (Gálatas 6:7), lista riscada (dinheiro/prosperidade/castigo/recompensa), evento (quinta-feira 20h, online), EBO em blocos de letra, final `{ te espero lá }` + botão "manda EBO na DM →".
- UI falsa: card do leitor bíblico (Gálatas 6, versículos 7–9 ARC) e caixa de mensagem digitando "EBO" com bolha "Enviado ✓".
- Áudio: highpass, afftdn, compressor, loudnorm −14 LUFS. SFX sintetizados (whoosh, pop, click, riser) e pad leve só no CTA.

**Reasoning log:**
- A cabeça fica muito perto do topo (topo a ~110–260 px), então a legenda no topo e a palavra-herói competem pelo espaço. Por isso a legenda some enquanto a palavra está ativa.
- O concat da primeira versão acumulou 0,6 s de drift (o áudio de cada segmento ficava 10–45 ms mais curto que o vídeo). Corrigido com `-frames:v N` + `apad,atrim` no tamanho exato do vídeo.

**Outstanding:**
- Música real no CTA, se o usuário enviar uma faixa.
- Revisão do usuário sobre o corte (1,1× e trechos removidos).
