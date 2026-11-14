import json, numpy as np, soundfile as sf, sys
J=json.load(open(sys.argv[1])); W=J["words"]
x,sr=sf.read(sys.argv[2],dtype="float32")
hop=int(0.01*sr); n=len(x)//hop
rms=20*np.log10(np.sqrt((x[:n*hop].reshape(n,hop)**2).mean(1))+1e-9)
floor=np.percentile(rms,10); thr=-38.0
print("floor",round(floor,1))
for i,w in enumerate(W):
    s=w["start"]; nxt=W[i+1]["start"] if i+1<len(W) else len(x)/sr
    a=int(s/0.01); b=int(nxt/0.01)
    seg=rms[a:b]; above=np.where(seg>thr)[0]
    e=(a+above[-1]+1)*0.01 if len(above) else s+0.15
    w["end"]=round(min(max(e,s+0.1),nxt),2)
    a2=int(s/0.01); b2=int(min(w["end"], s+0.5)/0.01)
    ab2=np.where(rms[a2:b2]>thr)[0]
    if len(ab2) and ab2[0]>0: w["start"]=round(s+ab2[0]*0.01,2)
    # true onset: scan back up to 120ms for energy start
    a0=max(0,int((s-0.15)/0.01)); pre=rms[a0:a+3]; ab=np.where(pre>thr)[0]
    w["onset"]=round((a0+ab[0])*0.01,2) if len(ab) else s
    if i: w["onset"]=max(w["onset"],W[i-1]["end"])
    w["i"]=i
json.dump(J,open(sys.argv[1],"w"),ensure_ascii=False,indent=0)
for w in W: print(f'{w["i"]:3d} {w["onset"]:6.2f}-{w["end"]:6.2f} {w["text"]}')
