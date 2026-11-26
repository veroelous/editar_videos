"""Sintetizador mínimo (numpy) da trilha e dos SFX dos reels G2B: bateria, baixo, pad, whoosh, impacto, riser, tick, ding, brilho."""
import numpy as np
SR = 48000
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

