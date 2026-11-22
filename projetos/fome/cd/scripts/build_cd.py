"""Monta o vídeo final a partir de edl.json.

Cada segmento é extraído e codificado uma única vez (overlays → legendas por último),
com fades de 30 ms no áudio, e depois tudo é concatenado sem recodificar.
"""
import json, os, re, subprocess, sys

E = "/home/user/editar_videos/projetos/fome/edit"
SRC = "/home/user/editar_videos/projetos/fome/bruto.mp4"
FONTS = f"{E}/fonts"
OUT_W, OUT_H, FPS = 1920, 1080, "30000/1001"
VENC = ["-c:v", "libx264", "-preset", os.environ.get("X264_PRESET", "veryfast"), "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", FPS]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]

PROPER = {"deus", "jesus", "cristo", "senhor", "paulo", "timóteo", "tiago", "moisés", "satanás",
          "dostoiévski", "filipenses", "joão", "mateus", "instagram", "facebook", "paulo", "periago",
          "ebenézer", "espírito", "santo"}


FIX = {"Dostoyevsky": "Dostoiévski", "periago": "Periago", "apurrinhando": "apoquentando"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"falhou: {' '.join(cmd[:6])}...")


def load_words():
    data = json.load(open(f"{E}/transcripts/bruto_small.json"))
    words = []
    for s in data:
        for w in s["words"]:
            t = w["w"].strip()
            for a, b in FIX.items():
                t = t.replace(a, b)
            if t:
                words.append({"w": t, "s": w["s"], "e": w["e"]})
    lower_seen = {re.sub(r"[^\wÀ-ÿ]", "", w["w"]) for w in words if w["w"][:1].islower()}
    for w in words:
        core = re.sub(r"[^\wÀ-ÿ]", "", w["w"])
        if core[:1].isupper() and core.lower() in lower_seen and core.lower() not in PROPER:
            w["w"] = w["w"][0].lower() + w["w"][1:]
        if core.lower() in PROPER and core.lower() in ("deus", "jesus", "cristo"):
            w["w"] = w["w"].replace(core, core.capitalize())
    return words


def clean(t):
    t = re.sub(r"[.,;:!?…\"“”]", "", t)
    return t.strip()


def chunks_for(words, start, end, max_chars=44, max_words=9):
    """Agrupa palavras em legendas de 1–2 linhas (estilo da referência)."""
    ws = [w for w in words if w["s"] >= start - 0.05 and w["e"] <= end + 0.05]
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = " ".join(clean(x["w"]) for x in cur)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        gap = (nxt["s"] - w["e"]) if nxt else 9
        punct = w["w"][-1:] in ".?!"
        if len(txt) >= max_chars or len(cur) >= max_words or gap > 0.45 or punct or not nxt:
            out.append({"s": cur[0]["s"], "e": cur[-1]["e"], "t": txt})
            cur = []
    # estender cada legenda até a próxima (até 0.6 s) para não piscar
    for a, b in zip(out, out[1:]):
        a["e"] = min(max(a["e"], a["e"] + 0.4), b["s"]) if b["s"] - a["e"] < 0.8 else a["e"] + 0.3
    if out:
        out[-1]["e"] += 0.3
    return out


def wrap2(t, maxline=30):
    if len(t) <= maxline:
        return t
    ws = t.split()
    best, bi = 1e9, 1
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        sc = abs(len(a) - len(b)) + (100 if len(a) > 40 or len(b) > 40 else 0)
        if sc < best:
            best, bi = sc, i
    return " ".join(ws[:bi]) + r"\N" + " ".join(ws[bi:])


def ass_time(x):
    x = max(0, x)
    h, m = int(x // 3600), int(x % 3600 // 60)
    return f"{h}:{m:02d}:{x % 60:05.2f}"


def write_ass(path, subs):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Ref,Montserrat Thin Medium,64,&H0000F8E8,&H0000F8E8,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,1.2,2,110,110,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as f:
        f.write(head)
        for s in subs:
            f.write(f"Dialogue: 0,{ass_time(s['s'])},{ass_time(s['e'])},Ref,,0,0,0,,{wrap2(s['t'])}\n")


def esc(p):
    return p.replace(":", r"\:").replace(",", r"\,")


def seg_source(seg, words, i, tmp):
    """Segmento do vídeo bruto: corte + grade + overlays + legendas (por último)."""
    s, e = seg["start"], seg["end"]
    dur = e - s
    vf = [f"scale={OUT_W}:{OUT_H}:flags=lanczos", "setsar=1"]
    if seg.get("bw"):
        vf += ["hue=s=0", "eq=contrast=1.18:brightness=-0.05:gamma=0.95",
               "curves=all='0/0 0.2/0.1 0.55/0.55 0.85/0.8 1/0.88'"]
    z = seg.get("zoom")
    if seg.get("track"):  # punch-in seguindo o pregador
        Z = seg["track"]
        kf = json.loads(subprocess.run(["python3", "-I", f"{E}/scripts/track.py", str(s), str(e)],
                                       capture_output=True, text=True, check=True).stdout)
        head = seg.get("head", 0.40)  # onde fica o topo dos ombros no quadro de saída
        xs, ys = [], []
        for t, cx, cy, top in kf:
            x0 = min(max(cx - 0.5 / Z, 0), 1 - 1 / Z)
            y0 = min(max(top - head / Z, 0), 1 - 1 / Z)
            xs.append((t, x0 * OUT_W * Z)); ys.append((t, y0 * OUT_H * Z))

        def pw(pts):
            ex = f"{pts[-1][1]:.1f}"
            for (t0, v0), (t1, v1) in reversed(list(zip(pts, pts[1:]))):
                ex = f"if(lt(t\\,{t1:.3f})\\,{v0:.1f}+({v1 - v0:.1f})*(t-{t0:.3f})/{t1 - t0:.3f}\\,{ex})"
            return ex
        vf += [f"scale={round(OUT_W * Z / 2) * 2}:{round(OUT_H * Z / 2) * 2}:flags=lanczos",
               f"crop={OUT_W}:{OUT_H}:{pw(xs)}:{pw(ys)}", "unsharp=5:5:0.6"]
    elif z:  # punch-in fixo + leve push-in ao longo do plano
        z0, z1 = z
        vf += [f"scale=w='iw*({z0}+({z1}-{z0})*t/{dur:.3f})':h=-2:eval=frame:flags=bicubic",
               f"crop={OUT_W}:{OUT_H}:(iw-{OUT_W})/2:(ih-{OUT_H})/2*{seg.get('ybias', 0.6)}"]
    vf += [f"fps={FPS}"]
    if seg.get("blur_in"):
        b = seg["blur_in"]
        vf += [f"split[a][bb];[bb]gblur=sigma=45,format=yuva420p,fade=t=out:st={b*0.35:.2f}:d={b*0.65:.2f}:alpha=1[bl];[a][bl]overlay"]
    if seg.get("blur_out"):
        b = seg["blur_out"]
        vf += [f"split[c][dd];[dd]gblur=sigma=45,format=yuva420p,fade=t=in:st={dur-b:.2f}:d={b:.2f}:alpha=1[dl];[c][dl]overlay"]
    chain = ",".join(vf)
    inputs = ["-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    fc = f"[0:v]{chain}[v0]"
    last = "v0"
    nin = 1
    sfx = []
    for k, ov in enumerate(seg.get("overlays", [])):
        inputs += ["-i", ov["file"]]
        x, y = ov.get("x", 0), ov.get("y", 0)
        fc += f";[{nin}:v]setpts=PTS-STARTPTS+{ov['at']}/TB[o{k}];[{last}][o{k}]overlay={x}:{y}:eof_action=pass[v{k+1}]"
        last = f"v{k+1}"; nin += 1
        if ov.get("sfx"):
            inputs += ["-i", ov["sfx"]]; sfx.append((nin, ov["at"], ov.get("sfx_gain", -4))); nin += 1
    if seg.get("logo"):
        inputs += ["-i", seg["logo"]]
        fc += f";[{nin}:v]scale=150:-1[lg];[{last}][lg]overlay=30:24[vl]"
        last = "vl"; nin += 1
    if seg.get("subs", True):
        subs = chunks_for(words, s, e)
        for x in subs:
            x["s"] -= s
            x["e"] -= s
        ap = f"{tmp}/seg{i:02d}.ass"
        write_ass(ap, subs)
        fc += f";[{last}]subtitles=filename='{esc(ap)}':fontsdir='{esc(FONTS)}'[vs]"
        last = "vs"
    af = f"[0:a]aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03:.3f}:d=0.03"
    if seg.get("afade_out"):
        af += f",afade=t=out:st={dur-seg['afade_out']:.3f}:d={seg['afade_out']}"
    if seg.get("gain"):
        af += f",volume={seg['gain']}dB"
    if sfx:
        fc += f";{af}[a0]"
        labs = "[a0]"
        for j, (idx, at, g) in enumerate(sfx):
            ms = int(at * 1000)
            fc += f";[{idx}:a]aresample=48000,volume={g}dB,adelay={ms}|{ms}[s{j}]"
            labs += f"[s{j}]"
        fc += f";{labs}amix=inputs={len(sfx)+1}:duration=first:normalize=0[a]"
    else:
        fc += f";{af}[a]"
    out = f"{tmp}/seg{i:02d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", f"[{last}]", "-map", "[a]",
         *VENC, *AENC, "-t", f"{dur:.3f}", out])
    return out


def seg_clip(seg, i, tmp):
    """Clipe pronto (kit da referência): só normaliza formato e aplica fades."""
    f = seg["file"]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                               capture_output=True, text=True).stdout)
    vf = f"scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1,fps={FPS}"
    af = f"aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03:.3f}:d=0.03"
    if seg.get("gain"):
        af += f",volume={seg['gain']}dB"
    out = f"{tmp}/seg{i:02d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", vf, "-af", af, *VENC, *AENC, out])
    return out


def main():
    edl = json.load(open(sys.argv[1]))
    out_path = sys.argv[2]
    only = set(map(int, sys.argv[3].split(","))) if len(sys.argv) > 3 else None
    tmp = os.environ.get("SEGDIR", "/home/user/editar_videos/projetos/fome/cd/segments")
    os.makedirs(tmp, exist_ok=True)
    words = load_words()
    files = []
    for i, seg in enumerate(edl["segments"]):
        out = f"{tmp}/seg{i:02d}.mp4"
        if only is None or i in only or not os.path.exists(out):
            print(f"[{i}] {seg.get('label', '')}", flush=True)
            out = seg_clip(seg, i, tmp) if "file" in seg else seg_source(seg, words, i, tmp)
        files.append(out)
    with open(f"{tmp}/list.txt", "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
         "-movflags", "+faststart", out_path])
    print("ok", out_path)


if __name__ == "__main__":
    main()
