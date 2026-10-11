# RFID and TV

A valid card displays confirmation, followed by a QR code after 3 seconds.
On `TASK_DONE`, Python creates a video and starts HackTV.
An invalid card resets the QR process; the original behavior leaves an
already-running HackTV process active.

- **Pair:** `TV_RFID_PART/TV_RFID_PART.ino` (Mega 2560) ↔ `RFID_code_Driver.py`.
- **USB:** 115200 baud; `rfid_tv` in `serial_ports.json` (COM7 by default).
- **Messages:** `RFID_OK`, `NOT_OK`, `TASK_DONE`; Python ignores diagnostic `ID:…;STATUS:…` messages.
- **Requirements:** pyserial, Pillow, Tkinter; FFmpeg in PATH, HackTV and HackRF for TV output.
- **Arduino libraries:** Adafruit GFX, ST7735/ST7789, QRCode, and their dependencies.

| Module | Mega wiring |
| --- | --- |
| RDM6300 | VCC → 5V, GND → GND, TX → RX1/D19; UART at 9600 baud |
| ST7789 240×240 | VCC/BLK → 3.3V, GND → GND, SCK → D52, MOSI → D51, DC → D9, RES → D8; no CS |

Set `SPRAVNA_KARTA` and `QR_TEXT` in the sketch.
In Python, set `BASE` (default `C:\RFID-TV`), place `image.png` there,
and set `HACKTV` (default `C:\hacktv\bin\hacktv.exe`).
Output files are `broadcast.png` and `access.mpg`.
If the TFT lacks level shifters, convert the Mega's 5V signals to 3.3V.
RF/TV settings are at the beginning of the Python file.

Upload the sketch, close Serial Monitor, and run `RFID_code_Driver.py`.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
