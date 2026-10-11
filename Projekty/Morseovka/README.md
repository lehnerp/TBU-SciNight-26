# Morse Code with Light

The Mega transmits `UTB` and `FAI` through five IR and five RGB modules.
Python displays Morse symbols, letters, and the complete result.

- **Pair:** Mega `Morse_Part_Driver/Morse_Part_Driver.ino` ↔ `Morse_Driver.py`.
- **USB:** 115200 baud; `morse` in `serial_ports.json`.
- **Port:** an empty value enables the original automatic detection; specify a COM port when multiple boards are connected.
- **Messages:** `CLEAR`, `MORSE:symbols`, `LETTER:letter`, `RESULT:text|morse`.
- **Requirements:** pyserial, Tkinter; no external Arduino libraries.

| Module | Mega wiring |
| --- | --- |
| IR 1–5 | Control outputs D2/D3/D4/D5/D6; use LED resistors and a transistor driver if required |
| RGB KY-016 no. 1 | R/G/B → D22/D23/D24 |
| RGB KY-016 no. 2 | R/G/B → D25/D26/D27 |
| RGB KY-016 no. 3 | R/G/B → D28/D29/D30 |
| RGB KY-016 no. 4 | R/G/B → D31/D32/D33 |
| RGB KY-016 no. 5 | R/G/B → D34/D35/D36 |
| KY-016 common “−” pin | GND |

Upload the sketch and run `Morse_Driver.py`.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
