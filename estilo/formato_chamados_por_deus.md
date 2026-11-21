# Formato — canal "Chamados por Deus"

Referência: "A Raiz Oculta do Mal Que Ignoramos | Pr. Zé Bruno"
(youtube.com/watch?v=OnO7TwvtPB4). Base de edição: `estilo/referencia_somente_a_graca.md`
(hook em P&B → ponte → contagem → pregação com legenda amarela → encerramento). Abaixo, o
que muda neste canal.

## Estrutura medida no vídeo de referência (arquivo final, 40:28)

| Tempo | Bloco | Detalhes |
|---|---|---|
| 0:00–1:13 | **Hook** (~72 s) | Em **P&B**. Música `intro_suspense.mp3` desde 0:00 (confirmado por correlação de áudio). Usa um trecho quase contínuo da pregação (~6:02–6:50: "você não é mal porque tem um demônio, é mal porque é mal… nascemos na ausência de Deus…") e fecha com uma frase de outro ponto (~14:09: "todos nós temos violência dentro de nós"). Termina numa **afirmação forte**, não numa pergunta. Tem flashes de bokeh/corações brancos em ~0:29 e ~0:58 |
| 0:02–0:59 | **Título do tema na tela** | "ONDE O MAL COMEÇA": fonte condensada e grossa amarela, contorno preto, brilho em degradê quente atrás. Fica centralizado a ~40% da altura, por cima do hook, com entrada glitch |
| 0:07–0:17 | **Inscreva-se #1** (já dentro do hook) | Clipe de tela verde em **50% de escala**, centralizado na horizontal, com o elemento a ~58% da altura (acima da legenda) |
| 1:13–1:27 | **Ponte** | Bokeh → **apresentador de IA** (homem numa sala, falando para a câmera) dizendo o resumo da tese + "Assista até o final e se inscreva no canal". Música `intro_fala_chamados.mp3` entrando em 1:13,5 |
| 1:27–1:30 | **Contagem estilo película** | "2, 1, 0" em branco sobre fundo cinza com círculo e mira (crosshair) e varredura, com a fala do pregador ("eu quero ler com você Gênesis 4…") já rolando por baixo |
| 1:30–40:20 | **Pregação** | Colorida, legenda amarela, versículos em tela cheia mantidos. Começa direto na leitura bíblica |
| 9:55 · 20:25 · 30:45 | **Inscreva-se #2–#4** | Mesmo clipe e posição, **a cada ~10 min** |
| 40:20–40:28 | **Despedida** | `despedida.mp4` logo após a última frase ("graças a Deus"). A oração final foi cortada |

- **Logo** "Chamados por Deus" no canto superior esquerdo, ~95 px a 720p (~140 px a 1080p), o vídeo inteiro.
- **Legenda:** amarela, Montserrat Medium, ~42 px de altura de maiúscula a 1080p, base a ~86% da altura, 1–2 linhas, palavras de ênfase em CAIXA ALTA ("EU sou mal").
- Não há narração de "curta e compartilhe" no fim; a despedida cumpre esse papel.

## Kit do canal (`projetos/kit_canal/`, fora do Git)

| Arquivo | O que é | Uso |
|---|---|---|
| `intro_fala_chamados.mp3` | Música, 1:53, sem voz | Fundo da ponte (apresentador), a partir do fim do hook |
| `logo_chamados_por_deus.png` | Medalhão CD, 940×788 RGBA | Canto superior esquerdo, o vídeo todo |
| `intro_suspense.mp3` | Música de tensão, 87 s, -15 LUFS, sem voz | Fundo do **hook**, entrando já no começo. Deixar a ~-24 LUFS sob a voz (~-9 dB) e dar fade-out na transição para a ponte |
| `inscreva_se_greenscreen.mp4` | Tela verde 4K, 10 s, com efeitos sonoros: LIKE (0–2,4 s) → INSCREVA-SE (3–4,7 s) → ATIVA AS NOTIFICAÇÕES (5,3–8,3 s) | Recorte: `chromakey=0x31FE00:0.18:0.08,despill=type=green` (em yuva444p). Escala ~55%, centralizado acima da legenda. **Duas vezes:** no 1º minuto da pregação (logo depois do hook/contagem) e de 4 a 5 min antes do fim |
| `despedida.mp4` | 7,9 s, 720p: família na vinha → Bíblia brilhando. Narração: "Obrigada por assistir mais uma transmissão do canal Chamados por Deus. Até a próxima!" | Última cena do vídeo |

## Título (padrão)

`<Afirmação-mistério> | Pr. Zé Bruno`
Ex.: "A Raiz Oculta do Mal Que Ignoramos". Usa curiosidade ("oculta") e acusa o
espectador ("que ignoramos"). O nome do pregador fica no fim, para a busca.

## Thumbnail (padrão)

- 1280×720. Fundo escuro e desfocado, com um **raio de luz dourada vindo de cima** e
  **faíscas/brasas laranja**.
- Pregador **em close à direita** (~45% da largura), olhando para a câmera, expressão
  séria/pensativa (mão no queixo), pele retocada e contraste alto.
- Texto à esquerda em **2 linhas**, fonte condensada e grossa (estilo Bebas/Anton):
  - linha 1, em branco envelhecido com sombra: a crença que vai ser negada ("NÃO É O DIABO!")
  - linha 2, em dourado/fogo com textura metálica: a revelação ("ESTÁ EM NÓS")
- O texto **complementa** o título, não repete.
- Paleta: preto, dourado, laranja e branco.

## Descrição do YouTube

Ainda falta a descrição original da referência (o YouTube bloqueou a leitura a partir do
servidor). Até lá, use esta estrutura padrão de SEO:
1. 1ª linha (aparece na busca): a palavra-chave principal + a promessa do vídeo.
2. Um parágrafo de 2–3 frases resumindo a mensagem, repetindo a palavra-chave e variações.
3. Texto bíblico base.
4. Capítulos (minutagem).
5. CTA: inscrever-se, ativar o sino, comentar.
6. 3–5 hashtags.
