import json, re
W = json.load(open('../transcripts/culto.json'))['words']
def n(s): return re.sub(r'[^\wà-ú]', '', s.lower())
NW = [n(w['text']) for w in W]
def find(ph, after=2256):
    p = [n(x) for x in ph.split()]
    for i in range(after, 9835):
        if NW[i:i + len(p)] == p: return i
    raise KeyError(ph)
def fend(ph, after=2256): i = find(ph, after); return i + len(ph.split()) - 1
INI, FIM = 2256, 9834
CUTS = [("Vamos pegar diferente assim", "Não tinha conversinha, gente."),
        ("Historicamente, eu não vou entrar", "o pastor Aragão, enfim."),
        ("Aí me veio a letra da música", "ver o versículo agora."),
        ("Se você quiser entender um pouco disso, assista.", "Babilônia na época."),
        ("Porra!", "Porra!"),
        ("Inclusive porque eu faço parte", "Vamos continuar aqui para você entender."),
        ("Quem estava aqui quando a gente fez", "concordo com você, mas e aqui dentro?"),
        ("Pode mudar o slide aí, Leandro.", "Pode mudar o slide aí, Leandro."),
        ("voz da biga", "foi o Nemias."),
        ("Quem falou Esdras aí?", "pau a pau com a biga."),
        ("não está, Marcinha?", "não está, Marcinha?"),
        ("Vamos para o outro slide aí.", "Vamos para o outro slide aí."),
        ("Vou te pedir uma gentileza, Leandro.", "Primeiro e segundo slide."),
        ("Pode voltar lá agora, por favor.", "Põe o fruto aí, por favor."),
        ("Vamos ver se tem. Pode pôr o próximo aí,", "que também é interessante."),
        ("A gente tinha um costume, quando", "Deixa o tato quieto com Jesus, gente."),
        ("Quem faz isso vai buscar", "transformar a vida daquela criança."),
        ("É por isso que você vira para a esquerda", "Deixa para lá."),
        ("Não é, Caio?", "Não é, Caio?")]
cut = set()
for a, b in CUTS:
    i = find(a); j = fend(b, i); cut |= set(range(i, j + 1))
# capítulos (frase de início) e sub-blocos para âncoras
CH = [("O fio vermelho *da história*", "Hoje a gente vai falar do."),
      ("Um reino *dividido*", "Então vieram os reis,"),
      ("O inimigo vem *devagarzinho*", "Não tem esse negócio. Ah, adorado."),
      ("O ataque é contra *a sua identidade*", "Vem o povo a Sírio."),
      ("Síria, Babilônia *e Pérsia*", "Porém, depois da Babilônia ela foi derrubada,"),
      ("A Bíblia não é *self-service*", "A Bíblia não é um catálogo"),
      ("Sesbazar *ou Zorobabel?*", "Aí a gente vai falar então do Zorobabel"),
      ("O altar *antes dos muros*", "Esdras, capítulo 1,"),
      ("Não por força, *nem por violência*", "Vencendo a resistência."),
      ("Do templo de pedra *ao templo vivo*", "templo de pedra ao templo vivo."),
      ("Fruto *se carrega*", "Fruto não se faz, fruto se carrega."),
      ("2026: o ano *do altar*", "Conclusão aí, ó. 2026.")]
SUB = ["Gênesis. Adão, Eva", "Ao longo da linha do tempo", "Estou falando tudo isso, gente,",
       "Veio a construção do templo.", "Durante toda essa história", "Hoje a gente está domesticado.", "Divisão das doze tribos",
       "O diabo, gente,", "Aí Deus teve que vir", "Tem dia que eu estou aqui,", "A Bíblia relata o que é o ser humano", "Nós não vamos aqui agora fazer",
       "Quando vem um ataque,", "Porém, lá no reino do sul.", "Engraçado é que todo vilão", "Acompanha porque eu falei besteira",
       "É só você pegar a história de Daniel,", "No meio disso tudo vem o Zorobabel.", "conquistou o rei da Pérsia,", "E para isso eu quero que você aplique",
       "A Bíblia não é um amontoado", "Pode ouvir uma palestra",
       "E aí na Babilônia o nome dele", "Mas esse sesbazar aqui", "E quando eu falo de adorador do fogo,", "Muitos cristãos hoje são apenas",
       "Imagina, acabei de falar", "Você não pode estar lembrando de Deus lá no fórum?",
       "Hoje em dia, se a gente estivesse", "O altar antes dos muros.", "A religião quer primeiro", "Quando o Guilherme fala isso,", "A gente só precisa de repente completar",
       "Muitas vezes você começa no pique", "Zacarias, capítulo 4,", "E eu já vou dar mais uma pincelada", "A gente tem que se centrar.", "Eu nem gosto de falar mais desse termo,", "Agora Jesus te ama mesmo assim.",
       "Deus não mora em prédios.", "João 15, versículos 1 e 2,", "Mas eu quero te falar que essa nova identidade", "E daí desse nome deriva", "Acabou essa oração,", "Surge Jesus numa época",
       "Fruto mostra o caráter transformado.", "Permaneçam em mim e eu permanecerei", "A poda, né? A poda dói,", "Deus trata da gente,", "Vamos ver os sinais e frutos aí.", "Quem transforma é o Espírito Santo,", "João 15, versículo 8,", "Meu vocabulário muda.", "Lembrando vocês aí que nós estamos em 40 dias", "Jejum não é para isso.", "Eu quero partir para o encerramento", "Eu costumo brincar, mas é uma"]
marks = sorted([(find(p), f"c{k+1}") for k, (_, p) in enumerate(CH)] + [(find(p), f"s{k}") for k, p in enumerate(SUB)])
blk = {}; cur = "c1"; mi = 0
for i in range(INI, FIM + 1):
    while mi < len(marks) and marks[mi][0] <= i: cur = marks[mi][1]; mi += 1
    blk[i] = cur
spans = [["card", 4.2, "intro"]]; i = INI; chap_start = {find(p): k + 1 for k, (_, p) in enumerate(CH)}
while i <= FIM:
    if i in chap_start: spans.append(["card", 2.6, f"cap{chap_start[i]}"])
    if i in cut: i += 1; continue
    j = i
    while j + 1 <= FIM and j + 1 not in cut and blk[j + 1] == blk[i] and (j + 1) not in chap_start: j += 1
    spans.append([7, i, j, blk[i]]); i = j + 1
spans.append(["card", 18.0, "fim"])
ev = [dict(k="intro", t0="b:intro", t1="B:intro", kicker="estudo bíblico · Esdras · Zacarias · João 15", title="O altar *antes dos muros*", sub="pregação de Manoel Gonçalves")]
for k, (t, _) in enumerate(CH, 1): ev.append(dict(k="chapter", t0=f"b:cap{k}", t1=f"B:cap{k}", n=k, title=t))
E = lambda **kw: ev.append(kw)
E(k="c_flow", t0="b:s0-0.1", t1="B:s1+0.2", title="o fio vermelho", steps=[["f:gênesis@s0", "Criação"], ["f:patriarcas@s0", "Patriarcas: Abraão, Isaque, Jacó"], ["f:lei@s0", "A lei, por Moisés"], ["f:tribos@s1", "As doze tribos de Israel"]])
E(k="c_statement", t0="f:levi@s1-0.2", t1="B:s1+0.2", lines=[["Levi não ganhou terra:", "f:levi@s1"], ["*os levitas cuidavam do altar.*", "f:altar@s1"]])
E(k="c_title", t0="b:s2-0.1", t1="B:s2+0.2", kicker="uma pergunta", lines=["Por que judeu", "*se chama judeu?*"])
E(k="c_flow", t0="b:c2-0.1", t1="B:c2+0.2", title="os reis", steps=[["f:saul@c2", "Saul"], ["f:davi@c2", "Davi"], ["f:salomão@c2", "Salomão"]])
E(k="c_title", t0="b:s3-0.1", t1="B:s3+0.2", kicker="Salomão", lines=["O templo", "*todo de ouro.*"])
E(k="f_word", t0="f:domesticado@s5-0.2", t1="B:s5+0.3", lines=["Não é civilização.", "*É domesticação.*"], size=110)
E(k="c_versus", t0="b:s6-0.1", t1="B:s6+0.3", left=["reino do norte", "10|tribos", "f:norte@s6"], right=["reino do sul", "Judá e|Benjamim", "f:judá@s6"])
E(k="c_list", t0="b:c3-0.1", t1="B:c3+0.2", title="pequenas concessões", numbered=False, items=[["f:adorado@c3", "“deixa isso pra lá”"], ["f:igreja@c3", "“não precisa ir à igreja”"], ["f:errado@c3", "“não é errado, pode fazer”"]])
E(k="f_word", t0="f:devagarzinho@s7-0.3", t1="B:s7+0.3", kicker="o inimigo não chega gritando", lines=["Ele vem *devagarzinho.*"], size=120)
E(k="c_verse", t0="b:s8-0.2", t1="B:s8+0.3", ref="2 Crônicas 7:14", text="Se o meu povo, que se chama pelo meu nome, se humilhar e orar, buscar a minha face e se afastar dos seus maus caminhos, dos céus o ouvirei.")
E(k="c_title", t0="b:s10-0.1", t1="B:s10+0.2", kicker="a Bíblia sem máscara", lines=["Até o maior rei", "*teve a sua história contada.*"], size=80)
E(k="f_word", t0="f:perfeito@s10+1.5", t1="B:s11-0.2", lines=["Perfeito só teve um:", "*Jesus Cristo.*"], size=120)
E(k="c_statement", t0="f:tudo@s11-0.1", t1="B:s11+0.2", lines=[["Toda pregação,", "f:pregação@s11"], ["todo estudo:", "f:estudo@s11"], ["*tudo leva para Jesus.*", "f:leva@s11"]])
E(k="f_word", t0="f:identidade@s12-0.2", t1="B:s12+0.4", kicker="a estratégia do inimigo", lines=["Apagar a sua", "*identidade de filho.*"], size=120)
E(k="c_statement", t0="b:s13-0.1", t1="B:s13+0.2", lines=[["No sul, um povo", "b:s13"], ["*segurou a identidade.*", "f:identidade@s13"]])
E(k="c_flow", t0="b:c5-0.1", t1="B:s16+0.2", title="três impérios", steps=[["b:c5", "Síria: acabou com o norte"], ["f:babilônia@c5", "Babilônia: levou o sul"], ["f:pérsia@c5", "Pérsia: o rei Ciro"]])
E(k="c_title", t0="b:s16-0.1", t1="B:s16+0.2", kicker="Daniel 3", lines=["“Nós não vamos", "*nos misturar.*”"])
E(k="c_statement", t0="b:s18-0.1", t1="B:s18+0.2", lines=[["Ciro não era bonzinho:", "f:ciro@s18"], ["*foi instrumento", "f:instrumento@s18"], ["*nas mãos de Deus.*", "f:instrumento@s18+0.6"]])
E(k="c_flow", t0="b:s19-0.1", t1="B:s19+0.3", title="quando a gente não se corrige", steps=[["f:síria@s19", "vem uma Síria"], ["f:babilônia@s19", "depois uma Babilônia"], ["f:pérsia@s19", "e depois uma Pérsia"]])
E(k="f_word", t0="b:c6-0.1", t1="f:nós@c6-0.1", lines=["A Bíblia não é", "*um livro de autoajuda.*"], size=110)
E(k="c_statement", t0="f:nós@c6-0.1", t1="B:c6+0.2", lines=[["Não é coach, não é palestra:", "f:nós@c6"], ["*é ministração da Palavra.*", "f:ministração@c6"]])
E(k="f_word", t0="f:self@s20-0.3", t1="B:s20+0.3", lines=["Não é *self-service.*", "É tudo sobre *Ele.*"], size=110)
E(k="c_versus", t0="b:s22-0.1", t1="B:s23+0.3", left=["na Babilônia", "Sesbazar|“semeado”", "b:s22"], right=["o nome espiritual", "Zorobabel|“adorador”", "f:zorobabel@s23"])
E(k="f_word", t0="f:engrenagem@s23-0.3", t1="B:s23+0.4", lines=["Você não é uma *engrenagem.*", "É um *adorador.*"], size=100)
E(k="c_statement", t0="b:s24-0.1", t1="B:s24+0.2", lines=[["Não confunda", "b:s24"], ["*adoração com música.*", "f:música@s24"]])
E(k="c_title", t0="b:s25-0.1", t1="B:s25+0.2", kicker="carreira, sucesso, propósito", lines=["Deus recebe", "*o bagaço?*"])
E(k="c_statement", t0="b:s26-0.1", t1="B:s26+0.2", lines=[["Conectado com Deus", "f:conectado@s26"], ["*o dia inteiro,", "f:conexão@s26"], ["*como sinal de 5G.*", "f:5g@s26"]])
E(k="f_word", t0="b:s27-0.1", t1="B:s27+0.3", lines=["Você é *o mesmo*", "em todo lugar?"], size=120)
E(k="c_verse", t0="b:c8-0.2", t1="B:c8+0.3", ref="Esdras 1:1,5", text="O Senhor despertou o espírito de Ciro, rei da Pérsia… Então se levantaram os chefes das famílias e todo aquele cujo espírito Deus despertou.")
E(k="c_statement", t0="b:s28-0.1", t1="B:s28+0.2", lines=[["Você seria", "b:s28"], ["*um dos que Deus despertou?*", "f:despertou@s28"]])
E(k="c_flow", t0="b:s29-0.1", t1="B:s29+0.3", title="a reconstrução", steps=[["f:neemias@s29", "Neemias: os muros"], ["f:ensino@s29", "Esdras: o ensino"], ["f:altar@s29", "Zorobabel: o altar"]])
E(k="f_word", t0="b:s30-0.1", t1="B:s30+0.3", kicker="Zorobabel não começou pelas casas", lines=["O altar", "*antes dos muros.*"], size=130)
E(k="c_statement", t0="b:s31-0.1", t1="B:s32-0.1", lines=[["Um altar de adoração", "f:altar@s31"], ["*não é sobre música:", "f:música@s31"], ["*é entronizar Jesus.*", "f:entronizar@s31"]])
E(k="f_word", t0="f:quem@s32+3", t1="B:s32+0.4", lines=["Quem muda você", "*é Jesus.*"], size=140)
E(k="c_title", t0="b:c9-0.1", t1="B:s33+0.2", kicker="Esdras 4", lines=["A obra parou", "*por 18 anos.*"])
E(k="f_verse", t0="b:s34-0.2", t1="f:pare@s34-0.1", ref="Zacarias 4:6", text="Não por força nem por violência, mas pelo meu Espírito, diz o Senhor dos Exércitos.", size=84)
E(k="c_statement", t0="f:pare@s34-0.1", t1="B:s34+0.2", lines=[["Pare de resolver", "f:pare@s34"], ["*tudo no braço.*", "f:braço@s34"]])
E(k="f_word", t0="f:direita@s35-0.4", t1="B:s35+0.3", lines=["Nem pela direita,", "nem pela esquerda:", "*pelo Espírito.*"], size=100)
E(k="f_word", t0="f:cristocêntrico@s36-0.3", t1="B:s36+0.3", lines=["*Cristocêntrico.*"], size=150)
E(k="c_statement", t0="b:s37-0.1", t1="B:s37+0.2", lines=[["A vida não tem gavetas:", "b:s37"], ["*a vida é uma só.*", "f:vida@s37+2"]])
E(k="c_statement", t0="b:s38-0.1", t1="B:s38+0.2", lines=[["Jesus te ama", "f:ama@s38"], ["*mesmo você sendo errado.*", "f:errado@s38"], ["Ele não concorda com o erro.", "f:concorda@s38"]])
E(k="f_word", t0="b:s39-0.1", t1="B:s39+0.3", lines=["Deus não mora", "*em prédios.*"], size=140)
E(k="f_verse", t0="b:s40-0.2", t1="B:s40+0.4", ref="João 15:1-2", size=64, text="Eu sou a videira verdadeira, e meu Pai é o agricultor. Todo ramo que, estando em mim, não dá fruto, ele corta; e todo que dá fruto ele poda, para que dê mais fruto ainda.")
E(k="c_statement", t0="b:s41-0.1", t1="B:s41+0.2", lines=[["A nova identidade em Jesus", "b:s41"], ["*é por fé, é por aliança.*", "f:fé@s41"]])
E(k="c_flow", t0="b:s42-0.3", t1="B:s42+0.3", title="por que judeu?", steps=[["b:s42", "10 tribos dispersas"], ["b:s42+2", "Benjamim e Levi diluídos em Judá"], ["f:judeu@s42", "todos passam a ser *judeus*"]])
E(k="c_versus", t0="b:s43-0.1", t1="B:s44+0.3", left=["agora", "judeus", "f:judeus@s43"], right=["e também", "gentios", "f:gentios@s43"])
E(k="f_word", t0="b:c11-0.1", t1="B:c11+0.4", lines=["Fruto não se faz.", "*Fruto se carrega.*"], size=120)
E(k="c_statement", t0="b:s45-0.1", t1="B:s45+0.2", lines=[["Fruto é transformação interna:", "b:s45"], ["*as pessoas veem Cristo em você.*", "f:cristo@s45"]])
E(k="f_verse", t0="b:s46-0.2", t1="B:s46+0.4", ref="João 15:4-5", size=64, text="Permaneçam em mim, e eu permanecerei em vocês. Nenhum ramo pode dar fruto por si mesmo, se não permanecer na videira… sem mim vocês não podem fazer coisa alguma.")
E(k="f_word", t0="b:s47-0.1", t1="B:s47+0.3", lines=["A poda dói,", "*mas cura.*"], size=140)
E(k="c_statement", t0="b:s48-0.1", t1="B:s48+0.2", lines=[["O Pai é o agricultor:", "b:s48"], ["*corta o que suga a vida.*", "f:corta@s48"], ["O centro é Jesus.", "f:centro@s48"]])
E(k="c_versus", t0="b:s49-0.1", t1="B:s50+0.3", left=["sinal", "poder|externo", "f:sinal@s49"], right=["fruto", "transformação|interna", "f:fruto@s49"])
E(k="f_verse", t0="b:s51-0.2", t1="B:s51+0.3", ref="João 15:8", text="Meu Pai é glorificado pelo fato de vocês darem muito fruto.", size=84)
E(k="c_list", t0="b:s52-0.1", t1="B:s52+0.2", title="o fruto aparece", numbered=False, items=[["f:vocabulário@s52", "no vocabulário"], ["f:pessoas@s52", "nas pessoas ao redor"], ["f:investimentos@s52", "nos investimentos"]])
E(k="f_word", t0="f:2026@c12-0.2", t1="B:c12+0.4", lines=["2026:", "o ano da *reconstrução do altar.*"], size=110)
E(k="c_counter", t0="b:s53-0.1", t1="B:s53+0.3", rows=[["f:40@s53", "40", "dias de consagração"], ["f:consagração@s53+1", "12/1", "a 20/2"]], total=False)
E(k="c_list", t0="f:jejum@s53+8", t1="B:s54+0.3", title="o jejum não é", numbered=False, items=[["f:carro@s54", "para comprar o carro"], ["f:quilo@s54", "para perder 5 quilos"], ["f:escutar@s53", "é para escutar a voz de Deus"]])
E(k="c_statement", t0="b:s55-0.1", t1="B:s55+0.2", lines=[["Gerar um ambiente", "f:ambiente@s55"], ["*onde o Espírito Santo", "f:espírito@s55"], ["*se sinta à vontade.*", "f:vontade@s55"]])
E(k="f_word", t0="f:onde@s56+3", t1="B:s56+0.6", lines=["Onde a gente chega,", "*Jesus chega.*"], size=130)
E(k="endcard", t0="b:fim", t1="B:fim", lines=["O altar", "*antes dos muros.*"], sub="Inscreva-se e comente o que essa palavra falou com você.")
plan = dict(id="culto1801", proj="/home/user/editar_videos/brutos/culto_1801", src="/home/user/editar_videos/brutos/culto_1801/dl/culto.m4a",
            audio_only=True, segs={"7": 0.0}, tfile={"7": "culto.json"}, tag="Estudo bíblico · Zorobabel", cold_title="Abertura",
            fix={"Zoropabel": "Zorobabel", "Chorou": "Zorobabel", "Emias": "Neemias", "Estras.": "Esdras.", "sesbazar": "Sesbazar", "Cesbazar": "Sesbazar", "cisbazares.": "Sesbazares.", "Pagaço.": "bagaço.", "pagaço": "bagaço", "vidéis.": "videira.", "potado,": "podado,", "potado": "podado", "Sírio.": "Assírio."},
            punch=[], spans=spans, events=ev, music={"off": True})
json.dump(plan, open('culto.json', 'w'), ensure_ascii=False, indent=1)
print(len(spans), 'trechos', len(ev), 'eventos', len(cut), 'palavras cortadas')
