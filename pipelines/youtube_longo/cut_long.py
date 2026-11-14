"""Corte do EBO longo (YouTube 16:9). Seleção por índices de palavra (inclusivos), agrupada por capítulo."""
import json, subprocess, os
E = "/home/user/editar_videos/brutos/longo/edit"; SRC = "/home/user/editar_videos/brutos/longo/longo.mp4"
W = json.load(open(f"{E}/transcripts/longo.json"))["words"]
L = {}  # linha do takes_packed -> (a,b)
for n, line in enumerate(open(f"{E}/takes_packed.md"), 1):
    a, b = line.split()[0][1:].split("-"); L[n] = (int(a), int(b))
def lines(*ns):
    out = []
    for n in ns:
        if isinstance(n, tuple): out += [L[k] for k in range(n[0], n[1] + 1)]
        else: out.append(L[n])
    return out

CHAPTERS = [
    ("hook", "Gancho", [(601, 630)]),
    ("c1", "O versículo", [(110, 150)] + lines(12, (14, 16), (18, 24))),
    ("c2", "O que vem na sua cabeça?", lines((25, 45))),
    ("c3", "Como ler o contexto", lines(46) + [(840, 844)] + lines((48, 69)) + [(1137, 1143)] + lines((75, 93))),
    ("c4", "Paulo não está falando de dinheiro", lines((94, 108))),
    ("c5", "Próximo estudo: Jeremias 17:5", lines((109, 116))),
    ("c6", "Semear para a carne ou para o Espírito", lines((117, 139)) + [(2244, 2271)]),
    ("c7", "Dá pra viver 100% no Espírito?", lines((144, 147), (154, 162), (165, 172)) + [(2880, 2904)]
           + lines((189, 191), (194, 200), (213, 218), (223, 225), (236, 241), 246)),
    ("c8", "Não nos cansemos de fazer o bem", lines((247, 305))),
    ("c9", "O que você está cultivando?", lines((306, 339)) + [(5307, 5312)]),
]
GAP, PRE, POST, FPS = 0.6, 0.08, 0.15, 24

ranges = []
for cid, title, spans in CHAPTERS:
    for (a, b) in spans:
        cur = None
        for i in range(a, b + 1):
            w = W[i]
            if cur and w["start"] - W[i - 1]["end"] < GAP:
                cur["end_w"] = w["end"]; cur["words"].append(i)
            else:
                if cur: ranges.append(cur)
                cur = {"ch": cid, "start_w": w["start"], "end_w": w["end"], "words": [i]}
        ranges.append(cur)
for r in ranges:
    f, l = r["words"][0], r["words"][-1]
    prev_end = W[f - 1]["end"] if f > 0 else 0
    nxt = W[l + 1]["start"] if l + 1 < len(W) else W[l]["end"] + 1
    r["start"] = round(max(r["start_w"] - PRE, prev_end + 0.02), 3)
    r["end"] = round(min(r["end_w"] + POST, nxt - 0.02), 3)

os.makedirs(f"{E}/clips", exist_ok=True)
lst = open(f"{E}/clips/list.txt", "w"); off = 0.0; words_out = []
for k, r in enumerate(ranges):
    d = r["end"] - r["start"]; NF = max(1, round(d * FPS)); od = NF / FPS
    out = f"{E}/clips/seg_{k:04d}.mov"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{r['start']:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                    "-map", "0:v", "-map", "0:a", "-frames:v", str(NF), "-vf", f"fps={FPS},format=yuv420p",
                    "-af", f"aresample=48000,apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, od - 0.03):.4f}:d=0.03",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-c:a", "pcm_s16le", "-ac", "2", out], check=True)
    for i in r["words"]:
        w = W[i]
        words_out.append({"i": i, "text": w["text"], "start": round(w["start"] - r["start"] + off, 3),
                          "end": round(w["end"] - r["start"] + off, 3), "seg": k, "ch": r["ch"]})
    r["out_start"] = round(off, 4); r["dur"] = round(od, 4); off += od
    lst.write(f"file 'seg_{k:04d}.mov'\n")
lst.close()
chap = []
for cid, title, spans in CHAPTERS:
    st = min(r["out_start"] for r in ranges if r["ch"] == cid); chap.append({"id": cid, "title": title, "start": st})
json.dump({"ranges": ranges, "words": words_out, "total": round(off, 3), "chapters": chap}, open(f"{E}/edl_out.json", "w"), ensure_ascii=False, indent=0)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{E}/clips/list.txt", "-c", "copy", f"{E}/base.mov"], check=True)
print(len(ranges), "segmentos, total", round(off / 60, 2), "min")
for c in chap: print(f'{int(c["start"]//60):02d}:{c["start"]%60:04.1f} {c["title"]}')
