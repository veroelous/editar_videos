"""Áudio do EBO longo: voz nivelada (-14 LUFS) + inserções (título, capítulos, final) com SFX/pad sintetizados."""
import json, subprocess, numpy as np, soundfile as sf
E = "/home/user/editar_videos/brutos/longo/edit"; SR = 48000
J = json.load(open(f"{E}/edl_out.json")); CH = J["chapters"]; BT = J["total"]
INS = [(CH[1]["start"], 3.2, "title")] + [(c["start"], 1.7, "chapter") for c in CH[2:]] + [(BT, 20.0, "end")]
chain = ("highpass=f=80,afftdn=nf=-30:nr=8,dynaudnorm=f=400:g=21:m=6:p=0.9,"
         "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1.5")
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{E}/base.mov", "-af", chain + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{E}/base.mov", "-af", chain + "," + ln, "-ar", str(SR), "-ac", "2", f"{E}/voice_clean.wav"], check=True)
v, _ = sf.read(f"{E}/voice_clean.wav", dtype="float32")
rng = np.random.default_rng(3)
def bandnoise(n, f0, f1):
    x = rng.standard_normal(n); X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR); X[(fr < f0) | (fr > f1)] = 0; return np.fft.irfft(X, n)
def whoosh(d=0.45):
    n = int(d * SR); out = np.zeros(n); seg = 10
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg; f = 300 + 3000 * (k / seg) ** 1.5; out[a:b] = bandnoise(b - a, f, f * 2.2)
    out *= np.sin(np.linspace(0, np.pi, n)) ** 2; return out / (np.abs(out).max() + 1e-9)
def chime(f=880, d=0.9):
    n = int(d * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t) + 0.2 * np.sin(2 * np.pi * f * 2 * t)) * np.exp(-t * 5)
    return s / np.abs(s).max()
def pad(d, bpm=96):
    n = int(d * SR); t = np.arange(n) / SR; out = np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 392.0]]
    beat = 60 / bpm
    for k in range(int(d / beat) + 1):
        a = int(k * beat * SR); b = min(n, a + int(beat * 2 * SR)); seg = np.arange(b - a) / SR
        ch = chords[(k // 4) % 4]
        out[a:b] += sum(np.sin(2 * np.pi * f * seg) for f in ch) / 4 * np.exp(-seg * 2.2)
    out *= np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 2.0)
    return out / (np.abs(out).max() + 1e-9)
parts = []; pos = 0
def g(db): return 10 ** (db / 20)
for tb, d, kind in INS:
    i = int(round(tb * SR)); parts.append(v[pos:i]); pos = i
    n = int(round(d * SR)); ins = np.zeros((n, 2), np.float32)
    def put(sig, at, db):
        j = int(at * SR); sig = sig[: n - j]; ins[j:j + len(sig)] += (sig * g(db))[:, None]
    if kind == "title": put(pad(d), 0, -24); put(whoosh(), 0, -22); put(chime(660), 0.9, -26)
    elif kind == "chapter": put(whoosh(), 0, -23); put(chime(988, 0.8), 0.15, -30)
    else: put(pad(d), 0, -22)
    parts.append(ins)
parts.append(v[pos:])
mix = np.concatenate(parts)
peak = np.abs(mix).max()
if peak > 0.97: mix *= 0.97 / peak
sf.write(f"{E}/audio_mix.wav", mix, SR)
print("audio", round(len(mix) / SR, 2), "s  peak", round(float(peak), 3))
