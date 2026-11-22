"""Corrige os tempos de culto.json (feito do áudio m4a) para o áudio real do vídeo (sermao.mp4 = culto - 2040 s).
Alinha as sequências de palavras (difflib) com a transcrição nova do vídeo e interpola o desvio nas não casadas."""
import json, re, sys, unicodedata, difflib, numpy as np
S = "/tmp/claude-0/-home-user-editar-videos/0ca601e2-5ead-5526-97c2-0a2240f4e1d5/scratchpad/sync"
E = "/home/user/editar_videos/brutos/culto_1801/edit/transcripts"
n = lambda s: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())
T = json.load(open(f"{E}/culto.json")); TW = T["words"]
NW = json.load(open(f"{S}/full.json"))["words"]; OFF = 2040.0
idx = [i for i, w in enumerate(TW) if OFF - 30 <= w["start"] <= OFF + 4100]
a = [n(TW[i]["text"]) for i in idx]; b = [n(w["text"]) for w in NW]
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
pairs = []
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        if len(a[blk.a + k]) >= 2: pairs.append((idx[blk.a + k], NW[blk.b + k]["start"] + OFF - TW[idx[blk.a + k]]["start"], NW[blk.b + k]["end"] + OFF - TW[idx[blk.a + k]]["end"]))
pi = np.array([p[0] for p in pairs]); ds = np.array([p[1] for p in pairs]); de = np.array([p[2] for p in pairs])
from scipy.ndimage import median_filter
dsm = median_filter(ds, 9)   # tira casamentos errados isolados
print("casadas", len(pairs), "de", len(idx), "| desvio (s): p10 %.2f  mediana %.2f  p90 %.2f" % tuple(np.percentile(dsm, [10, 50, 90])))
exact = {p[0]: (p[1], p[2]) for p, m in zip(pairs, dsm) if abs(p[1] - m) < 0.35}
allx = np.arange(len(TW)); interp = np.interp(allx, pi, dsm)
for i, w in enumerate(TW):
    d0, d1 = exact.get(i, (interp[i], interp[i]))
    w["start"] = round(w["start"] + d0, 3); w["end"] = round(max(w["start"] + 0.05, w["end"] + d1), 3)
json.dump(T, open(f"{E}/culto_sync.json", "w"), ensure_ascii=False)
for t in (660, 1500, 2400, 3200, 3900): j = int(np.searchsorted([TW[i]["start"] for i in pi], t + OFF)); print(t, round(float(dsm[min(j, len(dsm) - 1)]), 2))
