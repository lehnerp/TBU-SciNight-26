#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RGB Filtr Studio v2 – české GUI
Samostatný nástroj bez Arduina; main.py a Filter_Text_QE.py jsou stejné varianty.
Knihovny: numpy, Pillow, qrcode, reportlab, Tkinter; viz README.md.

Opravy:
- kontrola konfliktu balíčku/modulu "qrcode"
- QR generování používá qrcode.QRCode jen pokud je dostupné
- náhled se obnovuje po změně typu, textu i varianty (debounce)
- okno se otevře maximalizované (není F11 fullscreen)
- náhled se přizpůsobuje velikosti okna
"""

import os, math, sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Bezpečný import správného balíčku qrcode
try:
    import qrcode
except Exception as e:
    qrcode = None
    QRCODE_IMPORT_ERROR = str(e)
else:
    QRCODE_IMPORT_ERROR = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    HAVE_REPORTLAB = True
except Exception:
    HAVE_REPORTLAB = False

CHANNELS = {"Červená":0, "Zelená":1, "Modrá":2}

VARIANTS = [
    # (dlaždice, červená, zelená, modrá, NORMÁLNÍ)
    # Normální vrstva je záměrně výraznější než filtrované vrstvy.
    (8,38,24,14,70),(8,42,27,16,80),(8,46,30,18,90),(8,50,33,20,100),
    (9,38,24,14,80),(9,42,27,16,90),(9,46,30,18,100),(9,50,33,20,110),
    (10,38,24,14,90),(10,42,27,16,100),(10,46,30,18,110),(10,50,33,20,120),
]

def qrcode_diagnostika():
    if qrcode is None:
        return False, "Balíček qrcode se nepodařilo importovat: " + str(QRCODE_IMPORT_ERROR)
    if not hasattr(qrcode, "QRCode"):
        location = getattr(qrcode, "__file__", "neznámé umístění")
        return False, (
            "Python načetl jiný modul jménem 'qrcode', který nemá QRCode.\n\n"
            f"Načtený modul: {location}\n\n"
            "Oprava v terminálu:\n"
            "  pip uninstall qrcode -y\n"
            "  pip install --upgrade qrcode[pil]\n\n"
            "Také zkontroluj, že ve stejné složce jako tento program nemáš "
            "soubor nebo složku pojmenovanou qrcode.py / qrcode."
        )
    return True, ""

def najdi_font():
    for fp in (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(fp): return fp
    return None

def text_mask(text,W,H):
    fp=najdi_font()
    size=max(14,int(H*.16))
    while True:
        f=ImageFont.truetype(fp,size) if fp else ImageFont.load_default()
        im=Image.new("L",(W,H),0); d=ImageDraw.Draw(im)
        bb=d.textbbox((0,0),text,font=f)
        tw,th=bb[2]-bb[0],bb[3]-bb[1]
        if tw <= W*.88 or size<=12: break
        size-=2
    d.text(((W-tw)//2,(H-th)//2),text,font=f,fill=255)
    return np.asarray(im)>127

def qr_mask(text,W,H):
    ok,msg=qrcode_diagnostika()
    if not ok: raise RuntimeError(msg)
    qr=qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=4
    )
    qr.add_data(text)
    qr.make(fit=True)
    a=np.array(qr.get_matrix(),dtype=np.uint8)*255
    im=Image.fromarray(a,"L")
    s=min(W,H)
    im=im.resize((s,s),Image.Resampling.NEAREST)
    out=Image.new("L",(W,H),0)
    out.paste(im,((W-s)//2,(H-s)//2))
    return np.asarray(out)>127

def maska(typ,text,W,H):
    if typ=="Vypnuto" or not text:
        return np.zeros((H,W),bool)
    if typ=="Text":
        return text_mask(text,W,H)
    if typ=="QR":
        return qr_mask(text,W,H)
    raise ValueError("Neznámý typ vrstvy.")

def generuj(vrstvy, varianta=7, size=900, seed=260925, normal_mult=1.0):
    tile,dr,dg,db,dn=VARIANTS[varianta-1]
    dn = int(dn * normal_mult)
    W=H=size; ds=[dr,dg,db]
    masks={k:maska(*v,W,H) for k,v in vrstvy.items()}
    rng=np.random.default_rng(seed)
    arr=np.empty((H,W,3),np.uint8)
    gh,gw=math.ceil(H/tile),math.ceil(W/tile)

    for gy in range(gh):
        for gx in range(gw):
            yy=min(H-1,gy*tile+tile//2)
            xx=min(W-1,gx*tile+tile//2)
            rgb=np.array(rng.integers(55,226,size=3),dtype=np.int16)

            q=rng.random()
            if q<.12: rgb[:]=rng.integers(205,246,size=3)
            elif q<.24: rgb[:]=rng.integers(30,96,size=3)

            for name,ch in CHANNELS.items():
                if masks[name][yy,xx]:
                    delta=ds[ch]
                    rgb[ch]-=delta
                    others=[i for i in range(3) if i!=ch]
                    rgb[others[0]]+=int(delta*.35)
                    rgb[others[1]]+=int(delta*.35)

            if masks["Normální"][yy,xx]:
                # QR potřebuje pro mobilní skener výraznější jasový rozdíl než běžný text.
                normal_delta = dn
                if vrstvy["Normální"][0] == "QR":
                    normal_delta = int(dn * 1.35)
                rgb -= normal_delta

            rgb=np.clip(rgb,18,242).astype(np.uint8)
            arr[gy*tile:min(H,(gy+1)*tile),
                gx*tile:min(W,(gx+1)*tile)] = rgb
    return Image.fromarray(arr)

def uloz_pdf(files,path):
    if not HAVE_REPORTLAB:
        raise RuntimeError("Chybí reportlab. Nainstaluj: pip install reportlab")
    c=canvas.Canvas(str(path),pagesize=A4)
    PW,PH=A4; mm=72/25.4
    mx=12*mm; top=17*mm; gapx=6*mm; gapy=9*mm; sw=58*mm; sh=48*mm
    c.setFont("Helvetica-Bold",14)
    c.drawString(mx,PH-top+3,"RGB Filter Studio - calibration")
    c.setFont("Helvetica",7.5)
    c.drawString(mx,PH-top-9,"Print 100% / Actual Size. Test normally and through R/G/B filters.")
    sy=PH-top-23
    for i,f in enumerate(files):
        row,col=divmod(i,3); x=mx+col*(sw+gapx); y=sy-(row+1)*sh-row*gapy
        s=44*mm
        c.drawImage(ImageReader(str(f)),x+(sw-s)/2,y+3*mm,width=s,height=s)
        t,r,g,b,n=VARIANTS[i]
        c.setFont("Helvetica-Bold",8.5); c.drawString(x,y-9,f"{i+1:02d}")
        c.setFont("Helvetica",6.2); c.drawRightString(x+sw,y-9,f"T{t} R{r} G{g} B{b} N{n}")
    c.save()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RGB Filtr Studio v2")
        self.minsize(900,650)

        # Maximalizované běžné okno, nikoli F11/exclusive fullscreen.
        try:
            self.state("zoomed")            # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
                self.geometry(f"{sw}x{sh}+0+0")

        self.preview_photo=None
        self.preview_source=None
        self.preview_job=None
        self.vars={}
        self._build()
        self.after(200,self.schedule_preview)

    def _build(self):
        root=ttk.Frame(self,padding=14); root.pack(fill="both",expand=True)
        ttk.Label(root,text="RGB Filtr Studio",font=("TkDefaultFont",20,"bold")).pack(anchor="w")
        ttk.Label(root,text="Text / QR pro červený, zelený a modrý filtr + normální vrstva.").pack(anchor="w",pady=(2,10))

        paned=ttk.Panedwindow(root,orient="horizontal"); paned.pack(fill="both",expand=True)
        left=ttk.Frame(paned,padding=(0,0,14,0)); right=ttk.Frame(paned)
        paned.add(left,weight=1); paned.add(right,weight=2)

        for name in ("Červená","Zelená","Modrá","Normální"):
            box=ttk.LabelFrame(left,text=name,padding=8); box.pack(fill="x",pady=4)
            typ=tk.StringVar(value="Text")
            val=tk.StringVar(value={"Červená":"ČERVENÁ","Zelená":"ZELENÁ","Modrá":"MODRÁ","Normální":"NORMÁLNÍ"}[name])
            self.vars[name]=(typ,val)
            combo=ttk.Combobox(box,textvariable=typ,values=("Vypnuto","Text","QR"),state="readonly",width=12)
            combo.pack(side="left")
            ent=ttk.Entry(box,textvariable=val)
            ent.pack(side="left",fill="x",expand=True,padx=(8,0))
            combo.bind("<<ComboboxSelected>>",lambda e:self.schedule_preview())
            ent.bind("<KeyRelease>",lambda e:self.schedule_preview())
            ent.bind("<<Paste>>",lambda e:self.after(20,self.schedule_preview))

        opts=ttk.LabelFrame(left,text="Varianta",padding=8); opts.pack(fill="x",pady=(10,4))
        self.variant=tk.IntVar(value=7)
        for i in range(1,13):
            ttk.Radiobutton(opts,text=str(i),value=i,variable=self.variant,
                            command=self.schedule_preview).grid(row=(i-1)//6,column=(i-1)%6,padx=7,pady=4)

        strength=ttk.LabelFrame(left,text="Síla normální vrstvy",padding=8)
        strength.pack(fill="x",pady=(6,4))
        self.normal_mult=tk.DoubleVar(value=1.25)
        ttk.Scale(strength,from_=0.5,to=2.5,variable=self.normal_mult,
                  command=lambda _=None:self.schedule_preview()).pack(side="left",fill="x",expand=True)
        self.normal_strength_label=ttk.Label(strength,text="125 %",width=7)
        self.normal_strength_label.pack(side="left",padx=(8,0))
        self.normal_mult.trace_add("write",self._normal_strength_changed)

        b=ttk.Frame(left); b.pack(fill="x",pady=10)
        ttk.Button(b,text="Obnovit náhled",command=self.schedule_preview).pack(side="left",padx=(0,6))
        ttk.Button(b,text="Uložit PNG",command=self.save_png).pack(side="left",padx=(0,6))
        ttk.Button(b,text="12 variant + A4 PDF",command=self.calibration).pack(side="left")

        ok,msg=qrcode_diagnostika()
        if not ok:
            ttk.Label(left,text="⚠ QR modul není správně nainstalovaný. Text funguje; pro QR klikni na „Diagnostika QR“.",
                      wraplength=430).pack(anchor="w",pady=(6,2))
            ttk.Button(left,text="Diagnostika QR",command=lambda:messagebox.showerror("QR diagnostika",msg)).pack(anchor="w")

        ttk.Label(right,text="Živý náhled",font=("TkDefaultFont",13,"bold")).pack(anchor="w")
        self.preview_frame=ttk.Frame(right)
        self.preview_frame.pack(fill="both",expand=True,pady=(8,0))
        self.preview_label=ttk.Label(self.preview_frame,anchor="center")
        self.preview_label.pack(fill="both",expand=True)
        self.preview_frame.bind("<Configure>",lambda e:self.fit_preview())

        self.status=tk.StringVar(value="Připraveno")
        ttk.Label(root,textvariable=self.status).pack(fill="x",pady=(8,0))

    def _normal_strength_changed(self,*_):
        try:
            self.normal_strength_label.configure(text=f"{self.normal_mult.get()*100:.0f} %")
        except Exception:
            pass
        self.schedule_preview()

    def vrstvy(self):
        return {k:(v[0].get(),v[1].get()) for k,v in self.vars.items()}

    def schedule_preview(self,*_):
        # Debounce: při psaní nerenderujeme po každém jednotlivém znaku.
        if self.preview_job is not None:
            try: self.after_cancel(self.preview_job)
            except Exception: pass
        self.preview_job=self.after(180,self.render_preview)

    def render_preview(self):
        self.preview_job=None
        try:
            self.status.set("Obnovuji náhled…")
            self.update_idletasks()
            # Menší interní render = rychlé GUI; tiskový export zůstává velký.
            self.preview_source=generuj(self.vrstvy(),self.variant.get(),size=520,normal_mult=self.normal_mult.get())
            self.fit_preview()
            self.status.set(f"Náhled varianty {self.variant.get()} je aktuální.")
        except Exception as e:
            self.status.set("Chyba náhledu.")
            messagebox.showerror("Chyba",str(e))

    def fit_preview(self):
        if self.preview_source is None:return
        w=max(100,self.preview_frame.winfo_width()-12)
        h=max(100,self.preview_frame.winfo_height()-12)
        s=max(100,min(w,h))
        im=self.preview_source.copy()
        im.thumbnail((s,s),Image.Resampling.NEAREST)
        self.preview_photo=ImageTk.PhotoImage(im)
        self.preview_label.configure(image=self.preview_photo)

    def save_png(self):
        path=filedialog.asksaveasfilename(defaultextension=".png",
             filetypes=[("PNG obrázek","*.png")],initialfile="rgb_skryty_obsah.png")
        if not path:return
        try:
            self.status.set("Generuji tiskové PNG…"); self.update_idletasks()
            im=generuj(self.vrstvy(),self.variant.get(),size=1800,normal_mult=self.normal_mult.get())
            im.save(path,dpi=(300,300))
            self.status.set(f"Uloženo: {path}")
            messagebox.showinfo("Hotovo","PNG bylo vytvořeno.")
        except Exception as e: messagebox.showerror("Chyba",str(e))

    def calibration(self):
        folder=filedialog.askdirectory(title="Vyber složku pro kalibraci")
        if not folder:return
        try:
            self.status.set("Generuji 12 variant…"); self.update_idletasks()
            files=[]
            for i in range(1,13):
                p=Path(folder)/f"varianta_{i:02d}.png"
                generuj(self.vrstvy(),i,size=720,seed=260925+i,normal_mult=self.normal_mult.get()).save(p,dpi=(300,300))
                files.append(p)
                self.status.set(f"Generuji variantu {i}/12…"); self.update_idletasks()
            pdf=Path(folder)/"kalibrace_A4.pdf"
            uloz_pdf(files,pdf)
            self.status.set(f"Hotovo: {pdf}")
            messagebox.showinfo("Hotovo",f"Vytvořeno 12 PNG + A4 PDF:\n{pdf}")
        except Exception as e: messagebox.showerror("Chyba",str(e))

if __name__=="__main__":
    App().mainloop()

