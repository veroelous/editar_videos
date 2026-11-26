"""Trilha + SFX do reels de portfólio (trabalho concluído): 120 bpm, tom maior (C G Am F), clima de entrega.
Uso: PROJ=... JOB=... python3 portfolio_audio.py  ->  PROJ/audio_mix.wav (usa PROJ/amb.wav se existir)."""
import os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portfolio as P
from portfolio import SEGS, END0, END1, COVER, PHRASES, HOOK_TITLE, FEATURES
from synth import *  # noqa

PROJ = os.environ.get("PROJ", "brutos/g2b_pergolado")
N = int((END1 + 0.6) * SR); B = 0.5
def bell(m, d=1.2, g=0.12):
    t = T(d); f = note(m); return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.45) * g

M = np.zeros(N)
CH = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [57, 60, 64]), (41, [57, 60, 65])]  # C G Am F
for b in range(int(END1 / 2) + 1):
    t0 = b * 2.0; root, ch = CH[b % 4]
    if t0 >= END1: break
    add(M, pad(ch + [ch[0] + 12], 2.0) * 1.1, t0)
    for s in range(4):
        ts = t0 + s * B
        if END0 - 0.5 <= ts < END0: continue
        add(M, bass(root, B * 0.9), ts, 0.7)
    # arpejo de sino (brilho de vidro) nas colcheias da segunda metade do compasso
    for s, m in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]):
        ts = t0 + 1.0 + s * 0.25
        if ts < END1 - 0.8 and not (END0 - 0.5 <= ts < END0): add(M, bell(m, 0.8, 0.07), ts)
for i in range(int(END1 / B) + 1):
    ts = i * B
    if END0 - 0.5 <= ts < END0 or ts > END1 - 0.8: continue
    if ts < 3.0:
        if i % 2 == 0: add(M, kick(0.5), ts)
        continue
    add(M, kick(0.85 if ts < END0 else 0.6), ts); add(M, hat(i % 4 == 3), ts + B / 2)
    if i % 2 == 1 and ts < END0: add(M, clap(), ts)
fe = int((END1 - 1.4) * SR); M[fe:] *= np.linspace(1, 0, N - fe) ** 1.5

S = np.zeros(N)
for (o0, o1, s0, s1, z0, z1, tr, *_) in SEGS[1:]:
    if tr in ("whip_x", "whip_y"): add(S, whoosh(0.42), o0 - 0.28, 0.9)
    elif tr == "zoom": add(S, whoosh(0.35), o0 - 0.25, 0.7); add(S, impact(0.4), o0)
    elif tr == "leak": add(S, shimmer(), o0 - 0.1); add(S, impact(0.45), o0)
add(S, impact(0.6), 0.05)
for i in range(len(HOOK_TITLE)): add(S, tick(2200 + 90 * i, 0.15), 0.2 + i * 0.06)
for ta, *_ in FEATURES: add(S, tick(2600, 0.14), ta); add(S, shimmer(0.4), ta + 0.02, 0.6)  # cada destaque
for ws, _te in PHRASES: add(S, tick(1800, 0.09), ws[0][0])
add(S, riser(1.6), END0 - 2.0, 0.8); add(S, whoosh(0.5), END0 - 0.45, 1.0); add(S, impact(0.9), END0)
add(S, shimmer(1.0), END0 + 0.15, 1.2)
if getattr(P, "CONTACTS", None):  # CTA com contatos
    for i in range(len(P.CTA_TITLE.replace(" ", ""))): add(S, tick(2000 + 40 * i, 0.10), END0 + 0.6 + 0.15 + i * 0.04)
    for j in range(len(P.CONTACTS)): add(S, impact(0.25), END0 + 2.2 + 0.3 * j); add(S, tick(2600, 0.14), END0 + 2.2 + 0.3 * j)
    add(S, ding(), END0 + 3.0)
else:  # CTA "comenta PALAVRA"
    for i in range(len(P.CTA_WORD.replace(" ", ""))): add(S, tick(2000 + 60 * i, 0.12), END0 + 0.8 + 0.15 + i * 0.05)
    for i in range(len(P.CTA_WORD)): add(S, tick(3200, 0.05), END0 + 2.3 + i * 0.6 / len(P.CTA_WORD))  # digitação do comentário
    add(S, ding(), END0 + 3.1)

amb = np.zeros(N)
if os.path.exists(f"{PROJ}/amb.wav"):
    a, _ = sf.read(f"{PROJ}/amb.wav", dtype="float32"); a = a.mean(1) if a.ndim > 1 else a
    n = min(N, len(a)); amb[:n] = a[:n] * 0.15; amb[int(END0 * SR):] = 0
mix = M * 0.75 + S * 0.8 + amb
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
C = np.zeros(int(COVER * SR))
add(C, impact(0.7), 0.0); add(C, shimmer(0.9), 0.05, 1.2); add(C, riser(COVER - 0.1), 0.0, 0.7); add(C, whoosh(0.35), COVER - 0.3, 0.8)
C = np.tanh(C * 1.1) / np.tanh(1.1); C = C / (np.abs(C).max() + 1e-9) * 0.7
mix = np.concatenate([C, mix])
sf.write(f"{PROJ}/audio_mix.wav", np.stack([mix, mix], 1), SR)
print("ok", len(mix) / SR)
