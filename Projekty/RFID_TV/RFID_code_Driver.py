"""RFID/TV stanoviště: TV_RFID_PART.ino přes USB (115200 baud).
RFID_OK/NOT_OK zobrazí stav, TASK_DONE po QR spustí přípravu videa a HackTV.
Knihovny: pyserial, Pillow, Tkinter; externě FFmpeg a HackTV.
Port v serial_ports.json; cesty BASE/HACKTV níže, zapojení v README.md.
"""

from connection_config import serial_endpoint

import tkinter as tk
import serial
import subprocess
import threading
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# NASTAVENÍ
# ============================================================

# Arduino
PORT, BAUD = serial_endpoint("rfid_tv")

# HackTV
FREQUENCY = "197000000"
SAMPLE_RATE = "6000000"
GAIN = "20"

# Soubory
BASE = Path(r"C:\RFID-TV")

SOURCE_IMAGE = BASE / "image.png"
BROADCAST_IMAGE = BASE / "broadcast.png"
VIDEO = BASE / "access.mpg"

HACKTV = Path(r"C:\hacktv\bin\hacktv.exe")

# Text, který se ukáže AŽ PO SPLNĚNÍ ÚKOLU na CRT
BROADCAST_TEXT = "101.5 FM"

# Délka vysílání
VIDEO_SECONDS = 15

# Doba zobrazení chybné karty
WRONG_SCREEN_MS = 3000


# ============================================================
# GLOBÁLNÍ PROMĚNNÉ
# ============================================================

hacktv_process = None
ser = None
wrong_screen_timer = None
running = True


# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title("RFID ÚKOL")
root.configure(bg="#05070A")

root.attributes("-fullscreen", True)
root.attributes("-topmost", True)

SCREEN_W = root.winfo_screenwidth()
SCREEN_H = root.winfo_screenheight()


# ============================================================
# BARVY
# ============================================================

BG = "#05070A"
PANEL = "#0D1218"
PANEL_2 = "#111A22"

WHITE = "#F4F7FA"
GRAY = "#7F8C96"

CYAN = "#00D9FF"
GREEN = "#20E070"
RED = "#FF334F"
YELLOW = "#FFD43B"


# ============================================================
# VELIKOSTI PÍSMA
# ============================================================

TITLE_FONT = max(20, int(SCREEN_H * 0.035))
BIG_FONT = max(48, int(SCREEN_H * 0.085))
MEDIUM_FONT = max(25, int(SCREEN_H * 0.045))
SMALL_FONT = max(15, int(SCREEN_H * 0.022))


# ============================================================
# HLAVNÍ PLOCHA
# ============================================================

main_frame = tk.Frame(
    root,
    bg=BG
)

main_frame.pack(
    fill="both",
    expand=True
)


# ============================================================
# VYČIŠTĚNÍ OBRAZOVKY
# ============================================================

def clear_screen():

    global wrong_screen_timer

    if wrong_screen_timer is not None:

        try:
            root.after_cancel(wrong_screen_timer)
        except Exception:
            pass

        wrong_screen_timer = None

    for widget in main_frame.winfo_children():
        widget.destroy()


# ============================================================
# HORNÍ LIŠTA
# ============================================================

def create_header(status_text, status_color):

    header = tk.Frame(
        main_frame,
        bg=PANEL,
        height=int(SCREEN_H * 0.10)
    )

    header.pack(fill="x")
    header.pack_propagate(False)


    left = tk.Frame(
        header,
        bg=PANEL
    )

    left.pack(
        side="left",
        fill="y",
        padx=35
    )


    tk.Label(
        left,
        text="RFID ÚKOL",
        fg=WHITE,
        bg=PANEL,
        font=("Arial", TITLE_FONT, "bold")
    ).pack(
        side="left"
    )


    right = tk.Frame(
        header,
        bg=PANEL
    )

    right.pack(
        side="right",
        fill="y",
        padx=35
    )


    indicator = tk.Canvas(
        right,
        width=22,
        height=22,
        bg=PANEL,
        highlightthickness=0
    )

    indicator.pack(
        side="left",
        padx=(0, 12)
    )


    indicator.create_oval(
        4,
        4,
        18,
        18,
        fill=status_color,
        outline=""
    )


    tk.Label(
        right,
        text=status_text,
        fg=status_color,
        bg=PANEL,
        font=("Arial", SMALL_FONT, "bold")
    ).pack(
        side="left"
    )


# ============================================================
# SPODNÍ LIŠTA
# ============================================================

def create_footer():

    footer = tk.Frame(
        main_frame,
        bg=PANEL,
        height=int(SCREEN_H * 0.075)
    )

    footer.pack(
        side="bottom",
        fill="x"
    )

    footer.pack_propagate(False)


    tk.Label(
        footer,
        text="RFID01",
        fg=GRAY,
        bg=PANEL,
        font=("Arial", SMALL_FONT)
    ).pack(
        side="left",
        padx=35
    )


    tk.Label(
        footer,
        text="SYSTÉM PŘIPRAVEN",
        fg=GRAY,
        bg=PANEL,
        font=("Arial", SMALL_FONT, "bold")
    ).pack(
        side="right",
        padx=35
    )


# ============================================================
# IKONA RFID KARTY
# ============================================================

def draw_rfid_card(parent, color):

    canvas = tk.Canvas(
        parent,
        width=300,
        height=210,
        bg=BG,
        highlightthickness=0
    )

    canvas.pack(
        pady=(20, 5)
    )


    # Karta
    canvas.create_rectangle(
        45, 35,
        255, 175,
        outline=color,
        width=5
    )

    canvas.create_rectangle(
        52, 42,
        248, 168,
        outline=color,
        width=2
    )


    # Čip
    canvas.create_rectangle(
        75, 80,
        120, 120,
        fill=color,
        outline=color
    )


    # RFID vlny
    canvas.create_arc(
        130, 65,
        180, 135,
        start=-60,
        extent=120,
        style="arc",
        outline=color,
        width=4
    )

    canvas.create_arc(
        130, 45,
        210, 155,
        start=-60,
        extent=120,
        style="arc",
        outline=color,
        width=4
    )

    canvas.create_arc(
        130, 25,
        240, 175,
        start=-60,
        extent=120,
        style="arc",
        outline=color,
        width=4
    )


# ============================================================
# ČEKACÍ OBRAZOVKA
# ============================================================

def show_waiting():

    clear_screen()

    create_header(
        "SYSTÉM PŘIPRAVEN",
        GREEN
    )

    create_footer()


    center = tk.Frame(
        main_frame,
        bg=BG
    )

    center.pack(
        fill="both",
        expand=True
    )


    tk.Label(
        center,
        text="RFID ÚKOL",
        fg=CYAN,
        bg=BG,
        font=("Arial", TITLE_FONT, "bold")
    ).pack(
        pady=(25, 0)
    )


    draw_rfid_card(
        center,
        CYAN
    )


    tk.Label(
        center,
        text="PŘILOŽ KARTU",
        fg=WHITE,
        bg=BG,
        font=("Arial", BIG_FONT, "bold")
    ).pack(
        pady=5
    )


    tk.Label(
        center,
        text="ČEKÁM NA RFID...",
        fg=YELLOW,
        bg=BG,
        font=("Arial", MEDIUM_FONT, "bold")
    ).pack(
        pady=10
    )


    tk.Label(
        center,
        text="Přilož kartu ke čtečce",
        fg=GRAY,
        bg=BG,
        font=("Arial", SMALL_FONT)
    ).pack(
        pady=15
    )


# ============================================================
# SPRÁVNÁ KARTA
# ============================================================

def show_correct():

    clear_screen()

    create_header(
        "KARTA PŘIJATA",
        GREEN
    )

    create_footer()


    center = tk.Frame(
        main_frame,
        bg=BG
    )

    center.pack(
        fill="both",
        expand=True
    )


    check = tk.Canvas(
        center,
        width=230,
        height=230,
        bg=BG,
        highlightthickness=0
    )

    check.pack(
        pady=(30, 5)
    )


    check.create_oval(
        15, 15,
        215, 215,
        outline=GREEN,
        width=8
    )


    check.create_line(
        65, 120,
        105, 160,
        fill=GREEN,
        width=13,
        capstyle="round"
    )


    check.create_line(
        105, 160,
        170, 85,
        fill=GREEN,
        width=13,
        capstyle="round"
    )


    tk.Label(
        center,
        text="SPRÁVNÁ KARTA",
        fg=GREEN,
        bg=BG,
        font=("Arial", BIG_FONT, "bold")
    ).pack(
        pady=5
    )


    tk.Label(
        center,
        text="DOKONČUJI ÚKOL...",
        fg=WHITE,
        bg=BG,
        font=("Arial", MEDIUM_FONT, "bold")
    ).pack(
        pady=10
    )


    tk.Label(
        center,
        text="Počkej na dokončení",
        fg=GRAY,
        bg=BG,
        font=("Arial", SMALL_FONT)
    ).pack(
        pady=15
    )


# ============================================================
# ŠPATNÁ KARTA
# ============================================================

def show_wrong():

    global wrong_screen_timer

    clear_screen()

    create_header(
        "KARTA ODMÍTNUTA",
        RED
    )

    create_footer()


    center = tk.Frame(
        main_frame,
        bg=BG
    )

    center.pack(
        fill="both",
        expand=True
    )


    cross = tk.Canvas(
        center,
        width=230,
        height=230,
        bg=BG,
        highlightthickness=0
    )

    cross.pack(
        pady=(30, 5)
    )


    cross.create_oval(
        15, 15,
        215, 215,
        outline=RED,
        width=8
    )


    cross.create_line(
        75, 75,
        155, 155,
        fill=RED,
        width=13,
        capstyle="round"
    )


    cross.create_line(
        155, 75,
        75, 155,
        fill=RED,
        width=13,
        capstyle="round"
    )


    tk.Label(
        center,
        text="ŠPATNÁ KARTA",
        fg=RED,
        bg=BG,
        font=("Arial", BIG_FONT, "bold")
    ).pack(
        pady=5
    )


    tk.Label(
        center,
        text="ZKUS TO ZNOVU",
        fg=WHITE,
        bg=BG,
        font=("Arial", MEDIUM_FONT, "bold")
    ).pack(
        pady=10
    )


    tk.Label(
        center,
        text="Tato karta není správná",
        fg=GRAY,
        bg=BG,
        font=("Arial", SMALL_FONT)
    ).pack(
        pady=15
    )


    wrong_screen_timer = root.after(
        WRONG_SCREEN_MS,
        show_waiting
    )


# ============================================================
# ÚKOL SPLNĚN
# ============================================================

def show_task_done():

    clear_screen()

    create_header(
        "ÚKOL SPLNĚN",
        GREEN
    )

    create_footer()


    center = tk.Frame(
        main_frame,
        bg=BG
    )

    center.pack(
        fill="both",
        expand=True
    )


    check = tk.Canvas(
        center,
        width=230,
        height=230,
        bg=BG,
        highlightthickness=0
    )

    check.pack(
        pady=(40, 5)
    )


    check.create_oval(
        15, 15,
        215, 215,
        outline=GREEN,
        width=8
    )


    check.create_line(
        65, 120,
        105, 160,
        fill=GREEN,
        width=13,
        capstyle="round"
    )


    check.create_line(
        105, 160,
        170, 85,
        fill=GREEN,
        width=13,
        capstyle="round"
    )


    tk.Label(
        center,
        text="ÚKOL SPLNĚN",
        fg=GREEN,
        bg=BG,
        font=("Arial", BIG_FONT, "bold")
    ).pack(
        pady=10
    )


    tk.Label(
        center,
        text="SLEDUJ TELEVIZI",
        fg=WHITE,
        bg=BG,
        font=("Arial", MEDIUM_FONT, "bold")
    ).pack(
        pady=10
    )


# ============================================================
# VYTVOŘENÍ FINÁLNÍHO OBRAZU PRO CRT
#
# TATO FUNKCE SE SPUSTÍ AŽ PO TASK_DONE
# ============================================================

def create_broadcast_video():

    print()
    print("==========================================")
    print("ÚKOL SPLNĚN")
    print("VYTVÁŘÍM OBRAZ PRO TELEVIZI")
    print("==========================================")
    print()


    if not SOURCE_IMAGE.exists():

        print(
            "CHYBA: Obrázek nebyl nalezen:"
        )

        print(
            SOURCE_IMAGE
        )

        return False


    try:

        # PAL obraz
        canvas = Image.new(
            "RGB",
            (720, 576),
            "black"
        )


        source = Image.open(
            SOURCE_IMAGE
        ).convert("RGB")


        # Necháme dole místo pro 101.5 FM
        source.thumbnail(
            (680, 420)
        )


        x = (
            720 - source.width
        ) // 2


        y = 20


        canvas.paste(
            source,
            (x, y)
        )


        # ----------------------------------------------------
        # TEXT 101.5 FM
        # ----------------------------------------------------

        draw = ImageDraw.Draw(
            canvas
        )


        font_path = Path(
            r"C:\Windows\Fonts\arialbd.ttf"
        )


        if font_path.exists():

            font = ImageFont.truetype(
                str(font_path),
                70
            )

        else:

            font = ImageFont.load_default()


        box = draw.textbbox(
            (0, 0),
            BROADCAST_TEXT,
            font=font,
            stroke_width=3
        )


        text_width = (
            box[2] - box[0]
        )


        text_x = (
            720 - text_width
        ) // 2


        text_y = 470


        # Panel pod textem
        draw.rounded_rectangle(
            (
                text_x - 30,
                text_y - 15,
                text_x + text_width + 30,
                text_y + 90
            ),
            radius=15,
            fill="#101820",
            outline="white",
            width=2
        )


        # Samotný text
        draw.text(
            (
                text_x,
                text_y
            ),
            BROADCAST_TEXT,
            font=font,
            fill="white",
            stroke_width=3,
            stroke_fill="black"
        )


        canvas.save(
            BROADCAST_IMAGE
        )


        print(
            "Obraz vytvořen:"
        )

        print(
            BROADCAST_IMAGE
        )


    except Exception as error:

        print(
            "CHYBA při vytváření obrazu:"
        )

        print(
            error
        )

        return False


    # ========================================================
    # VYTVOŘENÍ MPEG VIDEA
    # ========================================================

    ffmpeg_command = [

        "ffmpeg",

        "-y",

        "-loop",
        "1",

        "-framerate",
        "25",

        "-i",
        str(BROADCAST_IMAGE),

        "-t",
        str(VIDEO_SECONDS),

        "-r",
        "25",

        "-c:v",
        "mpeg2video",

        "-q:v",
        "2",

        "-an",

        str(VIDEO)
    ]


    try:

        result = subprocess.run(
            ffmpeg_command
        )


        if result.returncode != 0:

            print(
                "CHYBA: FFmpeg selhal."
            )

            return False


    except FileNotFoundError:

        print(
            "CHYBA: ffmpeg.exe nebyl nalezen."
        )

        return False


    except Exception as error:

        print(
            "CHYBA FFmpeg:"
        )

        print(
            error
        )

        return False


    print()
    print(
        "Video pro CRT je připraveno:"
    )

    print(
        VIDEO
    )

    print()
    print(
        "Na obrazu bude:"
    )

    print(
        BROADCAST_TEXT
    )

    print()

    return True


# ============================================================
# SPUŠTĚNÍ HACKTV
# ============================================================

def start_stream():

    global hacktv_process


    # Pokud už HackTV běží, nespouštěj druhou kopii
    if hacktv_process is not None:

        if hacktv_process.poll() is None:

            print(
                ">>> HackTV už běží."
            )

            return

        hacktv_process = None


    if not HACKTV.exists():

        print(
            ">>> CHYBA: HackTV nebyl nalezen:"
        )

        print(
            HACKTV
        )

        return


    if not VIDEO.exists():

        print(
            ">>> CHYBA: Video nebylo nalezeno:"
        )

        print(
            VIDEO
        )

        return


    command = [

        str(HACKTV),

        "-m",
        "b",

        "-s",
        SAMPLE_RATE,

        "-f",
        FREQUENCY,

        "-g",
        GAIN,

        "-o",
        "hackrf",

        str(VIDEO)
    ]


    print()
    print("==========================================")
    print("SPOUŠTÍM TV VYSÍLÁNÍ")
    print("==========================================")

    print(
        "RF frekvence:",
        FREQUENCY
    )

    print(
        "Vzorkovací frekvence:",
        SAMPLE_RATE
    )

    print(
        "Video:",
        VIDEO
    )

    print()


    try:

        hacktv_process = subprocess.Popen(
            command
        )


        print(
            ">>> HackTV spuštěn."
        )


    except Exception as error:

        print(
            ">>> CHYBA při spuštění HackTV:"
        )

        print(
            error
        )

        hacktv_process = None


# ============================================================
# TASK_DONE
# ============================================================

def task_finished():

    print()
    print("==========================================")
    print(">>> ÚKOL BYL DOKONČEN")
    print("==========================================")
    print()


    # PC obrazovka
    root.after(
        0,
        show_task_done
    )


    # --------------------------------------------------------
    # TEPRVE TEĎ:
    #
    # 1. vytvoříme obraz s 101.5 FM
    # 2. vytvoříme video
    # 3. spustíme HackTV
    # --------------------------------------------------------

    if create_broadcast_video():

        start_stream()


# ============================================================
# ZPRÁVY Z ARDUINA
# ============================================================

def handle_message(line):

    print(
        "PŘIJATO:",
        repr(line)
    )


    # --------------------------------------------------------
    # SPRÁVNÁ KARTA
    # --------------------------------------------------------

    if line == "RFID_OK":

        print(
            ">>> SPRÁVNÁ KARTA"
        )


        root.after(
            0,
            show_correct
        )


        # POZOR:
        # ZDE SE HACKTV JEŠTĚ NESPOUŠTÍ!

        return


    # --------------------------------------------------------
    # ŠPATNÁ KARTA
    # --------------------------------------------------------

    if line == "NOT_OK":

        print(
            ">>> ŠPATNÁ KARTA"
        )


        root.after(
            0,
            show_wrong
        )


        # HackTV se nezastavuje.

        return


    # --------------------------------------------------------
    # ÚKOL DOKONČEN
    # --------------------------------------------------------

    if line == "TASK_DONE":

        print(
            ">>> TASK_DONE"
        )


        threading.Thread(
            target=task_finished,
            daemon=True
        ).start()


        return


    print(
        ">>> Zpráva ignorována."
    )


# ============================================================
# SÉRIOVÁ KOMUNIKACE
# ============================================================

def serial_worker():

    global ser
    global hacktv_process
    global running


    try:

        ser = serial.Serial(
            PORT,
            BAUD,
            timeout=0.1
        )


        print()
        print(
            ">>> Arduino připojeno:",
            PORT
        )


        # Mega se po otevření COM portu může resetovat
        time.sleep(2)


        ser.reset_input_buffer()


        print(
            ">>> Čekám na RFID kartu..."
        )

        print()


        while running:

            try:

                raw = ser.readline()


                if raw:

                    line = raw.decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()


                    if line:

                        handle_message(
                            line
                        )


                # --------------------------------------------
                # HackTV skončilo samo
                # --------------------------------------------

                if hacktv_process is not None:

                    if hacktv_process.poll() is not None:

                        print()
                        print(
                            ">>> TV vysílání skončilo."
                        )

                        print(
                            ">>> HackTV skončilo přirozeně."
                        )

                        print()


                        # Pouze zapomeneme proces.
                        # Nic nezabíjíme.
                        hacktv_process = None


            except Exception as error:

                if running:

                    print(
                        ">>> CHYBA SÉRIOVÉ KOMUNIKACE:"
                    )

                    print(
                        error
                    )

                break


    except Exception as error:

        print()
        print(
            ">>> NELZE OTEVŘÍT SÉRIOVÝ PORT:"
        )

        print(
            error
        )

        print()
        print(
            "Zkontroluj, že COM7 nepoužívá "
            "Serial Monitor, Serial Plotter "
            "nebo jiný Python program."
        )


# ============================================================
# UKONČENÍ PROGRAMU
# ============================================================

def close_program():

    global ser
    global running


    running = False


    print()
    print(
        ">>> Ukončuji RFID program."
    )


    try:

        if ser is not None:

            if ser.is_open:

                ser.close()

    except Exception:

        pass


    # ========================================================
    # DŮLEŽITÉ:
    #
    # HACKTV NEUKONČUJEME.
    # Žádné kill()
    # Žádné terminate()
    #
    # Pokud vysílání běží, necháme ho skončit samo.
    # ========================================================


    root.destroy()


# ESC zavře pouze Python GUI
root.bind(
    "<Escape>",
    lambda event: close_program()
)


# ============================================================
# START PROGRAMU
# ============================================================

print()
print("==========================================")
print("RFID ÚKOL")
print("==========================================")
print()

print(
    ">>> Čekám na dokončení úkolu."
)

print(
    ">>> 101.5 FM se zobrazí až po TASK_DONE."
)

print()


# POZOR:
# Při startu programu NEVYTVÁŘÍME video s 101.5 FM.
# To se udělá až po TASK_DONE.


show_waiting()


serial_thread = threading.Thread(
    target=serial_worker,
    daemon=True
)

serial_thread.start()


root.mainloop()