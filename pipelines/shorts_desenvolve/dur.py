"""Estima a duração final de spans (mesma regra do shorts.py). Uso: dur.py <bruto.json> 'a-b,c-d' ..."""
import json, sys
WS = json.load(open(sys.argv[1]))["words"]
for arg in sys.argv[2:]:
    sp = [tuple(map(int, x.split("-"))) for x in arg.split(",")]; tot = 0
    for a, b in sp:
        s = WS[a]["start"]
        for i in range(a + 1, b + 1):
            if WS[i]["start"] - WS[i - 1]["end"] > 0.35: tot += WS[i - 1]["end"] - s + 0.16; s = WS[i]["start"]
        tot += WS[b]["end"] - s + 0.16
    print(arg, round(tot + 2.4, 1))
