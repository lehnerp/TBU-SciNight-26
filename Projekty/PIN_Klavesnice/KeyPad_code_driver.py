"""PIN stanoviště: KeyPin_Driver_Part.ino + Circles_Breathing_Driver.ino.
Dva USB porty, 9600 baud; PIN:* události řídí GUI a NeoPixel STEP/SUCCESS/ERROR.
Požadavky: Windows (winsound), pyserial, Tkinter; viz serial_ports.json a README.md.
"""

from connection_config import serial_endpoint

import tkinter as tk
import serial
import threading
import time
import winsound
import queue
import math
import os


# ============================================================
# CONFIGURATION
# ============================================================

KEYPAD_PORT, KEYPAD_BAUD = serial_endpoint("keypad")

PIXEL_PORT, PIXEL_BAUD = serial_endpoint("neopixel")


# ============================================================
# WINDOWS XP SOUND FILES
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

XP_ERROR_SOUND = os.path.join(
    BASE_DIR,
    "xp_error.wav"
)

XP_LOGIN_SOUND = os.path.join(
    BASE_DIR,
    "vista_login.wav"
)


# ============================================================
# GLOBAL STATE
# ============================================================

entered_length = 0

# IDLE
# ENTERING
# SUCCESS
# ERROR

gui_mode = "IDLE"

keypad_serial = None
pixel_serial = None

pixel_lock = threading.Lock()
event_queue = queue.Queue()

running = True
animation_phase = 0.0

sound_lock = threading.Lock()


# ============================================================
# COLORS
# ============================================================

BG = "#05070A"
PANEL = "#0C1118"

BORDER = "#252D38"

TEXT = "#F4F7FA"
MUTED = "#667080"

WHITE = "#FFFFFF"

CYAN = "#00D9FF"
CYAN_DARK = "#005568"

GREEN = "#00E676"
GREEN_DARK = "#062B19"

RED = "#FF1833"


# ============================================================
# WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Bezpečnostní terminál"
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

root.config(
    cursor="none"
)


# ============================================================
# MAIN CONTAINER
# ============================================================

main = tk.Frame(
    root,
    bg=BG
)

main.pack(
    fill="both",
    expand=True,
    padx=60,
    pady=40
)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    main,
    bg=BG
)

header.pack(
    fill="x"
)


title = tk.Label(
    header,
    text="BEZPEČNOSTNÍ TERMINÁL",
    bg=BG,
    fg=TEXT,
    font=(
        "Segoe UI",
        30,
        "bold"
    )
)

title.pack(
    side="left"
)


system_status = tk.Label(
    header,
    text="●  SYSTÉM PŘIPRAVEN",
    bg=BG,
    fg=TEXT,
    font=(
        "Segoe UI",
        14,
        "bold"
    )
)

system_status.pack(
    side="right"
)


# ============================================================
# MAIN TERMINAL
# ============================================================

terminal = tk.Frame(
    main,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=2
)

terminal.pack(
    fill="both",
    expand=True,
    pady=(35, 25)
)


# ============================================================
# INSTRUCTION
# ============================================================

instruction = tk.Label(
    terminal,
    text="ZADEJTE PŘÍSTUPOVÝ PIN",
    bg=PANEL,
    fg=MUTED,
    font=(
        "Segoe UI",
        18,
        "bold"
    )
)

instruction.pack(
    pady=(35, 5)
)


# ============================================================
# MAIN ICON
# ============================================================

lock_icon = tk.Label(
    terminal,
    text="○",
    bg=PANEL,
    fg="#777F89",
    font=(
        "Segoe UI Symbol",
        110,
        "bold"
    )
)

lock_icon.pack(
    expand=True
)


# ============================================================
# PIN DISPLAY
# ============================================================

pin_display = tk.Label(
    terminal,
    text="○   ○   ○   ○",
    bg=PANEL,
    fg="#4A515B",
    font=(
        "Consolas",
        42,
        "bold"
    )
)

pin_display.pack(
    pady=(0, 15)
)


# ============================================================
# MAIN STATUS
# ============================================================

main_status = tk.Label(
    terminal,
    text="ČEKÁM NA VSTUP",
    bg=PANEL,
    fg=TEXT,
    font=(
        "Segoe UI",
        27,
        "bold"
    )
)

main_status.pack(
    pady=(5, 5)
)


sub_status = tk.Label(
    terminal,
    text="PIN potvrďte klávesou #",
    bg=PANEL,
    fg=MUTED,
    font=(
        "Segoe UI",
        14
    )
)

sub_status.pack(
    pady=(0, 20)
)


# ============================================================
# PROGRESS DOTS
# ============================================================

progress_frame = tk.Frame(
    terminal,
    bg=PANEL
)

progress_frame.pack(
    pady=(10, 35)
)


progress_dots = []


for i in range(4):

    dot = tk.Label(
        progress_frame,
        text="●",
        bg=PANEL,
        fg="#303946",
        font=(
            "Segoe UI",
            22
        )
    )

    dot.pack(
        side="left",
        padx=12
    )

    progress_dots.append(
        dot
    )


# ============================================================
# FOOTER
# ============================================================

footer = tk.Frame(
    main,
    bg=BG
)

footer.pack(
    fill="x"
)


footer_left = tk.Label(
    footer,
    text="*  SMAZAT",
    bg=BG,
    fg=MUTED,
    font=(
        "Segoe UI",
        12,
        "bold"
    )
)

footer_left.pack(
    side="left"
)


footer_center = tk.Label(
    footer,
    text="PIN SECURITY SYSTEM",
    bg=BG,
    fg="#343C46",
    font=(
        "Consolas",
        11
    )
)

footer_center.pack(
    side="left",
    expand=True
)


footer_right = tk.Label(
    footer,
    text="#  POTVRDIT",
    bg=BG,
    fg=MUTED,
    font=(
        "Segoe UI",
        12,
        "bold"
    )
)

footer_right.pack(
    side="right"
)


# ============================================================
# COLOR HELPERS
# ============================================================

def clamp(value, minimum=0, maximum=255):

    return max(
        minimum,
        min(
            maximum,
            int(value)
        )
    )


def rgb(r, g, b):

    return "#{:02X}{:02X}{:02X}".format(
        clamp(r),
        clamp(g),
        clamp(b)
    )


# ============================================================
# SET BACKGROUND
# ============================================================

def set_background(
    outside_color,
    terminal_color
):

    root.configure(
        bg=outside_color
    )

    main.configure(
        bg=outside_color
    )

    header.configure(
        bg=outside_color
    )

    footer.configure(
        bg=outside_color
    )

    title.configure(
        bg=outside_color
    )

    system_status.configure(
        bg=outside_color
    )

    footer_left.configure(
        bg=outside_color
    )

    footer_center.configure(
        bg=outside_color
    )

    footer_right.configure(
        bg=outside_color
    )


    terminal.configure(
        bg=terminal_color
    )

    instruction.configure(
        bg=terminal_color
    )

    lock_icon.configure(
        bg=terminal_color
    )

    pin_display.configure(
        bg=terminal_color
    )

    main_status.configure(
        bg=terminal_color
    )

    sub_status.configure(
        bg=terminal_color
    )

    progress_frame.configure(
        bg=terminal_color
    )


    for dot in progress_dots:

        dot.configure(
            bg=terminal_color
        )


# ============================================================
# UPDATE PIN DISPLAY
# ============================================================

def update_pin_display():

    symbols = []


    for i in range(4):

        if i < entered_length:

            symbols.append(
                "●"
            )

        else:

            symbols.append(
                "○"
            )


    pin_display.configure(
        text="   ".join(
            symbols
        )
    )


    for i in range(4):

        if i < entered_length:

            progress_dots[i].configure(
                fg=CYAN
            )

        else:

            progress_dots[i].configure(
                fg="#303946"
            )


# ============================================================
# STOP CURRENT SOUND
# ============================================================

def stop_sound():

    try:

        winsound.PlaySound(
            None,
            winsound.SND_PURGE
        )

    except RuntimeError:

        pass


# ============================================================
# IDLE
# ============================================================

def show_idle():

    global gui_mode
    global entered_length


    gui_mode = "IDLE"
    entered_length = 0


    stop_sound()


    set_background(
        BG,
        PANEL
    )


    terminal.configure(
        highlightbackground=BORDER,
        highlightthickness=2
    )


    title.configure(
        fg=TEXT
    )


    instruction.configure(
        text="ZADEJTE PŘÍSTUPOVÝ PIN",
        fg=MUTED
    )


    lock_icon.configure(
        text="○",
        fg="#777F89"
    )


    pin_display.configure(
        fg="#4A515B"
    )


    main_status.configure(
        text="ČEKÁM NA VSTUP",
        fg=TEXT
    )


    sub_status.configure(
        text="PIN potvrďte klávesou #",
        fg=MUTED
    )


    system_status.configure(
        text="●  SYSTÉM PŘIPRAVEN",
        fg="#9AA2AC"
    )


    footer_left.configure(
        fg=MUTED
    )

    footer_center.configure(
        fg="#343C46"
    )

    footer_right.configure(
        fg=MUTED
    )


    update_pin_display()


# ============================================================
# ENTERING PIN
# ============================================================

def show_entering():

    global gui_mode


    gui_mode = "ENTERING"


    set_background(
        BG,
        PANEL
    )


    terminal.configure(
        highlightbackground=CYAN_DARK,
        highlightthickness=2
    )


    title.configure(
        fg=TEXT
    )


    instruction.configure(
        text="OVĚŘUJI PŘÍSTUPOVÝ KÓD",
        fg=CYAN
    )


    lock_icon.configure(
        text="◎",
        fg=CYAN
    )


    pin_display.configure(
        fg=CYAN
    )


    main_status.configure(
        text="ZADÁVÁNÍ PINU",
        fg=TEXT
    )


    sub_status.configure(
        text="Po dokončení potvrďte klávesou #",
        fg=MUTED
    )


    system_status.configure(
        text="●  VSTUP AKTIVNÍ",
        fg=CYAN
    )


    footer_left.configure(
        fg=MUTED
    )

    footer_center.configure(
        fg="#343C46"
    )

    footer_right.configure(
        fg=MUTED
    )


    update_pin_display()


# ============================================================
# WINDOWS XP LOGIN SOUND
# ============================================================

def play_success_sound():

    try:

        if os.path.exists(
            XP_LOGIN_SOUND
        ):

            with sound_lock:

                winsound.PlaySound(
                    XP_LOGIN_SOUND,
                    winsound.SND_FILENAME
                )

        else:

            print(
                "Missing sound file:",
                XP_LOGIN_SOUND
            )

            print(
                "Using Windows fallback sound."
            )


            with sound_lock:

                winsound.PlaySound(
                    "SystemAsterisk",
                    winsound.SND_ALIAS
                )


    except RuntimeError as error:

        print(
            "SUCCESS SOUND ERROR:",
            error
        )


# ============================================================
# SUCCESS
# ============================================================

def show_success():

    global gui_mode


    # Prevent playing success sound twice.
    if gui_mode == "SUCCESS":
        return


    gui_mode = "SUCCESS"


    stop_sound()


    set_background(
        "#010805",
        GREEN_DARK
    )


    terminal.configure(
        highlightbackground=GREEN,
        highlightthickness=4
    )


    title.configure(
        fg=TEXT
    )


    instruction.configure(
        text="OVĚŘENÍ ÚSPĚŠNÉ",
        fg=GREEN
    )


    lock_icon.configure(
        text="✓",
        fg=GREEN
    )


    pin_display.configure(
        text="●   ●   ●   ●",
        fg=GREEN
    )


    main_status.configure(
        text="PŘÍSTUP POVOLEN",
        fg=GREEN
    )


    sub_status.configure(
        text="PIN BYL PŘIJAT",
        fg=TEXT
    )


    system_status.configure(
        text="●  PŘÍSTUP POVOLEN",
        fg=GREEN
    )


    footer_left.configure(
        fg=MUTED
    )

    footer_center.configure(
        fg="#315B43"
    )

    footer_right.configure(
        fg=MUTED
    )


    for dot in progress_dots:

        dot.configure(
            fg=GREEN
        )


    # Windows XP login sound once.
    threading.Thread(
        target=play_success_sound,
        daemon=True
    ).start()


# ============================================================
# WINDOWS XP ERROR SOUND
# ============================================================

def play_error_sound():

    # Play exactly three times.

    for repeat in range(3):

        if (
            not running or
            gui_mode != "ERROR"
        ):

            return


        try:

            if os.path.exists(
                XP_ERROR_SOUND
            ):

                with sound_lock:

                    winsound.PlaySound(
                        XP_ERROR_SOUND,
                        winsound.SND_FILENAME
                    )


            else:

                print(
                    "Missing sound file:",
                    XP_ERROR_SOUND
                )

                print(
                    "Using Windows fallback error sound."
                )


                with sound_lock:

                    winsound.PlaySound(
                        "SystemHand",
                        winsound.SND_ALIAS
                    )


        except RuntimeError as error:

            print(
                "ERROR SOUND ERROR:",
                error
            )

            return


        # No pause required after third sound.
        if repeat >= 2:

            break


        # 250 ms pause between sounds,
        # while still checking whether ERROR was reset.

        for _ in range(5):

            if (
                not running or
                gui_mode != "ERROR"
            ):

                return


            time.sleep(
                0.05
            )


# ============================================================
# ERROR
# ============================================================

def show_error():

    global gui_mode


    # Prevent multiple alarm threads.
    if gui_mode == "ERROR":

        return


    gui_mode = "ERROR"


    stop_sound()


    terminal.configure(
        highlightbackground=RED,
        highlightthickness=7
    )


    instruction.configure(
        text="⚠  BEZPEČNOSTNÍ UPOZORNĚNÍ  ⚠",
        fg=WHITE
    )


    lock_icon.configure(
        text="✕",
        fg=WHITE
    )


    pin_display.configure(
        text="✕   ✕   ✕   ✕",
        fg=WHITE
    )


    main_status.configure(
        text="PŘÍSTUP ZAMÍTNUT",
        fg=WHITE
    )


    sub_status.configure(
        text="NESPRÁVNÝ PŘÍSTUPOVÝ KÓD",
        fg=WHITE
    )


    system_status.configure(
        text="●  CHYBA AUTORIZACE",
        fg=WHITE
    )


    # Windows XP error sound three times.
    threading.Thread(
        target=play_error_sound,
        daemon=True
    ).start()


# ============================================================
# GUI ANIMATION
# ============================================================

def animate_gui():

    global animation_phase


    if not running:

        return


    animation_phase += 0.055


    # ========================================================
    # IDLE
    #
    # Calm white breathing.
    # ========================================================

    if gui_mode == "IDLE":

        wave = (
            math.sin(
                animation_phase
            ) + 1.0
        ) / 2.0


        brightness = (
            65 +
            wave * 100
        )


        idle_color = rgb(
            brightness,
            brightness,
            brightness
        )


        lock_icon.configure(
            fg=idle_color
        )


        status_brightness = (
            80 +
            wave * 70
        )


        system_status.configure(
            fg=rgb(
                status_brightness,
                status_brightness,
                status_brightness
            )
        )


    # ========================================================
    # ENTERING
    #
    # Calm cyan pulse.
    # ========================================================

    elif gui_mode == "ENTERING":

        wave = (
            math.sin(
                animation_phase * 1.6
            ) + 1.0
        ) / 2.0


        blue = (
            90 +
            wave * 150
        )


        green = (
            80 +
            wave * 130
        )


        lock_icon.configure(
            fg=rgb(
                0,
                green,
                blue
            )
        )


    # ========================================================
    # SUCCESS
    #
    # Green breathing.
    # ========================================================

    elif gui_mode == "SUCCESS":

        wave = (
            math.sin(
                animation_phase * 1.15
            ) + 1.0
        ) / 2.0


        green_value = (
            130 +
            wave * 100
        )


        success_color = rgb(
            0,
            green_value,
            90
        )


        background_green = (
            5 +
            wave * 10
        )


        panel_green = (
            22 +
            wave * 20
        )


        outside = rgb(
            0,
            background_green,
            4
        )


        panel = rgb(
            3,
            panel_green,
            14
        )


        set_background(
            outside,
            panel
        )


        terminal.configure(
            highlightbackground=GREEN,
            highlightthickness=4
        )


        title.configure(
            fg=TEXT
        )


        lock_icon.configure(
            text="✓",
            fg=success_color
        )


        instruction.configure(
            fg=GREEN
        )


        main_status.configure(
            fg=GREEN
        )


        system_status.configure(
            fg=GREEN
        )


        pin_display.configure(
            fg=GREEN
        )


        sub_status.configure(
            fg=TEXT
        )


        for dot in progress_dots:

            dot.configure(
                fg=GREEN
            )


    # ========================================================
    # ERROR
    #
    # Aggressive RED / BLACK flashing.
    # ========================================================

    elif gui_mode == "ERROR":

        flash_on = (
            int(
                time.monotonic() * 6
            ) % 2 == 0
        )


        if flash_on:

            # ==================================================
            # BRIGHT RED FRAME
            # ==================================================

            set_background(
                "#FF001E",
                "#C80018"
            )


            terminal.configure(
                highlightbackground=WHITE,
                highlightthickness=7
            )


            title.configure(
                fg=WHITE
            )


            system_status.configure(
                text="●  CHYBA AUTORIZACE",
                fg=WHITE
            )


            instruction.configure(
                text="⚠  BEZPEČNOSTNÍ UPOZORNĚNÍ  ⚠",
                fg=WHITE
            )


            lock_icon.configure(
                text="✕",
                fg=WHITE
            )


            pin_display.configure(
                text="✕   ✕   ✕   ✕",
                fg=WHITE
            )


            main_status.configure(
                text="PŘÍSTUP ZAMÍTNUT",
                fg=WHITE
            )


            sub_status.configure(
                text="NESPRÁVNÝ PŘÍSTUPOVÝ KÓD",
                fg=WHITE
            )


            footer_left.configure(
                fg=WHITE
            )

            footer_center.configure(
                fg=WHITE
            )

            footer_right.configure(
                fg=WHITE
            )


            for dot in progress_dots:

                dot.configure(
                    fg=WHITE
                )


        else:

            # ==================================================
            # NEAR BLACK FRAME
            # ==================================================

            set_background(
                "#050000",
                "#170002"
            )


            terminal.configure(
                highlightbackground=RED,
                highlightthickness=7
            )


            title.configure(
                fg=RED
            )


            system_status.configure(
                text="●  CHYBA AUTORIZACE",
                fg=RED
            )


            instruction.configure(
                text="⚠  BEZPEČNOSTNÍ UPOZORNĚNÍ  ⚠",
                fg=RED
            )


            lock_icon.configure(
                text="✕",
                fg=RED
            )


            pin_display.configure(
                text="✕   ✕   ✕   ✕",
                fg=RED
            )


            main_status.configure(
                text="PŘÍSTUP ZAMÍTNUT",
                fg=RED
            )


            sub_status.configure(
                text="NESPRÁVNÝ PŘÍSTUPOVÝ KÓD",
                fg="#FF7585"
            )


            footer_left.configure(
                fg="#70000D"
            )

            footer_center.configure(
                fg="#70000D"
            )

            footer_right.configure(
                fg="#70000D"
            )


            for dot in progress_dots:

                dot.configure(
                    fg=RED
                )


    root.after(
        40,
        animate_gui
    )


# ============================================================
# SEND COMMAND TO NEOPIXEL ARDUINO
# ============================================================

def send_pixel(command):

    global pixel_serial


    ser = pixel_serial


    if ser is None:

        print(
            "PIXEL OFFLINE:",
            command
        )

        return


    try:

        with pixel_lock:

            ser.write(
                (
                    command + "\n"
                ).encode(
                    "utf-8"
                )
            )


            ser.flush()


        print(
            "PC -> PIXEL:",
            command
        )


    except Exception as error:

        print(
            "PIXEL WRITE ERROR:",
            error
        )


# ============================================================
# PIN KEY PRESSED
# ============================================================

def process_key(length):

    global entered_length


    if gui_mode in (
        "SUCCESS",
        "ERROR"
    ):

        return


    entered_length = max(
        0,
        min(
            length,
            4
        )
    )


    show_entering()


    # 1 digit -> ring 1
    # 2 digits -> ring 2
    # 3/4 digits -> ring 3

    if entered_length <= 1:

        send_pixel(
            "STEP:1"
        )


    elif entered_length == 2:

        send_pixel(
            "STEP:2"
        )


    else:

        send_pixel(
            "STEP:3"
        )


# ============================================================
# BACKSPACE
# ============================================================

def process_backspace(length):

    global entered_length


    if gui_mode in (
        "SUCCESS",
        "ERROR"
    ):

        return


    entered_length = max(
        0,
        min(
            length,
            4
        )
    )


    if entered_length == 0:

        send_pixel(
            "RESET"
        )


        show_idle()

        return


    show_entering()


    if entered_length == 1:

        send_pixel(
            "STEP:1"
        )


    elif entered_length == 2:

        send_pixel(
            "STEP:2"
        )


    else:

        send_pixel(
            "STEP:3"
        )


# ============================================================
# RESET SYSTEM
# ============================================================

def reset_system():

    global entered_length


    entered_length = 0


    stop_sound()


    send_pixel(
        "RESET"
    )


    show_idle()


# ============================================================
# HANDLE KEYPAD MESSAGE
# ============================================================

def handle_keypad_message(message):

    print(
        "KEYPAD -> PC:",
        repr(message)
    )


    # ========================================================
    # DIGIT
    #
    # Example:
    # PIN:KEY:2:1
    # ========================================================

    if message.startswith(
        "PIN:KEY:"
    ):

        parts = message.split(
            ":"
        )


        if len(parts) >= 4:

            try:

                length = int(
                    parts[3]
                )


                process_key(
                    length
                )


            except ValueError:

                pass


        return


    # ========================================================
    # BACKSPACE
    # ========================================================

    if message.startswith(
        "PIN:BACKSPACE:"
    ):

        parts = message.split(
            ":"
        )


        if len(parts) >= 3:

            try:

                length = int(
                    parts[2]
                )


                process_backspace(
                    length
                )


            except ValueError:

                pass


        return


    # ========================================================
    # CORRECT PIN
    # ========================================================

    if message == "PIN:OK":

        send_pixel(
            "SUCCESS"
        )


        show_success()

        return


    # ========================================================
    # WRONG PIN
    # ========================================================

    if message == "PIN:WRONG":

        send_pixel(
            "ERROR"
        )


        show_error()

        return


    # ========================================================
    # RESET FROM KEYPAD ARDUINO
    # ========================================================

    if message == "PIN:RESET":

        reset_system()

        return


# ============================================================
# EVENT QUEUE
#
# Serial threads put events here.
# Tkinter is only modified by the main thread.
# ============================================================

def process_event_queue():

    if not running:

        return


    try:

        while True:

            event = event_queue.get_nowait()

            event_type = event[0]


            if event_type == "KEYPAD":

                handle_keypad_message(
                    event[1]
                )


            elif event_type == "PIXEL_CONNECTED":

                restore_pixel_state()


    except queue.Empty:

        pass


    root.after(
        30,
        process_event_queue
    )


# ============================================================
# RESTORE NEOPIXEL STATE AFTER RECONNECT
# ============================================================

def restore_pixel_state():

    if gui_mode == "IDLE":

        send_pixel(
            "RESET"
        )


    elif gui_mode == "SUCCESS":

        send_pixel(
            "SUCCESS"
        )


    elif gui_mode == "ERROR":

        send_pixel(
            "ERROR"
        )


    elif gui_mode == "ENTERING":

        if entered_length <= 1:

            send_pixel(
                "STEP:1"
            )


        elif entered_length == 2:

            send_pixel(
                "STEP:2"
            )


        else:

            send_pixel(
                "STEP:3"
            )


# ============================================================
# KEYPAD SERIAL WORKER
# ============================================================

def keypad_worker():

    global keypad_serial


    while running:

        ser = None


        try:

            print(
                "Připojuji KEYPAD:",
                KEYPAD_PORT
            )


            ser = serial.Serial(
                KEYPAD_PORT,
                KEYPAD_BAUD,
                timeout=0.1
            )


            keypad_serial = ser


            print(
                "KEYPAD PŘIPOJEN"
            )


            # Arduino can reset when COM opens.
            time.sleep(
                2
            )


            ser.reset_input_buffer()


            while running:

                raw = ser.readline()


                if not raw:

                    continue


                message = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()


                if message:

                    event_queue.put(
                        (
                            "KEYPAD",
                            message
                        )
                    )


        except Exception as error:

            print(
                "KEYPAD ERROR:",
                error
            )


            keypad_serial = None


            if ser is not None:

                try:

                    ser.close()

                except Exception:

                    pass


            if running:

                time.sleep(
                    2
                )


# ============================================================
# NEOPIXEL SERIAL WORKER
# ============================================================

def pixel_worker():

    global pixel_serial


    while running:

        ser = None


        try:

            print(
                "Připojuji NEOPIXEL:",
                PIXEL_PORT
            )


            ser = serial.Serial(
                PIXEL_PORT,
                PIXEL_BAUD,
                timeout=0.1
            )


            pixel_serial = ser


            print(
                "NEOPIXEL PŘIPOJEN"
            )


            # Arduino can reset when COM opens.
            time.sleep(
                2
            )


            ser.reset_input_buffer()


            event_queue.put(
                (
                    "PIXEL_CONNECTED",
                    None
                )
            )


            while running:

                raw = ser.readline()


                if not raw:

                    continue


                message = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()


                if message:

                    print(
                        "PIXEL -> PC:",
                        message
                    )


        except Exception as error:

            print(
                "NEOPIXEL ERROR:",
                error
            )


            pixel_serial = None


            if ser is not None:

                try:

                    ser.close()

                except Exception:

                    pass


            if running:

                time.sleep(
                    2
                )


# ============================================================
# CLEAN EXIT
# ============================================================

def close_program(event=None):

    global running
    global gui_mode


    running = False
    gui_mode = "IDLE"


    stop_sound()


    try:

        if keypad_serial is not None:

            keypad_serial.close()

    except Exception:

        pass


    try:

        if pixel_serial is not None:

            pixel_serial.close()

    except Exception:

        pass


    root.destroy()


root.bind(
    "<Escape>",
    close_program
)


root.protocol(
    "WM_DELETE_WINDOW",
    close_program
)


# ============================================================
# PC TEST KEYS
#
# 1 = first PIN position
# 2 = second
# 3 = third
# 4 = fourth
#
# O = correct
# X = wrong
# R = reset
# ESC = exit
# ============================================================

root.bind(
    "1",
    lambda event:
        process_key(1)
)


root.bind(
    "2",
    lambda event:
        process_key(2)
)


root.bind(
    "3",
    lambda event:
        process_key(3)
)


root.bind(
    "4",
    lambda event:
        process_key(4)
)


def test_success(event=None):

    send_pixel(
        "SUCCESS"
    )

    show_success()


def test_error(event=None):

    send_pixel(
        "ERROR"
    )

    show_error()


root.bind(
    "o",
    test_success
)

root.bind(
    "O",
    test_success
)


root.bind(
    "x",
    test_error
)

root.bind(
    "X",
    test_error
)


root.bind(
    "r",
    lambda event:
        reset_system()
)

root.bind(
    "R",
    lambda event:
        reset_system()
)


# ============================================================
# START
# ============================================================

show_idle()


threading.Thread(
    target=keypad_worker,
    daemon=True
).start()


threading.Thread(
    target=pixel_worker,
    daemon=True
).start()


process_event_queue()

animate_gui()

root.mainloop()