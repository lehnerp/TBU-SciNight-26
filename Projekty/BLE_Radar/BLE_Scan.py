"""BLE radar: Detector_Driver_ESP32C3.ino přes USB (460800 baud), AirWave vysílač přes BLE.
Knihovny: pygame, pyserial, bleak; port v serial_ports.json. Viz README.md.
"""

from connection_config import serial_endpoint

import pygame
import serial
import math
import time
import sys
import asyncio
import threading
from collections import deque
from bleak import BleakScanner

# ============================================================
# AIRWAVE // DUAL BLE RADAR
#
# ZDROJE:
#   1) ESP32-C3 přes USB
#   2) Bluetooth notebooku přes Bleak
#
# ============================================================

SERIAL_PORT, BAUD_RATE = serial_endpoint("ble_detector")

DEVICE_TIMEOUT = 5.0

NORMAL_SMOOTHING = 0.72
AIRWAVE_SMOOTHING = 1.0

RSSI_NEAR = -25
RSSI_FAR = -105

GRAPH_SECONDS = 5.0

SWEEP_DEGREES_PER_SECOND = 25.0
PULSE_SPEED = 2.0

MAX_LIST_DEVICES = 18

# ============================================================
# SDÍLENÁ DATA
# ============================================================

devices = {}

devices_lock = threading.Lock()

airwave_history = deque(maxlen=3000)

total_esp_packets = 0
total_ntb_packets = 0

esp_pps_counter = 0
ntb_pps_counter = 0

esp_pps = 0
ntb_pps = 0

notebook_scanner_ok = False
notebook_scanner_error = ""

start_time = time.time()

# ============================================================
# IDENTITA ZAŘÍZENÍ
# ============================================================

def normalize_address(address):
    if not address:
        return "NEZNÁMÉ"

    return str(address).upper()


def is_airwave_name(name):
    if not name:
        return False

    return name.lower() == "airwave"


# ============================================================
# PŘIDÁNÍ / AKTUALIZACE KONTAKTU
# ============================================================

def update_device(
    address,
    rssi,
    name,
    source,
    manufacturer=None,
    service_uuids=None,
    tx_power=None
):
    global total_esp_packets
    global total_ntb_packets
    global esp_pps_counter
    global ntb_pps_counter

    now = time.time()

    address = normalize_address(address)

    if not name:
        name = "NEZNÁMÉ"

    # --------------------------------------------------------
    # Statistika zdrojů
    # --------------------------------------------------------

    if source == "ESP":
        total_esp_packets += 1
        esp_pps_counter += 1

    elif source == "NTB":
        total_ntb_packets += 1
        ntb_pps_counter += 1

    with devices_lock:

        # ----------------------------------------------------
        # Nový kontakt
        # ----------------------------------------------------

        if address not in devices:

            devices[address] = {
                "name": name,

                "rssi": float(rssi),
                "raw": rssi,

                "first": now,
                "last": now,

                "packets": 1,

                "minimum": rssi,
                "maximum": rssi,

                "sources": {source},

                "esp_rssi": (
                    rssi
                    if source == "ESP"
                    else None
                ),

                "ntb_rssi": (
                    rssi
                    if source == "NTB"
                    else None
                ),

                "manufacturer": (
                    manufacturer or {}
                ),

                "service_uuids": (
                    service_uuids or []
                ),

                "tx_power": tx_power,

                "trail": deque(maxlen=200)
            }

        # ----------------------------------------------------
        # Existující kontakt
        # ----------------------------------------------------

        else:

            d = devices[address]

            d["sources"].add(source)

            # Jméno si zapamatujeme, pokud ho některý
            # přijímač získá později.

            if (
                name
                and
                name != "NEZNÁMÉ"
            ):
                d["name"] = name

            airwave = is_airwave_name(
                d["name"]
            )

            smoothing = (
                AIRWAVE_SMOOTHING
                if airwave
                else NORMAL_SMOOTHING
            )

            d["rssi"] += (
                rssi - d["rssi"]
            ) * smoothing

            d["raw"] = rssi
            d["last"] = now
            d["packets"] += 1

            d["minimum"] = min(
                d["minimum"],
                rssi
            )

            d["maximum"] = max(
                d["maximum"],
                rssi
            )

            if source == "ESP":
                d["esp_rssi"] = rssi

            elif source == "NTB":
                d["ntb_rssi"] = rssi

            if manufacturer:
                d["manufacturer"] = manufacturer

            if service_uuids:
                d["service_uuids"] = service_uuids

            if tx_power is not None:
                d["tx_power"] = tx_power

        # ----------------------------------------------------
        # AirWave historie
        # ----------------------------------------------------

        d = devices[address]

        if is_airwave_name(d["name"]):

            airwave_history.append(
                (
                    now,
                    rssi,
                    source
                )
            )


# ============================================================
# NOTEBOOK BLE SCANNER
# ============================================================

def notebook_detection_callback(
    device,
    advertisement_data
):
    """
    Callback z Bleak.

    Windows nám sem předává BLE zařízení
    a advertising data.
    """

    try:

        address = device.address

        # Priorita:
        # 1. local_name z advertisementu
        # 2. jméno zařízení od OS
        # 3. NEZNÁMÉ

        name = (
            advertisement_data.local_name
            or device.name
            or "NEZNÁMÉ"
        )

        rssi = advertisement_data.rssi

        manufacturer = (
            advertisement_data.manufacturer_data
            or {}
        )

        service_uuids = (
            advertisement_data.service_uuids
            or []
        )

        tx_power = (
            advertisement_data.tx_power
        )

        update_device(
            address=address,
            rssi=rssi,
            name=name,
            source="NTB",
            manufacturer=manufacturer,
            service_uuids=service_uuids,
            tx_power=tx_power
        )

    except Exception:
        pass


async def notebook_ble_loop():

    global notebook_scanner_ok
    global notebook_scanner_error

    try:

        scanner = BleakScanner(
            detection_callback=notebook_detection_callback,
            scanning_mode="active"
        )

        await scanner.start()

        notebook_scanner_ok = True
        notebook_scanner_error = ""

        # Skenuj pořád

        while True:
            await asyncio.sleep(1)

    except Exception as e:

        notebook_scanner_ok = False
        notebook_scanner_error = str(e)


def notebook_thread_main():

    try:
        asyncio.run(
            notebook_ble_loop()
        )

    except Exception as e:

        global notebook_scanner_error
        global notebook_scanner_ok

        notebook_scanner_ok = False
        notebook_scanner_error = str(e)


# ============================================================
# SPUŠTĚNÍ NOTEBOOK BLE
# ============================================================

ble_thread = threading.Thread(
    target=notebook_thread_main,
    daemon=True
)

ble_thread.start()

# ============================================================
# ESP32 SERIAL
# ============================================================

try:

    ser = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=0
    )

    esp_connected = True

except Exception as e:

    print(
        "ESP32 nelze otevřít:",
        e
    )

    # Notebookový BLE scanner může běžet i bez ESP32.

    ser = None
    esp_connected = False

serial_buffer = ""

# ============================================================
# PYGAME
# ============================================================

pygame.init()

info = pygame.display.Info()

WIDTH = info.current_w
HEIGHT = info.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption(
    "AIRWAVE // DUAL BLE RADAR"
)

pygame.mouse.set_visible(False)

clock = pygame.time.Clock()

# ============================================================
# BARVY
# ============================================================

BACKGROUND = (2, 7, 10)

PANEL = (3, 14, 17)
PANEL_LINE = (17, 68, 63)

GRID = (12, 55, 52)
GRID_DARK = (6, 30, 29)

TEXT = (75, 185, 165)
TEXT_DIM = (43, 105, 100)

NORMAL = (55, 140, 130)
NORMAL_DIM = (28, 78, 74)
NORMAL_TEXT = (65, 165, 150)

AIRWAVE = (100, 255, 190)
AIRWAVE_DIM = (30, 125, 95)
AIRWAVE_DARK = (15, 70, 55)

# ============================================================
# FONTY
# ============================================================

font_title = pygame.font.SysFont(
    "consolas",
    max(25, WIDTH // 58),
    bold=True
)

font_large = pygame.font.SysFont(
    "consolas",
    max(18, WIDTH // 78),
    bold=True
)

font = pygame.font.SysFont(
    "consolas",
    max(14, WIDTH // 105)
)

font_small = pygame.font.SysFont(
    "consolas",
    max(11, WIDTH // 140)
)

# ============================================================
# ROZLOŽENÍ
# ============================================================

PANEL_WIDTH = int(
    WIDTH * 0.31
)

RADAR_WIDTH = (
    WIDTH - PANEL_WIDTH
)

CX = (
    PANEL_WIDTH
    + RADAR_WIDTH // 2
)

CY = int(
    HEIGHT * 0.43
)

MAX_RADIUS = int(
    min(
        RADAR_WIDTH * 0.40,
        HEIGHT * 0.35
    )
)

GRAPH_HEIGHT = max(
    120,
    int(HEIGHT * 0.15)
)

GRAPH_WIDTH = int(
    RADAR_WIDTH * 0.55
)

GRAPH_X = (
    PANEL_WIDTH + 30
)

GRAPH_Y = (
    HEIGHT
    - GRAPH_HEIGHT
    - 45
)

# ============================================================
# FUNKCE
# ============================================================

def clamp(value, low, high):

    return max(
        low,
        min(high, value)
    )


def draw_text(
    text,
    font_object,
    color,
    x,
    y
):

    surface = font_object.render(
        str(text),
        True,
        color
    )

    screen.blit(
        surface,
        (
            int(x),
            int(y)
        )
    )


# ============================================================
# RSSI -> POLOMĚR
# ============================================================

def rssi_to_radius(rssi):

    calibration = [

        (-25, 0.03),
        (-30, 0.04),
        (-35, 0.06),

        (-40, 0.09),
        (-45, 0.13),

        (-50, 0.18),
        (-55, 0.24),

        (-60, 0.31),
        (-65, 0.39),

        (-70, 0.48),
        (-75, 0.58),

        (-80, 0.68),
        (-85, 0.78),

        (-90, 0.87),
        (-95, 0.94),

        (-100, 0.98),
        (-105, 1.00)
    ]

    if rssi >= calibration[0][0]:

        fraction = calibration[0][1]

    elif rssi <= calibration[-1][0]:

        fraction = calibration[-1][1]

    else:

        fraction = 1.0

        for i in range(
            len(calibration) - 1
        ):

            ra, fa = calibration[i]
            rb, fb = calibration[i + 1]

            if ra >= rssi >= rb:

                t = (
                    (ra - rssi)
                    /
                    (ra - rb)
                )

                fraction = (
                    fa
                    + (fb - fa) * t
                )

                break

    return (
        20
        + fraction
        * (MAX_RADIUS - 20)
    )


def device_angle(address):

    value = 0

    for char in address:

        value = (
            value * 31
            + ord(char)
        ) & 0xFFFFFFFF

    return math.radians(
        value % 360
    )


def signal_label(rssi):

    if rssi >= -35:
        return "EXTRÉMNĚ SILNÝ"

    if rssi >= -45:
        return "VELMI SILNÝ"

    if rssi >= -55:
        return "SILNÝ"

    if rssi >= -65:
        return "DOBRÝ"

    if rssi >= -75:
        return "STŘEDNÍ"

    if rssi >= -85:
        return "SLABÝ"

    if rssi >= -95:
        return "VELMI SLABÝ"

    return "NA HRANICI"


def source_label(d):

    esp = (
        d["esp_rssi"]
        is not None
    )

    ntb = (
        d["ntb_rssi"]
        is not None
    )

    if esp and ntb:
        return "ESP+NTB"

    if esp:
        return "ESP"

    if ntb:
        return "NTB"

    return "?"


# ============================================================
# HLAVNÍ SMYČKA
# ============================================================

running = True

pps_timer = time.time()

sweep_angle = 0.0

last_frame = time.time()

while running:

    now = time.time()

    dt = (
        now - last_frame
    )

    last_frame = now

    # ========================================================
    # KLÁVESNICE
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

    # ========================================================
    # ESP32 DATA
    # ========================================================

    if (
        esp_connected
        and ser is not None
    ):

        try:

            waiting = ser.in_waiting

            if waiting:

                incoming = ser.read(
                    waiting
                )

                serial_buffer += incoming.decode(
                    "utf-8",
                    errors="ignore"
                )

                lines = serial_buffer.split(
                    "\n"
                )

                serial_buffer = lines[-1]

                for line in lines[:-1]:

                    line = line.strip()

                    if not line.startswith(
                        "BLE,"
                    ):
                        continue

                    parts = line.split(
                        ",",
                        3
                    )

                    if len(parts) != 4:
                        continue

                    try:

                        address = (
                            parts[1]
                            .strip()
                            .upper()
                        )

                        rssi = int(
                            parts[2]
                        )

                        name = (
                            parts[3]
                            .strip()
                        )

                    except ValueError:
                        continue

                    if (
                        not name
                        or name == "-"
                    ):
                        name = "NEZNÁMÉ"

                    update_device(
                        address=address,
                        rssi=rssi,
                        name=name,
                        source="ESP"
                    )

        except Exception:

            esp_connected = False

    # ========================================================
    # PPS
    # ========================================================

    if (
        now - pps_timer
        >= 1.0
    ):

        esp_pps = esp_pps_counter
        ntb_pps = ntb_pps_counter

        esp_pps_counter = 0
        ntb_pps_counter = 0

        pps_timer = now

    # ========================================================
    # KOPIE DAT PRO RENDER
    # ========================================================

    with devices_lock:

        stale = []

        for address, d in devices.items():

            if (
                now - d["last"]
                > DEVICE_TIMEOUT
            ):
                stale.append(address)

        for address in stale:
            del devices[address]

        device_snapshot = list(
            devices.items()
        )

        history_snapshot = list(
            airwave_history
        )

    # ========================================================
    # POZADÍ
    # ========================================================

    screen.fill(
        BACKGROUND
    )

    pygame.draw.rect(
        screen,
        PANEL,
        (
            0,
            0,
            PANEL_WIDTH,
            HEIGHT
        )
    )

    pygame.draw.line(
        screen,
        PANEL_LINE,
        (
            PANEL_WIDTH,
            0
        ),
        (
            PANEL_WIDTH,
            HEIGHT
        ),
        2
    )

    # ========================================================
    # HEADER
    # ========================================================

    draw_text(
        "AIRWAVE",
        font_title,
        AIRWAVE,
        25,
        20
    )

    draw_text(
        "// DVOJITÝ BLE PŘIJÍMAČ",
        font_small,
        TEXT,
        27,
        60
    )

    # ========================================================
    # STAV PŘIJÍMAČŮ
    # ========================================================

    esp_status = (
        "ONLINE"
        if esp_connected
        else "OFFLINE"
    )

    ntb_status = (
        "ONLINE"
        if notebook_scanner_ok
        else "START / CHYBA"
    )

    draw_text(
        f"ESP32      {esp_status}",
        font,
        (
            AIRWAVE
            if esp_connected
            else TEXT_DIM
        ),
        25,
        100
    )

    draw_text(
        f"NOTEBOOK   {ntb_status}",
        font,
        (
            AIRWAVE
            if notebook_scanner_ok
            else TEXT_DIM
        ),
        25,
        126
    )

    draw_text(
        f"ESP32      {esp_pps}/s",
        font_small,
        TEXT,
        25,
        162
    )

    draw_text(
        f"NOTEBOOK   {ntb_pps}/s",
        font_small,
        TEXT,
        25,
        184
    )

    draw_text(
        f"KONTAKTY   {len(device_snapshot)}",
        font,
        TEXT,
        25,
        216
    )

    # ========================================================
    # AIRWAVE
    # ========================================================

    airwaves = [

        (address, d)

        for address, d
        in device_snapshot

        if is_airwave_name(
            d["name"]
        )
    ]

    airwaves.sort(
        key=lambda item:
        item[1]["rssi"],
        reverse=True
    )

    if airwaves:

        air_address, air = (
            airwaves[0]
        )

        draw_text(
            "● AIRWAVE ZACHYCEN",
            font_large,
            AIRWAVE,
            25,
            255
        )

        draw_text(
            f"RSSI       {air['raw']} dBm",
            font,
            AIRWAVE,
            25,
            294
        )

        draw_text(
            f"SÍLA       {signal_label(air['rssi'])}",
            font,
            TEXT,
            25,
            320
        )

        draw_text(
            f"ZDROJ      {source_label(air)}",
            font,
            TEXT,
            25,
            346
        )

        if air["esp_rssi"] is not None:

            draw_text(
                f"ESP32      {air['esp_rssi']} dBm",
                font_small,
                TEXT_DIM,
                25,
                375
            )

        if air["ntb_rssi"] is not None:

            draw_text(
                f"NOTEBOOK   {air['ntb_rssi']} dBm",
                font_small,
                TEXT_DIM,
                25,
                397
            )

        list_y = 440

    else:

        draw_text(
            "○ HLEDÁM AIRWAVE",
            font_large,
            TEXT_DIM,
            25,
            255
        )

        list_y = 310

    # ========================================================
    # SEZNAM
    # ========================================================

    draw_text(
        "BLE ZAŘÍZENÍ",
        font_large,
        TEXT,
        25,
        list_y
    )

    list_y += 35

    sorted_devices = sorted(

        device_snapshot,

        key=lambda item:
        item[1]["rssi"],

        reverse=True
    )

    for address, d in sorted_devices[
        :MAX_LIST_DEVICES
    ]:

        if (
            list_y
            > HEIGHT - 60
        ):
            break

        airwave = is_airwave_name(
            d["name"]
        )

        color = (
            AIRWAVE
            if airwave
            else NORMAL_TEXT
        )

        name = d["name"]

        if name == "NEZNÁMÉ":
            name = "ANONYMNÍ BLE"

        draw_text(
            "●" if airwave else "•",
            font,
            color,
            25,
            list_y
        )

        draw_text(
            name[:18],
            font,
            color,
            45,
            list_y
        )

        draw_text(
            f"{d['rssi']:.0f}",
            font,
            color,
            PANEL_WIDTH - 70,
            list_y
        )

        draw_text(
            address[-17:],
            font_small,
            TEXT_DIM,
            45,
            list_y + 19
        )

        draw_text(
            source_label(d),
            font_small,
            TEXT_DIM,
            PANEL_WIDTH - 82,
            list_y + 19
        )

        list_y += 46

    # ========================================================
    # RADAR HEADER
    # ========================================================

    draw_text(
        "BLE PROSTOR // ESP32 + NOTEBOOK",
        font_large,
        TEXT,
        PANEL_WIDTH + 30,
        22
    )

    draw_text(
        "POLOMĚR = RSSI // ÚHEL NENÍ SKUTEČNÝ SMĚR",
        font_small,
        TEXT_DIM,
        PANEL_WIDTH + 32,
        52
    )

    # ========================================================
    # RADAR
    # ========================================================

    for fraction, label in [

        (0.2, "-50"),
        (0.4, "-65"),
        (0.6, "-75"),
        (0.8, "-85"),
        (1.0, "-105")

    ]:

        radius = int(
            MAX_RADIUS
            * fraction
        )

        pygame.draw.circle(
            screen,
            GRID,
            (CX, CY),
            radius,
            1
        )

        draw_text(
            label,
            font_small,
            TEXT_DIM,
            CX + 5,
            CY - radius + 3
        )

    for degrees in range(
        0,
        360,
        30
    ):

        angle = math.radians(
            degrees
        )

        x = (
            CX
            + math.cos(angle)
            * MAX_RADIUS
        )

        y = (
            CY
            + math.sin(angle)
            * MAX_RADIUS
        )

        pygame.draw.line(
            screen,
            GRID_DARK,
            (CX, CY),
            (x, y),
            1
        )

    # ========================================================
    # SWEEP
    # ========================================================

    sweep_angle += (
        SWEEP_DEGREES_PER_SECOND
        * dt
    )

    sweep_angle %= 360

    for i in range(
        45,
        0,
        -1
    ):

        a = math.radians(
            sweep_angle
            - i * 0.65
        )

        x = (
            CX
            + math.cos(a)
            * MAX_RADIUS
        )

        y = (
            CY
            + math.sin(a)
            * MAX_RADIUS
        )

        intensity = int(
            10
            + (45 - i) * 1.7
        )

        pygame.draw.line(
            screen,
            (
                6,
                intensity,
                max(
                    6,
                    intensity - 12
                )
            ),
            (CX, CY),
            (x, y),
            1
        )

    a = math.radians(
        sweep_angle
    )

    pygame.draw.line(
        screen,
        AIRWAVE_DIM,
        (CX, CY),
        (
            CX
            + math.cos(a)
            * MAX_RADIUS,

            CY
            + math.sin(a)
            * MAX_RADIUS
        ),
        2
    )

    # ========================================================
    # KONTAKTY
    # ========================================================

    for address, d in device_snapshot:

        radius = rssi_to_radius(
            d["rssi"]
        )

        angle = device_angle(
            address
        )

        x = (
            CX
            + math.cos(angle)
            * radius
        )

        y = (
            CY
            + math.sin(angle)
            * radius
        )

        airwave = is_airwave_name(
            d["name"]
        )

        if airwave:

            pulse = (
                math.sin(
                    now * PULSE_SPEED
                )
                + 1
            ) / 2

            pygame.draw.line(
                screen,
                AIRWAVE_DARK,
                (CX, CY),
                (int(x), int(y)),
                1
            )

            pygame.draw.circle(
                screen,
                AIRWAVE_DARK,
                (int(x), int(y)),
                int(38 + pulse * 13),
                1
            )

            pygame.draw.circle(
                screen,
                AIRWAVE_DIM,
                (int(x), int(y)),
                int(25 + pulse * 8),
                1
            )

            pygame.draw.circle(
                screen,
                AIRWAVE,
                (int(x), int(y)),
                12,
                2
            )

            pygame.draw.circle(
                screen,
                AIRWAVE,
                (int(x), int(y)),
                5
            )

            draw_text(
                "AIRWAVE",
                font_large,
                AIRWAVE,
                x + 22,
                y - 24
            )

            draw_text(
                f"{d['raw']} dBm // {source_label(d)}",
                font_small,
                AIRWAVE,
                x + 23,
                y + 2
            )

        else:

            # Zařízení zachycené oběma přijímači
            # dostane dvojitý kruh.

            if source_label(d) == "ESP+NTB":

                pygame.draw.circle(
                    screen,
                    NORMAL_DIM,
                    (int(x), int(y)),
                    11,
                    1
                )

            pygame.draw.circle(
                screen,
                NORMAL,
                (int(x), int(y)),
                4
            )

            name = d["name"]

            if name == "NEZNÁMÉ":
                name = address[-8:]

            draw_text(
                f"{name[:13]} "
                f"{d['rssi']:.0f} "
                f"[{source_label(d)}]",
                font_small,
                NORMAL_TEXT,
                x + 9,
                y - 7
            )

    # ========================================================
    # PŘIJÍMAČ
    # ========================================================

    pygame.draw.circle(
        screen,
        AIRWAVE_DARK,
        (CX, CY),
        23,
        1
    )

    pygame.draw.circle(
        screen,
        AIRWAVE_DIM,
        (CX, CY),
        12,
        1
    )

    pygame.draw.circle(
        screen,
        AIRWAVE,
        (CX, CY),
        4
    )

    draw_text(
        "RX",
        font_small,
        AIRWAVE,
        CX + 17,
        CY + 7
    )

    # ========================================================
    # AIRWAVE GRAF
    # ========================================================

    pygame.draw.rect(
        screen,
        PANEL,
        (
            GRAPH_X,
            GRAPH_Y,
            GRAPH_WIDTH,
            GRAPH_HEIGHT
        )
    )

    pygame.draw.rect(
        screen,
        GRID,
        (
            GRAPH_X,
            GRAPH_Y,
            GRAPH_WIDTH,
            GRAPH_HEIGHT
        ),
        1
    )

    draw_text(
        "AIRWAVE // RSSI // POSLEDNÍCH 5 s",
        font_small,
        AIRWAVE,
        GRAPH_X + 10,
        GRAPH_Y + 8
    )

    graph_top = GRAPH_Y + 27

    graph_bottom = (
        GRAPH_Y
        + GRAPH_HEIGHT
        - 8
    )

    graph_h = (
        graph_bottom
        - graph_top
    )

    for mark in [
        -30,
        -50,
        -70,
        -90
    ]:

        f = (
            (mark - RSSI_FAR)
            /
            (RSSI_NEAR - RSSI_FAR)
        )

        f = clamp(
            f,
            0,
            1
        )

        gy = (
            graph_bottom
            - f * graph_h
        )

        pygame.draw.line(
            screen,
            GRID_DARK,
            (
                GRAPH_X,
                int(gy)
            ),
            (
                GRAPH_X
                + GRAPH_WIDTH,
                int(gy)
            ),
            1
        )

        draw_text(
            mark,
            font_small,
            TEXT_DIM,
            GRAPH_X + 3,
            gy - 13
        )

    # pouze posledních 5 sekund

    points = []

    for timestamp, rssi, source in history_snapshot:

        age = now - timestamp

        if (
            age < 0
            or age > GRAPH_SECONDS
        ):
            continue

        fx = (
            1
            - age / GRAPH_SECONDS
        )

        fy = (
            (rssi - RSSI_FAR)
            /
            (RSSI_NEAR - RSSI_FAR)
        )

        fy = clamp(
            fy,
            0,
            1
        )

        gx = (
            GRAPH_X
            + fx * GRAPH_WIDTH
        )

        gy = (
            graph_bottom
            - fy * graph_h
        )

        points.append(
            (
                int(gx),
                int(gy)
            )
        )

    if len(points) > 1:

        pygame.draw.lines(
            screen,
            AIRWAVE,
            False,
            points,
            2
        )

    # ========================================================
    # FOOTER
    # ========================================================

    draw_text(
        "ESP = ESP32-C3",
        font_small,
        TEXT_DIM,
        GRAPH_X + GRAPH_WIDTH + 20,
        GRAPH_Y + 25
    )

    draw_text(
        "NTB = BLUETOOTH NOTEBOOKU",
        font_small,
        TEXT_DIM,
        GRAPH_X + GRAPH_WIDTH + 20,
        GRAPH_Y + 47
    )

    draw_text(
        "ESP+NTB = ZACHYCENO OBOJÍM",
        font_small,
        TEXT_DIM,
        GRAPH_X + GRAPH_WIDTH + 20,
        GRAPH_Y + 69
    )

    draw_text(
        "RSSI NENÍ PŘESNÁ VZDÁLENOST",
        font_small,
        TEXT_DIM,
        GRAPH_X + GRAPH_WIDTH + 20,
        GRAPH_Y + 100
    )

    draw_text(
        "ESC // KONEC",
        font_small,
        TEXT_DIM,
        WIDTH - 125,
        25
    )

    pygame.display.flip()

    clock.tick(120)

# ============================================================
# KONEC
# ============================================================

if ser is not None:
    ser.close()

pygame.quit()