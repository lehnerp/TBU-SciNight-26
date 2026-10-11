"""Samostatný nástroj pro převod obrazu na zvuk a zobrazení spektrogramu; bez Arduina.
Knihovny: numpy, Pillow, Tkinter; sounddevice pro mikrofon/přehrávání. Viz README.md.
"""

import queue
import time
import wave
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageOps

try:
    import sounddevice as sd
except ImportError:
    sd = None

SR = 44100
DURATION = 5.0
NFFT = 2048
HOP = 512
FMIN = 400.0
FMAX = 8500.0

BG="#090d14"; PANEL="#111824"; BAR="#172131"; TEXT="#f5f7fb"
MUTED="#8293aa"; ACCENT="#25b7e5"; GREEN="#55e6a4"; BORDER="#26364d"

def save_wav(path, y):
    q=(np.clip(y,-1,1)*32767).astype("<i2")
    with wave.open(path,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(q.tobytes())

def read_wav(path):
    with wave.open(path,"rb") as w:
        ch,sw,rate=w.getnchannels(),w.getsampwidth(),w.getframerate()
        raw=w.readframes(w.getnframes())
    if sw==2:
        y=np.frombuffer(raw,"<i2").astype(np.float32)/32768
    elif sw==1:
        y=(np.frombuffer(raw,np.uint8).astype(np.float32)-128)/128
    else:
        raise ValueError("Použij PCM WAV 8/16 bit.")
    if ch>1: y=y.reshape(-1,ch).mean(1)
    if rate!=SR:
        y=np.interp(np.linspace(0,len(y)-1,int(len(y)*SR/rate)),
                    np.arange(len(y)),y).astype(np.float32)
    return y

def image_to_stft_audio(im):
    """
    Image -> complex STFT -> inverse overlap-add.
    This follows the user's reference idea, but uses a mathematically
    consistent STFT grid and no SciPy.
    """
    bins=np.fft.rfftfreq(NFFT,1/SR)
    use=np.where((bins>=FMIN)&(bins<=FMAX))[0]
    rows=len(use)

    frames=1+int(np.ceil((SR*DURATION-NFFT)/HOP))
    frames=max(2,frames)

    g=ImageOps.grayscale(im)
    g=ImageOps.autocontrast(g)
    g=g.resize((frames,rows),Image.Resampling.LANCZOS)
    A=np.asarray(g,np.float32)/255.0
    A=np.flipud(A)                    # top of picture = high frequency
    A=np.clip(A,0,1)**1.15

    win=np.hanning(NFFT).astype(np.float32)
    out_len=(frames-1)*HOP+NFFT
    y=np.zeros(out_len,np.float64)
    norm=np.zeros(out_len,np.float64)

    # Phase continuity across time prevents each image column becoming
    # an unrelated click/noise burst.
    phase=np.random.default_rng().uniform(0,2*np.pi,len(use))
    phase_step=2*np.pi*bins[use]*HOP/SR

    for t in range(frames):
        X=np.zeros(NFFT//2+1,np.complex128)
        amp=A[:,t]
        X[use]=amp*np.exp(1j*phase)
        frame=np.fft.irfft(X,n=NFFT)
        start=t*HOP
        y[start:start+NFFT]+=frame*win
        norm[start:start+NFFT]+=win*win
        phase=(phase+phase_step)%(2*np.pi)

    good=norm>1e-8
    y[good]/=norm[good]
    # Short silence around payload makes acoustic recordings easier to inspect.
    y=np.concatenate((np.zeros(int(.35*SR)),y,np.zeros(int(.25*SR))))
    peak=np.max(np.abs(y))
    if peak>0:y=.82*y/peak
    return y.astype(np.float32)

def stft_matrix(y):
    """Real received audio -> ordinary magnitude STFT, like plt.specgram."""
    if len(y)<NFFT:
        return np.zeros((10,1),np.float32)
    starts=np.arange(0,len(y)-NFFT+1,HOP)
    win=np.hanning(NFFT).astype(np.float32)
    bins=np.fft.rfftfreq(NFFT,1/SR)
    use=(bins>=FMIN)&(bins<=FMAX)
    M=np.empty((use.sum(),len(starts)),np.float32)
    for j,s in enumerate(starts):
        x=y[s:s+NFFT].astype(np.float32)
        x=(x-x.mean())*win
        M[:,j]=np.abs(np.fft.rfft(x))[use]
    # dB-like view. This is visualization of the actual received spectrum,
    # not a binary image decoder.
    M=20*np.log10(M+1e-7)
    hi=np.percentile(M,99.7)
    lo=hi-55.0
    M=np.clip((M-lo)/(hi-lo),0,1)
    return M

def spectrogram_image(y,w=720,h=500):
    M=stft_matrix(y)
    # Frequency axis: low at bottom, high at top.
    z=np.flipud(M)
    im=Image.fromarray((255*(1-z)).astype(np.uint8),"L")  # gray_r look
    return im.resize((w,h),Image.Resampling.BILINEAR).convert("RGB")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spektrogramový přenos obrazu")
        self.configure(bg=BG)
        # Skutečný fullscreen bez titulku, rámečku a systémových okrajů.
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        # ESC ukončí fullscreen, F11 ho znovu zapne/vypne.
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not bool(self.attributes("-fullscreen"))))
        self.img=Image.new("L",(700,500),0)
        self.draw=ImageDraw.Draw(self.img)
        self.last=None; self.source=None; self.tx=None
        self.q=queue.Queue(); self.rx=[]; self.stream=None
        self.recording=False; self.playing=False; self.last_render=0
        self.make_style(); self.build(); self.refresh_devices()
        self.after(50,self.tick)

    def make_style(self):
        s=ttk.Style(self)
        try:s.theme_use("clam")
        except:pass
        s.configure(".",font=("Segoe UI",10))
        s.configure("TFrame",background=BG);s.configure("P.TFrame",background=PANEL)
        s.configure("Bar.TFrame",background=BAR)
        s.configure("TLabel",background=BG,foreground=TEXT)
        s.configure("P.TLabel",background=PANEL,foreground=TEXT)
        s.configure("M.TLabel",background=PANEL,foreground=MUTED)
        s.configure("Title.TLabel",background=BG,foreground=TEXT,font=("Segoe UI",24,"bold"))
        s.configure("Head.TLabel",background=PANEL,foreground=TEXT,font=("Segoe UI",15,"bold"))
        s.configure("State.TLabel",background=PANEL,foreground=GREEN,font=("Segoe UI",13,"bold"))
        s.configure("TButton",padding=(11,8),background=BAR,foreground=TEXT)
        s.configure("Go.TButton",padding=(14,9),background="#168bb3",foreground="white",
                    font=("Segoe UI",10,"bold"))
        s.configure("Horizontal.TProgressbar",troughcolor="#1a2636",background=ACCENT)

    def build(self):
        h=ttk.Frame(self);h.pack(fill="x",padx=24,pady=(18,10))
        ttk.Label(h,text="Spektrogramový přenos obrazu",style="Title.TLabel").pack(side="left")
        ttk.Label(h,text="  přenos obrazu zvukem",foreground=ACCENT,
                  font=("Segoe UI",11)).pack(side="left",pady=(10,0))

        d=ttk.Frame(self,style="Bar.TFrame",padding=10);d.pack(fill="x",padx=24,pady=(0,12))
        ttk.Label(d,text="Reproduktor",background=BAR,foreground=MUTED).pack(side="left")
        self.out=ttk.Combobox(d,state="readonly",width=37);self.out.pack(side="left",padx=(7,18))
        ttk.Label(d,text="Mikrofon",background=BAR,foreground=MUTED).pack(side="left")
        self.inp=ttk.Combobox(d,state="readonly",width=37);self.inp.pack(side="left",padx=7)
        ttk.Button(d,text="↻ Zařízení",command=self.refresh_devices).pack(side="left",padx=8)

        body=ttk.Frame(self);body.pack(fill="both",expand=True,padx=24,pady=(0,12))
        body.columnconfigure(0,weight=1);body.columnconfigure(1,weight=1);body.rowconfigure(0,weight=1)
        L=ttk.Frame(body,style="P.TFrame",padding=14)
        R=ttk.Frame(body,style="P.TFrame",padding=14)
        L.grid(row=0,column=0,sticky="nsew",padx=(0,7));R.grid(row=0,column=1,sticky="nsew",padx=(7,0))

        ttk.Label(L,text="VYSÍLAČ — OBRAZ → ZVUK",style="Head.TLabel").pack(anchor="w")
        ttk.Label(L,text="Kresba se převede na frekvence a odešle jako zvuk.",
                  style="M.TLabel").pack(anchor="w",pady=(2,9))
        b=ttk.Frame(L,style="P.TFrame");b.pack(fill="x",pady=(0,8))
        for t,c,st in [
            ("＋ Obrázek",self.open_image,"TButton"),("Vymazat",self.clear,"TButton"),
            ("Připravit přenos",self.generate,"TButton"),("▶ VYSÍLAT",self.play,"Go.TButton"),
            ("■ Stop",self.stop_play,"TButton"),("Uložit zvuk",self.save_tx,"TButton")]:
            ttk.Button(b,text=t,command=c,style=st).pack(side="left",padx=(0,5))

        self.canvas=tk.Canvas(L,bg="black",highlightthickness=1,highlightbackground=BORDER)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Button-1>",self.paint)
        self.canvas.bind("<B1-Motion>",self.paint)
        self.canvas.bind("<ButtonRelease-1>",lambda e:setattr(self,"last",None))
        self.canvas.bind("<Configure>",self.canvas_resize)
        self.txinfo=tk.StringVar(value=f"Délka {DURATION:g} s • pásmo {FMIN:.0f}–{FMAX:.0f} Hz")
        ttk.Label(L,textvariable=self.txinfo,style="M.TLabel").pack(anchor="w",pady=(8,4))
        self.prog=ttk.Progressbar(L,maximum=100);self.prog.pack(fill="x")

        ttk.Label(R,text="PŘIJÍMAČ — MIKROFON → OBRAZ",style="Head.TLabel").pack(anchor="w")
        ttk.Label(R,text="Přijatý zvuk se průběžně převádí zpět na obraz.",
                  style="M.TLabel").pack(anchor="w",pady=(2,9))
        b=ttk.Frame(R,style="P.TFrame");b.pack(fill="x",pady=(0,8))
        for t,c,st in [
            ("● START PŘÍJMU",self.start_rx,"Go.TButton"),("■ Stop",self.stop_rx,"TButton"),
            ("Vymazat",self.clear_rx,"TButton"),("Načíst zvuk",self.load_wav,"TButton"),
            ("Uložit obrázek",self.save_png,"TButton")]:
            ttk.Button(b,text=t,command=c,style=st).pack(side="left",padx=(0,5))

        line=ttk.Frame(R,style="P.TFrame");line.pack(fill="x")
        self.state=tk.StringVar(value="PŘIPRAVENO")
        ttk.Label(line,textvariable=self.state,style="State.TLabel").pack(side="left")
        self.rxinfo=tk.StringVar(value="čekám na signál")
        ttk.Label(line,textvariable=self.rxinfo,style="M.TLabel").pack(side="right")

        self.picture=tk.Label(R,bg="white",fg="#333",text="1. Spusť příjem   •   2. Spusť vysílání",
                              font=("Segoe UI",13))
        self.picture.pack(fill="both",expand=True,pady=(8,8))

        m=ttk.Frame(R,style="P.TFrame");m.pack(fill="x")
        ttk.Label(m,text="MIC",style="M.TLabel").pack(side="left",padx=(0,8))
        self.level=ttk.Progressbar(m,maximum=100);self.level.pack(side="left",fill="x",expand=True)
        self.db=tk.StringVar(value="-∞ dB")
        ttk.Label(m,textvariable=self.db,style="M.TLabel",width=9).pack(side="left",padx=8)
        self.status=tk.StringVar(value="Připraveno.")
        ttk.Label(self,textvariable=self.status).pack(fill="x",padx=24,pady=(0,10))

    def refresh_devices(self):
        if sd is None:
            self.status.set("Chybí sounddevice.");return
        try:
            ds=sd.query_devices();ins=[];outs=[]
            for i,d in enumerate(ds):
                name=f"{i}: {d['name']}"
                if d["max_input_channels"]>0:ins.append(name)
                if d["max_output_channels"]>0:outs.append(name)
            self.inp["values"]=ins;self.out["values"]=outs
            di,do=sd.default.device
            for box,arr,idx in ((self.inp,ins,di),(self.out,outs,do)):
                hit=next((x for x in arr if x.startswith(str(idx)+":")),None)
                if hit:box.set(hit)
                elif arr:box.current(0)
        except Exception as e:self.status.set(str(e))

    def dev(self,box):
        try:return int(box.get().split(":",1)[0])
        except:return None

    def clear(self):
        self.source=None
        self.img=Image.new("L",(max(10,self.canvas.winfo_width()),max(10,self.canvas.winfo_height())),0)
        self.draw=ImageDraw.Draw(self.img);self.show_source()

    def canvas_resize(self,e):
        if e.width<10 or e.height<10:return
        if self.source is None and self.img.size!=(e.width,e.height):
            self.img=self.img.resize((e.width,e.height),Image.Resampling.LANCZOS)
            self.draw=ImageDraw.Draw(self.img)
        self.show_source()

    def show_source(self):
        if not hasattr(self,"canvas"):return
        w=max(10,self.canvas.winfo_width());h=max(10,self.canvas.winfo_height())
        if self.source is not None:
            im=ImageOps.contain(self.source,(w,h))
            bg=Image.new("L",(w,h),0)
            bg.paste(ImageOps.grayscale(im),((w-im.width)//2,(h-im.height)//2))
        else:
            bg=self.img.resize((w,h),Image.Resampling.LANCZOS)
        self.src_tk=ImageTk.PhotoImage(bg)
        self.canvas.delete("all");self.canvas.create_image(0,0,anchor="nw",image=self.src_tk)

    def paint(self,e):
        if self.source is not None:
            self.source=None
            self.img=Image.new("L",(max(10,self.canvas.winfo_width()),max(10,self.canvas.winfo_height())),0)
            self.draw=ImageDraw.Draw(self.img)
        if self.last:
            self.draw.line((*self.last,e.x,e.y),fill=255,width=7)
        else:self.draw.ellipse((e.x-3,e.y-3,e.x+3,e.y+3),fill=255)
        self.last=(e.x,e.y);self.show_source()

    def open_image(self):
        p=filedialog.askopenfilename(filetypes=[("Obrázky","*.png *.jpg *.jpeg *.bmp *.webp")])
        if p:self.source=Image.open(p).convert("L");self.show_source()

    def get_image(self):
        return self.source if self.source is not None else self.img

    def generate(self):
        try:
            self.tx=image_to_stft_audio(self.get_image())
            self.status.set("Zvuk s obrazem je připraven.")
        except Exception as e:messagebox.showerror("Generování",str(e))

    def play(self):
        if self.tx is None:self.generate()
        if self.tx is None or sd is None:return
        self.stop_play()
        try:
            self.playing=True;self.play_t=time.time()
            sd.play(self.tx,SR,device=self.dev(self.out))
            self.status.set("Vysílám obraz zvukem…")
        except Exception as e:messagebox.showerror("Audio",str(e))

    def stop_play(self):
        if sd:
            try:sd.stop()
            except:pass
        self.playing=False

    def save_tx(self):
        if self.tx is None:self.generate()
        if self.tx is None:return
        p=filedialog.asksaveasfilename(defaultextension=".wav",filetypes=[("WAV","*.wav")])
        if p:save_wav(p,self.tx)

    def cb(self,indata,frames,t,status):self.q.put(indata[:,0].copy())

    def start_rx(self):
        if sd is None:return
        self.stop_rx();self.rx=[];self.recording=True;self.rec_t=time.time()
        try:
            self.stream=sd.InputStream(samplerate=SR,channels=1,dtype="float32",
                                       blocksize=1024,device=self.dev(self.inp),callback=self.cb)
            self.stream.start();self.state.set("PŘIJÍMÁM ŽIVĚ")
            self.status.set("Mikrofon běží — teď stiskni VYSÍLAT.")
        except Exception as e:
            self.recording=False;messagebox.showerror("Mikrofon",str(e))

    def stop_rx(self):
        if self.stream:
            try:self.stream.stop();self.stream.close()
            except:pass
            self.stream=None
        if self.recording:self.state.set("ZASTAVENO")
        self.recording=False

    def clear_rx(self):
        self.rx=[];self.picture.configure(image="",text="Příjem vymazán")
        self.rxinfo.set("čekám na signál")

    def render(self,y):
        if len(y)<NFFT:return
        # Keep roughly the latest transmission-width view during live reception.
        maxn=int((DURATION+.8)*SR)
        view=y[-maxn:]
        self.result=spectrogram_image(view)
        self.result_tk=ImageTk.PhotoImage(self.result)
        self.picture.configure(image=self.result_tk,text="")
        self.rxinfo.set(f"{len(y)/SR:.1f} s • rozlišení spektra {NFFT}")

    def load_wav(self):
        p=filedialog.askopenfilename(filetypes=[("WAV","*.wav")])
        if not p:return
        try:
            y=read_wav(p);self.rx=[y];self.render(y);self.state.set("SOUBOR NAČTEN")
        except Exception as e:messagebox.showerror("WAV",str(e))

    def save_png(self):
        if not hasattr(self,"result"):return
        p=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png")])
        if p:self.result.save(p)

    def tick(self):
        changed=False
        while True:
            try:
                a=self.q.get_nowait();self.rx.append(a);changed=True
                rms=float(np.sqrt(np.mean(a*a))+1e-12);db=20*np.log10(rms)
                self.level["value"]=np.clip((db+60)/50*100,0,100);self.db.set(f"{db:.1f} dB")
            except queue.Empty:break

        now=time.time()
        if changed and now-self.last_render>.25:
            # bounded concatenate for responsiveness
            need=int((DURATION+.8)*SR)
            parts=[];n=0
            for a in reversed(self.rx):
                parts.append(a);n+=len(a)
                if n>=need:break
            y=np.concatenate(parts[::-1])
            self.render(y)
            self.last_render=now

        if self.playing and self.tx is not None:
            p=(now-self.play_t)/(len(self.tx)/SR)*100
            self.prog["value"]=min(100,p)
            if p>=100:self.playing=False;self.status.set("Přenos byl dokončen.")
        self.after(50,self.tick)

if __name__=="__main__":
    App().mainloop()
