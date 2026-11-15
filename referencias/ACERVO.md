# Acervo de efeitos e guia de decisão

Consolidado das referências:
- **R1** `reels_claude`: tipografia chapada (creme, preto e azul), palavra-herói atrás da cabeça, cartões em tela cheia.
- **R2** `nelmoricalde_meet`: desfoque, vidro, template "Exemplo N", badges, toasts, demo de interface.
- **R3** `nelmoricalde_chatgpt`: objetos na mão, partículas, mockup 3D, card que evolui, bastidor no editor, recap.

Status: ✅ implementado em `pipelines/efeitos/fx.py` · 🟡 parcial · ⬜ catalogado (implementar quando for usado pela primeira vez).

---

## 1. Guia de decisão: o que a fala pede → qual efeito usar

| Quando a fala… | Use | Ref | Status |
|---|---|---|---|
| **Abre o vídeo** (gancho) | Título cinético letra a letra no topo + legenda em 2 camadas | R2/R3 | ✅ `kinetic_title`, `caption2` |
| Tem **uma palavra que é a tese** ("impossível", "dinheiro") | Palavra-herói gigante atrás da cabeça (se houver espaço acima) | R1 | ✅ (compose do reels) |
| **Nega/corrige** algo ("não é sobre dinheiro") | Risco azul na palavra, ou ✕ vermelho sobre um objeto | R1/R3 | ✅ risco · ✅ `strike_x` |
| Cita um **número impressionante** ("4 bilhões", "50%") | Kicker + número gigante amarelo/creme no topo; contador animado em tela cheia, se couber | R1/R3 | 🟡 título ✅ · contador ✅ (reels) |
| Diz **"muita gente / muita coisa"** | Chuva de cartões que converge numa esfera entre as mãos | R3 | ✅ `cards_to_sphere`, `disintegrate` |
| **Enumera** ("primeiro, dois, três") | Badge numérico no canto + contagem nos dedos; se cada item tem exemplo, use o template de lista | R2/R3 | ✅ `number_badge`, `example_template` |
| **Explica como algo funciona** / mostra produto | Interface recriada e animada, sincronizada com a palavra (digitação, itens em cascata) | R2/R3 | 🟡 (cards no reels e no longo) |
| Mostra **resultado num celular/app** | Mockup de celular 3D na mão ou ao lado; troca de tela girando no eixo Y | R3 | ✅ `phone_mockup`, `y_flip` |
| Fala de **um objeto que muda de estado** ao longo da frase | Card que evolui (foto → selo → badge → tira) em vez de trocar de gráfico | R3 | ✅ `evolving_card` |
| Cita **versículo/referência/fonte** | Card de versículo (vidro ou creme) no topo + pessoa em card embaixo (R2), ou painel lateral (16:9) | R1/R2 | ✅ |
| Dá um **aviso / ressalva** | Lista de chips no canto ("1 Em teste…") ou toast com ponto pulsando | R2 | ✅ `chip_list`, `toast` |
| Entra num **bloco de opinião** ("minha aposta") | Etiqueta persistente no canto enquanto durar o bloco | R2 | ✅ `section_tag` |
| **Algo está sendo gerado / processado** | Painel de vidro translúcido sobre o vídeo | R2 | ✅ `glass_panel` |
| Fala de **novidade chegando / lançamento** | Notificação push descendo do topo | R3 | ✅ `push_notification` |
| Usa uma **metáfora** ("a ata acabou") | Objeto ilustrado que sofre a ação (riscado, picotado, quebrado) | R2 | ⬜ |
| Mostra **bastidor / "como foi feito"** | Quadro perde a cor, inclina e recua para dentro de uma interface | R3 | ⬜ |
| **Revela** algo importante | "Plim" + objeto que pipoca (overshoot) ou objeto flutuando sobre a mão | R2 | ✅ `chime`, `object_float` |
| **Muda de assunto** (Reels) | Desfoque → encolher para card (entrar em demo) e o inverso para sair | R2 | ✅ `shrink_to_card` |
| **Muda de assunto** (YouTube) | Cartão de capítulo numerado (tela cheia curta) | R1 | ✅ (pipeline longo) |
| **Recapitula** antes do final | Elementos do vídeo em órbita ao redor da pessoa, com linhas de velocidade | R3 | ✅ `orbit_recap` |
| "Eu **só fiz X**" (contraste antigo × novo) | UI apoiada nas mãos: o antigo riscado em uma, o novo com ✓ na outra | R3 | 🟡 `strike_x` (falta apoiar nas mãos) |
| **CTA** | Título "COMENTA / PALAVRA" + comentário fixado simulado; saída com letras se espalhando | R2/R3 | ✅ `kinetic_title(exit_t)`, `comment_card` |

## 2. Regras de bom gosto (valem para tudo)
1. **Uma ideia visual por vez.** Nunca dois elementos novos entrando no mesmo instante; espaçar ~0,3 s.
2. **Toda entrada sincronizada com a palavra falada.** O elemento chega 1–3 frames antes da palavra.
3. **Reaproveite o objeto** (card que evolui) em vez de empilhar gráficos novos.
4. **Densidade conforme o formato:** Reels, algo novo a cada 0,5–1,5 s; YouTube longo, um elemento de destaque a cada 20–60 s, e o resto do tempo a pessoa limpa na tela.
5. **No máximo 2 cores de acento** por vídeo (ex.: EBO = azul + creme; tech = laranja/amarelo + verde-água).
6. **Legenda nunca sob objetos.** Legenda no peito, UI no terço superior ou nas laterais. Mãos podem passar na frente da legenda.
7. **Easing sempre** (ease-out para entrar, overshoot leve para "pop"). Nada linear.
8. **Respeite o enquadramento:** sem espaço acima da cabeça, nada de título atrás da cabeça. Use o título na frente, no topo, menor.
9. **Conteúdo sério (estudo bíblico):** prefira os efeitos "limpos": legenda em 2 camadas, cards de versículo, badges, vidro, capítulos. Use **com parcimônia** os efeitos de espetáculo (partículas, esfera, órbita): só em ganchos e recapitulações.

## 3. Paletas
| Nome | Uso | Fundo | Acento 1 | Acento 2 | Bordas |
|---|---|---|---|---|---|
| `PAL_EBO` | EBO / conteúdo bíblico | creme #F2EEE6 / escuro #0A0A0E | azul #2B6BFB | creme | branco |
| `PAL_TECH` | tecnologia/IA | azul-marinho #0C0C1C | laranja #E8734A | creme #F3E3B0 | roxo #8460FF |
| `PAL_GOLD` | impacto/números (R3) | quarto desfocado | amarelo-ouro #F5C542 | branco | verde-água #5EE6C8 |

## 4. Aprendizados de produção (por tipo de material)
| Material | O que fazer | Onde |
|---|---|---|
| Vídeo longo 16:9 → Shorts | Recorte 9:16 por segmento, centrado na mediana do rosto (OpenCV a 2 fps); título no espaço de parede acima da cabeça; cards de vidro na parte de baixo; legenda no peito com as mãos na frente | `pipelines/shorts_desenvolve/` |
| Selfie vertical (rosto ocupa o quadro) | Objetos no peito e nas laterais, nunca na altura do rosto; órbita com `front_layer` | `pipelines/efeitos/README.md` |
| Gravação de Meet | Detectar layout (participante vertical vs. câmera principal); participante com fundo desfocado; cortar pedidos pessoais | `pipelines/youtube_longo/` |
| Títulos letra a letra | Corrigido: `kinetic_title` alinha as letras pela linha de base (`text_sprite(ref=...)`); antes as acentuadas desciam | `fx.kinetic_title` |

