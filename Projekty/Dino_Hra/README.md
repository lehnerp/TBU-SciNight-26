# Dino Game

Arduino renders the game on three 8×8 NeoPixel panels (24×8 in total).
Python controls starting and jumping; clearing five obstacles reveals code `2012`.

- **Pair:** `Dino_Driver_part/Dino_Driver_part.ino` ↔ `DinoRun_Driver.py`.
- **Board:** Uno/Mega with an adequate LED power supply; USB at 9600 baud.
- **Port:** `dino` in `serial_ports.json` (COM7 by default).
- **PC → Arduino:** `START`, `RESTART`, `JUMP`, `RESET`.
- **Arduino → PC:** `GAME:READY/RESET/START/JUMP/WIN`, `GAME:SCORE:n`, `GAME:OVER:n`.
- **Requirements:** pyserial, Tkinter; Adafruit NeoPixel.

| Module | Wiring |
| --- | --- |
| Panels 1/2/3, 64 LEDs each | DIN → D2/D3/D4 |
| Panel power | External 5V supply; connect its GND to Arduino GND |

Use a supply sized for 192 LEDs and an approximately 330 Ω series resistor
in each data line. The sketch assumes GRB/800 kHz and a specific pixel layout;
check orientation when using different panels.
Python sets the victory threshold and secret text (`WIN_SCORE`,
`SECRET_MESSAGE`); the obstacle count must match the Arduino game.

Upload the sketch and run `DinoRun_Driver.py`.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
