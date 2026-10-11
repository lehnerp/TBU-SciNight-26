"""Společné porty Arduino/Python; upravte serial_ports.json, rychlosti odpovídají .ino."""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("serial_ports.json")
BAUD_RATES = {'rfid_tv': 115200}


def serial_endpoint(name):
    """Vrátí (port, baud); prázdný port dovolujeme jen pro automatickou Morse detekci."""
    ports = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    port = ports[name]
    if not isinstance(port, str) or (not port.strip() and name != "morse"):
        raise ValueError(f"Neplatný port pro {name} v {CONFIG_PATH}")
    return port.strip(), BAUD_RATES[name]
