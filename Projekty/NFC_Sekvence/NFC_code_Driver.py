"""NFC sekvence: NFC_Smiley_Parat.ino (Uno) + Displays_Driver_part.ino (Mega).
Dva USB porty, 9600 baud; CARD:UID -> OK/WRONG/RESET a KEY:/UNLOCKED.
Knihovny: pyserial, Tkinter; porty v serial_ports.json, zapojení v README.md.
"""

from connection_config import serial_endpoint

import tkinter as tk
import serial
import threading
import time


# ============================================================
# NASTAVENI COM PORTU
# ============================================================

# Arduino UNO
# RC522 + MAX7219
RC522_PORT, RC522_BAUD = serial_endpoint("nfc_reader")

# Arduino MEGA
# ST7789 + SH1106
DISPLAY_PORT, DISPLAY_BAUD = serial_endpoint("nfc_display")


# ============================================================
# RFID SEKQUENCE
# ============================================================
#
# Spravne poradi:
#
# 1. 00:39:55:D3
# 2. A0:5E:E1:28
# 3. C0:67:A1:2B
#
# UID jsou ulozena bez dvojtecek.
# ============================================================

SPRAVNE_PORADI = [
    "003955D3",
    "A05EE128",
    "C067A12B"
]


# ============================================================
# POSTUPNE ODKRYVANI KODU
# ============================================================

KOD_STAVY = [
    "____",
    "2___",
    "20__",
    "2012"
]


# ============================================================
# STAV HRY
# ============================================================

aktualni_krok = 0
odemceno = False
reset_probiha = False


# ============================================================
# SERIAL
# ============================================================

rc522_serial = None
display_serial = None

rc522_lock = threading.Lock()
display_lock = threading.Lock()


# ============================================================
# BARVY GUI
# ============================================================

BG = "#070A0F"

PANEL = "#10151D"
PANEL_ACTIVE = "#151C26"

TEXT = "#F4F7FA"
MUTED = "#667080"

CYAN = "#00E5FF"
YELLOW = "#FFD740"
GREEN = "#00E676"
RED = "#FF3D4A"

GREEN_BG = "#09261A"
RED_BG = "#2A0C10"

BORDER = "#252D38"


# ============================================================
# HLAVNI OKNO
# ============================================================

root = tk.Tk()

root.title(
    "Přístupová sekvence"
)

root.configure(
    bg=BG
)

root.attributes(
    "-fullscreen",
    True
)

root.attributes(
    "-topmost",
    True
)


# ESC = ukonceni programu
root.bind(
    "<Escape>",
    lambda event: root.destroy()
)


# ============================================================
# HLAVNI GRID
# ============================================================

root.grid_columnconfigure(
    0,
    weight=1
)

root.grid_rowconfigure(
    0,
    weight=0
)

root.grid_rowconfigure(
    1,
    weight=1
)

root.grid_rowconfigure(
    2,
    weight=0
)


# ============================================================
# HLAVICKA
# ============================================================

header = tk.Frame(
    root,
    bg=BG
)

header.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=50,
    pady=(30, 10)
)

header.grid_columnconfigure(
    0,
    weight=1
)

header.grid_columnconfigure(
    1,
    weight=0
)


# ============================================================
# LEVA CAST HLAVICKY
# ============================================================

header_left = tk.Frame(
    header,
    bg=BG
)

header_left.grid(
    row=0,
    column=0,
    sticky="w"
)


title = tk.Label(
    header_left,
    text="PŘÍSTUPOVÁ SEKVENCE",
    bg=BG,
    fg=TEXT,
    font=(
        "Segoe UI",
        30,
        "bold"
    )
)

title.pack(
    anchor="w"
)


subtitle = tk.Label(
    header_left,
    text="Přiložte RFID karty ve správném pořadí",
    bg=BG,
    fg=MUTED,
    font=(
        "Segoe UI",
        15
    )
)

subtitle.pack(
    anchor="w",
    pady=(4, 0)
)


# ============================================================
# STAV SYSTEMU VPRAVO NAHORE
# ============================================================

status_box = tk.Frame(
    header,
    bg=PANEL,
    padx=20,
    pady=10,
    highlightbackground=BORDER,
    highlightthickness=1
)

status_box.grid(
    row=0,
    column=1,
    sticky="e"
)


status_dot = tk.Label(
    status_box,
    text="●",
    bg=PANEL,
    fg=CYAN,
    font=(
        "Segoe UI",
        17,
        "bold"
    )
)

status_dot.pack(
    side="left"
)


status_label = tk.Label(
    status_box,
    text="  PŘIPRAVENO",
    bg=PANEL,
    fg=TEXT,
    font=(
        "Segoe UI",
        13,
        "bold"
    )
)

status_label.pack(
    side="left"
)


# ============================================================
# HLAVNI OBLAST KARET
# ============================================================

content = tk.Frame(
    root,
    bg=BG
)

content.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=50,
    pady=20
)


for i in range(3):

    content.grid_columnconfigure(
        i,
        weight=1,
        uniform="cards"
    )


content.grid_rowconfigure(
    0,
    weight=1
)


# ============================================================
# VYTVORENI PANELU KARTY
# ============================================================

def vytvor_kartu(
    parent,
    column,
    cislo
):

    container = tk.Frame(
        parent,
        bg=BG
    )

    container.grid(
        row=0,
        column=column,
        sticky="nsew",
        padx=14
    )


    card = tk.Frame(
        container,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=2
    )

    card.pack(
        fill="both",
        expand=True
    )


    # --------------------------------------------------------
    # CISLO KROKU
    # --------------------------------------------------------

    step_label = tk.Label(
        card,
        text=f"KROK 0{cislo}",
        bg=PANEL,
        fg=MUTED,
        font=(
            "Segoe UI",
            12,
            "bold"
        )
    )

    step_label.pack(
        pady=(30, 0)
    )


    # --------------------------------------------------------
    # KARTA
    # --------------------------------------------------------

    card_title = tk.Label(
        card,
        text=f"KARTA {cislo}",
        bg=PANEL,
        fg=TEXT,
        font=(
            "Segoe UI",
            26,
            "bold"
        )
    )

    card_title.pack(
        pady=(6, 15)
    )


    # --------------------------------------------------------
    # SYMBOL
    # --------------------------------------------------------

    symbol = tk.Label(
        card,
        text="○",
        bg=PANEL,
        fg=MUTED,
        font=(
            "Segoe UI Symbol",
            100,
            "bold"
        )
    )

    symbol.pack(
        expand=True
    )


    # --------------------------------------------------------
    # STAV
    # --------------------------------------------------------

    stav = tk.Label(
        card,
        text="ČEKÁ",
        bg=PANEL,
        fg=MUTED,
        font=(
            "Segoe UI",
            20,
            "bold"
        )
    )

    stav.pack(
        pady=(10, 5)
    )


    # --------------------------------------------------------
    # POPIS
    # --------------------------------------------------------

    popis = tk.Label(
        card,
        text="",
        bg=PANEL,
        fg=MUTED,
        font=(
            "Segoe UI",
            12
        )
    )

    popis.pack(
        pady=(0, 30)
    )


    return {
        "container": container,
        "frame": card,
        "step": step_label,
        "title": card_title,
        "symbol": symbol,
        "stav": stav,
        "popis": popis
    }


# ============================================================
# TRI PANELY
# ============================================================

panel1 = vytvor_kartu(
    content,
    0,
    1
)

panel2 = vytvor_kartu(
    content,
    1,
    2
)

panel3 = vytvor_kartu(
    content,
    2,
    3
)


panely = [
    panel1,
    panel2,
    panel3
]


# ============================================================
# SPODNI STAVOVY PANEL
# ============================================================

footer = tk.Frame(
    root,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1
)

footer.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=50,
    pady=(5, 35)
)


footer.grid_columnconfigure(
    0,
    weight=1
)

footer.grid_columnconfigure(
    1,
    weight=1
)

footer.grid_columnconfigure(
    2,
    weight=1
)


# ============================================================
# AKTUALNI STAV
# ============================================================

footer_left = tk.Frame(
    footer,
    bg=PANEL
)

footer_left.grid(
    row=0,
    column=0,
    sticky="w",
    padx=30,
    pady=20
)


footer_status_title = tk.Label(
    footer_left,
    text="AKTUÁLNÍ STAV",
    bg=PANEL,
    fg=MUTED,
    font=(
        "Segoe UI",
        10,
        "bold"
    )
)

footer_status_title.pack(
    anchor="w"
)


label_hlavni_stav = tk.Label(
    footer_left,
    text="ČEKÁM NA KARTU 1",
    bg=PANEL,
    fg=YELLOW,
    font=(
        "Segoe UI",
        18,
        "bold"
    )
)

label_hlavni_stav.pack(
    anchor="w",
    pady=(4, 0)
)


# ============================================================
# PRISTUPOVY KOD
# ============================================================

footer_middle = tk.Frame(
    footer,
    bg=PANEL
)

footer_middle.grid(
    row=0,
    column=1,
    pady=15
)


kod_title = tk.Label(
    footer_middle,
    text="PŘÍSTUPOVÝ KÓD",
    bg=PANEL,
    fg=MUTED,
    font=(
        "Segoe UI",
        10,
        "bold"
    )
)

kod_title.pack()


label_kod = tk.Label(
    footer_middle,
    text="____",
    bg=PANEL,
    fg=CYAN,
    font=(
        "Consolas",
        42,
        "bold"
    )
)

label_kod.pack()


# ============================================================
# POSTUP
# ============================================================

footer_right = tk.Frame(
    footer,
    bg=PANEL
)

footer_right.grid(
    row=0,
    column=2,
    sticky="e",
    padx=30
)


progress_title = tk.Label(
    footer_right,
    text="POSTUP",
    bg=PANEL,
    fg=MUTED,
    font=(
        "Segoe UI",
        10,
        "bold"
    )
)

progress_title.pack(
    anchor="e"
)


label_postup = tk.Label(
    footer_right,
    text="0 / 3",
    bg=PANEL,
    fg=TEXT,
    font=(
        "Segoe UI",
        25,
        "bold"
    )
)

label_postup.pack(
    anchor="e"
)


# ============================================================
# POMOCNA FUNKCE - BARVA PANELU
# ============================================================

def barva_karty(
    panel,
    bg
):

    panel["frame"].configure(
        bg=bg
    )

    panel["step"].configure(
        bg=bg
    )

    panel["title"].configure(
        bg=bg
    )

    panel["symbol"].configure(
        bg=bg
    )

    panel["stav"].configure(
        bg=bg
    )

    panel["popis"].configure(
        bg=bg
    )


# ============================================================
# NEAKTIVNI KARTA
# ============================================================

def nastav_neaktivni(panel):

    barva_karty(
        panel,
        PANEL
    )

    panel["frame"].configure(
        highlightbackground=BORDER
    )

    panel["step"].configure(
        fg=MUTED
    )

    panel["title"].configure(
        fg="#A0A8B3"
    )

    panel["symbol"].configure(
        text="○",
        fg="#39424F"
    )

    panel["stav"].configure(
        text="ČEKÁ",
        fg=MUTED
    )

    panel["popis"].configure(
        text="Nejdříve dokončete předchozí krok",
        fg=MUTED
    )


# ============================================================
# AKTIVNI KARTA
# ============================================================

def nastav_cekani(panel):

    barva_karty(
        panel,
        PANEL_ACTIVE
    )

    panel["frame"].configure(
        highlightbackground=CYAN
    )

    panel["step"].configure(
        fg=CYAN
    )

    panel["title"].configure(
        fg=TEXT
    )

    panel["symbol"].configure(
        text="◎",
        fg=CYAN
    )

    panel["stav"].configure(
        text="PŘILOŽ KARTU",
        fg=YELLOW
    )

    panel["popis"].configure(
        text="Čekám na správnou RFID kartu",
        fg=MUTED
    )


# ============================================================
# SPRAVNA KARTA
# ============================================================

def nastav_spravne(panel):

    barva_karty(
        panel,
        GREEN_BG
    )

    panel["frame"].configure(
        highlightbackground=GREEN
    )

    panel["step"].configure(
        fg=GREEN
    )

    panel["title"].configure(
        fg=TEXT
    )

    panel["symbol"].configure(
        text="✓",
        fg=GREEN
    )

    panel["stav"].configure(
        text="SPRÁVNĚ",
        fg=GREEN
    )

    panel["popis"].configure(
        text="Karta byla přijata",
        fg="#8EA99A"
    )


# ============================================================
# SPATNA KARTA
# ============================================================

def nastav_spatne(panel):

    barva_karty(
        panel,
        RED_BG
    )

    panel["frame"].configure(
        highlightbackground=RED
    )

    panel["step"].configure(
        fg=RED
    )

    panel["title"].configure(
        fg=TEXT
    )

    panel["symbol"].configure(
        text="✕",
        fg=RED
    )

    panel["stav"].configure(
        text="CHYBA",
        fg=RED
    )

    panel["popis"].configure(
        text="Nesprávná karta nebo pořadí",
        fg="#E8989E"
    )


# ============================================================
# OBNOVENI GUI PODLE STAVU
# ============================================================

def obnov_gui():

    # --------------------------------------------------------
    # ODEMCENO
    # --------------------------------------------------------

    if odemceno:

        label_kod.configure(
            text="2012",
            fg=GREEN
        )

        label_hlavni_stav.configure(
            text="PŘÍSTUP ODEMČEN",
            fg=GREEN
        )

        label_postup.configure(
            text="3 / 3",
            fg=GREEN
        )

        status_dot.configure(
            fg=GREEN
        )

        status_label.configure(
            text="  ODEMČENO",
            fg=GREEN
        )

        for panel in panely:

            nastav_spravne(
                panel
            )

        return


    # --------------------------------------------------------
    # NORMALNI STAV
    # --------------------------------------------------------

    label_kod.configure(
        text=KOD_STAVY[aktualni_krok],
        fg=CYAN
    )


    label_hlavni_stav.configure(
        text=f"ČEKÁM NA KARTU {aktualni_krok + 1}",
        fg=YELLOW
    )


    label_postup.configure(
        text=f"{aktualni_krok} / 3",
        fg=TEXT
    )


    status_dot.configure(
        fg=CYAN
    )


    status_label.configure(
        text="  PŘIPRAVENO",
        fg=TEXT
    )


    # --------------------------------------------------------
    # PANELY
    # --------------------------------------------------------

    for i in range(3):

        if i < aktualni_krok:

            nastav_spravne(
                panely[i]
            )

        elif i == aktualni_krok:

            nastav_cekani(
                panely[i]
            )

        else:

            nastav_neaktivni(
                panely[i]
            )


# ============================================================
# CHYBOVY STAV GUI
# ============================================================

def zobraz_chybu():

    label_kod.configure(
        text="XXXX",
        fg=RED
    )

    label_hlavni_stav.configure(
        text="ŠPATNÁ KARTA NEBO POŘADÍ",
        fg=RED
    )

    label_postup.configure(
        text="RESET...",
        fg=RED
    )

    status_dot.configure(
        fg=RED
    )

    status_label.configure(
        text="  CHYBA",
        fg=RED
    )


    # Dokoncene kroky zustanou zelene.
    # Aktualni krok bude cerveny.

    for i in range(3):

        if i < aktualni_krok:

            nastav_spravne(
                panely[i]
            )

        elif i == aktualni_krok:

            nastav_spatne(
                panely[i]
            )

        else:

            nastav_neaktivni(
                panely[i]
            )


# ============================================================
# ODESLANI DO RC522 UNO
# ============================================================

def posli_rc522(prikaz):

    global rc522_serial


    if rc522_serial is None:

        print(
            "RC522 NENÍ PŘIPOJENO:",
            prikaz
        )

        return


    try:

        with rc522_lock:

            rc522_serial.write(
                (
                    prikaz + "\n"
                ).encode("utf-8")
            )

            rc522_serial.flush()


        print(
            "PC -> RC522:",
            prikaz
        )


    except Exception as chyba:

        print(
            "CHYBA ZÁPISU RC522:",
            chyba
        )


# ============================================================
# ODESLANI DO DISPLAY MEGA
# ============================================================

def posli_display(prikaz):

    global display_serial


    if display_serial is None:

        print(
            "DISPLAY NENÍ PŘIPOJEN:",
            prikaz
        )

        return


    try:

        with display_lock:

            display_serial.write(
                (
                    prikaz + "\n"
                ).encode("utf-8")
            )

            display_serial.flush()


        print(
            "PC -> DISPLAY:",
            prikaz
        )


    except Exception as chyba:

        print(
            "CHYBA ZÁPISU DISPLAY:",
            chyba
        )


# ============================================================
# DOKONCENI RESETU PO CHYBE
# ============================================================

def dokonci_reset():

    global aktualni_krok
    global odemceno
    global reset_probiha


    aktualni_krok = 0
    odemceno = False
    reset_probiha = False


    obnov_gui()


    posli_display(
        "RESET"
    )


    posli_rc522(
        "RESET"
    )


    print()
    print(
        "============================"
    )

    print(
        "SYSTÉM RESETOVÁN"
    )

    print(
        "ČEKÁM NA KARTU 1"
    )

    print(
        "============================"
    )


# ============================================================
# SPATNA KARTA
# ============================================================

def spatna_karta():

    global reset_probiha


    if reset_probiha:
        return


    reset_probiha = True


    print()
    print(
        "!!! ŠPATNÁ KARTA / ŠPATNÉ POŘADÍ !!!"
    )


    # GUI
    zobraz_chybu()


    # MAX7219
    posli_rc522(
        "WRONG"
    )


    # TFT + OLED
    posli_display(
        "WRONG"
    )


    # Za 3 sekundy kompletni reset
    root.after(
        3000,
        dokonci_reset
    )


# ============================================================
# SPRAVNA KARTA
# ============================================================

def spravna_karta():

    global aktualni_krok
    global odemceno


    aktualni_krok += 1


    print()
    print(
        "SPRÁVNÁ KARTA:",
        aktualni_krok,
        "/ 3"
    )


    # --------------------------------------------------------
    # MAX7219
    # --------------------------------------------------------

    posli_rc522(
        "OK"
    )


    # --------------------------------------------------------
    # KOD
    # --------------------------------------------------------

    viditelny_kod = KOD_STAVY[
        aktualni_krok
    ]


    # --------------------------------------------------------
    # TFT + OLED
    # --------------------------------------------------------

    posli_display(
        f"KEY:{aktualni_krok}:{viditelny_kod}"
    )


    # --------------------------------------------------------
    # POSLEDNI KARTA
    # --------------------------------------------------------

    if aktualni_krok == 3:

        odemceno = True

        obnov_gui()


        # Nechame chvili zobrazit spravne 3/3,
        # potom Mega prepne na finalni obrazovku.

        root.after(
            1200,
            lambda: posli_display(
                "UNLOCKED"
            )
        )


        print()
        print(
            "============================"
        )

        print(
            "SEKVENCE DOKONČENA"
        )

        print(
            "PŘÍSTUPOVÝ KÓD: 2012"
        )

        print(
            "PŘÍSTUP ODEMČEN"
        )

        print(
            "============================"
        )

        return


    # --------------------------------------------------------
    # NORMALNI DALSI KROK
    # --------------------------------------------------------

    obnov_gui()


# ============================================================
# ZPRACOVANI UID
# ============================================================

def zpracuj_kartu(uid):

    # --------------------------------------------------------
    # BEHEM CHYBOVE OBRAZOVKY NIC NEDĚLÁME
    # --------------------------------------------------------

    if reset_probiha:

        print(
            "KARTA IGNOROVÁNA - PROBÍHÁ RESET"
        )

        return


    # --------------------------------------------------------
    # NORMALIZACE UID
    # --------------------------------------------------------

    uid = (
        uid
        .replace(":", "")
        .replace(" ", "")
        .upper()
        .strip()
    )


    print()
    print(
        "NAČTENA KARTA:",
        uid
    )


    # ========================================================
    # PUZZLE JE HOTOVE
    #
    # Jakakoliv dalsi karta pripravi novou hru.
    # ========================================================

    if odemceno:

        print(
            "DALŠÍ KARTA PO ODEMČENÍ -> NOVÁ HRA"
        )

        rucni_reset()

        return


    # ========================================================
    # OCEKAVANA KARTA
    # ========================================================

    ocekavana = SPRAVNE_PORADI[
        aktualni_krok
    ]


    print(
        "OČEKÁVÁM:",
        ocekavana
    )


    # ========================================================
    # SPRAVNE
    # ========================================================

    if uid == ocekavana:

        spravna_karta()

        return


    # ========================================================
    # SPATNE UID NEBO SPATNE PORADI
    # ========================================================

    spatna_karta()


# ============================================================
# ZPRACOVANI ZPRAVY Z RC522
# ============================================================

def zpracuj_rc522_zpravu(zprava):

    print(
        "RC522 -> PC:",
        repr(zprava)
    )


    # Ocekavany format:
    #
    # CARD:003955D3

    if not zprava.startswith(
        "CARD:"
    ):
        return


    uid = zprava[
        len("CARD:"):
    ]


    # Tkinter musi byt aktualizovan
    # v hlavnim vlakne.

    root.after(
        0,
        lambda karta=uid:
            zpracuj_kartu(karta)
    )


# ============================================================
# ZPRACOVANI ZPRAVY Z DISPLAY MEGA
# ============================================================

def zpracuj_display_zpravu(zprava):

    print(
        "DISPLAY -> PC:",
        repr(zprava)
    )


# ============================================================
# RC522 SERIAL WORKER
# ============================================================

def rc522_worker():

    global rc522_serial


    while True:

        ser = None


        try:

            print(
                "Připojuji RC522 na",
                RC522_PORT
            )


            ser = serial.Serial(
                RC522_PORT,
                RC522_BAUD,
                timeout=0.1
            )


            rc522_serial = ser


            print(
                "RC522 PŘIPOJENO"
            )


            # Arduino UNO se po otevreni
            # COM portu muze restartovat.

            time.sleep(2)


            ser.reset_input_buffer()


            while True:

                raw = ser.readline()


                if not raw:
                    continue


                zprava = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()


                if zprava:

                    zpracuj_rc522_zpravu(
                        zprava
                    )


        except Exception as chyba:

            print(
                "CHYBA RC522:",
                chyba
            )


            rc522_serial = None


            if ser is not None:

                try:

                    ser.close()

                except:

                    pass


            print(
                "Další pokus o RC522 za 2 sekundy..."
            )


            time.sleep(2)


# ============================================================
# DISPLAY SERIAL WORKER
# ============================================================

def display_worker():

    global display_serial


    while True:

        ser = None


        try:

            print(
                "Připojuji DISPLAY na",
                DISPLAY_PORT
            )


            ser = serial.Serial(
                DISPLAY_PORT,
                DISPLAY_BAUD,
                timeout=0.1
            )


            display_serial = ser


            print(
                "DISPLAY PŘIPOJEN"
            )


            # Arduino Mega se po otevreni
            # COM portu muze restartovat.

            time.sleep(2)


            ser.reset_input_buffer()


            # Po restartu Mega obnovime
            # aktualni stav displeju.

            root.after(
                0,
                obnov_display
            )


            while True:

                raw = ser.readline()


                if not raw:
                    continue


                zprava = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()


                if zprava:

                    zpracuj_display_zpravu(
                        zprava
                    )


        except Exception as chyba:

            print(
                "CHYBA DISPLAY:",
                chyba
            )


            display_serial = None


            if ser is not None:

                try:

                    ser.close()

                except:

                    pass


            print(
                "Další pokus o DISPLAY za 2 sekundy..."
            )


            time.sleep(2)


# ============================================================
# OBNOVENI MEGA DISPLAYE
# ============================================================

def obnov_display():

    # --------------------------------------------------------
    # ODEMCENO
    # --------------------------------------------------------

    if odemceno:

        posli_display(
            "UNLOCKED"
        )

        return


    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if aktualni_krok == 0:

        posli_display(
            "RESET"
        )

        return


    # --------------------------------------------------------
    # ROZEHRANA SEKQUENCE
    # --------------------------------------------------------

    viditelny_kod = KOD_STAVY[
        aktualni_krok
    ]


    posli_display(
        f"KEY:{aktualni_krok}:{viditelny_kod}"
    )


# ============================================================
# RUCNI RESET
# ============================================================

def rucni_reset():

    global aktualni_krok
    global odemceno
    global reset_probiha


    aktualni_krok = 0
    odemceno = False
    reset_probiha = False


    obnov_gui()


    posli_rc522(
        "RESET"
    )


    posli_display(
        "RESET"
    )


    print()
    print(
        "RUČNÍ RESET"
    )


# ============================================================
# TESTOVANI Z KLAVESNICE
# ============================================================
#
# 1 = prvni RFID karta
# 2 = druha RFID karta
# 3 = treti RFID karta
#
# X = spatna karta
# R = rucni reset
# ESC = ukonceni programu
#
# Diky tomu lze kompletni logiku otestovat
# i bez RC522.
# ============================================================


# ------------------------------------------------------------
# KARTA 1
# ------------------------------------------------------------

root.bind(
    "1",
    lambda event:
        zpracuj_kartu(
            "003955D3"
        )
)


# ------------------------------------------------------------
# KARTA 2
# ------------------------------------------------------------

root.bind(
    "2",
    lambda event:
        zpracuj_kartu(
            "A05EE128"
        )
)


# ------------------------------------------------------------
# KARTA 3
# ------------------------------------------------------------

root.bind(
    "3",
    lambda event:
        zpracuj_kartu(
            "C067A12B"
        )
)


# ------------------------------------------------------------
# SPATNA KARTA
# ------------------------------------------------------------

root.bind(
    "x",
    lambda event:
        zpracuj_kartu(
            "FFFFFFFF"
        )
)

root.bind(
    "X",
    lambda event:
        zpracuj_kartu(
            "FFFFFFFF"
        )
)


# ------------------------------------------------------------
# RESET
# ------------------------------------------------------------

root.bind(
    "r",
    lambda event:
        rucni_reset()
)

root.bind(
    "R",
    lambda event:
        rucni_reset()
)


# ============================================================
# POCATECNI STAV GUI
# ============================================================

obnov_gui()


# ============================================================
# SPUSTENI SERIAL VLAKEN
# ============================================================

threading.Thread(
    target=rc522_worker,
    daemon=True
).start()


threading.Thread(
    target=display_worker,
    daemon=True
).start()


# ============================================================
# START PROGRAMU
# ============================================================

root.mainloop()