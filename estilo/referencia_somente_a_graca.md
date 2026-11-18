# Referência de edição — "Servindo a Deus ou ao Dinheiro" (canal Somente a Graça)

Vídeo analisado: pregação de Zé Bruno, 41:38, 1280×720, 30 fps, horizontal.
Fonte: arquivo no Google Drive enviado pelo usuário (18/11/2026).
Objetivo: replicar esta fórmula de edição em vídeos brutos de pregação.

> Limitação da análise: o áudio não foi transcrito (o modelo de transcrição foi
> bloqueado pela rede). O conteúdo falado foi lido nas legendas embutidas. O
> arquivo tem 2 faixas de áudio diferentes (a 2ª não é cópia da 1ª, mas não foi
> possível identificar o que ela contém).

## Estrutura (linha do tempo)

| Tempo | Bloco | O que acontece |
|---|---|---|
| 0:00–0:02 | Abertura | Bokeh de corações em P&B que se resolve no palco (transição de entrada) |
| 0:02–0:55 | **HOOK** (~53 s) | Montagem em **preto e branco** de frases fortes tiradas do meio da pregação |
| 0:55–0:56 | Transição | Flash de bokeh/luz colorida (vazamento de luz) |
| 0:56–1:14 | **Ponte cinematográfica** (~18 s) | B-roll gerado por IA (homem bíblico numa caverna com chuva, Bíblia na mão), colorido, com câmera lenta. Narrador resume a tese e faz a **1ª chamada**: "assista a mensagem até o final e deixe seu comentário" |
| 1:14–1:17 | Contagem | Bokeh colorido + **contagem 3-2-1** dentro de um círculo amarelo que se abre e revela o palco |
| 1:17–41:22 | **Pregação** | Pregação completa, colorida, multicâmera (plano aberto, médio, close e lateral), com legenda o tempo todo |
| ~18:00 | CTA no meio | Botão animado "Deixe o Like!" com cursor clicando |
| 41:22–41:24 | Transição | Bokeh dourado |
| 41:24–41:38 | **Encerramento** | B-roll de IA (Jesus num olival, semeador no trigal, caminhada no campo). Narrador: "sentiu-se abençoado por esta mensagem? então curta e compartilhe pra abençoar outras pessoas… fique com Deus e até o próximo vídeo" |

## O HOOK (a peça mais importante)

- **Duração:** ~50–55 s.
- **Conteúdo:** 10–14 frases curtas e de impacto, tiradas de pontos diferentes da
  pregação (ex.: a frase das 0:19 aparece de novo aos ~15:00). Não segue a ordem
  cronológica; segue um **arco argumentativo**:
  1. Pergunta-provocação: "quando a gente diz eu amo a Deus… eu amo a Deus ou amo as coisas que eu quero?"
  2. Desdobramento em contrastes "isto **ou** aquilo" ("a vontade dele ou o que ele compra", "porque você o ama… ou porque quer uma vitória", "pela graça… ou pela oportunidade")
  3. Termina em aberto, numa tensão sem resposta → corta para a ponte.
- **Visual:** tudo em **P&B com alto contraste** (pretos esmagados, brancos fortes),
  o que separa o hook do resto do vídeo (que é colorido).
- **Ritmo:** troca de plano a cada **2–5 s** (aberto → close → lateral). Muda de
  ângulo também *dentro* da mesma frase.
- **Punch-ins/zooms:** alternância de planos aberto, médio e close dá energia sem
  efeitos chamativos.
- **Transições internas:** corte seco na maioria. Em 2–3 pontos há um *flash de
  desfoque* (bokeh) que dura 0,3–0,5 s (ex.: 0:14, 0:38).

## Cortes na pregação

- A pregação fica **praticamente inteira** (41 min), sem cortar o conteúdo. A
  edição está na embalagem (hook, ponte, legenda e CTAs), não em encurtar.
- Alterna entre as câmeras da igreja; a duração média de cada plano é longa
  (de 10 s até mais de 1 min). O multicam já vem da transmissão.
- As legendas de versículo (ex.: "1 TIMÓTEO 6:3-10 (NAA)", caixa preta
  semitransparente no canto inferior esquerdo) vêm da transmissão da igreja.
  Foram mantidas, e a legenda amarela fica por cima delas.

## Legenda

- **Cor:** amarelo-limão `#E8F800` (≈ RGB 232,248,0), contorno preto fino e sem caixa.
- **Fonte:** sans-serif geométrica de peso médio (aparência de Montserrat/Gotham
  Medium). Em 720p, a altura das maiúsculas fica em ~30 px; no ASS, use FontSize ≈ 22 a 1280×720.
- **Posição:** centralizada embaixo; base do texto a ~48 px da borda inferior.
- **Agrupamento:** 5–9 palavras, até **2 linhas**, frase natural.
- **Caixa:** minúsculas naturais, **sem pontuação**. Palavras de ênfase em CAIXA
  ALTA de vez em quando ("EU posso ser honrado OU humilhado").
- **Presença:** o vídeo inteiro (hook, ponte, pregação e encerramento). Não é
  karaokê palavra por palavra; aparece a frase inteira de uma vez.

Estilo ASS equivalente:
```
FontName=Montserrat Medium,FontSize=22,PrimaryColour=&H0000F8E8,
OutlineColour=&H00000000,BorderStyle=1,Outline=1.2,Shadow=0,
Alignment=2,MarginV=40
```

## Efeitos e identidade

- **Marca d'água:** logo circular "Somente a Graça" (leão), canto superior
  esquerdo, ~85 px a 720p, o vídeo inteiro.
- **Gradação de cor:** hook em P&B contrastado; ponte e encerramento com B-roll de
  IA em cores (azul-petróleo frio na ponte, dourado quente no final); pregação com
  a cor natural.
- **Transições:** *bokeh/light leak* (corações em P&B na abertura, bokeh azul ou
  colorido na ponte, bokeh dourado no final). São sempre curtas, de 0,5–1,5 s.
- **Contagem 3-2-1:** números brancos em fonte quadrada dentro de uma elipse
  amarela (mesmo amarelo da legenda), ~1 s por número, sobre bokeh → palco.
- **Botão "Deixe o Like!":** pílula branca com ícone de joinha e cursor que clica,
  aparece por ~2–3 s no meio do vídeo.

## Gatilhos mentais usados

- **Curiosidade/lacuna:** o hook faz uma pergunta e não responde. Para saber, só assistindo.
- **Confronto/identificação:** "você ama a Deus ou ama o que ele te dá?" leva a pessoa a se avaliar.
- **Contraste (dicotomia):** a estrutura "isto OU aquilo" se repete.
- **Autoridade/emoção:** B-roll cinematográfico bíblico + narrador dão peso.
- **Compromisso:** "assista até o final" logo no começo.
- **Reciprocidade/propósito:** "curta e compartilhe **pra abençoar outras pessoas**"
  (o pedido vira uma missão).

## Chamadas (CTAs)

1. ~1:10 — narrador: "assista a mensagem até o final e deixe seu comentário" (retenção + engajamento)
2. ~18:00 — botão animado "Deixe o Like!"
3. ~41:30 — narrador: "sentiu-se abençoado por esta mensagem? então curta e
   compartilhe pra abençoar outras pessoas"
4. Despedida: "fique com Deus e até o próximo vídeo"

## Receita para replicar num vídeo bruto

1. Transcrever o bruto (palavra por palavra) e escolher **10–14 frases-gancho**
   que formem um arco pergunta → contrastes → tensão aberta (~50 s).
2. Montar o hook em P&B contrastado, trocando o plano a cada 2–5 s, com 1–2
   flashes de bokeh.
3. Ponte de ~15–20 s: B-roll cinematográfico (IA ou banco de imagens) + narração
   resumindo a tese + "assista até o final e comente".
4. Transição de bokeh + contagem 3-2-1 na elipse amarela → pregação começa.
5. Pregação inteira, colorida, com legenda amarela, versículos mantidos, logo no canto.
6. Botão "Deixe o Like!" perto de 40% do vídeo.
7. Encerramento de ~15 s: bokeh dourado + B-roll + narração "curta e compartilhe pra
   abençoar outras pessoas… fique com Deus e até o próximo vídeo".

Itens que dependem do usuário: o arquivo do logo, a voz do narrador (gravada ou
TTS), o B-roll (gerado ou de banco) e a fonte exata da legenda.
