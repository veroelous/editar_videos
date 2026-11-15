# Biblioteca de efeitos (`fx.py`)

Consolida as técnicas das duas referências:
- `referencias/reels_claude/ANALISE.md`: tipografia gráfica chapada (creme, preto e azul), palavra-herói atrás da cabeça, cartões em tela cheia, UI falsa.
- `referencias/nelmoricalde_meet/ANALISE.md`: visual "tech premium" com desfoque, vidro, profundidade, template "Exemplo N", badges e toasts.

Demo com as imagens do reels do EBO: `demo_fx.py` (saída em `brutos/demo_fx/demo_fx.mp4`).

## Funções
| # | Função | O que faz | Reels | YouTube |
|---|---|---|---|---|
| 1 | `caption2(...)` | Legenda em duas camadas (ligação em branco, palavra forte maior em creme). Cada palavra entra **desfocada → nítida**; a frase sai desfocando | **padrão** | frases de destaque |
| 2 | `number_badge(...)` | Badge numérico que pipoca (overshoot), sincronizado com a contagem nos dedos | listas | pontos de lista |
| 3 | `toast`, `chip_list`, `section_tag` | Pílula com ponto pulsando; lista de avisos empilhada; etiqueta de seção persistente ("MINHA LEITURA") | sim | sim |
| 4 | `kinetic_title(...)` | Kicker espaçado + título digitado letra a letra com desfoque; `exit_t` espalha as letras | gancho/CTA | abertura/final |
| 5 | `glass_panel(...)` | Painel de vidro fosco sobre o vídeo (desfoca o que está atrás + véu + borda) | "algo sendo gerado" | painel lateral |
| 6 | `shrink_to_card(...)` + `dark_bg(...)` | Transição: desfoque → o quadro encolhe até virar um card (e o inverso com `1-k`) | entrar em demos | entrar em versículos |
| 7 | `example_template(...)` | Layout "Exemplo N": demo em cima, pessoa em card com borda brilhante, kicker + título + legenda curta | seções | versículos/demos |
| 8 | `comment_card`, `keycaps` | Comentário fixado simulado (CTA "Comenta X"); teclas numeradas ao redor do rosto | **CTA padrão** | Shorts |
| 9 | `object_float(...)` | Objeto PNG flutuando com brilho (ex.: logo na palma da mão) | sim | sim |
| 10 | `hand_mask(...)` | Máscara de mãos por cor de pele (rápida, sem modelo). Falha com roupa avermelhada e luz fria; use só como fallback | — | — |
| 11 | `HandMasker(models_dir)` | **Máscara de mãos precisa** (MediaPipe: polígono da mão ∩ "pele do corpo" do segmentador). Use para a legenda ficar **atrás das mãos** sem sumir atrás do tronco | sim | sim |
| — | `chime()` | "Plim" sintetizado para revelações | sim | com parcimônia |

## Ordem das camadas em cada frame
1. Vídeo (ou fundo `dark_bg` nos templates).
2. **Camada "no espaço":** títulos atrás da cabeça e `caption2`.
3. **Oclusão:** `Image.composite(src, frame, máscara)`. A máscara é a pessoa só no topo (para títulos atrás da cabeça) **e** as mãos (`HandMasker`) para a legenda no peito.
4. UI flutuante: badges, toasts, chips, cards, comentário.

## Dependências
`pillow numpy` sempre. Para `HandMasker`:
- `pip install mediapipe` e `apt-get install -y libegl1 libgles2`;
- modelos `hand_landmarker.task` e `selfie_multiclass.tflite` (storage.googleapis.com/mediapipe-models) numa pasta passada em `models_dir`.

## Cuidados aprendidos
- **Pouco espaço acima da cabeça** (selfie no carro): títulos atrás da cabeça ficam ilegíveis. Suba e diminua o título, ou coloque na frente.
- **Legenda atrás da pessoa inteira some** quando o corpo ocupa a parte de baixo do quadro. A oclusão tem que ser **só das mãos**.
- Teste a oclusão num quadro com a mão na frente do peito antes de renderizar tudo (o exemplo está em `referencias/nelmoricalde_meet/teste_oclusao_mao.jpg`).
