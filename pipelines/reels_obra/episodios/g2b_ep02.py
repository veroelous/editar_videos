"""G2B Esquadrias e Vidros — Diário da Reforma EP.02 "A demolição" (bruto: WhatsApp 2026-11-18).
Pouca evolução real: a barra sobe só 2% (5% → 7%), continuando de onde o EP.01 terminou.
Correspondência com o EP.01: dois comparativos ANTES|AGORA no mesmo ponto (corredor e entrada da oficina)."""
from compose_helpers import ph  # noqa

EP01 = "brutos/g2b/src"
SEGS = [
    # gancho: corredor do EP.01 (com o carro) → divisória → corredor hoje (vazio, com entulho)
    (0.0, 4.0, 13.0, 15.0, 1.00, 1.08, None, dict(src=EP01, a=(11.8, 13.0), wipe=(1.7, 0.8), ly=820, a_sub="EP. 01", b_sub="EP. 02")),
    (4.0, 8.5, 5.0, 12.6, 1.12, 1.02, "whip_x"),     # corredor (0–4,5 s do bruto têm o portão e a placa "Golfinho")
    (8.5, 13.0, 15.0, 19.0, 1.02, 1.12, "zoom"),     # pilhas de entulho
    (13.0, 17.5, 19.0, 24.5, 1.10, 1.00, "leak"),    # telhado retirado
    (17.5, 22.0, 29.3, 31.5, 1.00, 1.06, "whip_y", dict(src=EP01, a=(32.4, 35.0), wipe=(1.3, 0.8), ly=330, a_sub="EP. 01", b_sub="EP. 02")),
    (22.0, 26.5, 32.5, 37.5, 1.04, 1.12, "whip_x"),  # interior com o forro aberto
    (26.5, 31.0, 38.5, 46.4, 1.04, 1.16, "zoom"),    # quintal
]
END0, END1 = 31.0, 38.6
PHRASES = [
    ph(0.55, "Lembra", "disso?", 1.65),
    ph(2.05, "Olha como", "está agora.", 3.85),
    ph(4.35, "A obra", "já começou.", 8.3),
    ph(8.85, "O que era velho", "está saindo.", 12.8),
    ph(13.35, "Até o telhado", "já saiu do lugar.", 17.3),
    ph(19.4, "Mesmo lugar,", "outra cara.", 21.8),
    ph(22.35, "Por dentro,", "o forro já foi aberto.", 26.3),
    ph(26.85, "E isso", "é só o começo.", 30.6),
]
HOOK_KICKER, HOOK_TITLE = "diário da reforma · ep. 02", "COMEÇOU."
TOAST_TXT = "ATUALIZAÇÃO DA OBRA"
TAG_TXT = "EP. 02  •  A DEMOLIÇÃO"
PILL = (5, 7)
END_PCT = (5, 7)
END_NOTE = "+2% desde o EP. 01"
ANTES_FREEZE = (EP01, 4.2)
COVER_SRC = 20.5      # telhado aberto, fios e céu: o quadro mais dramático
EP_LABEL, COVER_TITLE, COVER_SUB = "EP. 02", "A DEMOLIÇÃO", "A sede da G2B já está mudando."
OUTRO_TXT = "Acompanhe a reforma. O DEPOIS vem aí."
