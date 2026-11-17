"""SRT da aula a partir das palavras (tempos / SP) + lista de capítulos para a descrição."""
import json, os, re
D = os.environ.get("PROJ", "/home/user/editar_videos/brutos/aula"); E = f"{D}/edit"; SP = 1.15
WS = json.load(open(f"{E}/transcripts/bruto.json"))["words"]
FIX = {"Traho": "Trabalho", "aon": "aonde", "desenvolve": "Desenvolve"}
def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
cues, cur = [], []
for i, w in enumerate(WS):
    txt = FIX.get(w["text"], w["text"])
    if cur and (w["start"] - WS[i - 1]["end"] > 0.7 or len(" ".join(c[2] for c in cur) + " " + txt) > 74):
        cues.append(cur); cur = []
    cur.append((w["start"] / SP, w["end"] / SP, txt))
    if txt[-1] in ".?!" and len(" ".join(c[2] for c in cur)) > 25: cues.append(cur); cur = []
if cur: cues.append(cur)
out = []
for n, c in enumerate(cues, 1):
    text = " ".join(x[2] for x in c)
    if len(text) > 40:
        ws = text.split(); best = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(text) / 2)); text = " ".join(ws[:best]) + "\n" + " ".join(ws[best:])
    end = c[-1][1] + 0.25
    if n < len(cues): end = min(end, cues[n][0][0] - 0.02)
    out.append(f"{n}\n{ts(c[0][0])} --> {ts(end)}\n{text}\n")
open(f"{D}/entrega/aula_legendas.srt", "w").write("\n".join(out))
J = json.load(open(f"{E}/events.json"))
chs = [("0:00", "Você trabalha muito e não vê resultado?")]
for e in J["events"]:
    if e["kind"] == "chapter":
        t = int(e["t0"] + 0.2); chs.append((f"{t // 60}:{t % 60:02d}", e["title"]))
for e in J["events"]:
    if e["kind"] == "kinetic" and "CRESCER" in e["title"]:
        t = int(e["t0"]); chs.append((f"{t // 60}:{t % 60:02d}", "Crescer pra onde?"))
print(len(out), "legendas"); print("\n".join(f"{a} {b}" for a, b in chs))
