# Análise: "reels_claude": técnicas de edição para replicar

Fonte: `reels_claude.mp4`, 720×1280 (9:16), 30 fps, 29,4 s, H.264 + AAC 44,1 kHz.
Formato: talking head (criador sentado, fundo de parede creme) com **motion design tipográfico pesado** por cima.
Tese do vídeo: "esse vídeo foi editado por IA". A própria edição serve de prova: cada tipo de elemento gráfico aparece *enquanto* é citado.

Imagens de referência nesta pasta:
- `frames/sheet_0..4.png`: contact sheet a 2 fps (o vídeo inteiro em 5 imagens)
- `detail/*.png`: tiras a 10 fps de cada momento-chave, e `detail/x_cut*.png` com os cortes frame a frame (30 fps)
- `detail/spectrum.png`, `detail/spec_end.png`: espectrograma do áudio

---

## 1. Estrutura narrativa (o esqueleto)

| Tempo | Beat | Fala (reconstruída das legendas) | O que a tela faz |
|---|---|---|---|
| 0,0–2,1 | **HOOK** | "esse vídeo foi editado por IA" | Legenda progressiva + "editado" gigante **atrás da cabeça** + "por \|IA" com cursor de texto |
| 2,1–4,1 | **PROMESSA** | "cada legenda, número, gráfico… quer ver?" | Moldura `{ legenda, número, gráfico }` (os itens entram um por um) → caixa de chat de IA digitando "quer ver?" |
| 4,1–6,4 | **PROVA 1: número** | (faturamento) | Tela cheia creme, contador 0 → 10.000 → 100.000 → 1.000.000 |
| 6,4–7,4 | **PROVA 2: UI** | (seguidores) | Card de perfil estilo Instagram sobe; seguidores contam 1,2 mil → 98,4 mil; botão "Seguir" vira "Seguindo ✓" |
| 7,4–8,8 | **PROVA 3: gráfico** | "explodindo" | Tela escura, barras crescem 16 → 30 → 47 → 70 → 100 %, título com sublinhado ondulado |
| 8,8–10,4 | **VIRADA** | "a palavra é impossível" | "impossível" gigante atrás da cabeça, depois **riscado** por um traço azul |
| 10,4–12,4 | **REVELAÇÃO** | "eu não abri nenhum programa, eu só falei." | **Punch-in** (~115 %), legenda à esquerda com "faíscas", `{ eu só falei. }` |
| 12,4–14,5 | **INSIGHT** | "é por isso que qualquer criador consegue fazer isso hoje." | "criador" gigante + sublinhado reto azul + anotação lateral empilhada ("consegue / fazer isso / **hoje.**") |
| 14,5–17,9 | **REENQUADRE** | "você não precisa mais saber editar… você precisa saber o que quer mostr–" | "editar" com caixa azul → **apagado letra por letra** (backspace). "most…" em blocos de letras, cortado no meio da palavra |
| 17,9–19,0 | **TESE** | "a ideia sempre foi sua" | Cartão azul em tela cheia `← { a ideia sempre foi sua } →` |
| 19,0–21,0 | **TESE (parte 2)** | "agora o vídeo também é." | "vídeo" com caixa azul + "também é." em azul |
| 21,0–23,2 | **VISÃO** | "então acho que vai ser uma revolução pra galera que quer começar a criar conteúdo" | Parede cinética "revolução revolução" → sujeito recortado na frente de um **carrossel 3D de vídeos**, pílula "começar" → "criar conteúdo" |
| 23,2–25,9 | **VISÃO (parte 2)** | "porque vai ter muitas formas dinâmicas de você criar agora." | "dinâmicas" + sublinhado, "criar" atrás da cabeça, "agora." **estampado na camiseta** com caixa azul |
| 25,9–29,4 | **CTA** | "Por que não você?" | Cartão creme `← { Por que não você? } →` + botão azul "me segue para mais →" com alças de seleção (estilo Figma) |

**Arquétipo para copiar:** HOOK meta → PROMESSA → 3 PROVAS rápidas → VIRADA (quebrar uma crença) → INSIGHT → TESE em cartão → VISÃO → CTA em pergunta.
São 14 beats em 29 s, cerca de **2 s por beat**.

---

## 2. Ritmo e corte

- **Jump cuts sem respiro.** O nível mínimo do áudio durante a fala nunca cai abaixo de −40 dB: todas as pausas foram removidas. Na prática, uma palavra termina e a próxima começa.
- **Cerca de 16 planos em 29 s**, média de **1,8 s por plano**. Algum elemento gráfico novo surge a cada **0,3–0,5 s** (cada palavra da legenda conta).
- **Cutaways em tela cheia a cada 3–5 s** (4,1 / 7,4 / 17,9 / 21,0 / 22,2 / 25,9 s) quebram o padrão visual. **A voz continua por cima** de todos eles: o áudio nunca é cortado, só a imagem.
- **Punch-in de ênfase.** Em 10,4–12,4 s o rosto fica cerca de 15 % maior ("eu não abri nenhum programa"). Ele volta ao enquadramento aberto no corte seguinte. Use punch-in só na frase mais importante do trecho.
- **Glitch de 1 frame num jump cut** (2,13 s, ver `detail/x_cut2.png`): um único frame com a faixa superior repetida verticalmente (um "slide" vertical com tiling e blur) esconde o pulo de enquadramento.
- **Higiene de texto no corte.** O texto antigo some **no frame exato do corte**, e o novo aparece **1–2 frames depois** (ver `detail/x_cut10.png`). Nunca sobra texto velho sobre imagem nova.
- **Palavra interrompida como transição.** "você precisa saber o que quer mostr–" é cortado no meio da palavra direto para o cartão azul "a ideia sempre foi sua". O gráfico completa o pensamento.

---

## 3. Sistema visual (design tokens)

```json
{
  "canvas": "1080x1920 @30fps (o original está em 720x1280; multiplique as medidas por 1,5)",
  "cores": {
    "creme_fundo":   "#F2EEE6",
    "tinta":         "#111111",
    "azul_acento":   "#2B6BFB",
    "escuro_fundo":  "#0A0A0E",
    "azul_marinho":  "#1A3278",
    "cinza_entrada": "rgba(17,17,17,0.40)"
  },
  "fonte": "grotesca neo-geométrica (Inter / Inter Display / SF Pro Display)",
  "legenda":       { "peso": 600, "tamanho_1080": 32, "tracking": "-0.01em", "y": "~5% do topo", "alinhamento": "esquerda ou centro" },
  "palavra_heroi": { "peso": 800, "tamanho_1080": 140, "tracking": "-0.045em", "y": "~10% do topo, atrás da cabeça" },
  "anotacao":      { "peso": 600, "tamanho_1080": 22, "cor": "tinta, e a palavra-chave final em azul" },
  "cards_ui":      { "raio": 24, "fundo": "#FFFFFF", "sombra": "0 8px 30px rgba(0,0,0,.12)" }
}
```

Regras do sistema:
- **Uma cor de acento só (azul).** Todo o resto é preto, branco ou creme. Azul = "isso é importante".
- **Três fundos de cartão**, todos com uma grade sutil de linhas finas a ~4 % de opacidade: creme (neutro), azul (tese) e escuro (dados ou energia).
- Estética de **interface e ferramenta de design**: chaves de código `{ }`, cursor de texto, caixa de prompt, alças de seleção do Figma, card de rede social. Isso reforça o tema "IA / software".

---

## 4. Catálogo de elementos gráficos, com receita de cada um

> Tempos de animação medidos frame a frame. Easing é sempre cubic-out ou com leve overshoot, nunca linear.

### 4.1 Legenda progressiva (a base de tudo)
- Palavra por palavra, sincronizada com o timestamp de cada palavra. A frase vai crescendo na linha.
- **A palavra nova nasce cinza (~40 %) e chega ao preto em ~100 ms** (3 frames). É sutil, mas dá vida ao texto.
- Tamanho pequeno no topo da tela; nunca cobre o rosto. A linha é **limpa por frase** ou no corte, nunca rola.
- Quebra para 2 linhas quando a frase passa de ~60 % da largura ("eu não abri / nenhum programa,").
- **Receita:** transcrição word-level (Scribe) → para cada palavra, `start` = início da palavra − 30 ms. Desenhe a frase até a palavra *i* e aplique opacidade 0,4 → 1 em 3 frames na palavra *i*.

### 4.2 Palavra-herói atrás do sujeito (a assinatura do vídeo)
- Uma palavra por frase, em tamanho gigante e preto, ocupando a largura entre o topo e a cabeça. **O cabelo e a cabeça passam por cima das letras** (editado, impossível, criador, vídeo, dinâmicas, criar). O mesmo vale para "agora." estampado no peito, encoberto pela luva.
- Entrada: fade cinza → preto em ~3–4 frames, com leve escala 0,96 → 1. Saída: some no corte.
- **Receita (ordem das camadas):** `vídeo` → `palavra-herói` → `máscara do sujeito (só a pessoa recortada)` → `legenda/UI`.
  A máscara sai de segmentação por frame (rembg / MediaPipe Selfie Segmentation / RobustVideoMatting). No CapCut: "Remover fundo" num clipe duplicado acima do texto. No After Effects: Roto Brush.

### 4.3 Decorações de palavra-chave (sempre em azul)
| Decoração | Onde aparece | Como anima |
|---|---|---|
| Sublinhado reto | criador, dinâmicas | Desenha da esquerda para a direita em ~6 frames, começando ~0,2 s depois da palavra |
| Sublinhado ondulado | explodindo | Path em onda, desenhado da esquerda para a direita |
| Risco (strikethrough) | impossível | Traço grosso de marcador, levemente diagonal (sobe para a direita), cresce da esquerda para a direita em ~4 frames e passa das bordas da palavra |
| Caixa de destaque | vídeo, editar, agora. | Retângulo azul varre da esquerda para a direita **por trás** do texto, que inverte para branco. A caixa ganha alças de seleção nos cantos |
| Backspace | editar → edit → (vazio) | As letras somem da direita para a esquerda, ~1 letra a cada 2 frames |
| Tiles de letra | m-o-s-t-r | Cada letra num quadrado azul com texto branco, entrando como máquina de escrever, ~1 letra a cada 2 frames |
| Cursor de texto | por \|IA | Caret azul piscando antes da palavra digitada |
| "Faíscas" | eu não abri, dinâmicas | 3 traços curtos azuis irradiando de um canto, como um "pow" mínimo, marcando a frase de ênfase |

### 4.4 Moldura de chaves `← { texto } →`
- Usada para **frases-tese** (eu só falei., a ideia sempre foi sua, Por que não você?, e a lista legenda, número, gráfico).
- Sequência: as chaves `{ }` surgem já na largura final com um ponto acima de cada uma; em ~2 frames as setas `←` e `→` deslizam para fora; o texto é digitado dentro, palavra por palavra (palavra nova em cinza → cor final).
- As chaves e setas são azuis sobre fundo claro, ou brancas sobre fundo azul.

### 4.5 UI falsa
- **Caixa de prompt de IA:** pílula branca com sombra, caret azul e botão circular azul com ↑. O texto é digitado a ~1 caractere por frame ("quer ver?").
- **Card de perfil:** avatar, posts / **seguidores (em azul)** / seguindo, e botão azul "Seguir". Entra **de baixo, girado ~5°, com spring** até ficar reto em ~0,3 s. Os seguidores contam com easing (1,2 mil → 98,4 mil), e no fim o botão troca para cinza "Seguindo ✓".
- **Pílula-rótulo** ("começar" → "criar conteúdo"): o texto troca exatamente na palavra falada.

### 4.6 Contador de número em tela cheia
- Fundo creme, rótulo pequeno "• faturamento em R$" (bolinha azul) e o número gigante abaixo.
- Contagem **em degraus**: 0 → 10.000 (para) → 100.000 (para) → 1.000.000. Cada subida leva ~0,25 s com **motion blur vertical nos dígitos**; cada parada dura ~0,4 s.
- Formato brasileiro com ponto como separador de milhar. Sincronize cada parada com a palavra falada.

### 4.7 Gráfico de barras
- Fundo escuro com grade sutil. Título branco grande que entra cinza → branco, seguido do sublinhado ondulado.
- Barras azul-marinho crescem **em cascata** (stagger de ~2 frames), com a borda superior em degradê durante o crescimento. A última barra é **azul vivo** (o "100 %"). Os rótulos de % ficam acima de cada barra.

### 4.8 Parede de palavra cinética
- "revolução revolução" repetido em 9 linhas. A linha central é a maior e branca; as linhas vão diminuindo e ficando cinza em direção às bordas, num efeito de cilindro ou olho de peixe.
- Entrada: **escala a partir de um ponto** (≈5 % → 100 % em ~0,3 s, cubic-out). Depois, drift vertical lento.
- A legenda continua em micro-rótulos com bolinha azul ("• pra galera" no topo à esquerda, "• que quer" embaixo à direita), então a narração nunca fica sem texto.

### 4.9 Sujeito recortado em frente a um carrossel 3D
- Fundo trocado por escuro. Atrás do sujeito, uma parede curva de miniaturas de vídeo em perspectiva (um cilindro), com os painéis virando para dentro.
- A pílula azul no topo muda o rótulo conforme a fala.

### 4.10 Cartão final (CTA)
- Fundo creme, frase em `{ }`, e um botão azul "me segue para mais →" que **pipoca** (escala 0 → 1,08 → 1 em ~4 frames) com bounding box e alças de seleção do Figma.
- O cartão fica parado ~2,5 s para dar tempo de ler e seguir.

---

## 5. Áudio

- **Voz seca e comprimida:** −14,1 LUFS integrado (o padrão de Reels/TikTok), LRA de 4,4 LU (bem comprimida, volume constante).
- **Sem trilha durante a fala.** O espectrograma mostra só voz até 25,9 s, com transientes curtos nos cortes (cliques e whooshes discretos).
- **Final:** um **riser** (tom subindo de ~200 → 1500 Hz em ~0,5 s) leva ao cartão de CTA; daí entra um **loop musical leve** (pulsos tonais a cada ~0,27 s, ≈113 BPM) e um **"pop" com pitch descendo** (1600 → 400 Hz) no exato frame em que o botão aparece (≈27,1 s).
- **Regra para copiar:** trilha só no CTA, e um SFX para cada evento visual grande (entrada de card, pop de botão, troca para tela cheia).

---

## 6. Como replicar em outro vídeo (passo a passo com a skill video-use)

1. **Gravação:** talking head vertical, fundo liso e claro (com espaço vazio acima da cabeça para a palavra-herói), luz frontal suave, roupa escura que contraste com o fundo, para que a máscara do sujeito saia limpa.
2. **Transcrição word-level** (`helpers/transcribe.py`, que precisa de `ELEVENLABS_API_KEY`). Todo o timing das legendas e gráficos sai daí.
3. **Corte:** remova todas as pausas acima de ~150 ms (padding de 30–50 ms, porque o ritmo é rápido). Escolha um trecho para punch-in de 115 %.
4. **Roteiro gráfico:** para cada frase, decida (a) a palavra-herói, (b) a decoração dela, (c) se o momento vira cutaway em tela cheia. Mire em **um cutaway a cada 3–5 s** e **uma palavra-herói a cada ~2 s**.
5. **Máscara do sujeito** (rembg ou MediaPipe por frame → PNG com alpha, ou WebM com alpha) para o efeito de texto atrás da cabeça.
6. **Animações:** HyperFrames (HTML/CSS/GSAP) é o motor ideal para este estilo, porque tudo aqui é tipografia e UI. Renderize cada slot como WebM transparente. Os cartões em tela cheia saem como MP4 normal.
7. **Composição** (ordem obrigatória): vídeo base → palavras-herói → máscara do sujeito → UI e decorações → **legenda por último**.
8. **Áudio:** normalize a voz para −14 LUFS, adicione SFX nos eventos e coloque riser + música só no CTA.

### Checklist de "parece com o reels_claude"
- [ ] Nenhuma pausa audível; algo novo na tela a cada ≤0,5 s
- [ ] Só uma cor de acento (azul `#2B6BFB`) sobre creme, preto e branco
- [ ] Palavra-herói gigante **atrás** da cabeça em quase toda frase falada para a câmera
- [ ] Legenda pequena no topo, palavra por palavra, com a palavra nova nascendo cinza
- [ ] 3+ cutaways em tela cheia (número, gráfico, frase-tese)
- [ ] Pelo menos um elemento de UI falsa ligado ao tema do vídeo
- [ ] Moldura `{ }` nas frases-tese
- [ ] CTA em forma de pergunta + botão que pipoca + pop SFX
