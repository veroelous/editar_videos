import os, sys, math, random, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
C="/home/user/editar_videos/projetos/fome/cd"; F="/home/user/editar_videos/projetos/fome/edit/fonts"
W,H,FPS=1920,1080,30
def eo(t): t=max(0,min(1,t)); return 1-(1-t)**3
def enc(d,out):
    subprocess.run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",f"{d}/f_%04d.png","-c:v","qtrle","-pix_fmt","argb",out],check=True)

def title(text="O QUE MATA A SUA FOME?", total=47.5):
    d=f"{C}/anim/title_frames"; os.makedirs(d,exist_ok=True)
    font=ImageFont.truetype(f"{F}/Anton.ttf",118)
    bb=font.getbbox(text); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    cx,cy=W//2,int(H*0.40)
    # base text layer
    base=Image.new("RGBA",(W,H),(0,0,0,0)); bd=ImageDraw.Draw(base)
    bd.text((cx,cy),text,font=font,anchor="mm",fill=(255,226,40,255),stroke_width=7,stroke_fill=(10,6,0,255))
    # glow: warm gradient band behind text
    glow=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.rounded_rectangle([cx-tw//2-60,cy-th//2-30,cx+tw//2+60,cy+th//2+30],radius=60,fill=(255,120,0,200))
    glow=glow.filter(ImageFilter.GaussianBlur(38))
    n=int(total*FPS)
    for i in range(n):
        t=i/FPS; im=Image.new("RGBA",(W,H),(0,0,0,0))
        a_in=eo(t/0.5); a_out=1-eo((t-(total-0.6))/0.6) if t>total-0.6 else 1
        pulse=0.75+0.25*math.sin(t*2.2)
        g=glow.copy(); g.putalpha(g.getchannel("A").point(lambda v:int(v*pulse*a_in*a_out)))
        im.alpha_composite(g)
        txt=base
        if t<0.45:  # glitch de entrada: fatias deslocadas
            txt=base.copy(); random.seed(i)
            for _ in range(8):
                y=random.randint(cy-th//2-10,cy+th//2+10); hh=random.randint(6,22); dx=random.randint(-60,60)
                sl=base.crop((0,y,W,y+hh)); txt.paste((0,0,0,0),(0,y,W,y+hh)); txt.alpha_composite(sl,(dx,y))
        tl=txt.copy(); tl.putalpha(tl.getchannel("A").point(lambda v:int(v*a_in*a_out)))
        im.alpha_composite(tl); im.save(f"{d}/f_{i+1:04d}.png")
    enc(d,f"{C}/anim/title.mov")

def countdown():
    d=f"{C}/anim/cd_frames"; os.makedirs(d,exist_ok=True)
    font=ImageFont.truetype(f"{F}/Montserrat-500.ttf",420)
    n=3*FPS
    for i in range(n):
        t=i/FPS; k=int(t); lt=t-k; num=str(2-k)
        im=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(im)
        # fundo cinza translúcido com vinheta
        dr.rectangle([0,0,W,H],fill=(150,150,150,150))
        R=420
        ang=-90+360*lt  # varredura
        dr.pieslice([W/2-1200,H/2-1200,W/2+1200,H/2+1200],start=-90,end=ang,fill=(90,90,90,120))
        dr.ellipse([W/2-R,H/2-R,W/2+R,H/2+R],outline=(20,20,20,230),width=8)
        dr.ellipse([W/2-R+40,H/2-R+40,W/2+R-40,H/2+R-40],outline=(240,240,240,200),width=4)
        dr.line([0,H/2,W,H/2],fill=(245,245,245,210),width=4); dr.line([W/2,0,W/2,H],fill=(245,245,245,210),width=4)
        dr.text((W/2,H/2),num,font=font,anchor="mm",fill=(255,255,255,255),stroke_width=4,stroke_fill=(30,30,30,255))
        # grão
        if i%2==0:
            random.seed(i)
            for _ in range(250):
                x,y=random.randint(0,W),random.randint(0,H); dr.point((x,y),fill=(255,255,255,90))
        a=1 if t<2.75 else max(0,(3-t)/0.25)
        if a<1: im.putalpha(im.getchannel("A").point(lambda v:int(v*a)))
        im.save(f"{d}/f_{i+1:04d}.png")
    enc(d,f"{C}/anim/countdown.mov")

def inscreva():
    K="/home/user/editar_videos/projetos/kit_canal/inscreva_se_greenscreen.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",K,"-vf","fps=30,scale=1920:1080,format=yuva444p,chromakey=0x31FE00:0.18:0.08,despill=type=green,scale=960:540",
                    "-c:v","qtrle","-pix_fmt","argb","-an",f"{C}/anim/inscreva.mov"],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",K,"-vn","-ac","2","-ar","48000",f"{C}/anim/inscreva_sfx.wav"],check=True)

{"title":title,"countdown":countdown,"inscreva":inscreva}[sys.argv[1]]()
print("ok",sys.argv[1])
