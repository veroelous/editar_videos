"""G2B Esquadrias e Vidros — Diário da Reforma EP.01 "O antes" (bruto: WhatsApp 2026-11-14)."""
from compose_helpers import ph  # noqa

SEGS = [
    (0.0, 4.0, 0.0, 4.4, 1.00, 1.10, None),
    (4.0, 8.5, 11.0, 17.4, 1.12, 1.02, "whip_x"),   # começa depois da placa "Vidraçaria Golfinho"
    (8.5, 12.5, 17.4, 24.2, 1.02, 1.12, "zoom"),
    (12.5, 18.5, 25.0, 37.4, 1.10, 1.00, "leak"),
    (18.5, 22.5, 38.6, 45.2, 1.00, 1.10, "whip_y"),
    (22.5, 28.0, 46.0, 56.3, 1.04, 1.16, "zoom"),
]
END0, END1 = 28.0, 35.6
PHRASES = [
    ph(1.75, "Guarde bem", "essa imagem.", 3.85),
    ph(4.35, "Essa é a sede da", "G2B hoje.", 8.3),
    ph(8.85, "Onde cada vidro e esquadria", "ganha forma.", 12.3),
    ph(12.9, "Aqui o trabalho", "não para…", 15.35),
    ph(15.55, "…mas chegou a hora de", "EVOLUIR.", 18.3),
    ph(18.85, "Cada canto", "vai mudar.", 22.3),
    ph(22.85, "Daqui a pouco,", "nada disso vai existir.", 27.6),
]
HOOK_KICKER, HOOK_TITLE = "diário da reforma", "O ANTES"
TOAST_TXT = "REGISTRANDO O INÍCIO DA REFORMA"
TAG_TXT = "EP. 01  •  O INÍCIO"
PILL = (0, 3)          # pílula REFORMA durante o vídeo
END_PCT = (0, 5)       # barra do cartão final (é onde o próximo episódio começa)
END_NOTE = ""
ANTES_FREEZE = ("brutos/g2b/src", 4.2)   # quadro do ANTES no cartão final (portão aberto, EP.01)
COVER_SRC = 12.5
EP_LABEL, COVER_TITLE, COVER_SUB = "EP. 01", "O ANTES", "A sede da G2B vai mudar."
OUTRO_TXT = "Acompanhe a reforma. O DEPOIS vem aí."
