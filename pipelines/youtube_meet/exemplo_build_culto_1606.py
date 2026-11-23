import json, re
W = json.load(open('../transcripts/culto.json'))['words']
def n(s): return re.sub(r'[^\wà-ú]', '', s.lower())
NW = [n(w['text']) for w in W]
INI, FIM = 2285, 9081          # "Bom dia. A graça e a paz…" até "…que Deus abençoe. Aleluia."
def find(ph, after=INI):
    p = [n(x) for x in ph.split()]
    for i in range(after, FIM + 1):
        if NW[i:i + len(p)] == p: return i
    raise KeyError(ph)
def fend(ph, after=INI): i = find(ph, after); return i + len(ph.split()) - 1
CUTS = [("Que nem diz o Marçal", "A gente encara porque precisa."),          # conversa: dengue, gripe, viagens
        ("Eu vou acompanhar. Tem projeção?", "não tem problema não."),       # projeção
        ("Sabe aquele hino assembleano?", "ou é ruim."),
        ("Você já conseguiu mudar a versão aí?", "segura aí."),
        ("se você não quer ouvir pelo aplicativo,", "que é você que vai ser usado?"),   # Cid Moreira
        ("Ajuda aí, Hugo.", "Ajuda aí, Hugo."),
        ("Oi, Elton.", "Oi, Elton."),
        ("Vou lá no Lugo agora pedir ajuda de novo,", "capítulo 4, né?")]
cut = set()
for a, b in CUTS:
    i = find(a); j = fend(b, i); cut |= set(range(i, j + 1))
CH = [("Quem disse *que parou?*", "Bom dia. A graça e a paz"),
      ("Me pede, *que hoje eu faço*", "Na hora do louvor aqui,"),
      ("O centurião *de Cafarnaum*", "Vocês abram a Bíblia,"),
      ("Peça para *quem resolve*", "O que é um centurião?"),
      ("Só *uma palavra*", "Jesus, quando foi interpelado"),
      ("A fé vem *pelo ouvir*", "Vamos entender então um pouco essa questão de fé,"),
      ("Com Deus, *nada é impossível*", "tenho ido em muita empresa"),
      ("O leite *que derrama*", "Qual que é o contrário da fé?"),
      ("Não se preocupem *com nada*", "Bom, mas vamos ver Bíblia"),
      ("Persistir *ou confiar?*", "A gente não vai ler, porque agora"),
      ("O inimigo *está dentro de você*", "inimigo aqui não é o diabo."),
      ("Louva *ou respira*", "E aí para mostrar como que resolve,"),
      ("Peça *sem duvidar*", "Mas Manu, você falou que é para entregar,"),
      ("Porque *Ele é Deus*", "O PG que você faz durante a semana,"),
      ("Não se preocupe, *mas ore*", "Aí vem Filipenses, para terminar aí,")]
SUB = {"pede": "olha, pede-me o que quiseres,", "tocou": "Aquele versículo onde a mulher", "leitura": "Tendo Jesus entrado em Cafarnaum,",
       "digno": "Mas o centurião respondeu:", "conforme": "Então disse Jesus ao centurião:", "inimigo": "Além dele não ser crente,",
       "pedir": "Eu não vou pedir. Para o meu chefe", "onde": "Eu te pergunto aqui, meu querido,", "coitado": "Eu assisti um desenho",
       "venha": "Venha como está.", "palavra": "Repete para mim. Uma palavra.", "mexeu": "Essa fé desse centurião mexeu com Jesus.",
       "ouvir": "A fé vem pelo ouvir.", "dono": "donos de empresa são seres humanos", "impossivel": "Eu quero falar de que com Deus nada",
       "marido": "Eu queria tanto fazer tal coisa, mas o meu marido", "duvida": "Agora, na sua Bíblia, quantas coisas",
       "leite": "Você pega o leite,", "gui": "O Gui, por exemplo,", "deus": "Agora presta atenção como que a gente faz com Deus,",
       "sente": "O que você acha que Deus está sentindo de você?", "estraga": "você estraga. Você estraga a resposta",
       "tiques": "Mando uma mensagem e fico olhando", "sl37": "Salmo capítulo trinta e sete,", "sl23": "Agora o 23:1.",
       "mt633": "Mateus 6, 33. Portanto,", "fp46": "Filipenses 4, versículo 6,", "nada": "De acordo com o Filipenses? Com nada.",
       "parabolas": "Na mesma Bíblia, lá em Lucas,", "dilema": "Aí a gente acabou de falar que eu não tenho",
       "automaticos": "Conseguir parar de pensar tem um conceito", "cerebro": "Porque a cabeça da gente aqui dentro",
       "jesussabia": "E Jesus sabia disso.", "tg15": "Tiago um, versículo cinco.", "volta": "Você fica, você acredita enquanto",
       "comigo": "Mas onde eu vou, o problema vai comigo.", "pensa": "É pensa em um problemão",
       "canta": "Vai pensando agora, canta comigo.", "abre": "Agora abre o olho.", "naoda": "Tem lugar que não dá para cantar.",
       "fogo": "Você não combate fogo com fogo,", "respira": "Enquanto eu conto, você vai puxar o ar",
       "mecanismo": "É incrível o mecanismo", "pedro": "Gente, eu acredito que Jesus respirou fundo",
       "volta2": "Agora ele voltou, né?", "entregar": "quem falou que entregar para Deus é esquecer.",
       "tg43": "Quando pedem, não recebem,", "tg16": "Porém, peçam com fé, e não duvidem de modo nenhum, é aqui",
       "firmeza": "Quando eu peço uma coisa, eu tenho que ter firmeza.", "daniel": "você lembra que Daniel orava",
       "circuito": "Fechou. Opa, vou voltar agora", "sirvo": "Porque eu não te sirvo porque",
       "estilo": "Então eu estou aqui de novo. É estilo de vida.", "posso": "apóstolo Paulo fala, posso todas as coisas",
       "louvaou": "Louva ou respira. Depende de onde", "fp46b": "Não se preocupem com nada. Mas em todas as orações.",
       "agradecido": "Já ora e agradece.", "fp47": "Versículo 7 para fechar."}
marks = sorted([(find(p), f"c{k+1}") for k, (_, p) in enumerate(CH)] + [(find(p), k) for k, p in SUB.items()])
blk = {}; cur = "c1"; mi = 0
for i in range(INI, FIM + 1):
    while mi < len(marks) and marks[mi][0] <= i: cur = marks[mi][1]; mi += 1
    blk[i] = cur
spans = [["card", 4.2, "intro"]]; i = INI
while i <= FIM:
    if i in cut: i += 1; continue
    j = i
    while j + 1 <= FIM and j + 1 not in cut and blk[j + 1] == blk[i]: j += 1
    spans.append([7, i, j, blk[i], "stage"]); i = j + 1
spans.append(["card", 18.0, "fim"])
ev = [dict(k="intro", t0="b:intro", t1="B:intro", kicker="pregação · Mateus 8 · Tiago 1 · Filipenses 4", title="Louva *ou respira*", sub="pregação de Manoel Gonçalves")]
for k, (t, _) in enumerate(CH, 1): ev.append(dict(k="chapter", t0=f"b:c{k}" + ("+0.6" if k == 1 else "+0.3"), t1=f"b:c{k}+3.4", n=k, title=t))
E = lambda **kw: ev.append(kw)
B = lambda b, **kw: E(t0=f"b:{b}-0.1", t1=f"B:{b}+0.2", **kw)
E(k="lower3", t0="b:c1+4.0", t1="b:c1+10", name="Manoel Gonçalves", role="culto de domingo", x=1430, y=860)
E(k="f_word", t0="f:quem@c1-0.3", t1="f:quem@c1+5", lines=["Quem disse", "*que parou?*"], size=130)
E(k="c_statement", t0="f:tema@c2-0.2", t1="b:pede-0.2", lines=[["O tema de hoje:", "f:tema@c2"], ["*fé.*", "f:fé@c2"]])
B("pede", k="f_word", kicker="quando o céu se abre", lines=["“Pede-me o que quiseres,", "*e eu farei.*”"], size=110)
B("tocou", k="c_title", kicker="a mulher do fluxo de sangue", lines=["Todo mundo tocava em Jesus.", "*Ela tocou diferente.*"], size=76)
B("leitura", k="c_verse", ref="Mateus 8:5-6", text="Tendo Jesus entrado em Cafarnaum, apresentou-se a ele um centurião, implorando: Senhor, o meu criado jaz em casa, paralítico, sofrendo horrivelmente.")
B("digno", k="f_verse", ref="Mateus 8:8", text="Senhor, não sou digno de que entres em minha casa; mas apenas manda uma palavra, e o meu rapaz será curado.", size=80)
B("conforme", k="f_verse", ref="Mateus 8:13", text="Vai, e seja feito conforme a tua fé. E naquela mesma hora o servo foi curado.", size=88)
B("inimigo", k="c_versus", left=["quem pediu", "o centurião|soldado romano", "b:inimigo"], right=["para quem", "Jesus|quem resolve", "f:jesus@inimigo"])
B("pedir", k="c_list", title="eu não vou pedir para…", numbered=False, items=[["f:chefe@pedir", "o meu chefe"], ["f:esposa@pedir", "a família"], ["f:pastor@pedir", "o pastor"], ["f:jesus@pedir", "*vou pedir para Jesus*"]])
B("onde", k="f_word", lines=["Ele está aqui.", "*Peça para quem resolve.*"], size=120)
B("coitado", k="c_title", kicker="“eu sou tão coitadinho…”", lines=["O centurião era pior.", "*E Jesus o atendeu.*"], size=80)
B("venha", k="f_word", lines=["Venha", "*como está.*"], size=150)
B("c5", k="c_title", kicker="Mateus 8:7-8", lines=["Não precisa nem ir.", "*Só fala.*"])
B("palavra", k="c_statement", lines=[["É Deus falar “abre”:", "f:abre@palavra"], ["*e vai abrir.*", "f:abre@palavra+0.8"], ["É Deus falar “saúde”:", "f:saúde@palavra"], ["*e a saúde vem.*", "f:saúde@palavra+0.8"]])
B("mexeu", k="c_title", kicker="Jesus se admirou", lines=["“Nem em Israel achei", "*fé como essa.*”"], size=80)
B("ouvir", k="f_verse", ref="Romanos 10:17", text="A fé vem pelo ouvir, e o ouvir pela palavra de Deus.", size=96)
B("dono", k="c_statement", lines=[["O dono da empresa", "b:dono"], ["*também precisa de Deus.*", "f:precisa@dono"]])
B("impossivel", k="f_word", lines=["Com Deus,", "*nada é impossível.*"], size=130)
B("marido", k="c_list", title="também precisa de fé", numbered=False, items=[["f:marido@marido", "o casamento"], ["f:filho@marido", "os filhos"], ["f:dinheiro@marido", "o dinheiro"]])
B("duvida", k="c_statement", lines=[["Você sabe o que está escrito…", "b:duvida"], ["*mas duvida.*", "f:duvida@duvida"]])
B("leite", k="c_flow", title="o leite no fogo", steps=[["b:leite", "você fica olhando: não sobe"], ["f:vira@leite", "você vira as costas"], ["f:derramou@leite", "*derrama tudo no fogão*"]])
B("gui", k="c_versus", left=["com o Gui", "“o caminhão|vai mesmo?”", "f:caminhão@gui"], right=["com Deus", "“o Senhor vai|fazer mesmo?”", "f:deus@deus"])
B("sente", k="f_word", kicker="feitos à imagem de Deus", lines=["O que Deus sente", "*quando você desconfia?*"], size=110)
B("estraga", k="f_word", lines=["A ansiedade", "*estraga a resposta.*"], size=130)
B("tiques", k="c_title", kicker="os dois tiques azuis", lines=["O cúmulo", "*da ansiedade.*"])
B("sl37", k="c_verse", ref="Salmo 37:5", text="Ponha a sua vida nas mãos do Senhor, confie nele, e ele o ajudará.")
B("sl23", k="c_verse", ref="Salmo 23:1", text="O Senhor é o meu pastor; nada me faltará.")
B("mt633", k="c_verse", ref="Mateus 6:33", text="Ponham em primeiro lugar na sua vida o Reino de Deus e aquilo que Deus quer, e ele lhes dará todas as coisas.")
B("fp46", k="f_verse", ref="Filipenses 4:6", text="Não se preocupem com nada, mas em todas as orações peçam a Deus o que vocês precisam e orem sempre com o coração agradecido.", size=72)
B("nada", k="f_word", lines=["Se preocupar com o quê?", "*Com nada.*"], size=120)
B("parabolas", k="c_flow", title="Lucas 11 e 18", steps=[["f:amigo@parabolas", "o amigo insistente"], ["f:viúva@parabolas", "a viúva persistente"], ["f:persistência@parabolas", "*persistir em pedir*"]])
B("dilema", k="c_versus", left=["Filipenses 4", "não se|preocupe", "b:dilema"], right=["Lucas 11 e 18", "persista|em pedir", "f:persistir@dilema"])
B("c11", k="f_word", lines=["O inimigo não é o diabo.", "*Está dentro de você.*"], size=110)
B("automaticos", k="c_title", kicker="a psicologia chama de", lines=["Pensamentos automáticos", "*disfuncionais.*"], size=76)
B("cerebro", k="c_list", title="o cérebro foi feito para", numbered=False, items=[["f:comer@cerebro", "comer"], ["f:sobreviver@cerebro", "sobreviver"], ["f:economizar@cerebro", "*economizar energia*"]])
B("tg15", k="f_verse", ref="Tiago 1:5-6", text="Peçam com fé e não duvidem de modo nenhum, pois quem duvida é como as ondas do mar, que o vento leva de um lado para o outro.", size=72)
B("comigo", k="f_word", lines=["Onde eu vou,", "*o problema vai comigo.*"], size=120)
B("pensa", k="c_flow", title="a experiência", steps=[["b:pensa", "pense no problema"], ["f:canta@canta", "agora cante"], ["f:abre@abre", "*e o problema?*"]])
B("abre", k="c_statement", lines=[["Cantando,", "b:abre"], ["*não dá para pensar no problema.*", "f:conseguia@abre"]])
B("naoda", k="c_title", kicker="e quando não dá para cantar?", lines=["*Respire.*"], size=120)
B("fogo", k="f_word", lines=["Fogo se combate", "*com água.*"], size=130)
B("respira", k="c_flow", title="respire", steps=[["f:um@respira", "puxe o ar: 1, 2, 3, 4"], ["f:segura@respira", "segure"], ["f:solta@respira", "*solte devagar*"]])
B("mecanismo", k="c_statement", lines=[["Deus te deu um mecanismo", "b:mecanismo"], ["*para desconectar.*", "f:desconectar@mecanismo"]])
B("pedro", k="c_title", kicker="e com o Pedro por perto…", lines=["Jesus respirou fundo", "*muitas vezes.*"], size=80)
B("volta2", k="f_word", kicker="o problema voltou?", lines=["Louva", "*ou respira.*"], size=150)
B("entregar", k="f_word", lines=["Entregar", "*não é esquecer.*"], size=140)
B("tg43", k="c_verse", ref="Tiago 4:3", text="Quando pedem, não recebem, porque os seus motivos são maus.")
B("firmeza", k="c_statement", lines=[["Pediu para quem?", "f:pediu@firmeza"], ["*Confia no Pai, filho.*", "f:confia@firmeza"]])
B("daniel", k="c_title", kicker="Daniel 6:10", lines=["Três vezes por dia", "*diante de Deus.*"])
B("circuito", k="c_flow", title="o circuito da oração", steps=[["b:circuito", "apresente a petição"], ["f:vida@circuito", "siga a sua vida"], ["f:orar@circuito", "*volte e apresente de novo*"]])
B("sirvo", k="f_word", lines=["Eu te sirvo", "*porque o Senhor é Deus.*"], size=120)
B("estilo", k="c_statement", lines=[["Não é para resolver problema.", "b:estilo"], ["*É estilo de vida.*", "f:estilo@estilo"]])
B("posso", k="f_verse", ref="Filipenses 4:13", text="Posso todas as coisas naquele que me fortalece.", size=100)
B("louvaou", k="f_word", lines=["Louva", "*ou respira.*"], size=150)
B("fp46b", k="c_statement", lines=[["Não se preocupe…", "b:fp46b"], ["*mas ore.*", "f:orações@fp46b"]])
B("agradecido", k="c_statement", lines=[["Peça e agradeça", "b:agradecido"], ["*antes de ver.*", "f:agradece@agradecido"]])
B("fp47", k="f_verse", ref="Filipenses 4:7", text="E a paz de Deus, que ninguém consegue entender, guardará o coração e a mente de vocês, pois vocês estão unidos com Cristo Jesus.", size=72)
E(k="endcard", t0="b:fim", t1="B:fim", lines=["Louva", "*ou respira.*"], sub="Inscreva-se e comente o que essa palavra falou com você.")
plan = dict(id="culto1606", proj="/home/user/editar_videos/brutos/culto_1606", src="/home/user/editar_videos/brutos/culto_1606/dl/culto_av.mp4",
            audio_only=False, segs={"7": 0.0}, layout="stage", max_dur={"c_": 13.0, "c_flow": 26.0, "c_list": 22.0, "c_versus": 16.0, "c_verse": 16.0, "f_": 6.5, "f_verse": 9.0},
            fps=600 / 23, speed=1.15, gap=999.0, fade_in=1.0, fade_out=2.5, part_crf=21, tfile={"7": "culto.json"}, tag="Pregação · Fé", cold_title="Abertura",
            fix={"Manuel,": "Manoel,", "Manuel.": "Manoel.", "Manuel": "Manoel", "Manu,": "Manoel,", "Matheus": "Mateus", "anciosas.": "ansiosas.", "Cafarnaú,": "Cafarnaum,",
                 "Judé,": "Judeia,", "jaza": "jaz", "elter.": "Elder.", "Lugo": "Hugo"},
            punch=[], spans=spans, events=ev, music={"off": True})
json.dump(plan, open('culto.json', 'w'), ensure_ascii=False, indent=1)
print(len(spans), 'trechos', len(ev), 'eventos', len(cut), 'palavras cortadas')
