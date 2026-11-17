"""Áudio da vídeo-aula: voz (base acelerada) nivelada a -14 LUFS + SFX sincronizados aos eventos de aula.py
(whoosh nos capítulos/painéis, plim nas frases-chave, pop nos ícones/itens, clique na inscrição) + pad no card final.
Pré-requisito: `aula.py events` (gera edit/events.json)."""
import json, os, subprocess, numpy as np, soundfile as sf
D = os.environ.get("PROJ", "/home/user/editar_videos/brutos/aula"); E = f"{D}/edit"; SR = 48000
J = json.load(open(f"{E}/events.json")); BASE, TOTAL, EV = J["base"], J["total"], J["events"]
chain = "highpass=f=80,afftdn=nf=-30:nr=6,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=120:makeup=1.3"
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{E}/base_fast.mov", "-af", chain + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{E}/base_fast.mov", "-af", chain + "," + ln, "-ar", str(SR), "-ac", "2", f"{E}/voice_clean.wav"], check=True)
v, _ = sf.read(f"{E}/voice_clean.wav", dtype="float32")
mix = np.zeros((int(round(TOTAL * SR)) + SR, 2), np.float32); mix[:len(v)] += v
rng = np.random.default_rng(3)
def bandnoise(n, f0, f1):
    x = rng.standard_normal(n); X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR); X[(fr < f0) | (fr > f1)] = 0; return np.fft.irfft(X, n)
def whoosh(d=0.45):
    n = int(d * SR); out = np.zeros(n); seg = 10
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg; f = 300 + 3000 * (k / seg) ** 1.5; out[a:b] = bandnoise(b - a, f, f * 2.2)
    out *= np.sin(np.linspace(0, np.pi, n)) ** 2; return out / (np.abs(out).max() + 1e-9)
def chime(f=1318.5, d=0.8):
    n = int(d * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t) + 0.2 * np.sin(2 * np.pi * f * 2 * t)) * np.exp(-t * 5); return s / np.abs(s).max()
def pop(f=520, d=0.09):
    n = int(d * SR); t = np.arange(n) / SR; fr = f * (1 + 1.2 * np.exp(-t * 60))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 45); return s / np.abs(s).max()
def click(d=0.03):
    n = int(d * SR); return bandnoise(n, 2000, 7000) * np.exp(-np.arange(n) / SR * 200)
def pad(d, bpm=92):
    n = int(d * SR); t = np.arange(n) / SR; out = np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 392.0]]
    beat = 60 / bpm
    for k in range(int(d / beat) + 1):
        a = int(k * beat * SR); b = min(n, a + int(beat * 2 * SR)); seg = np.arange(b - a) / SR
        out[a:b] += sum(np.sin(2 * np.pi * f * seg) for f in chords[(k // 4) % 4]) / 4 * np.exp(-seg * 2.2)
    out *= np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 2.5); return out / (np.abs(out).max() + 1e-9)
def put(sig, at, db):
    j = int(at * SR)
    if j < 0 or j >= len(mix): return
    sig = sig[: len(mix) - j]; mix[j:j + len(sig)] += (sig * 10 ** (db / 20)).astype(np.float32)[:, None]
for e in EV:
    k, t0 = e["kind"], e["t0"]
    if k == "chapter": put(whoosh(0.5), t0 - 0.05, -22); put(chime(988, 0.8), t0 + 0.2, -30)
    elif k == "panel":
        if not e.get("join_prev"): put(whoosh(0.4), t0 - 0.05, -27)
        for it in e["items"]:
            if it["t"] > t0 + 0.3: put(pop(620 if it["k"] == "chip" else 480), it["t"] - 0.03, -31 if it["k"] == "chip" else -28)
    elif k == "statement": put(chime(), t0 + 0.05, -27)
    elif k == "pop": put(pop(400, 0.12), t0, -24); put(chime(1568, 0.6), t0 + 0.12, -33)
    elif k == "kinetic": put(whoosh(0.5), t0, -24)
    elif k == "lower": put(whoosh(0.35), t0, -29)
    elif k == "subscribe": put(pop(500), t0, -26); put(click(), t0 + 1.4, -18); put(chime(1760, 0.5), t0 + 2.0, -31); put(pop(700), t0 + 2.6, -28)
    elif k == "comment": put(pop(560), t0, -27)
put(pad(TOTAL - BASE + 0.5), BASE - 0.5, -22)
mix = mix[:int(round(TOTAL * SR))]
peak = np.abs(mix).max()
if peak > 0.97: mix *= 0.97 / peak
sf.write(f"{E}/audio_mix.wav", mix, SR); print("audio", round(len(mix) / SR, 2), "s peak", round(float(peak), 3))
