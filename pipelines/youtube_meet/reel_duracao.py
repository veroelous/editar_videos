import json,sys,re,unicodedata
def norm(s): return re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())
for f in sys.argv[1:]:
    R=json.load(open(f)); P=json.load(open(R["plan"])); D=json.load(open(f"{P['proj']}/edit/work_{P['id']}/dump.json"))
    ws=[w for w in D["words"] if w["blk"] in R["blks"]]
    def find(ph,last=False):
        n=norm(ph).split();k=len(n)
        for i in range(len(ws)-k+1):
            if [norm(w["text"]) for w in ws[i:i+k]]==n: return i+k-1 if last else i
        raise KeyError(f+": "+ph)
    try:
        a=find(R["from"]) if R.get("from") else 0; b=find(R["to"],True) if R.get("to") else len(ws)-1
        drop=set()
        for x,y in R.get("skip",[]): drop|=set(range(find(x),find(y,True)+1))
    except KeyError as e: print("ERRO",e); continue
    sel=[w for j,w in enumerate(ws) if a<=j<=b and j not in drop]
    rg=D["ranges"];o=0;last=None;s0=s1=None
    for w in sel:
        r=rg[w["rk"]];x=r["s"]+w["start"]-r["o"];y=r["s"]+w["end"]-r["o"]
        if last==(w["rk"],w["i"]-1): s1=y
        else:
            if s0 is not None: o+=s1-s0+0.37
            s0,s1=x,y
        last=(w["rk"],w["i"])
    o+=s1-s0+0.37
    print(f, round((o+2.95)/1.15,1),"s", " ".join(w["text"] for w in sel[:8]),"…"," ".join(w["text"] for w in sel[-6:]))
