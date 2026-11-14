import sys, json, soundfile as sf, numpy as np, sherpa_onnx
d=sys.argv[1]; wav=sys.argv[2]; out=sys.argv[3]
rec=sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx",
    tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)
x,sr=sf.read(wav,dtype="float32")
# chunk on silences roughly every <=20s to stay in model limits
import subprocess
words=[]
CH=20.0
i=0.0; N=len(x)/sr
# pick chunk boundaries at quietest 50ms frame near target
hop=int(0.05*sr); rms=np.sqrt(np.convolve(x**2,np.ones(hop)/hop,'same'))
bounds=[0]
t=0
while t+CH<N:
    lo=int((t+CH-4)*sr); hi=int((t+CH)*sr)
    b=lo+int(np.argmin(rms[lo:hi])); bounds.append(b); t=b/sr
bounds.append(len(x))
for a,b in zip(bounds[:-1],bounds[1:]):
    s=rec.create_stream(); s.accept_waveform(sr,x[a:b]); rec.decode_stream(s)
    r=s.result; off=a/sr
    toks=r.tokens; ts=r.timestamps
    durs=getattr(r,'durations',None)
    cur=None
    for k,(tok,tt) in enumerate(zip(toks,ts)):
        st=off+tt
        if tok.startswith("▁") or tok.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur={"text":tok.replace("▁","").strip(),"start":round(st,3),"end":round(st+0.08,3)}
        else:
            cur["text"]+=tok; cur["end"]=round(st+0.08,3)
    if cur: words.append(cur)
# refine end: next word start bound
for w,n in zip(words,words[1:]):
    w["end"]=round(min(max(w["end"],w["start"]+0.12), n["start"]),3)
json.dump({"words":words},open(out,"w"),ensure_ascii=False,indent=1)
print(" ".join(f"[{w['start']:.2f}]{w['text']}" for w in words))
