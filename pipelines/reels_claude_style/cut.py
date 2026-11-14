import json, subprocess, os, sys
E="/home/user/editar_videos/brutos/edit"; SRC="/home/user/editar_videos/brutos/reels_claude_2.mp4"
W=json.load(open(f"{E}/transcripts/reels_claude_2.json"))["words"]
DROP=set(range(16,20))|{95,105,106}|set(range(107,115))|set(range(129,133))|set(range(145,158))
SPD=1.1
PUNCH={63,64,65,66,67,68,133,134}
GAP=0.15; PRE=0.05; POST=0.07
keep=[w for w in W if w["i"] not in DROP]
ranges=[]
for w in keep:
    st=w["start"]
    if ranges and (w["i"]==ranges[-1]["last"]+1) and st-ranges[-1]["end_w"]<GAP and ((w["i"] in PUNCH)==ranges[-1]["punch"]):
        r=ranges[-1]; r["end_w"]=w["end"]; r["last"]=w["i"]; r["words"].append(w["i"])
    else:
        ranges.append({"start_w":st,"end_w":w["end"],"first":w["i"],"last":w["i"],"words":[w["i"]],"punch":w["i"] in PUNCH})
# padding without overlap with neighbors' words (source-time)
for k,r in enumerate(ranges):
    prev_end=W[r["first"]-1]["end"] if r["first"]>0 else 0
    nxt_st=W[r["last"]+1]["start"] if r["last"]+1<len(W) else 71.9
    r["start"]=round(max(r["start_w"]-PRE,prev_end+0.01, 0),3)
    r["end"]=round(min(r["end_w"]+POST,nxt_st-0.01),3)
# last range: give tail for end card (silence after "lá.")
ranges[-1]["end"]=round(min(71.9,ranges[-1]["end_w"]+0.25),3)
os.makedirs(f"{E}/clips",exist_ok=True)
off=0.0; words_out=[]
lst=open(f"{E}/clips/list.txt","w")
for k,r in enumerate(ranges):
    d=round(r["end"]-r["start"],3); NF=max(1,round(d/SPD*30)); od=NF/30
    vf="scale=1080:1920:flags=lanczos"
    if r["punch"]: vf="scale=1242:2208:flags=lanczos,crop=1080:1920:81:150"
    out=f"{E}/clips/seg_{k:03d}.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(r["start"]),"-t",str(d),"-i",SRC,
         "-vf",vf+f",setpts=PTS/{SPD},fps=30,format=yuv420p","-af",f"aresample=48000,atempo={SPD},apad,atrim=0:{od:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0,od-0.03):.3f}:d=0.03",
         "-frames:v",str(NF),"-c:v","libx264","-preset","fast","-crf","14","-c:a","pcm_s16le","-ar","48000","-ac","2",out.replace(".mp4",".mov")]
    subprocess.run(cmd,check=True)
    # actual duration
    ad=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out.replace(".mp4",".mov")]).decode())
    for i in r["words"]:
        w=W[i]; words_out.append({"i":i,"text":w["text"],"start":round((w["start"]-r["start"])/SPD+off,3),"end":round((w["end"]-r["start"])/SPD+off,3),"seg":k})
    r["out_start"]=round(off,3); r["dur"]=round(ad,3); off+=ad
    lst.write(f"file 'seg_{k:03d}.mov'\n")
lst.close()
json.dump({"ranges":ranges,"words":words_out,"total":round(off,3)},open(f"{E}/edl_out.json","w"),ensure_ascii=False,indent=1)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",f"{E}/clips/list.txt","-c","copy",f"{E}/base.mov"],check=True)
print(len(ranges),"ranges, total",round(off,2),"s")
for r in ranges: print(f'{r["out_start"]:6.2f} +{r["dur"]:.2f} src {r["start"]:.2f}-{r["end"]:.2f} {"P" if r["punch"] else " "} ',' '.join(W[i]["text"] for i in r["words"]))
