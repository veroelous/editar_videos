# Reels elegantes a partir de gravação de Meet (câmera em miniatura)

Para estudos/aulas gravados no Meet em que o slide ocupa a tela e a câmera do autor é uma miniatura (~320x180).

## Estilo (estilo.py): elegante, nada "brega"
- Fundo grafite liso com grão de filme e uma luz dourada muito discreta (sem estrelas, partículas ou neon).
- **Rosto em foco:** recorte só do autor na miniatura, ampliado **x4 com super-resolução** (Real-ESRGAN `realesr-general-x4v3`,
  `sr.py`, roda em onnxruntime, sem PyTorch), numa moldura de cantos suaves com sombra e filete claro. Zoom alterna a cada corte
  (1,16 ↔ 1,34) com aproximação lenta e *punch-in* leve nas palavras de ênfase.
- Tipografia editorial: Inter (texto) + **Instrument Serif** (títulos; itálico dourado como destaque). Uma única cor de acento.
  Marcação: `*trecho*` sai em serifa itálica dourada.
- Legenda em ordem natural; a frase aparece inteira e cada palavra "acende" quando é dita.
- Blocos (lado de baixo): `cover`, `title`, `verse`, `statement`, `list` (com risco fino), `versus`, `counter`, `flow`, `dots`, `lanes`, `hero`, `cta`.
- **Capa = quadro 0**: o bloco `cover` já está completo em t=0 (sem animação pela metade); sai quando termina o gancho.
- Áudio: trilha sintetizada (piano + pad + pulso discreto; progressão e BPM por plano), ducking sob a voz, pausa sem percussão no trecho
  emocional, *swell* no clímax; SFX discretos (whoosh suave, tique, sino). Mix −14 LUFS.
- O Meet troca a miniatura para quem faz barulho: quadros que não são o autor são substituídos pelo último quadro bom (`fixmap`).

## Layout "pip" (padrão quando a câmera é ruim)
`"layout": "pip"` no plano: o rosto vira um quadrinho de 240 px no canto superior direito e os gráficos sobem
para o centro (ampliados), com a legenda logo abaixo. Use sempre que a imagem da câmera for fraca (miniatura do Meet):
o feedback foi que a imagem ampliada ficava ruim; pequena e discreta, os gráficos carregam o vídeo.

## Plano (JSON)
`segs` (transcrições por trecho e seu início no bruto), `spans` [seg, palavra_ini, palavra_fim, bloco], `events` (blocos gráficos com tempos
"w:SEG.I", "e:SEG.I", "b:bloco", "B:bloco", "f:texto@bloco", "F:texto@bloco", "end", com +/-seg), `punch`, `key`, `cta`, `music`
(`prog`, `bpm`, `break`, `swell`). Exemplo: `planos/exemplo_largadas_injustas.json`.

## Passos
1. Transcrição por palavra dos trechos (Parakeet + refine) → `edit/transcripts/segN.json`; rosto na miniatura → `edit/faces_tile.json`.
2. `reel_meet.py plano.json prep` → `events` (confere texto de cada bloco) → `frames t…` (prévia).
3. `lote.sh <pasta_planos> <saida> r1 r2 …` (render em 4 partes + áudio + entrega, um reel após o outro).
