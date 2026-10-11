"""Ovládání Dino hry: Dino_Driver_part.ino přes USB (9600 baud).
Knihovny: pyserial, Tkinter; příkazy START/JUMP/RESET, odpovědi GAME:*.
Port v serial_ports.json; zapojení v README.md.
"""

from connection_config import serial_endpoint

import tkinter as tk
import serial
import threading
import queue
import time


# ============================================================
# CONFIGURATION
# ============================================================

GAME_PORT, GAME_BAUD = serial_endpoint("dino")

WIN_SCORE = 5

# Secret shown after successful completion
SECRET_MESSAGE = "2012"


# ============================================================
# GLOBAL STATE
# ============================================================

game_state = "CONNECTING"
score = 0

ser = None
running = True

message_queue = queue.Queue()
serial_lock = threading.Lock()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title("DINO RUN")
root.configure(bg="#050708")

root.attributes("-fullscreen", True)

# Hide mouse cursor
root.config(cursor="none")


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,
    text="DINO RUN",
    font=("Consolas", 54, "bold"),
    fg="#00D9FF",
    bg="#050708"
)

title_label.pack(
    pady=(70, 15)
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,
    text="PŘIPOJUJI ARDUINO...",
    font=("Consolas", 28, "bold"),
    fg="#888888",
    bg="#050708"
)

status_label.pack(
    pady=20
)


# ============================================================
# SCORE
# ============================================================

score_label = tk.Label(
    root,
    text=f"SKÓRE  0 / {WIN_SCORE}",
    font=("Consolas", 44, "bold"),
    fg="#FFFFFF",
    bg="#050708"
)

score_label.pack(
    pady=25
)


# ============================================================
# SECRET TITLE
# ============================================================

secret_title_label = tk.Label(
    root,
    text="",
    font=("Consolas", 28, "bold"),
    fg="#00FF66",
    bg="#050708"
)

secret_title_label.pack(
    pady=(25, 5)
)


# ============================================================
# SECRET MESSAGE
# ============================================================

secret_label = tk.Label(
    root,
    text="",
    font=("Consolas", 82, "bold"),
    fg="#00FF66",
    bg="#050708"
)

secret_label.pack(
    pady=10
)


# ============================================================
# INFORMATION
# ============================================================

info_label = tk.Label(
    root,
    text="PŘESKOČ 5 PŘEKÁŽEK",
    font=("Consolas", 18),
    fg="#555555",
    bg="#050708"
)

info_label.pack(
    pady=20
)


# ============================================================
# CONTROLS
# ============================================================

controls_label = tk.Label(
    root,
    text="SPACE / ↑  SKOK     R  RESTART     ESC  KONEC",
    font=("Consolas", 18),
    fg="#777777",
    bg="#050708"
)

controls_label.pack(
    side="bottom",
    pady=(10, 35)
)


# ============================================================
# CONNECTION STATUS
# ============================================================

connection_label = tk.Label(
    root,
    text="ARDUINO: PŘIPOJUJI...",
    font=("Consolas", 14),
    fg="#777777",
    bg="#050708"
)

connection_label.pack(
    side="bottom",
    pady=10
)


# ============================================================
# SEND COMMAND TO ARDUINO
# ============================================================

def send_command(command):
    global ser

    with serial_lock:

        if ser is None:
            return

        try:

            if ser.is_open:

                data = (command + "\n").encode("utf-8")

                ser.write(data)

                print("PC -> ARDUINO:", command)

        except Exception as error:

            print("Send error:", error)


# ============================================================
# CLEAR SECRET
# ============================================================

def clear_secret():

    secret_title_label.config(
        text=""
    )

    secret_label.config(
        text=""
    )


# ============================================================
# WAITING SCREEN
# ============================================================

def show_waiting():

    global game_state
    global score

    game_state = "WAITING"
    score = 0

    title_label.config(
        text="DINO RUN",
        fg="#00D9FF"
    )

    status_label.config(
        text="STISKNĚTE SPACE",
        fg="#00D9FF"
    )

    score_label.config(
        text=f"SKÓRE  0 / {WIN_SCORE}",
        fg="#FFFFFF"
    )

    info_label.config(
        text="PŘESKOČ 10 PŘEKÁŽEK",
        fg="#555555"
    )

    clear_secret()


# ============================================================
# PLAYING SCREEN
# ============================================================

def show_playing():

    global game_state

    game_state = "PLAYING"

    clear_secret()

    title_label.config(
        text="DINO RUN",
        fg="#00D9FF"
    )

    status_label.config(
        text="BĚŽ!",
        fg="#00D9FF"
    )

    score_label.config(
        fg="#FFFFFF"
    )

    info_label.config(
        text="SPACE / ↑ = SKOK",
        fg="#555555"
    )


# ============================================================
# FAILURE SCREEN
# ============================================================

def show_failure(final_score):

    global game_state

    game_state = "GAME_OVER"

    clear_secret()

    title_label.config(
        text="NEÚSPĚCH",
        fg="#FF3030"
    )

    status_label.config(
        text="NARAZIL JSI!",
        fg="#FF3030"
    )

    score_label.config(
        text=f"SKÓRE  {final_score} / {WIN_SCORE}",
        fg="#FF3030"
    )

    info_label.config(
        text="DINO SE ZA 3 SEKUNDY VRÁTÍ",
        fg="#777777"
    )


# ============================================================
# SUCCESS SCREEN
# ============================================================

def show_success():

    global game_state
    global score

    game_state = "WIN"
    score = WIN_SCORE

    title_label.config(
        text="ÚKOL SPLNĚN",
        fg="#00FF66"
    )

    status_label.config(
        text="",
        fg="#00FF66"
    )

    score_label.config(
        text=f"SKÓRE  {WIN_SCORE} / {WIN_SCORE}",
        fg="#00FF66"
    )

    secret_title_label.config(
        text="TAJNÁ ZPRÁVA"
    )

    secret_label.config(
        text=SECRET_MESSAGE
    )

    info_label.config(
        text="",
        fg="#00FF66"
    )


# ============================================================
# PROCESS MESSAGE FROM ARDUINO
# ============================================================

def process_message(message):

    global game_state
    global score

    message = message.strip()

    print("ARDUINO -> PC:", message)


    # --------------------------------------------------------
    # READY
    # --------------------------------------------------------

    if message == "GAME:READY":

        connection_label.config(
            text="ARDUINO: PŘIPOJENO",
            fg="#00CC66"
        )

        # IMPORTANT:
        #
        # After winning, Arduino returns to idle after 3 seconds
        # and sends GAME:READY.
        #
        # We intentionally keep the secret visible.

        if game_state == "WIN":
            return

        show_waiting()

        return


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if message == "GAME:RESET":

        show_waiting()

        return


    # --------------------------------------------------------
    # GAME START
    # --------------------------------------------------------

    if message == "GAME:START":

        score = 0

        show_playing()

        score_label.config(
            text=f"SKÓRE  0 / {WIN_SCORE}"
        )

        return


    # --------------------------------------------------------
    # JUMP
    # --------------------------------------------------------

    if message == "GAME:JUMP":

        return


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    if message.startswith("GAME:SCORE:"):

        try:

            score = int(
                message.split(":")[2]
            )

        except (ValueError, IndexError):

            return

        score_label.config(
            text=f"SKÓRE  {score} / {WIN_SCORE}",
            fg="#FFFFFF"
        )

        return


    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    if message.startswith("GAME:OVER:"):

        try:

            final_score = int(
                message.split(":")[2]
            )

        except (ValueError, IndexError):

            final_score = score

        show_failure(final_score)

        return


    # --------------------------------------------------------
    # WIN
    # --------------------------------------------------------

    if message == "GAME:WIN":

        show_success()

        return


# ============================================================
# SERIAL CONNECTION THREAD
# ============================================================

def serial_worker():

    global ser
    global running

    while running:

        new_serial = None

        try:

            message_queue.put(
                "__CONNECTING__"
            )

            print(
                f"Connecting to {GAME_PORT} at {GAME_BAUD} baud..."
            )


            # ------------------------------------------------
            # OPEN SERIAL PORT
            # ------------------------------------------------

            new_serial = serial.Serial(
                GAME_PORT,
                GAME_BAUD,
                timeout=0.1
            )


            # Arduino can reset when serial connection opens.
            # Give it time to boot.

            time.sleep(2.0)


            new_serial.reset_input_buffer()


            with serial_lock:
                ser = new_serial


            message_queue.put(
                "__CONNECTED__"
            )


            print("Arduino connected.")


            # ------------------------------------------------
            # RESET GAME
            # ------------------------------------------------

            send_command(
                "RESET"
            )


            # ------------------------------------------------
            # SERIAL READ LOOP
            # ------------------------------------------------

            while running:

                try:

                    raw_line = new_serial.readline()

                    if not raw_line:
                        continue


                    line = raw_line.decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()


                    if line:

                        message_queue.put(
                            line
                        )


                except Exception as error:

                    print(
                        "Serial read error:",
                        error
                    )

                    break


        except Exception as error:

            print(
                "Serial connection error:",
                error
            )


        # ----------------------------------------------------
        # CONNECTION LOST / CLOSED
        # ----------------------------------------------------

        with serial_lock:

            ser = None


        if new_serial is not None:

            try:
                new_serial.close()

            except Exception:
                pass


        if running:

            message_queue.put(
                "__DISCONNECTED__"
            )

            print(
                "Arduino disconnected. Retrying..."
            )

            time.sleep(2.0)


# ============================================================
# PROCESS SERIAL QUEUE
#
# Serial thread puts messages into a queue.
# Tkinter reads them here on the main thread.
# ============================================================

def process_queue():

    if not running:
        return

    try:

        while True:

            message = (
                message_queue.get_nowait()
            )


            # ------------------------------------------------
            # CONNECTING
            # ------------------------------------------------

            if message == "__CONNECTING__":

                connection_label.config(
                    text="ARDUINO: PŘIPOJUJI...",
                    fg="#888888"
                )


            # ------------------------------------------------
            # CONNECTED
            # ------------------------------------------------

            elif message == "__CONNECTED__":

                connection_label.config(
                    text="ARDUINO: PŘIPOJENO",
                    fg="#00CC66"
                )


            # ------------------------------------------------
            # DISCONNECTED
            # ------------------------------------------------

            elif message == "__DISCONNECTED__":

                connection_label.config(
                    text="ARDUINO: ODPOJENO",
                    fg="#FF3030"
                )


            # ------------------------------------------------
            # ARDUINO MESSAGE
            # ------------------------------------------------

            else:

                process_message(
                    message
                )


    except queue.Empty:

        pass


    root.after(
        30,
        process_queue
    )


# ============================================================
# JUMP KEY
# ============================================================

def jump_key(event=None):

    # First SPACE while waiting:
    #
    # Arduino receives JUMP.
    # Arduino starts the game and immediately jumps.

    if game_state == "WAITING":

        send_command(
            "JUMP"
        )

        return


    # Normal jump during game.

    if game_state == "PLAYING":

        send_command(
            "JUMP"
        )

        return


    # Do nothing during GAME_OVER or WIN.
    # This preserves the full 3-second result animation.


# ============================================================
# RESTART KEY
# ============================================================

def restart_key(event=None):

    global score

    # Do not interrupt success/failure animation.

    if game_state in (
        "GAME_OVER",
        "WIN"
    ):
        return


    score = 0

    clear_secret()


    score_label.config(
        text=f"SKÓRE  0 / {WIN_SCORE}",
        fg="#FFFFFF"
    )


    send_command(
        "RESTART"
    )


# ============================================================
# EXIT PROGRAM
# ============================================================

def exit_program(event=None):

    global running
    global ser

    running = False


    try:

        with serial_lock:

            if ser is not None:

                ser.close()

                ser = None

    except Exception:
        pass


    root.destroy()


# ============================================================
# KEY BINDINGS
# ============================================================

root.bind(
    "<space>",
    jump_key
)

root.bind(
    "<Up>",
    jump_key
)

root.bind(
    "<r>",
    restart_key
)

root.bind(
    "<R>",
    restart_key
)

root.bind(
    "<Escape>",
    exit_program
)


# Make sure keyboard input goes to this window.

root.focus_force()


# ============================================================
# START SERIAL THREAD
# ============================================================

serial_thread = threading.Thread(
    target=serial_worker,
    daemon=True
)

serial_thread.start()


# ============================================================
# START SERIAL MESSAGE PROCESSOR
# ============================================================

process_queue()


# ============================================================
# START GUI
# ============================================================

root.mainloop()