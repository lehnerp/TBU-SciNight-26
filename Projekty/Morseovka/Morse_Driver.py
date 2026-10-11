"""Zobrazení Morseovky: Morse_Part_Driver.ino přes USB (115200 baud).
Přijímá CLEAR, MORSE:, LETTER:, RESULT:; knihovny pyserial a Tkinter.
Port v serial_ports.json (prázdný = automatické hledání); viz README.md.
"""

from connection_config import serial_endpoint

import tkinter as tk
import serial
import serial.tools.list_ports
import threading
import queue
import time


# ============================================================
# NASTAVENÍ
# ============================================================

MORSE_PORT, BAUD = serial_endpoint("morse")

fronta = queue.Queue()

ser = None
bezi = True


# ============================================================
# HLAVNÍ OKNO
# ============================================================

okno = tk.Tk()

okno.title("Morseovka světlem")

okno.configure(bg="black")


# FULLSCREEN
okno.attributes("-fullscreen", True)


# VŽDY NAHOŘE
okno.attributes("-topmost", True)


# Schovat kurzor
okno.config(cursor="none")


# ============================================================
# HORNÍ STAV
# ============================================================

stav = tk.Label(
    okno,
    text="HLEDÁM ARDUINO...",
    font=("Arial", 20, "bold"),
    fg="gray",
    bg="black"
)

stav.pack(pady=(25, 0))


# ============================================================
# HLAVNÍ TEXT
# ============================================================

hlavni_text = tk.Label(
    okno,
    text="",
    font=("Arial", 180, "bold"),
    fg="white",
    bg="black"
)

hlavni_text.pack(
    expand=True,
    fill="both"
)


# ============================================================
# MORSEOVKA DOLE
# ============================================================

morse_text = tk.Label(
    okno,
    text="",
    font=("Arial", 65, "bold"),
    fg="white",
    bg="black"
)

morse_text.pack(
    pady=(0, 70)
)


# ============================================================
# NAJÍT ARDUINO
# ============================================================

def najdi_arduino():

    if MORSE_PORT:
        return MORSE_PORT

    porty = list(
        serial.tools.list_ports.comports()
    )

    # Nejprve hledáme něco,
    # co vypadá jako Arduino.

    for port in porty:

        popis = (
            port.description or ""
        ).lower()

        vyrobce = (
            port.manufacturer or ""
        ).lower()

        if (
            "arduino" in popis
            or "arduino" in vyrobce
            or "ch340" in popis
            or "usb serial" in popis
        ):
            return port.device


    # Pokud máme jen jeden COM port,
    # použijeme ho.

    if len(porty) == 1:
        return porty[0].device


    return None


# ============================================================
# SERIAL VLÁKNO
# ============================================================

def serial_vlakno():

    global ser
    global bezi

    while bezi:

        # ----------------------------------------------------
        # NENÍ PŘIPOJENO
        # ----------------------------------------------------

        if ser is None:

            port = najdi_arduino()

            if port is None:

                fronta.put(
                    ("STATUS", "HLEDÁM ARDUINO...")
                )

                time.sleep(1)

                continue


            try:

                fronta.put(
                    (
                        "STATUS",
                        "PŘIPOJUJI " + port
                    )
                )


                ser = serial.Serial(
                    port,
                    BAUD,
                    timeout=0.2
                )


                # Mega se může po otevření
                # sériového portu restartovat.

                time.sleep(2)


                fronta.put(
                    (
                        "STATUS",
                        "ARDUINO PŘIPOJENO • " + port
                    )
                )


            except Exception:

                ser = None

                time.sleep(1)

                continue


        # ----------------------------------------------------
        # ČTENÍ
        # ----------------------------------------------------

        try:

            radek = ser.readline()

            if not radek:
                continue


            zprava = radek.decode(
                "utf-8",
                errors="ignore"
            ).strip()


            if zprava:

                fronta.put(
                    ("DATA", zprava)
                )


        except Exception:

            fronta.put(
                (
                    "STATUS",
                    "ARDUINO ODPOJENO"
                )
            )

            try:
                ser.close()
            except Exception:
                pass

            ser = None

            time.sleep(1)


# ============================================================
# SPUSTIT SERIAL NA POZADÍ
# ============================================================

threading.Thread(
    target=serial_vlakno,
    daemon=True
).start()


# ============================================================
# VYČISTIT OBRAZOVKU
# ============================================================

def vycistit():

    hlavni_text.config(
        text=""
    )

    morse_text.config(
        text=""
    )


# ============================================================
# ZPRACOVÁNÍ ZPRÁV
# ============================================================

def aktualizuj():

    while not fronta.empty():

        typ, zprava = fronta.get()


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if typ == "STATUS":

            stav.config(
                text=zprava
            )

            continue


        # ----------------------------------------------------
        # CLEAR
        # ----------------------------------------------------

        if zprava == "CLEAR":

            vycistit()


        # ----------------------------------------------------
        # MORSE
        # ----------------------------------------------------

        elif zprava.startswith("MORSE:"):

            morse = zprava[6:]


            hlavni_text.config(
                text=morse,
                font=(
                    "Arial",
                    190,
                    "bold"
                )
            )


            morse_text.config(
                text=""
            )


        # ----------------------------------------------------
        # LETTER
        # ----------------------------------------------------

        elif zprava.startswith("LETTER:"):

            pismeno = zprava[7:]


            hlavni_text.config(
                text=pismeno,
                font=(
                    "Arial",
                    220,
                    "bold"
                )
            )


            morse_text.config(
                text=""
            )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        elif zprava.startswith("RESULT:"):

            data = zprava[7:]


            try:

                text, morse = data.split(
                    "|",
                    1
                )


                hlavni_text.config(
                    text=text,
                    font=(
                        "Arial",
                        190,
                        "bold"
                    )
                )


                morse_text.config(
                    text=morse,
                    font=(
                        "Arial",
                        65,
                        "bold"
                    )
                )


            except ValueError:

                pass


    okno.after(
        20,
        aktualizuj
    )


# ============================================================
# KLÁVESY
# ============================================================

def fullscreen_off(event=None):

    okno.attributes(
        "-fullscreen",
        False
    )

    okno.config(
        cursor=""
    )


def fullscreen_on(event=None):

    okno.attributes(
        "-fullscreen",
        True
    )

    okno.attributes(
        "-topmost",
        True
    )

    okno.config(
        cursor="none"
    )


def ukoncit(event=None):

    global bezi

    bezi = False


    try:

        if ser is not None:
            ser.close()

    except Exception:
        pass


    okno.destroy()


# ESC = opustit fullscreen
okno.bind(
    "<Escape>",
    fullscreen_off
)


# F11 = fullscreen
okno.bind(
    "<F11>",
    fullscreen_on
)


# Q = ukončit program
okno.bind(
    "<q>",
    ukoncit
)

okno.bind(
    "<Q>",
    ukoncit
)


# ============================================================
# ZAJISTIT, ŽE JE OKNO NAHOŘE
# ============================================================

def drz_nahore():

    try:

        okno.attributes(
            "-topmost",
            True
        )

    except Exception:
        pass


    okno.after(
        2000,
        drz_nahore
    )


# ============================================================
# START
# ============================================================

aktualizuj()

drz_nahore()

okno.mainloop()