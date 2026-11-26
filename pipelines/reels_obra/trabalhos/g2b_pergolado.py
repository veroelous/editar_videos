"""G2B — trabalho concluído: pergolado em vidro (bruto: WhatsApp 2026-11-26, 11,6 s, filmado de cima, sem fala)."""
from compose_helpers import ph  # noqa

SEGS = [
    (0.0, 3.0, 1.6, 4.2, 1.00, 1.12, None),                   # câmera revela o pergolado inteiro até a rua
    (3.0, 7.0, 4.2, 7.6, 1.10, 1.00, "whip_x"),               # panorâmica sobre o vidro (destaques)
    (7.0, 10.5, 7.6, 10.4, 1.00, 1.10, "zoom"),
    (10.5, 13.5, 9.4, 11.6, 1.55, 1.70, "leak", (0.55, 0.30)), # detalhe: encontro dos perfis no topo
    (13.5, 16.0, 0.0, 1.6, 1.00, 1.10, "whip_y"),             # vista de cima, piso através do vidro
]
END0, END1 = 16.0, 23.5   # cartão final mais longo: tempo para anotar os telefones
HOOK_KICKER, HOOK_TITLE, HOOK_EXIT = "trabalho entregue", "PERGOLADO", 2.7
TAG_TXT = "ENTREGUE  •  PERGOLADO EM VIDRO"
PHRASES = [
    ph(0.9, "Pergolado em vidro", "concluído.", 2.85),
    ph(7.35, "Mais luz,", "mais conforto.", 10.3),
    ph(10.85, "Acabamento", "em cada detalhe.", 13.3),
    ph(13.85, "Seu espaço,", "protegido e iluminado.", 15.8),
]
# destaques (t_aparece, título, subtítulo) — confirmar com o cliente se algum dado técnico mudar
FEATURES = [
    (3.35, "Cobertura em vidro", "luz natural o dia todo"),
    (4.05, "Estrutura em alumínio", "leve, firme e sem ferrugem"),
    (4.75, "Feito sob medida", "pensado para o seu espaço"),
]
FEATURES_END = 6.75
# CTA com contatos (aparece no cartão final)
CTA_KICKER, CTA_TITLE = "quer um assim no seu espaço?", "PEÇA SEU ORÇAMENTO"
CTA_SUB = "Envie uma foto e as medidas do local."
CTA_SUB2 = "A G2B avalia as possibilidades para o seu projeto."
CONTACTS = ["(12) 98146-2275", "(12) 99662-3231"]
LOCATION = "São José dos Campos e região"
COVER_SRC, END_BG_SRC = 3.2, 9.5
COVER_KICKER, COVER_PILL = "trabalho entregue", "G2B ESQUADRIAS E VIDROS"
COVER_TITLE = ["PERGOLADO", "EM VIDRO"]
COVER_SUB = "Luz natural com proteção."
