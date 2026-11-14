"""Compositor 16:9 (YouTube) do EBO longo. Uso: compose_long.py <chunk_idx> <n_chunks> <out.mp4>
Camadas: video (reenquadrado) | painéis laterais / statements | lower-thirds. Cartões inseridos (título, capítulos, final)."""
import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

E = "/home/user/editar_videos/brutos/longo/edit"
FPS, W, H = 24, 1920, 1080
SW, SH = 1280, 720
J = json.load(open(f"{E}/edl_out.json"))
WL = J["words"]; WD = {w["i"]: w for w in WL if w["ch"] != "hook"}; WH = {w["i"]: w for w in WL if w["ch"] == "hook"}
RNG = J["ranges"]; BT = J["total"]
CH = J["chapters"]
CREAM = (242, 238, 230); INK = (17, 17, 17); BLUE = (43, 107, 251); DARK = (10, 10, 14); WHITE = (255, 255, 255); GRAY = (110, 110, 115)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(n, s):
    if (n, s) not in _fc: _fc[(n, s)] = ImageFont.truetype(FD + n + ".otf", s)
    return _fc[(n, s)]
def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def back(x, s=1.6): x = cl(x) - 1; return x * x * ((s + 1) * x + s) + 1
def pr(t, t0, d): return cl((t - t0) / d)
def tw(s, f): b = f.getbbox(s); return b[2] - b[0]
def S(i): return WD[i]["start"]
def EN(i): return WD[i]["end"]
def find(txt, lo, hi):
    for i in list(range(lo, hi + 1)) + list(range(max(0, lo - 30), lo)) + list(range(hi + 1, hi + 40)):
        if i in WD and WD[i]["text"].lower().strip(".,;:?!").startswith(txt.lower()):
            if not (lo <= i <= hi): print("find fora da janela", txt, lo, hi, "->", i, flush=True)
            return i
    raise KeyError((txt, lo, hi))
def wrap(text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if tw(c, font) > maxw and cur: out.append(cur); cur = w
        else: cur = c
    if cur: out.append(cur)
    return out

# ------------------------------------------------------------- inserções (cartões cheios)
CHS = {c["id"]: c for c in CH}
HOOK_END = CHS["c1"]["start"]
INS = [(HOOK_END, 3.2, ("title", None))]
for k, c in enumerate(CH[2:], 2):
    INS.append((c["start"], 1.7, ("chapter", k)))
INS.append((BT, 20.0, ("end", None)))
INS.sort(key=lambda x: x[0])
TOTAL = BT + sum(d for _, d, _ in INS)
def final_to(t):
    """tempo final -> ('base', t_base) ou ('card', kind, arg, t_local)"""
    acc = 0.0
    for tb, d, kind in INS:
        if t < tb + acc: return ("base", t - acc)
        if t < tb + acc + d: return ("card", kind, t - tb - acc)
        acc += d
    return ("base", t - acc)
def base_to_final(tb):
    return tb + sum(d for t0, d, _ in INS if t0 <= tb)

# ------------------------------------------------------------- layout + zoom
LAY = json.load(open(f"{E}/layout4fps.json"))
def portrait(fr_arr):
    cm = fr_arr.mean(axis=(0, 2))
    return cm[:200].mean() < 8 and cm[-200:].mean() < 8 and cm[500:780].mean() > 25
ZOOM = {}; last_t, z = -99, 1.04
BOTTOM_FROM = 1163.0  # a partir daqui a Ester aparece ao lado: sem zoom e painéis embaixo
for k, r in enumerate(RNG):
    if r["out_start"] - last_t >= 25: z = 1.18 if z == 1.04 else 1.04; last_t = r["out_start"]
    ZOOM[k] = z if r["out_start"] < BOTTOM_FROM else 1.04
SEG_STARTS = [r["out_start"] for r in RNG]
import bisect
def seg_of(tb): return max(0, bisect.bisect_right(SEG_STARTS, tb) - 1)

RMASK = Image.new("L", (565, 1000), 0); ImageDraw.Draw(RMASK).rounded_rectangle([0, 0, 564, 999], radius=28, fill=255)
SHADOW = Image.new("RGBA", (565 + 120, 1000 + 120), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).rounded_rectangle([60, 72, 625, 1072], radius=28, fill=(0, 0, 0, 120))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(24))
def frame_from_base(im, tb):
    arr = np.asarray(im)
    if portrait(arr):
        tile = im.crop((444, 0, 836, 680))
        small = tile.resize((32, 57), Image.BILINEAR).crop((0, 14, 32, 32))
        bg = small.resize((W, H), Image.BICUBIC)
        bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.38)
        tl = tile.resize((565, 1000), Image.BICUBIC)
        bg.paste(SHADOW, (700 - 282 - 60, 40 - 60), SHADOW)
        bg.paste(tl, (700 - 282, 40), RMASK)
        return bg, "P"
    z = ZOOM[seg_of(tb)]
    w, h = SW / z, SH / z
    if z > 1.1:
        cx, cy = 0.45 * SW, 0.40 * SH
        x0 = min(max(0, cx - w / 2), SW - w); y0 = min(max(0, cy - h / 2), SH - h)
    else:
        x0, y0 = (SW - w) / 2, 0
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)), "S"

# ------------------------------------------------------------- conteúdo: versículos e statements
V = {
 "g6_7": ("7", "Não vos enganeis: de Deus não se zomba; pois aquilo que o homem semear, isso também ceifará."),
 "g6_8": ("8", "Porque o que semeia para a sua própria carne da carne colherá corrupção; mas o que semeia para o Espírito do Espírito colherá vida eterna."),
 "g6_9": ("9", "E não nos cansemos de fazer o bem, porque a seu tempo ceifaremos, se não desfalecermos."),
 "g6_10": ("10", "Por isso, enquanto tivermos oportunidade, façamos o bem a todos, mas principalmente aos da família da fé."),
 "g6_1": ("1", "Irmãos, se alguém for surpreendido nalguma falta, vós, que sois espirituais, corrigi-o com espírito de brandura; e guarda-te para que não sejas também tentado."),
 "g6_2": ("2", "Levai as cargas uns dos outros e, assim, cumprireis a lei de Cristo."),
 "g6_3": ("3", "Porque, se alguém julga ser alguma coisa, não sendo nada, a si mesmo se engana."),
 "g6_5": ("5", "Porque cada um levará o seu próprio fardo."),
 "g6_6": ("6", "Mas aquele que está sendo instruído na palavra faça participante de todas as coisas boas aquele que o instrui."),
}
# painéis: (t0, t1, tipo, dados)
P = []
def verse_panel(ref, items, t1, label=None):
    """items: [(t_aparece, chave_versiculo)] — mostra versículos acumulando (máx 2 visíveis)"""
    P.append((items[0][0] - 0.2, t1, "verse", dict(ref=ref, items=items, label=label)))
def statement(t0, t1, lines, label=None):
    """lines: [(t_aparece, texto, estilo)] estilo: ink|blue|strike|small"""
    P.append((min(t0, min(x[0] for x in lines)) - 0.15 if False else min(x[0] for x in lines) - 0.15, t1, "stmt", dict(lines=lines, label=label)))

# Gl 6:7-10 lido pela Sandra (linhas 18-23 -> palavras 255..360)
i9 = find("E", 294, 306); i10 = find("por", 330, 360); ife = find("fé", 340, 368)
verse_panel("Gálatas 6:7-10", [(S(255), "g6_7"), (S(273), "g6_8"), (S(i9), "g6_9"), (S(i10), "g6_10")], EN(ife) + 1.0, label="ARA")
# envelope de oferta (gancho e cap.2)
statement(WH[618]["start"], WH[630]["end"] + 0.3, [(WH[618]["start"], "já vi em", "small"), (WH[618]["start"], "envelope", "ink"), (WH[619]["start"], "de oferta", "blue")])
statement(S(618), EN(630) + 0.5, [(S(618), "já vi em", "small"), (S(618), "envelope", "ink"), (S(619), "de oferta", "blue")])
# 2 Co 9:6 (outro texto)
P.append((S(704) + 2.0, EN(738) + 0.5, "single", dict(ref="2 Coríntios 9:6", label="outro texto · outro estudo",
          text="Aquele que semeia pouco pouco também ceifará; e o que semeia com fartura com abundância também ceifará.")))
# contexto: antes / texto / depois
statement(S(849), EN(935) + 0.5, [(S(849), "Gálatas 6:7-10", "ink"), (S(851), "← o que vem antes", "blue"), (S(find("depois", 860, 883)), "o que vem depois →", "blue")], label="como ler o contexto")
# Gálatas 5: carne x Espírito
P.append((S(find("obras", 956, 990)) - 0.25, EN(1083) + 0.5, "two", dict(ref="Gálatas 5", t_left=S(find("obras", 956, 990)), t_right=S(find("fruto", 1009, 1033)),
          left=("obras da carne", "v.19-21", ["prostituição", "impureza", "inimizades", "ciúmes", "iras", "invejas", "…"]),
          right=("fruto do Espírito", "v.22-23", ["amor", "alegria", "paz", "longanimidade", "benignidade", "bondade", "fidelidade", "mansidão", "domínio próprio"]))))
# Gl 6:1-2
verse_panel("Gálatas 6:1-2", [(S(1094), "g6_1"), (S(1288), "g6_2")], EN(1299) + 0.4, label="ARA")
# Gl 6:3-6
_inv = find("enganeis", 1351, 1390) - 1
verse_panel("Gálatas 6:3-6", [(S(1300), "g6_3"), (S(1340), "g6_5"), (S(find("aquele", 1351, 1376)), "g6_6")], S(_inv) - 0.3, label="ARA")
verse_panel("Gálatas 6:7", [(S(_inv), "g6_7")], EN(1409) + 0.4, label="ARA")
# não é investimento
statement(S(1410), EN(1450) + 1.2, [(S(find("investimento", 1410, 1420)), "investimento financeiro", "strike"),
                                    (S(1435), "comportamento", "ink"), (S(find("vida", 1439, 1450)), "vida cristã", "blue")])
statement(S(find("isolado", 1535, 1551)), EN(1582) + 0.5, [(S(find("isolado", 1535, 1551)), "versículo isolado", "strike"), (S(find("contexto", 1575, 1582)), "contexto", "blue")])
# Jeremias 17:5 (próximo estudo)
P.append((S(1668) - 0.2, EN(1764), "single", dict(ref="Jeremias 17:5", label="próximo estudo",
          text="Maldito o homem que confia no homem, faz da carne mortal o seu braço e aparta o seu coração do SENHOR!")))
verse_panel("Gálatas 6:8", [(S(1817), "g6_8")], EN(1843) + 0.6, label="ARA")
# semear para a carne
statement(S(1857), EN(2017) + 0.3, [(S(find("egoísmo", 1894, 1905)), "egoísmo", "ink"), (S(find("desejos", 1904, 1930)), "desejos", "ink"),
                                    (S(find("inveja", 1913, 1940)), "inveja", "ink"), (S(find("rivalidade", 1931, 2017)), "rivalidade", "ink"),
                                    (S(find("comportamentos", 1939, 2017)), "comportamentos que destroem", "blue")], label="semear para a carne")
# cap 7
statement(S(2312), EN(2328) + 0.4, [(S(find("plenamente", 2312, 2328)), "100%", "blue"), (S(find("plenamente", 2312, 2328)), "no Espírito?", "ink")])
statement(S(2880), EN(2904) + 0.8, [(S(2880), "não é 100%…", "small"), (S(find("alimenta", 2880, 2904)), "quem você", "ink"), (S(find("alimenta", 2880, 2904)), "alimenta mais?", "blue")])
irel = find("relacionamento", 3153, 3219)
statement(S(irel), EN(3219) + 0.3, [(S(irel), "relacionamento", "blue"), (S(irel) + 0.3, "com Deus", "ink")])
statement(S(3951), EN(3989) + 1.0, [(S(3951), "como alimentar o espírito", "small"), (S(find("palavra", 3951, 3989)), "palavra", "ink"),
                                    (S(find("oração", 3951, 3989)), "oração", "ink"), (S(find("adoração", 3951, 3989)), "adoração", "ink"),
                                    (S(find("estudo", 3951, 3989)), "estudo bíblico", "blue")])
# cap 8
statement(S(4320), EN(4336) + 0.6, [(S(4320), "fazer o bem", "ink"), (S(4324), "cansa.", "blue")])
verse_panel("Gálatas 6:9", [(S(4490), "g6_9")], EN(4504) + 0.4, label="ARA")
verse_panel("Gálatas 6:10", [(S(4505), "g6_10")], EN(4550) + 0.4, label="ARA")
statement(S(find("todos", 4528, 4532)), EN(4538) + 0.6, [(S(find("todos", 4528, 4532)), "a todos.", "blue")])
statement(S(4620), EN(4653) + 0.3, [(S(4620), "a carne", "ink"), (S(find("sozinha", 4620, 4633)), "se alimenta sozinha", "blue")])
iq = find("quebra-fofoca", 4665, 4747)
statement(S(iq) - 0.6, EN(4767) + 0.4, [(S(iq) - 0.6, "quebra-fofoca:", "small"), (S(iq) - 0.6, "vamos alimentar", "ink"), (S(iq) - 0.6, "o espírito", "blue")])
# cap 9
statement(S(5066), EN(5073) + 1.2, [(S(5066), "o que eu estou", "ink"), (S(find("cultivando", 5066, 5073)), "cultivando?", "blue")])
statement(S(find("muda", 5083, 5106)), EN(5106) + 0.6, [(S(find("muda", 5083, 5106)), "muda", "ink"), (S(find("semente", 5083, 5106)), "a semente", "blue")])
statement(S(5148), EN(5158) + 0.6, [(S(find("colher", 5148, 5158)), "colher", "strike"), (S(find("semear", 5148, 5158)), "semear", "blue")], label="o foco")
FINALQ = (S(5242) - 0.1, EN(5269) + 1.6)
# lower-thirds
LT = [(S(110) + 0.3, "Manoel Gonçalves", "EBO · Estudo Bíblico Online")]
NAMES = {"Sandra": "Sandra Maria", "Lilian": "Lilian Crepaldi", "Jose": "José Correia", "Gabriela": "Gabriela Castro"}
# participantes: detecção de layout P (4 fps) + rótulo do Meet no tempo de origem
import re as _re
caps = open(f"{E}/meet_captions.srt", encoding="utf-8").read().strip().split("\n\n")
def tss(s): h, m, r = s.split(":"); a, b = r.split(","); return int(h) * 3600 + int(m) * 60 + int(a) + int(b) / 1000
CB = []
for b in caps:
    Ls = b.split("\n")
    if len(Ls) < 2 or "-->" not in Ls[1]: continue
    a, e = [tss(x.strip()) for x in Ls[1].split("-->")]; cur = None; sp = []
    for l in Ls[2:]:
        m = _re.match(r"\((.+)\)$", l.strip())
        if m: cur = m[1]
        elif l.strip() and l.strip() != "-" and cur: sp.append((cur, len(l.split())))
    CB.append((a, e, sp))
def spk_at(src_t):
    for a, e, sp in CB:
        if a <= src_t < e and sp: return max(sp, key=lambda x: x[1])[0].split()[0]
    return None
def base_to_src(tb):
    r = RNG[seg_of(tb)]; return r["start"] + (tb - r["out_start"])
runs = []; s = "".join(LAY); st = None
for i, c in enumerate(s + "S"):
    if c == "P" and st is None: st = i
    if c != "P" and st is not None:
        if (i - st) / 4 >= 2.5: runs.append((st / 4, i / 4))
        st = None
last_shown = {}
for a, b in runs:
    name = None
    for k in range(int(a * 4), int(b * 4)):
        n = spk_at(base_to_src(k / 4 + 0.5))
        if n in NAMES: name = n; break
    if name and a - last_shown.get(name, -999) > 90:
        LT.append((a + 0.3, NAMES[name], "participante do EBO")); last_shown[name] = a
LT.sort()

# ------------------------------------------------------------- render helpers
PX, PW = 1150, 700
def panel_base(h, label, ref, k):
    img = Image.new("RGBA", (PW + 80, h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(img); sd.rounded_rectangle([40, 52, PW + 40, h + 52], radius=32, fill=(0, 0, 0, 90))
    img = img.filter(ImageFilter.GaussianBlur(18))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 40, PW + 40, h + 40], radius=32, fill=CREAM + (250,))
    y = 86
    if ref:
        d.ellipse([82, y + 12, 96, y + 26], fill=BLUE + (255,))
        d.text((110, y), ref, font=F("Inter-Bold", 34), fill=INK + (255,))
        if label: d.text((PW + 40 - 44 - tw(label, F("Inter-SemiBold", 26)), y + 6), label, font=F("Inter-SemiBold", 26), fill=GRAY + (255,))
        y += 70
    return img, d, y
def place_panel(layer, img, t, t0, t1):
    kin = eo(pr(t, t0, 0.35)); kout = eo(pr(t, t1 - 0.3, 0.3))
    a = min(kin, 1 - kout)
    if a < 1:
        arr = np.asarray(img).copy(); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); img = Image.fromarray(arr)
    if t >= BOTTOM_FROM:
        x = (W - img.width) // 2; y = H - img.height + 10 + int(120 * (1 - kin)) + int(120 * kout)
        layer.alpha_composite(img, (x, y))
    else:
        x = PX - 40 + int(120 * (1 - kin)) + int(120 * kout)
        layer.alpha_composite(img, (x, max(20, (H - img.height) // 2)))

def draw_verse(layer, t, t0, t1, D):
    fb = F("InterDisplay-SemiBold", 44); fn = F("InterDisplay-Bold", 34)
    shown = [(ta, key) for ta, key in D["items"] if t >= ta - 0.05][-2:]
    blocks = []; hh = 0
    for ta, key in shown:
        n, txt = V[key]; ls = wrap(txt, fb, PW - 150); blocks.append((ta, n, ls)); hh += len(ls) * 56 + 30
    img, d, y = panel_base(max(260, hh + 130), D.get("label"), D["ref"], 1)
    for j, (ta, n, ls) in enumerate(blocks):
        k = eo(pr(t, ta - 0.05, 0.3)); old = j < len(blocks) - 1
        col = (INK if not old else (150, 150, 152)) + (int(255 * (0.25 + 0.75 * k)),)
        d.text((84, y + 4), n, font=fn, fill=BLUE + (255,))
        for li, l in enumerate(ls): d.text((140, y + li * 56), l, font=fb, fill=col)
        y += len(ls) * 56 + 30
    place_panel(layer, img, t, t0, t1)

def draw_single(layer, t, t0, t1, D):
    fb = F("InterDisplay-SemiBold", 46); ls = wrap(D["text"], fb, PW - 120)
    img, d, y = panel_base(len(ls) * 58 + 150, D.get("label"), D["ref"], 1)
    for li, l in enumerate(ls):
        k = eo(pr(t, t0 + 0.2 + li * 0.15, 0.3))
        d.text((84, y + li * 58), l, font=fb, fill=INK + (int(255 * (0.25 + 0.75 * k)),))
    place_panel(layer, img, t, t0, t1)

def draw_two(layer, t, t0, t1, D):
    img, d, y = panel_base(640, None, D["ref"], 1)
    for side, (title, vv, items), ts, x in [(0, D["left"], D["t_left"], 84), (1, D["right"], D["t_right"], 84 + PW // 2 - 10)]:
        if t < ts - 0.05: continue
        col = (120, 120, 125) if side == 0 else BLUE
        d.text((x, y), title, font=F("InterDisplay-Bold", 38), fill=(INK if side == 0 else BLUE) + (255,))
        d.text((x, y + 46), vv, font=F("Inter-SemiBold", 24), fill=GRAY + (255,))
        for j, it in enumerate(items):
            k = eo(pr(t, ts + 0.15 + j * 0.12, 0.25))
            d.text((x, y + 96 + j * 46), it, font=F("Inter-Medium", 34), fill=(col if side == 1 else (70, 70, 75)) + (int(255 * k),))
    place_panel(layer, img, t, t0, t1)

def draw_stmt(layer, t, t0, t1, D):
    sizes = {"ink": 84, "blue": 84, "strike": 84, "small": 40}
    rows = []; hh = 0
    for ta, txt, sty in D["lines"]:
        f = F("InterDisplay-ExtraBold" if sty != "small" else "Inter-SemiBold", sizes[sty])
        while tw(txt, f) > PW - 110 and sty != "small": f = F("InterDisplay-ExtraBold", f.size - 6)
        rows.append((ta, txt, sty, f))
        if t >= ta - 0.05: hh += f.size * 1.18 + 8
    img, d, y = panel_base(int(hh + (150 if D.get("label") else 90)), None, D.get("label"), 1)
    if not D.get("label"): y = 84
    for ta, txt, sty, f in rows:
        if t >= ta - 0.05:
            k = back(pr(t, ta - 0.05, 0.28)); a = int(255 * min(1, pr(t, ta - 0.05, 0.12)))
            col = BLUE if sty == "blue" else (GRAY if sty == "small" else INK)
            dy = int(18 * (1 - min(1, k)))
            d.text((84, y + dy), txt, font=f, fill=col + (a,))
            if sty == "strike":
                ks = eo(pr(t, ta + 0.45, 0.25))
                if ks > 0:
                    bb = f.getbbox(txt); ww = bb[2] - bb[0]; ym = y + bb[1] + (bb[3] - bb[1]) * 0.55
                    d.line([(78, ym + 6), (78 + (ww + 16) * ks, ym + 6 - 14 * ks)], fill=BLUE + (255,), width=14)
        y += int(f.size * 1.18 + 8)
    place_panel(layer, img, t, t0, t1)
DRAW = {"verse": draw_verse, "single": draw_single, "two": draw_two, "stmt": draw_stmt}

def draw_lt(layer, t):
    for t0, name, role in LT:
        if t0 <= t < t0 + 5.5:
            k = eo(pr(t, t0, 0.4)); ko = eo(pr(t, t0 + 5.1, 0.4))
            fn, fr = F("InterDisplay-Bold", 46), F("Inter-Medium", 28)
            w = max(tw(name, fn), tw(role, fr)) + 90; h = 128
            x = 70 - int((w + 80) * (1 - k)) - int((w + 80) * ko); y = 880
            box = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rounded_rectangle([30, 40, w + 30, h + 40], radius=22, fill=(0, 0, 0, 80)); box = box.filter(ImageFilter.GaussianBlur(14))
            bd = ImageDraw.Draw(box)
            bd.rounded_rectangle([30, 30, w + 30, h + 30], radius=22, fill=(255, 255, 255, 250))
            bd.rectangle([30, 30, 42, h + 30], fill=BLUE + (255,))
            bd.text((72, 46), name, font=fn, fill=INK + (255,)); bd.text((72, 104), role, font=fr, fill=GRAY + (255,))
            layer.alpha_composite(box, (x - 30, y - 30))

def grid(img, col, alpha):
    d = ImageDraw.Draw(img, "RGBA")
    for gx in range(0, W, 120): d.line([(gx, 0), (gx, H)], fill=col + (alpha,), width=1)
    for gy in range(0, H, 120): d.line([(0, gy), (W, gy)], fill=col + (alpha,), width=1)
def label(d, text, x, y, col, size=34, center=False):
    f = F("Inter-SemiBold", size); w = tw(text, f) + 30
    if center: x = (W - w) // 2
    d.ellipse([x, y + size * 0.36, x + 14, y + size * 0.36 + 14], fill=BLUE + (255,)); d.text((x + 30, y), text, font=f, fill=col + (255,))

def card_title(tl):
    img = Image.new("RGB", (W, H), CREAM); grid(img, INK, 12); d = ImageDraw.Draw(img, "RGBA")
    label(d, "EBO · Estudo Bíblico Online · Gálatas 6:7-10", 0, 300, (80, 80, 85), center=True)
    f1 = F("InterDisplay-ExtraBold", 104); t1 = "Tudo que o homem semear…"
    k1 = eo(pr(tl, 0.1, 0.4)); bb = f1.getbbox(t1)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], 400 + int(30 * (1 - k1))), t1, font=f1, fill=INK + (int(255 * k1),))
    f2 = F("InterDisplay-ExtraBold", 92); t2 = "será que é sobre dinheiro?"
    k2 = eo(pr(tl, 0.9, 0.3)); bb = f2.getbbox(t2); w2 = bb[2] - bb[0]; x2 = (W - w2) // 2
    if k2 > 0:
        d.rectangle([x2 - 26, 588, x2 - 26 + (w2 + 52) * k2, 712], fill=BLUE)
        if k2 > 0.9: d.text((x2 - bb[0], 600 - bb[1] + 8), t2, font=f2, fill=WHITE)
    return img
def card_chapter(tl, k):
    c = CH[k]
    img = Image.new("RGB", (W, H), CREAM); grid(img, INK, 12); d = ImageDraw.Draw(img, "RGBA")
    ke = eo(pr(tl, 0.0, 0.35))
    num = f"{k:02d}"; fN = F("InterDisplay-Black", 230)
    d.text((160, 330 + int(40 * (1 - ke))), num, font=fN, fill=BLUE + (int(255 * ke),))
    ft = F("InterDisplay-ExtraBold", 84); ls = wrap(c["title"], ft, 1150)
    for j, l in enumerate(ls):
        kj = eo(pr(tl, 0.15 + 0.1 * j, 0.35))
        d.text((520 + int(40 * (1 - kj)), 390 + j * 100), l, font=ft, fill=INK + (int(255 * kj),))
    label(d, "EBO · Gálatas 6:7-10", 520, 320, (90, 90, 95))
    return img
def card_end(tl):
    img = Image.new("RGB", (W, H), CREAM); grid(img, INK, 12); d = ImageDraw.Draw(img, "RGBA")
    k = eo(pr(tl, 0, 0.4))
    label(d, "Estudo Bíblico Online", 140, 250, (80, 80, 85))
    rows = [("E", "studo"), ("B", "íblico"), ("O", "nline")]
    ft = F("InterDisplay-Black", 96); fr = F("InterDisplay-ExtraBold", 96)
    for r, (L, rest) in enumerate(rows):
        kt = back(pr(tl, 0.2 + 0.1 * r, 0.25)); y = 330 + r * 140; s = 120 * kt
        if kt > 0:
            d.rounded_rectangle([140 + 60 - s / 2, y + 60 - s / 2, 140 + 60 + s / 2, y + 60 + s / 2], radius=16, fill=BLUE)
            if kt > 0.85:
                bb = ft.getbbox(L); d.text((200 - (bb[2] - bb[0]) / 2 - bb[0], y + 60 - (bb[3] - bb[1]) / 2 - bb[1]), L, font=ft, fill=WHITE)
        kr = eo(pr(tl, 0.55 + 0.1 * r, 0.3))
        if kr > 0:
            bb = fr.getbbox("E"); d.text((280, y + 60 - (bb[3] - bb[1]) / 2 - bb[1]), rest, font=fr, fill=INK + (int(255 * kr),))
    kb = back(pr(tl, 1.2, 0.3))
    if kb > 0:
        fb = F("Inter-Bold", 44); txt = "toda quinta-feira · 20h · online"; bw = tw(txt, fb) + 70
        d.rounded_rectangle([140, 790, 140 + bw * kb, 880], radius=45, fill=BLUE)
        if kb > 0.9: d.text((175, 808), txt, font=fb, fill=WHITE)
    d.text((140, 920), "próximo estudo: Jeremias 17:5 — \"maldito o homem que confia no homem\"", font=F("Inter-Medium", 32), fill=(80, 80, 85, int(255 * pr(tl, 1.6, 0.4))))
    return img
def card_finalq(t):
    img = Image.new("RGB", (W, H), DARK); grid(img, WHITE, 10); d = ImageDraw.Draw(img, "RGBA")
    t0 = FINALQ[0]
    f1 = F("InterDisplay-Bold", 70); f2 = F("InterDisplay-ExtraBold", 100)
    a = "Se você não recebesse nada em troca…"; b = "continuaria fazendo o bem?"
    k1 = eo(pr(t, t0, 0.4)); bb = f1.getbbox(a)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], 400), a, font=f1, fill=WHITE + (int(255 * k1),))
    ib = find("continuaria", 5242, 5269); k2 = eo(pr(t, S(ib) - 0.1, 0.35)); bb = f2.getbbox(b)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], 520 + int(30 * (1 - k2))), b, font=f2, fill=BLUE + (int(255 * k2),))
    return img

# ------------------------------------------------------------- main (por chunk)
chunk, nchunks, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
NF = int(round(TOTAL * FPS)); per = math.ceil(NF / nchunks)
f0, f1 = chunk * per, min(NF, (chunk + 1) * per)
if len(sys.argv) > 5:
    if sys.argv[4].startswith("F"): f0, f1 = int(sys.argv[4][1:]), int(sys.argv[5][1:])
    else: f0, f1 = int(float(sys.argv[4]) * FPS), int(float(sys.argv[5]) * FPS)
# primeiro frame base necessário
first_b = None
for fi in range(f0, f1):
    m = final_to(fi / FPS)
    if m[0] == "base": first_b = int(round(m[1] * FPS)); break
dec = None; cur_b = None; last = None
if first_b is not None:
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{first_b / FPS:.4f}", "-i", f"{E}/base.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    cur_b = first_b - 1
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for fi in range(f0, f1):
    t = fi / FPS; m = final_to(t)
    if m[0] == "card":
        kind, arg = m[1]; tl = m[2]
        img = card_title(tl) if kind == "title" else card_chapter(tl, arg) if kind == "chapter" else card_end(tl)
        enc.stdin.write(img.tobytes()); continue
    tb = m[1]; want = min(int(round(tb * FPS)), int(BT * FPS) - 1)
    while cur_b < want:
        b = dec.stdout.read(SW * SH * 3)
        if len(b) < SW * SH * 3: break
        last = b; cur_b += 1
    if FINALQ[0] <= tb < FINALQ[1]:
        enc.stdin.write(card_finalq(tb).tobytes()); continue
    frame, lay = frame_from_base(Image.frombytes("RGB", (SW, SH), last), tb)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for t0, t1, kind, D in P:
        if t0 <= tb < t1: DRAW[kind](layer, tb, t0, t1, D)
    draw_lt(layer, tb)
    frame = frame.convert("RGBA"); frame.alpha_composite(layer)
    enc.stdin.write(frame.convert("RGB").tobytes())
    if fi % 2400 == 0: print("chunk", chunk, "frame", fi - f0, "/", f1 - f0, flush=True)
enc.stdin.close(); enc.wait()
if dec: dec.terminate()
print("done chunk", chunk, OUT, "frames", f1 - f0, "TOTAL", round(TOTAL, 2), flush=True)
