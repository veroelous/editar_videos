# Análise: "Claude no Google Meet" (referência 2)

Fonte: `ref.mp4`, 720×1280 (9:16), 30 fps, 2:17, AAC 48 kHz. Formato: talking head em quarto com luz neon roxa, com **muitas demonstrações de interface recriadas** e um template de lista "Exemplo 1…5".
Imagens: `frames/sheet_0..5.jpg` (1 fps, o vídeo inteiro) e `detail/*.jpg` (10 fps nos momentos-chave). Transcrição: `transcript.txt`.

Diferença para a referência 1 (reels_claude): lá era tipografia gráfica e chapada. Aqui o visual é **"produto/tech premium"**: profundidade, desfoque, vidro, brilho, interface realista. As duas linguagens se combinam bem.

---

## 1. Estrutura (lista numerada com template)

| Tempo | Bloco | Tratamento |
|---|---|---|
| 0–2,3 | Gancho "Tudo que você sempre quis no Google Meet acabou de chegar" | Kicker "ACABOU DE CHEGAR" + título "GOOGLE MEET" digitado letra a letra no topo. Logo do Meet 3D pipoca ao lado |
| 3,5–7,9 | "quem trouxe foi o Claude… melhor atualização até hoje" | **Logo 3D do Claude girando e pousando na palma da mão**, com brilho e raios de luz |
| 7,9–17,6 | "Claude lançou o Claude Meetings. Ele entra na sua chamada…" | **Desfoque → o quadro encolhe para um card →** interface do Meet recriada em fundo azul-marinho. Os tiles entram em cascata, e o tile "Claude" ganha notas ao vivo |
| 19,5–27 | "Primeiro… a ata acabou" | **Badge "1"** laranja pipoca junto com o dedo levantado. Ícone de documento "ATA" é riscado e **picotado em tiras**. Depois entra o template **EXEMPLO 1 · ANOTA SOZINHO** |
| 27–34 | "Dois, você pede em voz alta" | Badge "2" + **chip de voz** (microfone + forma de onda). EXEMPLO 2 · CRONOGRAMA NA HORA (Gantt montando) |
| 34–44 | "Três, brainstorm" | Post-its voando na sala, EXEMPLO 3 · QUADRO BRANCO, loader "Organizing ideas" |
| 44–55 | "Quatro, bateu uma dúvida" | Badge "4" + **"?" 3D** pipocando, EXEMPLO 4 · RESPOSTA NO CHAT (chips de ferramentas: Planilhas, Arquivos, CRM, depois "R$ 18.400") |
| 55–73 | "Cinco… reunião de venda" | Badge "5" (creme), EXEMPLO 5 · OBJEÇÕES ANOTADAS. **Pessoa recortada** em fundo escuro com a caixa de pergunta sendo digitada em cima |
| 73–88 | "Quando a chamada termina…" | DEPOIS DA CHAMADA · MEMÓRIA DA REUNIÃO. **Painel de vidro translúcido** "Claude está criando" sobre o quarto, montando uma apresentação |
| 88–106 | "Alguns avisos importantes" | **Lista de chips** no canto superior direito ("1 Em teste", "2 Só no Google Meet", "3 Team e Enterprise") entrando junto com a contagem nos dedos |
| 106–123 | "Minha aposta…" | Etiqueta **"MINHA APOSTA"** fixa no canto + widget "Claude falando" + balões de fala ("Está caro.") com avatar |
| 123–137 | CTA "Comenta CLAUDE" | "4 cliques" viram **teclas 1-2-3-4** ao redor da cabeça. "COMENTA / CLAUDE" gigante no topo, digitado e depois **letras se espalhando**. **Comentário fixado simulado** ("nelmoricalde · Passo a passo oficial") |

**Arquétipo:** GANCHO (novidade) → O QUE É (demo da interface) → **LISTA DE 5 COM TEMPLATE FIXO** → DEPOIS (bônus) → AVISOS (honestidade) → OPINIÃO ("minha aposta") → CTA de comentário com palavra-chave.

---

## 2. Linguagem visual

- **Cor:** quarto em roxo/azul neon (luz de fundo) e pele quente. Interfaces em **azul-marinho escuro com vinheta roxa**. Acentos em **laranja (#E8734A, cor do Claude)** e **creme/amarelo (#F3E3B0)** nos títulos. Interfaces claras (cards brancos/creme) aparecem só dentro das demos.
- **Tipografia:** grotesca bold arredondada (estilo SF Pro / Inter Display). Títulos de seção em **caixa alta, extra bold, creme**, com **kicker** pequeno espaçado acima ("EXEMPLO 1", "DEPOIS DA CHAMADA", "ACABOU DE CHEGAR").
- **Profundidade:** sombras longas e suaves, brilho nas bordas (glow roxo em volta dos cards), vidro fosco (UI translúcida sobre o vídeo) e **desfoque como transição**.

---

## 3. Catálogo de técnicas novas (com receita)

### 3.1 Legenda em duas camadas, com entrada por desfoque e atrás da pessoa
- **Posição:** no peito, centralizada, entre o queixo e a cintura (~52% da altura).
- **Linha 1:** palavras de ligação, pequenas, brancas, semibold. **Linha 2:** a palavra ou expressão forte, ~1,3× maior, **creme/amarela** e bold ("Tudo que você / **sempre quis**", "chegar e quem / **trouxe foi**").
- **Entrada da palavra:** começa **desfocada** (blur ~8 px, opacidade 40%) e entra em foco em ~4 frames. Na troca de frase, o bloco antigo se desfoca e some enquanto o novo foca (crossfade com desfoque).
- **Atrás das mãos:** a legenda é desenhada *antes* da máscara da pessoa. Quando ele gesticula, **as mãos passam na frente do texto**. Isso dá a sensação de que o texto está no espaço, e não colado na tela.
- Um ícone pequeno (marca) fica embaixo da legenda. Na referência é o logo do editor; no nosso caso seria um logo do canal/EBO, ou nada.

### 3.2 Badge numérico sincronizado com os dedos
- Quadrado arredondado **laranja** (≈110 px a 1080), número branco extra bold, no **canto superior direito**.
- Entra **no frame em que ele levanta o dedo / fala o número**: escala 0,6→1,08→1 em 5 frames, com sombra. Sai com fade quando a seção vira demo.
- Pode ganhar um acessório ao lado: chip de voz, "?" 3D, ícone de documento.

### 3.3 Template de seção "Exemplo N" (o coração do vídeo)
Layout fixo em 9:16 (sobre fundo azul-marinho com vinheta):
- **Topo (0–48%):** card claro com a demo (interface).
- **Base, à esquerda:** a pessoa num **card arredondado com borda roxa brilhante** (picture-in-picture: o vídeo continua rodando ali).
- **Base, à direita:** kicker "EXEMPLO 1" (pequeno, espaçado), título "ANOTA SOZINHO" (creme, extra bold, 2 linhas) e a legenda da fala em linha única pequena, com a palavra-chave em creme.

**Entrada:** 1 frame de **desfoque total** → o quadro inteiro **encolhe** até virar o card da base (~6 frames, ease-out) → o card da demo cai de cima → o título entra com desfoque. **Saída:** a demo fica cinza/translúcida → o card da pessoa **cresce de volta** para tela cheia → desfoque → plano normal.

### 3.4 Interfaces recriadas e animadas (demo de produto)
Grade do Meet, notas ao vivo, Gantt montando barra a barra, post-its, chat com chips de ferramentas, resultado em número grande, card de objeções. **Regra:** cada informação nova entra **sincronizada com a palavra falada**: digitação a ~1 caractere por frame, itens em cascata de 2–3 frames e checks verdes aparecendo.

### 3.5 UI de vidro sobre o vídeo
Painel translúcido (fundo branco a ~15–25% + desfoque do que está atrás + borda clara fina) flutuando sobre o quarto ("Claude está criando…"). A pessoa continua visível através do painel. É ótimo para mostrar "algo sendo gerado" sem cortar para tela cheia.

### 3.6 Toasts, chips e etiquetas flutuantes
- **Toast de gravação:** pílula escura com ponto vermelho ("Claude está transcrevendo esta reunião"), que surge perto da mão.
- **Lista de avisos:** chips empilhados no canto (número em quadradinho creme + título + subtítulo cinza), entrando um a um com a contagem.
- **Etiqueta de seção persistente:** pílula creme "MINHA APOSTA" no canto superior esquerdo, que fica enquanto durar o bloco de opinião.
- **Widget de áudio:** card escuro "Claude falando" com forma de onda animada, mais balões de fala com avatar.

### 3.7 Objeto 3D na palma da mão
O logo aparece pequeno, gira e pousa **sobre a mão aberta** (rastreando a mão), com brilho radial e raios. *Para nós:* dá para fazer com um PNG do objeto, uma posição fixa sobre a mão (marcada no quadro) e um leve "flutuar". O rastreamento automático da mão é opcional.

### 3.8 Metáfora visual animada
"A ata acabou": o documento "ATA" entra inclinado, é **riscado** em vermelho e **picotado em tiras** que caem. Ilustrar a frase com um objeto que sofre uma ação vale mais que um texto.

### 3.9 Título cinético do gancho e do CTA
- Kicker espaçado entra com desfoque. O título é **digitado letra a letra**, e cada letra nasce desfocada e com leve deslocamento (~1 letra a cada 1,5 frame).
- **Saída do CTA:** as letras **se espalham** (cada uma gira e voa numa direção) em ~0,5 s.

### 3.10 CTA "Comenta PALAVRA" com comentário simulado
Título gigante "COMENTA / CLAUDE" no topo e, no peito, um **card de comentário fixado** no estilo Instagram (avatar + @perfil + "agora" + linha com link). Uma segunda linha entra depois. Funciona com automação de DM (comentou a palavra → recebe o link).

### 3.11 Teclas numeradas ("são só 4 cliques")
Quatro **teclas brancas** com números 1–4 aparecem ao redor da cabeça, uma a cada clique falado.

---

## 4. Ritmo e áudio

- **Fala contínua:** nenhum silêncio acima de 120 ms no vídeo inteiro. Os jump cuts mantêm o mesmo enquadramento, então quase não se notam.
- **Elemento novo** a cada ~0,5–1 s. **Troca de layout** (rosto ↔ demo) a cada 5–10 s.
- **Áudio:** −14 LUFS, LRA 3,9 (voz bem comprimida). Há um **"plim" tonal** (acorde agudo) nas revelações importantes (logo na mão, resultados) e whooshes curtos nas transições. Há também um tom contínuo de ~1,4 kHz no fundo do vídeo todo (provável ruído de equipamento). Isso **não** é para copiar.

---

## 5. Como encaixar no nosso trabalho

| Técnica | Reels | YouTube longo |
|---|---|---|
| Legenda em 2 camadas + desfoque + atrás das mãos | **Padrão novo das legendas** | Só nas frases de destaque |
| Badge numérico | Listas ("3 erros", "5 sinais") | Abertura de cada ponto de uma lista |
| Template "Exemplo N" com PiP | Seções de uma lista | **Versículos e demonstrações**: texto/slide em cima, pessoa no card |
| Transição desfoque + encolher card | Entrar e sair de demos | Entrar em cartões de versículo e capítulos |
| UI de vidro | "Algo sendo gerado" | Painéis laterais (substitui o painel creme opaco) |
| Toasts/chips/etiquetas | Avisos, "minha opinião" | Etiqueta de seção persistente ("CONTEXTO", "APLICAÇÃO") |
| Metáfora animada | Gancho | Pontos-chave |
| Título letra a letra + letras espalhando | Gancho e CTA | Abertura e final |
| CTA "Comenta X" + comentário simulado | **CTA padrão** (ex.: "Comenta EBO") | Tela final / Shorts |
| "Plim" nas revelações | Sim | Sim, com mais parcimônia |
