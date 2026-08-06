import tkinter as tk
import serial
import threading
import time

# ==============================
# SETTINGS
# ==============================

PORT = "COM9"       # Change this to your Arduino port
BAUD_RATE = 9600

# Authorized RFID/NFC UIDs
ALLOWED_CARDS = {
    # "00:39:55:D3", # Yellow
    # "A0:5E:E1:28", # Red
    "00:39:55:D3", # Blue
}

# ==============================
# SERIAL
# ==============================

try:
    arduino = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
except serial.SerialException as e:
    print("Could not connect to Arduino:", e)
    arduino = None


# ==============================
# GUI
# ==============================

root = tk.Tk()
root.title("NFC Reader")
root.geometry("600x450")
root.configure(bg="#181818")

title = tk.Label(
    root,
    text="NFC READER",
    font=("Arial", 28, "bold"),
    fg="white",
    bg="#181818"
)
title.pack(pady=(30, 15))


status_label = tk.Label(
    root,
    text="●",
    font=("Arial", 120, "bold"),
    fg="gray",
    bg="#181818"
)
status_label.pack()


message_label = tk.Label(
    root,
    text="SCAN YOUR CARD",
    font=("Arial", 24, "bold"),
    fg="white",
    bg="#181818"
)
message_label.pack(pady=10)


uid_label = tk.Label(
    root,
    text="Waiting for NFC/RFID card...",
    font=("Arial", 14),
    fg="#aaaaaa",
    bg="#181818"
)
uid_label.pack(pady=10)


# ==============================
# GUI FUNCTIONS
# ==============================

def show_granted(uid):
    status_label.config(
        text="✓",
        fg="#00cc66"
    )

    message_label.config(
        text="ACCESS GRANTED :-)",
        fg="#00cc66"
    )

    uid_label.config(
        text=f"Card: {uid}"
    )

    # Return to waiting screen after 2 seconds
    root.after(2000, reset_screen)


def show_denied(uid):
    status_label.config(
        text="✕",
        fg="#ff3333"
    )

    message_label.config(
        text="ACCESS DENIED :-(",
        fg="#ff3333"
    )

    uid_label.config(
        text=f"Card: {uid}"
    )

    root.after(2000, reset_screen)


def reset_screen():
    status_label.config(
        text="●",
        fg="gray"
    )

    message_label.config(
        text="SCAN YOUR CARD",
        fg="white"
    )

    uid_label.config(
        text="Waiting for NFC/RFID card..."
    )


# ==============================
# RFID READER THREAD
# ==============================

def read_rfid():

    if arduino is None:
        root.after(
            0,
            lambda: message_label.config(
                text="ARDUINO NOT CONNECTED",
                fg="red"
            )
        )
        return

    while True:
        try:
            if arduino.in_waiting:

                uid = (
                    arduino.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                    .upper()
                )

                if not uid:
                    continue

                print("Card detected:", uid)

                if uid in ALLOWED_CARDS:
                    root.after(
                        0,
                        lambda card=uid: show_granted(card)
                    )
                else:
                    root.after(
                        0,
                        lambda card=uid: show_denied(card)
                    )

        except serial.SerialException:
            root.after(
                0,
                lambda: message_label.config(
                    text="CONNECTION LOST",
                    fg="red"
                )
            )
            break


# Run RFID reading separately so GUI doesn't freeze
reader_thread = threading.Thread(
    target=read_rfid,
    daemon=True
)

reader_thread.start()

root.mainloop()