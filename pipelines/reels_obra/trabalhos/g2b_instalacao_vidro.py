"""G2B — repost reeditado: bastidores da instalação de um vidro de grande porte com guindaste e ventosas
(bruto do Drive "VIDEO PARA HJ.mp4", postado em 2025; 75 s, 1080x1920, sem fala).
Obs.: parte da equipe veste camiseta de outra empresa; o texto não cita empresas além da G2B."""
from compose_helpers import ph  # noqa

SEGS = [
    (0.0, 3.0, 38.0, 43.0, 1.00, 1.10, None),                  # gancho: o vidro no alto, pendurado no guindaste
    (3.0, 7.5, 0.0, 14.0, 1.10, 1.00, "whip_x"),              # timelapse: preparação do içamento
    (7.5, 12.0, 14.0, 36.0, 1.00, 1.08, "zoom"),              # timelapse: guindaste trabalhando (destaques)
    (12.0, 15.5, 36.5, 44.0, 1.06, 1.00, "leak"),             # a peça entra
    (15.5, 19.5, 45.0, 52.0, 1.00, 1.08, "whip_y"),           # equipe posiciona com as ventosas
    (19.5, 23.5, 52.0, 60.0, 1.08, 1.00, "zoom"),             # ajuste fino
    (23.5, 27.5, 62.0, 74.5, 1.00, 1.10, "whip_x"),           # escada, acabamento, vidro no lugar
]
END0, END1 = 27.5, 35.0
HOOK_KICKER, HOOK_TITLE, HOOK_EXIT = "bastidores da instalação", "VIDRO NO ALTO", 2.7
TAG_TXT = "BASTIDORES  •  INSTALAÇÃO DE VIDRO"
PHRASES = [
    ph(0.9, "Como se instala", "um vidro desse tamanho?", 2.85),
    ph(3.35, "Tudo começa", "no planejamento.", 7.3),
    ph(12.35, "Peça por peça,", "com precisão.", 15.3),
    ph(15.85, "Muita técnica", "e cuidado no encaixe.", 19.3),
    ph(19.85, "Ajuste fino", "até ficar perfeito.", 23.3),
    ph(23.85, "Vidro instalado", "com segurança.", 27.3),
]
FEATURES = [
    (7.8, "Içamento com guindaste", "o vidro chega pelo alto"),
    (8.4, "Ventosas a vácuo", "firmeza para posicionar"),
    (9.0, "Equipe especializada", "cada movimento planejado"),
]
FEATURES_END = 11.7
CTA_KICKER, CTA_TITLE = "tem um projeto em vidro?", "PEÇA SEU ORÇAMENTO"
CTA_SUB = "Envie uma foto e as medidas do local."
CTA_SUB2 = "A G2B avalia as possibilidades para o seu projeto."
CONTACTS = ["(12) 98146-2275", "(12) 99662-3231"]
LOCATION = "São José dos Campos e região"
COVER_SRC, END_BG_SRC = 40.0, 70.0
COVER_KICKER, COVER_PILL = "bastidores da instalação", "G2B ESQUADRIAS E VIDROS"
COVER_TITLE = ["VIDRO DE", "GRANDE PORTE"]
COVER_SUB = "Do guindaste ao encaixe."
