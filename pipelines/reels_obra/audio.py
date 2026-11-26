"""Trilha + SFX sintetizados para o reels "Diário da Reforma" (120 bpm, cortes na batida).
Uso: PROJ=brutos/g2b python3 audio.py   ->  PROJ/amb.wav (lido) e PROJ/audio_mix.wav (escrito)
amb.wav: som ambiente do bruto já remontado na linha do tempo (gerado por render.sh).
"""
import os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from compose import SEGS, END0, END1, COVER, OUTRO, PHRASES, HOOK_TITLE
from synth import *  # noqa  (instrumentos e utilitários)

PROJ = os.environ.get("PROJ", "brutos/g2b")
N = int((END1 + 0.6) * SR); BPM = 120; B = 60 / BPM
# ---------------------------------------------------------------- música
M = np.zeros(N)
CH = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # Am F C G
bars = int(END1 / (4 * B)) + 1
for b in range(bars):
    t0 = b * 4 * B; root, ch = CH[b % 4]
    if t0 >= END1: break
    add(M, pad(ch + [ch[0] + 12], 4 * B), t0)
    for s in range(8):  # baixo em colcheias
        ts = t0 + s * B / 2
        if END0 - 0.5 <= ts < END0: continue
        if ts < 4.0 and s % 2: continue
        add(M, bass(root - 12, B / 2 * 0.9), ts, 0.55 if ts < 4 else 0.85)
for i in range(int(END1 / B) + 1):
    ts = i * B
    if END0 - 0.5 <= ts < END0: continue
    if ts < 4.0:
        if i % 2 == 0: add(M, kick(0.55), ts)  # "batimento" no gancho
        continue
    if ts >= END0:
        if i % 2 == 0 and ts < END1 - 0.6: add(M, kick(0.6), ts)
        continue
    add(M, kick(0.95), ts)
    add(M, hat(i % 4 == 3), ts + B / 2)
    if ts >= 12.5 and i % 2 == 1: add(M, clap(), ts)
# fade final
fe = int((END1 - 1.2) * SR); M[fe:] *= np.linspace(1, 0, N - fe) ** 1.5

# ---------------------------------------------------------------- SFX
S = np.zeros(N)
for (o0, o1, s0, s1, z0, z1, tr, *cmp) in SEGS[1:]:
    if tr in ("whip_x", "whip_y"): add(S, whoosh(0.42), o0 - 0.28, 0.9)
    elif tr == "zoom": add(S, whoosh(0.35), o0 - 0.25, 0.7); add(S, impact(0.45), o0)
    elif tr == "leak": add(S, shimmer(), o0 - 0.1); add(S, impact(0.5), o0)
for i in range(len(HOOK_TITLE.replace(" ", ""))): add(S, tick(2200 + 90 * i, 0.16), 0.2 + i * 0.07)  # letras do título do gancho
for sg in SEGS:  # comparativos ANTES|AGORA: whoosh na divisória + impacto na revelação
    if len(sg) > 7:
        w0, wd = sg[7]["wipe"]; add(S, whoosh(wd + 0.1, up=False), sg[0] + w0 - 0.05, 0.9); add(S, impact(0.55), sg[0] + w0 + wd)
add(S, impact(0.6), 0.05)
for ws, _te in PHRASES: add(S, tick(1800, 0.09), ws[0][0])  # entrada das legendas
add(S, riser(1.7), END0 - 2.2, 0.9)
add(S, whoosh(0.6), END0 - 0.7, 1.1)
add(S, impact(1.0), END0)
for i in range(10): add(S, tick(2000 + 60 * i, 0.12), END0 + 0.9 + 0.15 + i * 0.045)  # "SIGA A G2B"
add(S, ding(), END0 + 3.0)
add(S, whoosh(0.4), OUTRO - 0.35, 0.8); add(S, impact(0.8), OUTRO); add(S, shimmer(1.0), OUTRO + 0.05, 1.4)

# ---------------------------------------------------------------- ambiente + mix
amb = np.zeros(N)
if os.path.exists(f"{PROJ}/amb.wav"):
    a, sr = sf.read(f"{PROJ}/amb.wav", dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    n = min(N, len(a)); amb[:n] = a[:n]
    ga = np.full(N, 0.22); ga[: int(4.0 * SR)] = 0.55; ga[int(END0 * SR):] = 0
    amb *= ga
mix = M * 0.75 + S * 0.8 + amb
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
# capa: impacto + brilho + subida curta até o flash que abre o gancho
C = np.zeros(int(COVER * SR))
add(C, impact(0.7), 0.0); add(C, shimmer(0.9), 0.05, 1.2); add(C, riser(COVER - 0.1), 0.0, 0.7); add(C, whoosh(0.35), COVER - 0.3, 0.8)
C = np.tanh(C * 1.1) / np.tanh(1.1); C = C / (np.abs(C).max() + 1e-9) * 0.7
mix = np.concatenate([C, mix])
st = np.stack([mix, mix], 1)
sf.write(f"{PROJ}/audio_mix.wav", st, SR)
print("ok", len(mix) / SR)
