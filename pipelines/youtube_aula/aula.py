"""Vídeo-aula 16:9 para YouTube (Desenvolve Mais) — ritmo, zooms, capítulos, painéis didáticos com ícones.
Uso: aula.py <chunk> <nchunks> <out.mp4> [t0 t1]   (tempos de saída, para prévia)
Base: edit/base_fast.mov (fala acelerada SP×). Tempos dos eventos = palavras da transcrição / SP."""
import json, sys, os, math, bisect, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/user/editar_videos/pipelines/efeitos")
import fx
from fx import F, eo, eio, back, pr, tw, with_alpha, text_sprite, blur_reveal

D = os.environ.get("PROJ", "/home/user/editar_videos/brutos/aula"); E = f"{D}/edit"; ICONS = f"{E}/icons"
W, H, FPS, SP = 1920, 1080, 30, 1.15
END_CARD = 20.0
PAL = dict(bg=(14, 16, 26), ink=(255, 255, 255), accent=(43, 107, 251), cream=(255, 211, 77), glow=(43, 107, 251), muted=(170, 175, 190))
GOLD, BLUE, INK, MUTED = PAL["cream"], PAL["accent"], PAL["ink"], PAL["muted"]
WS = json.load(open(f"{E}/transcripts/bruto.json"))["words"]
BASE_DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{E}/base_fast.mov"]).decode())
TOTAL = BASE_DUR + END_CARD

def Wt(i): return WS[i]["start"] / SP
def We(i): return WS[i]["end"] / SP
def find(txt, lo, hi):
    for i in list(range(lo, hi + 1)) + list(range(max(0, lo - 25), lo)) + list(range(hi + 1, hi + 40)):
        if 0 <= i < len(WS) and WS[i]["text"].lower().strip(".,?!:;").startswith(txt.lower()):
            return i
    raise KeyError((txt, lo, hi))
def at(txt, lo, hi, d=-0.05): return Wt(find(txt, lo, hi)) + d

# ------------------------------------------------------------------ rosto (suavizado) para zoom
FA = json.load(open(f"{E}/faces.json"))
ft = np.array([f[0] / SP for f in FA]); fcx = np.array([f[1] for f in FA]); fcy = np.array([f[2] for f in FA])
def smooth(a, n=9):
    k = np.ones(n) / n; return np.convolve(np.pad(a, (n // 2, n // 2), mode="edge"), k, mode="valid")
fcx, fcy = smooth(fcx), smooth(fcy)
def face(t):
    return float(np.interp(t, ft, fcx)), float(np.interp(t, ft, fcy))

# ------------------------------------------------------------------ zoom por frase (ritmo)
phr, cur = [], []
for i, w in enumerate(WS):
    if cur and w["start"] - WS[i - 1]["end"] >= 0.6: phr.append(cur); cur = []
    cur.append(w)
phr.append(cur)
EMPH = ("?", "grava", "presta atenção", "ferrou", "cabeça de dono", "pra onde", "vida só", "chama ele", "meu deus", "pelo amor")
ZK = []  # (t, nível, duração da transição)
acc, lvl = 0.0, 1.0
for ph in phr:
    t0 = ph[0]["start"] / SP; txt = " ".join(w["text"] for w in ph).lower(); dur = (ph[-1]["end"] - ph[0]["start"]) / SP
    if dur < 5 and any(k in txt for k in EMPH):
        ZK.append((t0, 1.30, 0.22)); acc = 99; continue
    acc += dur
    if acc > 7:
        lvl = 1.14 if lvl == 1.0 else 1.0; acc = 0; ZK.append((t0, lvl, 0.7))
    elif ZK and ZK[-1][1] > 1.2:
        ZK.append((t0, lvl, 0.5))
ZT = [z[0] for z in ZK]
def zoom_at(t):
    k = bisect.bisect_right(ZT, t) - 1
    if k < 0: return 1.0
    prev = ZK[k - 1][1] if k > 0 else 1.0; t0, lv, d = ZK[k]
    return prev + (lv - prev) * eio(pr(t, t0, d))

# ------------------------------------------------------------------ roteiro gráfico
EV = []
def ev(kind, t0, t1, **kw): EV.append(dict(kind=kind, t0=t0, t1=t1, **kw))
# gancho + identificação
ev("kinetic", 0.05, Wt(12) + 0.3, kicker="você trabalha pra caramba e", title="NÃO VÊ RESULTADO?", exit=Wt(12) - 0.3, y=880, size=110)
ev("lower", Wt(12) + 0.5, Wt(12) + 6.0, name="Manoel Gonçalves", role="Desenvolve Mais · desenvolvimento de pessoas")
ev("subscribe", Wt(250), Wt(250) + 5.5, small=True)
CH = [("Minha trajetória", find("comecei", 285, 296) - 1), ("Ocupado, resultado ou crescimento?", 515), ("O cara que resolve tudo", 732),
      ("Técnico ou líder?", 946), ("A história das laranjas", 1060), ("Proatividade × sobrecarga", 1700),
      ("O que eu faria no seu lugar", 2064), ("Além da técnica", 2521), ("Exercício prático", 2887)]
CH_T = []
for n, (title, i) in enumerate(CH, 1):
    t = Wt(i) - 0.15; ev("chapter", t, t + 2.1, n=n, title=title); CH_T.append((t, title))
CH_T.append((Wt(3300), "Crescer pra onde?"))
def P(t0, t1, title, kicker="", items=()): ev("panel", t0, t1, title=title, kicker=kicker, items=list(items))
def row(t, icon, text, sub=""): return dict(t=t, k="row", icon=icon, text=text, sub=sub)
def num(t, n, icon, text, sub=""): return dict(t=t, k="num", n=n, icon=icon, text=text, sub=sub)
def chip(t, text): return dict(t=t, k="chip", text=text)
def bubble(t, text): return dict(t=t, k="bubble", text=text)
def stmt(t0, t1, lines): ev("statement", t0, t1, lines=lines)
def pop(t0, t1, icon, label): ev("pop", t0, t1, icon=icon, label=label)

pop(at("caramba", 82, 90), at("fulano", 91, 105) + 2.2, "weary_face", "por que pra mim não dá?")
stmt(at("carteira", 146, 165, -0.6), Wt(172) - 0.2, [("“trabalha bastante que um dia", "small"), ("o reconhecimento vai chegar”", "gold")])
stmt(at("será", 188, 204), at("será", 188, 204) + 4.6, [("será que só se esforçar", "ink"), ("é o suficiente?", "gold")])
t = at("competente", 205, 219, -0.3)
P(t, Wt(242) - 0.1, "Por que isso acontece?", "eu vejo muita gente", [
    row(t + 0.2, "hammer_and_wrench", "Competente…", "mas simplesmente não cresce"),
    row(at("qualificada", 227, 241), "rocket", "Não é a mais qualificada…", "mas essa pessoa evolui")])
c = Wt(CH[0][1]) + 2.0
P(c, at("porque", 433, 440, -0.2), "Minha trajetória", "de vendas ao desenvolvimento humano", [
    row(at("2012", 296, 302), "briefcase", "2012 · Seguros", "vendas"),
    row(at("2015", 303, 315), "package", "2015 · Logística", "São Bernardo do Campo"),
    row(at("josé", 316, 340), "round_pushpin", "São José dos Campos", "mudança, sem emprego, para recomeçar"),
    row(at("telecomunicações", 372, 385), "telephone_receiver", "Telecomunicações", "último emprego CLT"),
    row(at("empreender", 386, 397), "rocket", "Empreendedor", "vendendo notebooks"),
    row(at("hoje", 411, 432), "seedling", "Hoje", "consultoria e desenvolvimento de pessoas")])
c = Wt(515) + 2.0
P(c, Wt(561) - 0.1, "Não são a mesma coisa", "três situações", [
    num(c, 1, "hourglass_done", "Estar ocupado"),
    num(at("resultado", 521, 535), 2, "chart_increasing", "Entregar resultado"),
    num(at("crescimento", 530, 560), 3, "seedling", "Resultado que faz você crescer")])
P(at("quando", 593, 600), at("apagando", 634, 642, -0.3), "O que esse dia construiu?", "no fim do dia", [
    row(at("competência", 600, 633), "brain", "Uma competência nova?"),
    row(at("responsabilidade", 600, 633), "briefcase", "Uma responsabilidade nova?"),
    row(at("capacidade", 600, 633), "flexed_biceps", "Mais capacidade profissional?"),
    row(at("oportunidade", 600, 633), "handshake", "Uma nova oportunidade?")])
pop(at("apagando", 634, 642), at("apagando", 634, 642) + 3.5, "fire", "apagando incêndio")
stmt(at("ocupado", 701, 731), at("ocupado", 701, 731) + 5.5, [("estar ocupado", "ink"), ("≠ estar avançando", "gold")])
c = Wt(732) + 2.0
P(c, Wt(789), "O cara que todo mundo procura", "chama ele!", [
    row(at("equipamento", 732, 753), "gear", "O equipamento parou?", "chama ele!"),
    row(at("cliente", 754, 788), "telephone_receiver", "O cliente reclamou?", "chama ele!"),
    row(at("alguém", 754, 788), "puzzle_piece", "Ninguém consegue resolver?", "chama ele!"),
    row(at("importante", 770, 788), "crown", "Fica cada vez mais importante…")])
pop(Wt(815), Wt(815) + 4.0, "locked", "preso na própria função")
t = at("diferença", 895, 905)
P(t, We(935) + 2.5, "Tem uma diferença", "grava isso", [
    row(t + 0.3, "cross_mark", "Importante porque resolve tudo pessoalmente"),
    row(at("reconhecido", 923, 935), "check_mark_button", "Reconhecido porque cria resultados", "que continuam mesmo sem você")])
c = Wt(946) + 2.0
P(c, Wt(1031), "Competências diferentes", "técnico × líder", [
    row(c, "hammer_and_wrench", "Técnico", "resolve o problema muito bem"),
    row(at("liderar", 951, 989), "busts_in_silhouette", "Líder", "orienta pessoas · organiza processos · desenvolve a equipe"),
    chip(at("comunicação", 1013, 1030), "comunicação"), chip(at("relacionamento", 1013, 1030), "relacionamento"),
    chip(at("liderança", 1013, 1030), "liderança"), chip(at("tomada", 1013, 1030), "tomada de decisão"),
    chip(at("conflitos", 1013, 1030), "conflitos")])
stmt(at("contexto", 1049, 1052), Wt(1060) - 0.3, [("entender o contexto,", "ink"), ("o comportamento e a função", "gold")])
pop(at("laranja", 1147, 1156), at("laranja", 1147, 1156) + 4.5, "tangerine", "o vendedor de laranjas")
t = at("chefe", 1217, 1231)
P(t, Wt(1390) + 1.0, "Fulano", "o funcionário indignado", [
    row(t, "tangerine", "1ª ida: o preço da dúzia"),
    row(at("desconto", 1269, 1290), "tangerine", "2ª ida: tem desconto?"),
    row(at("descontinho", 1309, 1367), "tangerine", "3ª ida: e se for mais?"),
    row(at("pesquisador", 1378, 1389), "tired_face", "virou pesquisador de preço de laranja")])
t = at("ciclano", 1462, 1474)
P(t, Wt(1507) + 2.0, "Ciclano", "o que foi promovido · uma ida só", [
    row(t + 0.2, "money_bag", "O preço"),
    row(at("desconto", 1475, 1506), "chart_increasing", "Desconto em compras maiores"),
    row(at("quantidade", 1480, 1506), "package", "Negociação de uma quantidade maior"),
    row(at("laranjas", 1490, 1506), "tangerine", "Amostras para avaliar a qualidade")])
t = at("primeiro", 1563, 1580, -0.3)
P(t, Wt(1647) - 0.1, "A provocação da história", "fulano × ciclano", [
    row(t + 0.2, "check_mark_button", "O primeiro cumpriu a tarefa", "não deixou de cumprir"),
    row(at("segundo", 1581, 1590), "magnifying_glass_tilted_left", "O segundo enxergou além da tarefa", "o que poderia ser necessário"),
    row(at("merecia", 1613, 1646), "warning", "Nem um é ruim, nem o outro já merece promoção")])
stmt(at("profissional", 1659, 1679), Wt(1680) - 0.1, [("um executa a tarefa", "ink"), ("o outro entende o problema", "gold")])
pop(Wt(1680), Wt(1680) + 4.5, "key", "cabeça de dono")
P(Wt(1787), Wt(1864) - 0.1, "Quando a iniciativa vira abuso", "cuidado", [
    row(Wt(1787), "man_office_worker", "O trabalho dele"),
    row(at("colega", 1794, 1811), "busts_in_silhouette", "+ o do colega"),
    row(at("supervisor", 1794, 1811), "office_building", "+ o do supervisor"),
    row(at("dono", 1800, 1811), "crown", "+ o do dono"),
    row(at("reconhecer", 1825, 1863), "warning", "E na hora de reconhecer…", "a história é outra")])
stmt(at("confunda", 1864, 1920), at("confunda", 1864, 1920) + 5.0, [("proatividade", "gold"), ("≠ trabalhar sem limites", "ink")])
t = at("maneira", 1895, 1920, -1.2)
P(t, at("vale", 1950, 1964), "A iniciativa que eu defendo", "três perguntas", [
    num(t + 0.6, 1, "light_bulb", "Existe uma maneira melhor?"),
    num(at("compreendo", 1921, 1964), 2, "magnifying_glass_tilted_left", "Entendo o problema", "ou só cumpro ordem?"),
    num(at("solução", 1921, 1964), 3, "check_mark_button", "Levo uma solução", "não só mais um problema")])
stmt(at("autonomia", 1965, 2009), at("autonomia", 1965, 2009) + 5.0, [("cobrar iniciativa", "ink"), ("sem dar autonomia?", "gold")])
t = at("primeiro", 2086, 2201)
P(t, Wt(2234) - 0.1, "O que eu faria no seu lugar", "passo 1", [
    num(t, 1, "bullseye", "Descobrir o que a empresa espera", "para o próximo nível"),
    row(at("vendedor", 2150, 2201), "chart_increasing", "Vendedor que bate meta ≠ gerente", "são outras competências")])
P(Wt(2234), Wt(2314) + 2.5, "A conversa com o gestor", "passo 2", [
    bubble(at("crescer", 2263, 2279), "Eu quero crescer aqui."),
    bubble(Wt(2280), "O que vocês acham que eu já faço bem?"),
    bubble(at("desenvolver", 2291, 2313), "O que eu preciso desenvolver?"),
    bubble(at("chance", 2291, 2313), "Tenho chance de verdade de avançar?")])
stmt(at("continua", 2395, 2415), Wt(2437) - 0.2, [("“continua trabalhando, um dia chega”", "small"), ("chega quando? com quais critérios?", "gold")])
t = at("ponto", 2437, 2469, -0.4)
P(t, Wt(2470) + 3.0, "Do ponto A ao ponto B", "planejamento", [dict(t=t + 0.3, k="diagram")])
P(Wt(2521) + 2.0, Wt(2670), "Competente… mas", "além da técnica", [
    row(at("explicar", 2530, 2537), "speech_balloon", "Manja muito, mas não sabe explicar"),
    row(at("defensiva", 2578, 2621), "face_with_steam_from_nose", "Não aceita ser corrigido", "fica na defensiva"),
    row(at("delegar", 2578, 2621), "person_juggling", "Não delega", "acha que só ele faz direito")])
stmt(at("coração", 2689, 2709), at("coração", 2689, 2709) + 5.0, [("coração e cérebro", "gold"), ("não só conhecimento técnico", "ink")])
stmt(at("perfil", 2710, 2769), at("perfil", 2710, 2769) + 4.0, [("não existe", "small"), ("um perfil perfeito", "gold")])
pop(at("análise", 2773, 2781), at("análise", 2773, 2781) + 4.5, "clipboard", "análise comportamental")
EX1 = num(0, 1, "bullseye", "Onde eu quero chegar?", "seja específico")
EX2 = num(0, 2, "chart_increasing", "O que faço hoje que contribui?", "cumpro tarefa ou entendo problemas?")
EX3 = num(0, 3, "puzzle_piece", "O que está faltando?", "técnica · comunicação · organização · liderança")
t = at("papel", 2900, 2909)
q1 = at("onde", 2915, 2959)
P(t, Wt(3142), "Pega papel e caneta", "exercício prático · 3 perguntas", [dict(EX1, t=q1)] + [
    chip(at(w, 2960, 3003), lab) for w, lab in [("ganhar", "ganhar mais"), ("lideranças", "liderança"), ("própria", "conta própria"),
                                                ("empresa", "mudar de empresa"), ("profissão", "mudar de profissão"), ("família", "tempo para a família")]]
  + [dict(EX2, t=at("contribui", 3013, 3027)), dict(EX3, t=at("faltando", 3095, 3098))])
t = Wt(3142)
P(t, at("olha", 3260, 3299), "Agora, o mais importante", "exercício prático", [
    row(at("ação", 3148, 3156), "sparkles", "Escolha UMA ação", "que você consiga começar"),
    chip(at("conversa", 3204, 3230), "marcar a conversa com o gestor"), chip(at("treinamento", 3204, 3240), "um treinamento específico"),
    chip(at("registrar", 3204, 3260), "registrar seus resultados"), chip(at("orientação", 3204, 3270), "procurar orientação")])
ev("kinetic", Wt(3300) - 0.4, Wt(3303) + 3.0, kicker="talvez a pergunta seja", title="CRESCER PRA ONDE?", exit=Wt(3303) + 2.4, y=880, size=120)
pop(at("orientação", 3438, 3448), at("orientação", 3438, 3448) + 4.0, "handshake", "orientação individual")
stmt(at("contato", 3449, 3471), at("contato", 3449, 3471) + 4.5, [("quer conversar?", "small"), ("meu contato está na descrição", "gold")])
ev("subscribe", Wt(3484) - 0.3, We(3505) + 1.5, small=False)
ev("comment", Wt(3506), Wt(3582), text="Você conhece alguém que trabalha demais e não sai do lugar?")
ev("kinetic", Wt(3613) - 0.3, BASE_DUR + 0.5, kicker="porque isso é a sua vida", title="EXISTE UMA VIDA SÓ", exit=None, y=880, size=120)
EV.sort(key=lambda e: e["t0"])
_pn = [e for e in EV if e["kind"] == "panel"]
for a_, b_ in zip(_pn, _pn[1:]):
    if b_["t0"] - a_["t1"] < 0.4: a_["t1"] = b_["t0"]; a_["join_next"] = True; b_["join_prev"] = True

# ------------------------------------------------------------------ helpers de desenho
_ic = {}
def icon(name, size):
    k = (name, size)
    if k not in _ic: _ic[k] = Image.open(f"{ICONS}/{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _ic[k]
def wrap(text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if tw(c, font) > maxw and cur: out.append(cur); cur = w
        else: cur = c
    if cur: out.append(cur)
    return out
def shadow_box(size, radius, alpha=110, blur=18, off=12):
    w, h = size; im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([40, 40 + off, w + 40, h + 40 + off], radius=radius, fill=(0, 0, 0, alpha))
    return im.filter(ImageFilter.GaussianBlur(blur))

# ------------------------------------------------------------------ enquadramento
def crop_box(t, z, aspect=W / H, extra_y=0.0):
    cx, cy = face(t); sw, sh = 1920, 1080
    h = sh / z; w = h * aspect
    if w > sw: w = sw; h = w / aspect
    x0 = cx * sw - w / 2; y0 = cy * sh - h * (0.42 + extra_y)
    x0 = min(max(0, x0), sw - w); y0 = min(max(0, y0), sh - h)
    return (x0, y0, x0 + w, y0 + h)
CARD = (1080, 70, 1860, 1010)   # pessoa no layout de painel
PANEL = (60, 70, 1030, 1010)

def render_panel(t, e):
    pw, ph = PANEL[2] - PANEL[0], PANEL[3] - PANEL[1]
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = 40
    if e["kicker"]:
        spr, pad = text_sprite(" ".join(e["kicker"].upper()), F("Inter-Bold", 24), BLUE + (255,), shadow=False)
        im.alpha_composite(blur_reveal(spr, eo(pr(t, e["t0"] + 0.15, 0.35))), (48 - pad, y - pad)); y += 44
    ft = F("InterDisplay-ExtraBold", 66); lines = wrap(e["title"], ft, pw - 100)
    for j, l in enumerate(lines):
        spr, pad = text_sprite(l, ft, INK + (255,), shadow=False)
        im.alpha_composite(blur_reveal(spr, eo(pr(t, e["t0"] + 0.25 + 0.08 * j, 0.35))), (48 - pad, y - pad)); y += 76
    y += 26
    d.rounded_rectangle([48, y - 14, 140, y - 8], radius=3, fill=GOLD + (int(255 * eo(pr(t, e["t0"] + 0.4, 0.4))),))
    y += 18; cx_chip, cy_chip = 48, None
    for it in e["items"]:
        if t < it["t"] - 0.05: continue
        k = eo(pr(t, it["t"] - 0.05, 0.35)); dy = int(24 * (1 - k)); a = k
        if it["k"] in ("row", "num"):
            if cy_chip is not None: y = cy_chip + 84; cy_chip = None
            x = 48
            if it["k"] == "num":
                r = 30; kk = back(pr(t, it["t"] - 0.05, 0.3), 2.2)
                d.ellipse([x + 30 - r * kk, y + 44 - r * kk, x + 30 + r * kk, y + 44 + r * kk], fill=BLUE + (255,))
                if kk > 0.7:
                    fn = F("InterDisplay-Black", 34); bb = fn.getbbox(str(it["n"])); d.text((x + 30 - (bb[2] - bb[0]) / 2 - bb[0], y + 44 - (bb[3] - bb[1]) / 2 - bb[1]), str(it["n"]), font=fn, fill=(255, 255, 255, 255))
                x += 76
            ic = icon(it["icon"], 96); s = max(1, int(96 * back(pr(t, it["t"] - 0.05, 0.35), 2.0)))
            im.alpha_composite(with_alpha(ic.resize((s, s), Image.LANCZOS), a), (int(x + 46 - s / 2), int(y + 48 - s / 2 + dy)))
            tx = x + 118; fb = F("InterDisplay-Bold", 46); fs = F("Inter-Medium", 31)
            tl = wrap(it["text"], fb, pw - tx - 40); sl = wrap(it["sub"], fs, pw - tx - 40) if it["sub"] else []
            hh = len(tl) * 54 + len(sl) * 38; ty = y + 48 - min(hh, 92) / 2; top = ty
            for l in tl:
                spr, pad = text_sprite(l, fb, INK + (255,), shadow=False); im.alpha_composite(blur_reveal(spr, k), (int(tx - pad), int(ty - pad + dy))); ty += 54
            for l in sl:
                spr, pad = text_sprite(l, fs, GOLD + (255,), shadow=False); im.alpha_composite(blur_reveal(spr, k), (int(tx - pad), int(ty - pad + dy))); ty += 38
            y += max(108, int(top - y) + hh + 22)
        elif it["k"] == "chip":
            fc = F("Inter-Bold", 34); cw = tw(it["text"], fc) + 52
            if cy_chip is None: cy_chip = y + 6; cx_chip = 48
            if cx_chip + cw > pw - 40: cx_chip = 48; cy_chip += 74
            kk = back(pr(t, it["t"] - 0.05, 0.3), 2.0)
            box = Image.new("RGBA", (cw, 60), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rounded_rectangle([0, 0, cw - 1, 59], radius=30, fill=BLUE + (235,)); bd.text((26, 9), it["text"], font=fc, fill=(255, 255, 255, 255))
            if kk < 1: box = box.resize((max(1, int(cw * kk)), max(1, int(60 * kk))), Image.BICUBIC)
            im.alpha_composite(with_alpha(box, min(1, a * 1.5)), (int(cx_chip + cw / 2 - box.width / 2), int(cy_chip + 28 - box.height / 2)))
            cx_chip += cw + 14
        elif it["k"] == "bubble":
            fb = F("Inter-SemiBold", 40); ls = wrap(it["text"], fb, pw - 220); bh = len(ls) * 50 + 36; bw = max(tw(l, fb) for l in ls) + 56
            bx = 48; d.rounded_rectangle([bx, y + dy, bx + bw, y + bh + dy], radius=26, fill=(255, 255, 255, int(240 * a)))
            d.polygon([(bx + 30, y + bh + dy), (bx + 60, y + bh + dy), (bx + 26, y + bh + 24 + dy)], fill=(255, 255, 255, int(240 * a)))
            for j, l in enumerate(ls): d.text((bx + 28, y + 14 + j * 50 + dy), l, font=fb, fill=(20, 22, 30, int(255 * a)))
            y += bh + 44
        elif it["k"] == "diagram":
            kd = pr(t, it["t"], 2.2); ay = y + 300; ax, bx = 120, pw - 140
            for (px, lab, tt) in [(ax, "A", it["t"]), (bx, "B", it["t"] + 1.0)]:
                kk = back(pr(t, tt, 0.35), 2.0)
                if kk <= 0: continue
                s = int(110 * kk); im.alpha_composite(icon("round_pushpin", 110).resize((max(1, s), max(1, s))), (int(px - s / 2), int(ay - s)))
                fl = F("InterDisplay-Black", 56); d.text((px - tw(lab, fl) / 2, ay + 20), lab, font=fl, fill=(GOLD if lab == "B" else INK) + (255,))
            n = 18
            for j in range(n):
                if j / n > eio(cl_(kd * 1.2 - 0.2)): break
                xx = ax + 60 + (bx - ax - 120) * j / (n - 1); yy = ay - 50 - 70 * math.sin(math.pi * j / (n - 1))
                d.ellipse([xx - 6, yy - 6, xx + 6, yy + 6], fill=(255, 255, 255, 200))
            if t > it["t"] + 1.6:
                kq = back(pr(t, it["t"] + 1.6, 0.35), 2.0); fq = F("InterDisplay-Black", int(90 * max(0.1, kq)))
                d.text(((ax + bx) / 2 - tw("?", fq) / 2, ay - 230), "?", font=fq, fill=GOLD + (255,))
                fs = F("Inter-SemiBold", 32); s = "o que tem no meio do caminho?"
                d.text(((ax + bx) / 2 - tw(s, fs) / 2, ay + 120), s, font=fs, fill=INK + (int(255 * kq),) if kq <= 1 else INK + (255,))
            y += 420
    return im
def cl_(x): return 0.0 if x < 0 else 1.0 if x > 1 else x

def bg_blur(src):
    s = src.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BICUBIC)
    return Image.blend(s, Image.new("RGB", (W, H), PAL["bg"]), 0.55)

def compose_panel(src, t, e):
    """Transição tela cheia → (pessoa em card à direita + painel à esquerda)."""
    kin = 1.0 if e.get("join_prev") else eio(pr(t, e["t0"], 0.55)); kout = 0.0 if e.get("join_next") else eio(pr(t, e["t1"] - 0.55, 0.55)); k = min(kin, 1 - kout)
    z = zoom_at(t)
    full_box = crop_box(t, z); cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    card_src = crop_box(t, 1.0 + (z - 1.0) * 0.8, aspect=cw / ch)
    sb = tuple(full_box[j] + (card_src[j] - full_box[j]) * k for j in range(4))
    db = (0 + (CARD[0] - 0) * k, 0 + (CARD[1] - 0) * k, W + (CARD[2] - W) * k, H + (CARD[3] - H) * k)
    out = bg_blur(src).convert("RGBA") if k > 0.01 else Image.new("RGBA", (W, H))
    dw, dh = int(db[2] - db[0]), int(db[3] - db[1])
    piece = src.resize((dw, dh), Image.BICUBIC, box=sb).convert("RGBA")
    r = int(36 * k)
    if r > 0:
        out.alpha_composite(shadow_box((dw, dh), r, alpha=int(140 * k)), (int(db[0]) - 40, int(db[1]) - 40))
        m = Image.new("L", (dw, dh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, dw - 1, dh - 1], radius=r, fill=255)
        out.paste(piece, (int(db[0]), int(db[1])), m)
        ImageDraw.Draw(out).rounded_rectangle([db[0], db[1], db[2], db[3]], radius=r, outline=(255, 255, 255, int(60 * k)), width=2)
    else:
        out.paste(piece, (int(db[0]), int(db[1])))
    if k > 0.02:
        pnl = render_panel(t, e); pw, ph = pnl.size
        if e.get("join_next"): pnl = with_alpha(pnl, 1 - pr(t, e["t1"] - 0.25, 0.25))
        glass = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); ImageDraw.Draw(glass).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=36, fill=(10, 12, 22, 170), outline=(255, 255, 255, 40), width=2)
        glass.alpha_composite(pnl); x = PANEL[0] - int(80 * (1 - k))
        out.alpha_composite(with_alpha(glass, k), (x, PANEL[1]))
    return out

def full_frame(src, t):
    z = zoom_at(t)
    return src.resize((W, H), Image.BICUBIC, box=crop_box(t, z)).convert("RGBA")

def draw_statement(frame, layer, t, e):
    lines = e["lines"]; fbig = F("InterDisplay-ExtraBold", 64); fsm = F("Inter-SemiBold", 36)
    ws = [tw(l, fsm if s == "small" else fbig) for l, s in lines]; bw = max(ws) + 120; bh = 60 + sum(52 if s == "small" else 82 for _, s in lines)
    k = eo(pr(t, e["t0"], 0.35)) * (1 - eo(pr(t, e["t1"] - 0.35, 0.35)))
    x0 = (W - bw) // 2; y0 = H - bh - 60 + int(40 * (1 - k))
    frame = fx.glass_panel(frame, (x0, y0, x0 + bw, y0 + bh), t, e["t0"], e["t1"], tint=(12, 14, 24), alpha=0.6, blur=26)
    y = y0 + 30
    for j, (l, s) in enumerate(lines):
        f = fsm if s == "small" else fbig; col = GOLD if s == "gold" else (MUTED if s == "small" else INK)
        spr, pad = text_sprite(l, f, col + (255,)); spr = with_alpha(blur_reveal(spr, eo(pr(t, e["t0"] + 0.12 + 0.15 * j, 0.35))), k)
        layer.alpha_composite(spr, (int(W / 2 - spr.width / 2), int(y - pad))); y += 52 if s == "small" else 82
    return frame

def draw_pop(layer, t, e):
    k = back(pr(t, e["t0"], 0.4), 1.8); ko = eo(pr(t, e["t1"] - 0.35, 0.35)); a = min(1, k) * (1 - ko)
    cx, _ = face(t); side = 330 if cx > 0.45 else W - 330; y = 420 + 10 * math.sin((t - e["t0"]) * 2.5)
    s = max(1, int(190 * k)); g = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([60, 60, 360, 360], fill=GOLD + (70,))
    layer.alpha_composite(with_alpha(g.filter(ImageFilter.GaussianBlur(40)), a), (int(side - 210), int(y - 210)))
    layer.alpha_composite(with_alpha(icon(e["icon"], 190).resize((s, s), Image.LANCZOS), a), (int(side - s / 2), int(y - s / 2)))
    fl = F("InterDisplay-Bold", 38); lw = tw(e["label"], fl) + 56; kl = eo(pr(t, e["t0"] + 0.25, 0.3))
    pill = Image.new("RGBA", (lw, 66), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill); pd.rounded_rectangle([0, 0, lw - 1, 65], radius=33, fill=(12, 14, 24, 220)); pd.text((28, 10), e["label"], font=fl, fill=GOLD + (255,))
    layer.alpha_composite(with_alpha(pill, kl * (1 - ko)), (int(side - lw / 2), int(y + 120 + 20 * (1 - kl))))

def draw_chapter(frame, t, e):
    k = eio(pr(t, e["t0"], 0.35)) * (1 - eio(pr(t, e["t1"] - 0.4, 0.4)))
    blur = frame.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BICUBIC)
    tint = Image.new("RGBA", (W, H), PAL["bg"] + (200,)); blur.alpha_composite(tint)
    frame = Image.blend(frame, blur, k)
    d = ImageDraw.Draw(frame); kk = eo(pr(t, e["t0"] + 0.1, 0.4))
    fn = F("InterDisplay-Black", 260); num = f"{e['n']:02d}"
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((200, 360 + 40 * (1 - kk)), num, font=fn, fill=BLUE + (int(255 * kk * k),))
    fk = F("Inter-Bold", 30); ld.text((640, 430), " ".join("CAPÍTULO"), font=fk, fill=MUTED + (int(255 * kk * k),))
    ftt = F("InterDisplay-ExtraBold", 84); lines = wrap(e["title"], ftt, 1150)
    for j, l in enumerate(lines):
        kj = eo(pr(t, e["t0"] + 0.2 + 0.1 * j, 0.4)); spr, pad = text_sprite(l, ftt, INK + (255,))
        lay.alpha_composite(with_alpha(blur_reveal(spr, kj), k), (640 - pad + int(40 * (1 - kj)), 480 + j * 100 - pad))
    ld.rounded_rectangle([640, 480 + len(lines) * 100 + 10, 640 + 160 * kk, 488 + len(lines) * 100 + 10], radius=4, fill=GOLD + (int(255 * k),))
    frame.alpha_composite(lay); return frame

def draw_lower(layer, t, e):
    k = eo(pr(t, e["t0"], 0.45)); ko = eo(pr(t, e["t1"] - 0.45, 0.45))
    fn, fr = F("InterDisplay-Bold", 52), F("Inter-Medium", 30)
    w = max(tw(e["name"], fn), tw(e["role"], fr)) + 110; h = 150
    x = 80 - int((w + 120) * (1 - k)) - int((w + 120) * ko); y = H - h - 90
    layer.alpha_composite(shadow_box((w, h), 26), (x - 40, y - 40))
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(255, 255, 255, 245)); bd.rectangle([0, 18, 12, h - 18], fill=BLUE + (255,))
    bd.text((40, 24), e["name"], font=fn, fill=(18, 20, 30, 255)); bd.text((40, 92), e["role"], font=fr, fill=(90, 95, 110, 255))
    layer.alpha_composite(box, (x, y))

def draw_subscribe(layer, t, e):
    small = e["small"]; t0, t1 = e["t0"], e["t1"]
    k = back(pr(t, t0, 0.45), 1.6); ko = eo(pr(t, t1 - 0.4, 0.4)); a = min(1, k) * (1 - ko)
    sc = 0.75 if small else 1.15
    cx = 330 * sc + 60 if small else W / 2; cy = H - 150 * sc - 40 if small else H - 210
    tclick = t0 + 1.4; subscribed = t >= tclick + 0.1
    fb = F("InterDisplay-Bold", int(46 * sc)); txt = "Inscrito ✓" if subscribed else "Inscreva-se"
    bw, bh = int(360 * sc), int(96 * sc)
    press = 1 - 0.08 * math.sin(math.pi * pr(t, tclick, 0.2))
    btn = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, fill=((200, 200, 205, 255) if subscribed else (230, 33, 23, 255)))
    tx = bw / 2 - tw(txt, fb) / 2; bd.text((tx, bh * 0.2), txt, font=fb, fill=((40, 40, 45, 255) if subscribed else (255, 255, 255, 255)))
    btn = btn.resize((max(1, int(bw * press * min(1, k))), max(1, int(bh * press * min(1, k)))), Image.BICUBIC)
    layer.alpha_composite(shadow_box(btn.size, btn.height // 2, alpha=int(120 * a)), (int(cx - btn.width / 2 - 40), int(cy - btn.height / 2 - 40)))
    layer.alpha_composite(with_alpha(btn, a), (int(cx - btn.width / 2), int(cy - btn.height / 2)))
    # sino e joia
    for j, (name, tt) in enumerate([("bell", t0 + 2.0), ("thumbs_up", t0 + 2.6)]):
        kk = back(pr(t, tt, 0.35), 2.2)
        if kk <= 0: continue
        s = int(110 * sc * kk); wob = 12 * math.sin((t - tt) * 18) * math.exp(-(t - tt) * 3) if name == "bell" else 0
        ic = icon(name, 110).resize((max(1, s), max(1, s)), Image.LANCZOS).rotate(wob, resample=Image.BICUBIC)
        layer.alpha_composite(with_alpha(ic, a), (int(cx + bw / 2 + 30 * sc + j * 130 * sc), int(cy - s / 2)))
    # cursor que clica
    kc = eio(pr(t, t0 + 0.6, 0.8)); px = cx + 260 * sc - 220 * sc * kc; py = cy + 140 * sc - 120 * sc * kc
    if t < tclick + 0.9:
        cur = Image.new("RGBA", (60, 80), (0, 0, 0, 0)); cd = ImageDraw.Draw(cur)
        cd.polygon([(4, 4), (4, 64), (20, 50), (32, 76), (42, 72), (30, 46), (52, 46)], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255))
        if t >= tclick and t < tclick + 0.4:
            rr = 20 + 60 * pr(t, tclick, 0.4); ImageDraw.Draw(layer).ellipse([px - rr, py - rr, px + rr, py + rr], outline=(255, 255, 255, int(200 * (1 - pr(t, tclick, 0.4)))), width=4)
        layer.alpha_composite(with_alpha(cur, a), (int(px), int(py)))

def end_card(t):
    tl = t - BASE_DUR
    im = Image.new("RGBA", (W, H), PAL["bg"] + (255,)); gl = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(gl)
    for gx in range(0, W, 96): gd.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 14))
    for gy in range(0, H, 96): gd.line([(0, gy), (W, gy)], fill=(255, 255, 255, 14))
    im.alpha_composite(gl); d = ImageDraw.Draw(im)
    k = eo(pr(tl, 0, 0.6))
    for j, (txt, f, col, y) in enumerate([("DESENVOLVE MAIS", F("Inter-Bold", 34), MUTED, 300), ("Existe uma", F("InterDisplay-ExtraBold", 110), INK, 360), ("vida só.", F("InterDisplay-ExtraBold", 110), GOLD, 480)]):
        kj = eo(pr(tl, 0.15 * j, 0.6)); spr, pad = text_sprite(" ".join(txt) if j == 0 else txt, f, col + (255,))
        im.alpha_composite(blur_reveal(spr, kj), (130 - pad, y - pad))
    fs = F("Inter-Medium", 38)
    d.text((130, 680), "assista o próximo vídeo  →", font=fs, fill=INK + (int(255 * eo(pr(tl, 0.8, 0.5))),))
    d.text((130, 740), "e inscreva-se no canal", font=fs, fill=MUTED + (int(255 * eo(pr(tl, 1.0, 0.5))),))
    # áreas livres para os elementos de tela final do YouTube (à direita)
    return im

_grad = None
def bottom_grad(layer, t, e):
    global _grad
    if _grad is None:
        a = (np.clip((np.arange(H) - 560) / 520, 0, 1) ** 1.4 * 215).astype(np.uint8)
        g = np.zeros((H, W, 4), np.uint8); g[..., :3] = PAL["bg"]; g[..., 3] = a[:, None]; _grad = Image.fromarray(g)
    k = eo(pr(t, e["t0"], 0.4)) * (1 - (pr(t, e["exit"] + 0.3, 0.4) if e["exit"] else 0))
    layer.alpha_composite(with_alpha(_grad, k))

def draw_comment(layer, t, e):
    tmp = Image.new("RGBA", (1000, 220), (0, 0, 0, 0))
    fx.comment_card(tmp, "CanalDesenvolveMais", [(e["t0"] + 0.4, e["text"], None)], t, e["t0"], 20, 20, PAL, w=930, avatar_col=BLUE)
    ko = eo(pr(t, e["t1"] - 0.4, 0.4)); s = 1.45
    tmp = with_alpha(tmp.resize((int(1000 * s), int(220 * s)), Image.BICUBIC), 1 - ko)
    layer.alpha_composite(tmp, (int(W / 2 - 490 * s), H - int(220 * s) - 20))

def section_at(t):
    cur = None
    for tt, title in CH_T:
        if t >= tt + 2.1: cur = (tt, title)
    return cur

# ------------------------------------------------------------------ render
def render(src, t):
    if t >= BASE_DUR: return end_card(t)
    act = [e for e in EV if e["t0"] <= t < e["t1"]]
    pan = next((e for e in act if e["kind"] == "panel"), None)
    frame = compose_panel(src, t, pan) if pan else full_frame(src, t)
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    busy = pan is not None or any(e["kind"] in ("chapter", "kinetic") for e in act)
    sec = section_at(t)
    if sec and not busy: fx.section_tag(ui, sec[1].upper(), t, sec[0] + 2.4, 1e9, 50, 44, PAL, size=26)
    for e in act:
        k = e["kind"]
        if k == "statement": frame = draw_statement(frame, ui, t, e)
        elif k == "pop" and not pan: draw_pop(ui, t, e)
        elif k == "lower": draw_lower(ui, t, e)
        elif k == "subscribe": draw_subscribe(ui, t, e)
        elif k == "kinetic": bottom_grad(ui, t, e); fx.kinetic_title(ui, e["kicker"], e["title"], t, e["t0"], W / 2, e["y"], PAL, size=e["size"], exit_t=e["exit"], color=GOLD, kicker_scale=0.3)
        elif k == "comment": draw_comment(ui, t, e)
    frame.alpha_composite(ui)
    ch = next((e for e in act if e["kind"] == "chapter"), None)
    if ch: frame = draw_chapter(frame, t, ch)
    return frame

def grab(t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f"{E}/base_fast.mov", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), b) if len(b) == W * H * 3 else Image.new("RGB", (W, H))

if __name__ == "__main__" and sys.argv[1] == "frames":   # aula.py frames outdir t1 t2 ...
    os.makedirs(sys.argv[2], exist_ok=True)
    for ts in sys.argv[3:]:
        t = float(ts); render(grab(min(t, BASE_DUR - 0.1)), t).convert("RGB").save(f"{sys.argv[2]}/f_{t:07.2f}.jpg", quality=85)
    sys.exit()
if __name__ == "__main__" and sys.argv[1] == "events":
    for e in EV: print(f"{e['t0']:8.2f} {e['t1']:8.2f} {e['kind']:10s} {e.get('title') or e.get('label') or e.get('kicker') or e.get('lines', '')}")
    print("zoom keys", len(ZK))
    json.dump(dict(base=BASE_DUR, total=TOTAL, zoom=ZK, events=EV), open(f"{E}/events.json", "w"), ensure_ascii=False, default=str); sys.exit()

chunk, nch, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
NF = int(round(TOTAL * FPS)); per = math.ceil(NF / nch); f0, f1 = chunk * per, min(NF, (chunk + 1) * per)
if len(sys.argv) > 5: f0, f1 = int(float(sys.argv[4]) * FPS), int(float(sys.argv[5]) * FPS)
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.4f}", "-i", f"{E}/base_fast.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
last = bytes(W * H * 3)
for fi in range(f0, f1):
    t = fi / FPS
    if t < BASE_DUR:
        b = dec.stdout.read(W * H * 3)
        if len(b) == W * H * 3: last = b
    enc.stdin.write(render(Image.frombytes("RGB", (W, H), last), t).convert("RGB").tobytes())
    if (fi - f0) % 3000 == 0: print("chunk", chunk, fi - f0, "/", f1 - f0, flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
print("done chunk", chunk, OUT, "frames", f1 - f0, "TOTAL", round(TOTAL, 2), flush=True)
