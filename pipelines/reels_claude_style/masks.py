import subprocess, numpy as np, sys, time
from PIL import Image
from rembg import remove, new_session
E="/home/user/editar_videos/brutos/edit"
w,h=360,640
dec=subprocess.Popen(["ffmpeg","-v","error","-i",f"{E}/base.mov","-vf",f"scale={w}:{h}","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","gray","-s",f"{w}x{h}","-r","30","-i","-","-c:v","ffv1",f"{E}/mask.mkv"],stdin=subprocess.PIPE)
sess=new_session("u2net_human_seg"); n=0; t0=time.time()
while True:
    b=dec.stdout.read(w*h*3)
    if len(b)<w*h*3: break
    im=Image.frombytes("RGB",(w,h),b)
    m=remove(im,session=sess,only_mask=True)
    enc.stdin.write(np.asarray(m.convert("L")).tobytes()); n+=1
    if n%150==0: print(n, round(time.time()-t0,1), flush=True)
enc.stdin.close(); enc.wait(); print("done",n)
