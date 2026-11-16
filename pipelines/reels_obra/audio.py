"""Trilha + SFX sintetizados para o reels "Diário da Reforma" (120 bpm, cortes na batida).
Uso: PROJ=brutos/g2b python3 audio.py   ->  PROJ/amb.wav (lido) e PROJ/audio_mix.wav (escrito)
amb.wav: som ambiente do bruto já remontado na linha do tempo (gerado por render.sh).
"""
import os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from compose import SEGS, END0, END1, COVER, OUTRO

PROJ = os.environ.get("PROJ", "brutos/g2b")
SR = 48000; N = int((END1 + 0.6) * SR); BPM = 120; B = 60 / BPM
rng = np.random.default_rng(7)
def T(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r); return e
def add(buf, x, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += x[: j - i] * g
def lp(x, a):  # passa-baixa de 1 polo (a 0..1, menor = mais escuro)
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def lp_fast(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / np.sqrt(1 + (f / cutoff) ** 4); return np.fft.irfft(X, len(x))
def hp_fast(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 - 1 / np.sqrt(1 + (f / cutoff) ** 4); return np.fft.irfft(X, len(x))
def saw(f, d, det=0.0):
    t = T(d); return 2 * ((t * f * (1 + det)) % 1) - 1
def note(m): return 440 * 2 ** ((m - 69) / 12)

# ---------------------------------------------------------------- instrumentos
def kick(g=1.0):
    t = T(0.45); f = 48 + 110 * np.exp(-t / 0.035); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.16) * g
def clap():
    x = rng.standard_normal(int(0.25 * SR)); x = hp_fast(x, 900); e = env(len(x), 0.001, 0.07)
    for d in (0.0, 0.012, 0.024): e[int(d * SR):] += 0.5 * env(len(x) - int(d * SR), 0.001, 0.02)
    return x * e * 0.35
def hat(open_=False):
    x = hp_fast(rng.standard_normal(int(0.2 * SR)), 7000); return x * env(len(x), 0.001, 0.09 if open_ else 0.025) * 0.22
def bass(m, d):
    x = saw(note(m), d) + 0.5 * saw(note(m - 12), d); x = lp_fast(x, 380); return x * env(len(x), 0.004, d * 0.7) * 0.5
def pad(ms, d):
    x = sum(saw(note(m), d, det) for m in ms for det in (-0.004, 0.0, 0.005)); x = lp_fast(x, 1400)
    t = T(d); e = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4); return x * e * 0.045
def whoosh(d=0.45, up=True, g=1.0):
    x = rng.standard_normal(int(d * SR)); t = T(d)
    out = np.zeros_like(x); seg = 2048
    for i in range(0, len(x), seg):
        k = i / len(x); c = 300 + 5000 * (k if up else 1 - k) ** 1.5
        out[i:i + seg] = lp_fast(x[i:i + seg], c)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return out * e * 0.9 * g
def impact(g=1.0):
    t = T(1.6); f = 38 + 60 * np.exp(-t / 0.08); b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    n = lp_fast(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.12) * 0.5
    return (b + n) * g
def riser(d=1.6):
    t = T(d); f = 200 * 2 ** (3 * t / d); s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    n = hp_fast(rng.standard_normal(len(t)), 2000) * 0.25
    return (s + n) * (t / d) ** 2
def tick(f=2400, g=0.25):
    t = T(0.05); return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008) * g
def ding():
    t = T(1.2); return (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2349 * t)) * np.exp(-t / 0.35) * 0.18
def shimmer(d=0.7):
    t = T(d); x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (2093, 2637, 3136, 4186)) * 0.05
    return x * np.minimum(1, t / 0.05) * np.exp(-t / 0.25)

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
        if 27.5 <= ts < END0: continue
        if ts < 4.0 and s % 2: continue
        add(M, bass(root - 12, B / 2 * 0.9), ts, 0.55 if ts < 4 else 0.85)
for i in range(int(END1 / B) + 1):
    ts = i * B
    if 27.5 <= ts < END0: continue
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
for (o0, o1, s0, s1, z0, z1, tr) in SEGS[1:]:
    if tr in ("whip_x", "whip_y"): add(S, whoosh(0.42), o0 - 0.28, 0.9)
    elif tr == "zoom": add(S, whoosh(0.35), o0 - 0.25, 0.7); add(S, impact(0.45), o0)
    elif tr == "leak": add(S, shimmer(), o0 - 0.1); add(S, impact(0.5), o0)
for i in range(7): add(S, tick(2200 + 90 * i, 0.16), 0.2 + i * 0.07)  # letras do "O ANTES"
add(S, impact(0.6), 0.05)
for t in (1.75, 4.35, 8.85, 12.9, 15.55, 18.85, 22.85): add(S, tick(1800, 0.09), t)  # entrada das legendas
add(S, riser(1.7), 25.8, 0.9)
add(S, whoosh(0.6), 27.3, 1.1)
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
