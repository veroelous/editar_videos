# Reel viral a partir de gravação de Meet (câmera em miniatura)

Para aulas/estudos gravados no Meet em que o slide ocupa a tela e a câmera do autor é uma miniatura (~320x180).

## Ideia
- **Rosto em foco:** recorta só o autor da miniatura (sem a legenda do nome) e amplia **x4 com super-resolução**
  (Real-ESRGAN `realesr-general-x4v3`, `sr.py`; roda em onnxruntime, sem PyTorch). Vai para uma **moldura**
  arredondada com brilho azul, sobre fundo escuro animado (luzes que passeiam + partículas) que preenche o 9:16.
- **Ritmo:** cada corte alterna zoom (1,12 ↔ 1,32) + aproximação lenta; *punch-in* nas palavras de ênfase;
  pulso/desfoque da moldura na troca de bloco; tremida nos impactos; moldura flutuando; barra de progresso no topo.
- **Elementos na parte de baixo** contam a história, bloco a bloco: título do gancho em linhas + cinético,
  citação riscada com carimbo "NÃO É VERDADE", **pistas de corrida animadas** (largadas diferentes, corredores, chips com ícones 3D),
  "É JUSTO?", card de vidro com a frase-tese, "NÃO VOU PARAR", "o passado explica / Jesus ainda chama",
  "LEVANTA E ANDA" com flash, raios e partículas, CTA "comenta ANDA" + comentário simulado.
- **Legenda** `caption2` (duas camadas) entre a moldura e os gráficos.
- **Áudio:** voz −15 LUFS; trilha sintetizada (100 bpm, Am–F–C–G: pad, arpejo, baixo, bateria) com ducking sob a voz,
  quebra emocional sem bateria no bloco da frase-tese, riser + "drop" no clímax; SFX (whoosh nas trocas, pop nos chips,
  impacto no carimbo e no clímax, plim nas revelações). Mix final −14 LUFS.

## Passos
1. Transcrição por palavra dos trechos (Parakeet + refine) → `edit/transcripts/segN.json`; rosto na miniatura → `edit/faces_tile.json`.
2. Editar `SPANS` (seg, palavra_ini, palavra_fim, bloco) e o roteiro gráfico em `reel_meet.py`.
3. `reel_meet.py prep` → `reel_meet.py frames t…` (prévia) → `reel_meet.py render k 4` (×4 em paralelo)
   → `reel_meet.py audio` → `reel_meet.py pack 4 saida.mp4`.
