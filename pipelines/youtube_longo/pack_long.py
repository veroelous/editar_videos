import json, re, sys
W=json.load(open("transcripts/longo.json"))["words"]
# speaker blocks from Meet captions
t=open("meet_captions.srt",encoding="utf-8").read().strip().split("\n\n")
blocks=[]
def ts(s): h,m,r=s.split(":"); sec,ms=r.split(","); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
for b in t:
    L=b.split("\n")
    if len(L)<2 or "-->" not in L[1]: continue
    a,e=[ts(x.strip()) for x in L[1].split("-->")]
    cur=None; spk=[]
    for l in L[2:]:
        m=re.match(r"\((.+)\)$",l.strip())
        if m: cur=m[1]
        elif l.strip() and l.strip()!="-" and cur: spk.append((cur,len(l.split())))
    blocks.append((a,e,spk))
def speaker(t0):
    for a,e,spk in blocks:
        if a<=t0<e and spk:
            return max(spk,key=lambda x:x[1])[0].split()[0]
    return "?"
out=[]; cur=[]
for i,w in enumerate(W):
    if cur and (w["start"]-W[i-1]["end"]>=0.6):
        out.append(cur); cur=[]
    cur.append(w)
if cur: out.append(cur)
with open("takes_packed.md","w") as f:
    for ph in out:
        a=ph[0]["start"]; b=ph[-1]["end"]
        f.write(f"#{ph[0]['i']}-{ph[-1]['i']} [{int(a//60):02d}:{a%60:05.2f}-{b:7.2f}] {speaker(a+0.3)}: "+" ".join(x["text"] for x in ph)+"\n")
print(len(out),"frases")
