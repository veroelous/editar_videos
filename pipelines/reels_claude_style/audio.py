"""Voz limpa + SFX sintetizados (whoosh nos cartoes, pop/click nos elementos, riser + musica leve no CTA)."""
import json, subprocess, numpy as np, soundfile as sf
E = "/home/user/editar_videos/brutos/edit"
SR = 48000
J = json.load(open(f"{E}/edl_out.json")); WD = {w["i"]: w for w in J["words"]}
S = lambda i: WD[i]["start"]
TOTAL = round(J["total"] + 2.1, 3)
RNG = J["ranges"]
def _rng(i):
    for r in RNG:
        if i in r["words"]: return r
def SS(i): return _rng(i)["out_start"]

# 1) voz: passa-alta, redução de ruído leve, compressão, loudnorm -14 LUFS (2 passes)
voice = f"{E}/voice_clean.wav"
chain = "highpass=f=80,afftdn=nf=-28:nr=10,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2"
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{E}/base.mov", "-af", chain + ",loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{E}/base.mov", "-af", chain + "," + ln, "-ar", str(SR), "-ac", "2", voice], check=True)
v, _ = sf.read(voice, dtype="float32")
mix = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
mix[:len(v)] += v

rng = np.random.default_rng(7)
def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e *= np.exp(-np.linspace(0, r, n)); return e
def add(sig, t, gain_db):
    g = 10 ** (gain_db / 20); i = int(t * SR); sig = sig[: len(mix) - i]
    mix[i:i + len(sig)] += (sig * g)[:, None]
def bandnoise(n, f0, f1):
    x = rng.standard_normal(n); X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < f0) | (fr > f1)] = 0; return np.fft.irfft(X, n)
def whoosh(d=0.32):
    n = int(d * SR); out = np.zeros(n); seg = 8
    for k in range(seg):  # varredura de banda ascendente
        a, b = k * n // seg, (k + 1) * n // seg
        f = 300 + 3500 * (k / seg) ** 1.5
        out[a:b] = bandnoise(b - a, f, f * 2.2)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    out = out * e; return out / (np.abs(out).max() + 1e-9)
def pop(f0=1500, f1=380, d=0.09):
    n = int(d * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 45); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.002, 6)
def click(d=0.03):
    n = int(d * SR); return bandnoise(n, 2000, 9000) * env(n, 0.001, 9) / 3
def riser(d=0.6):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 220 * (1500 / 220) ** (tt / d); ph = 2 * np.pi * np.cumsum(f) / SR
    s = 0.6 * np.sin(ph) + 0.4 * bandnoise(n, 1500, 8000) / 3
    return s * (tt / d) ** 2
def pad(d, bpm=112):
    n = int(d * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 587.3], [220.0, 261.6, 329.6, 493.9]]
    beat = 60 / bpm / 2
    for k in range(int(d / beat) + 1):
        a = int(k * beat * SR); b = min(n, a + int(beat * SR))
        ch = chords[(k // 4) % 2]
        seg = np.arange(b - a) / SR
        tone = sum(np.sin(2 * np.pi * f * seg) for f in ch) / len(ch)
        out[a:b] += tone * np.exp(-seg * 6)
    out *= np.minimum(1, (d - tt) / 1.0)  # fade-out final
    return out / (np.abs(out).max() + 1e-9)

# cartões em tela cheia
for t in [SS(7), SS(32), S(79) - 0.03, SS(89)]: add(whoosh(), t - 0.12, -21)
# itens da lista + riscos
for i in [32, 33, 36, 39]: add(pop(900, 300, 0.07), S(i), -24)
for k in range(4): add(click(), S(40) + 0.07 * k, -20)
# card da Bíblia sobe, tiles do EBO, chat
add(whoosh(0.25), S(56) - 0.08, -25)
for r in range(3): add(pop(1300 + 200 * r, 500, 0.06), S(94) - 0.05 + 0.07 * r, -22)
for j in range(3): add(click(), S(144) + j * 0.08, -22)
add(pop(1700, 420), S(144) + 0.42, -17)
add(pop(1100, 350), S(134) + 0.05, -26)
# CTA: riser -> música leve -> pop do botão
add(riser(0.55), SS(158) - 0.55, -22)
add(pad(TOTAL - SS(158)), SS(158), -27)
add(pop(1600, 400, 0.1), S(160) + 0.45, -15)

mix = mix[: int(TOTAL * SR)]
peak = np.abs(mix).max()
if peak > 0.97: mix *= 0.97 / peak
sf.write(f"{E}/audio_mix.wav", mix, SR)
print("audio ok", round(TOTAL, 2), "s, peak", round(float(peak), 3))
