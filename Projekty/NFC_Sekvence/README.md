# NFC Sequence

Scanning cards `003955D3`, `A05EE128`, and `C067A12B` in that order
gradually reveals code `2012`. Change the order in Python's `SPRAVNE_PORADI`.

- **Pair 1:** Uno `NFC_Smiley_Parat/NFC_Smiley_Parat.ino` ↔ `NFC_code_Driver.py`.
- **Pair 2:** Mega `Displays_Driver_part/Displays_Driver_part.ino` ↔ the same Python application.
- **USB:** both at 9600 baud; `nfc_reader` (COM10) and `nfc_display` (COM7) in `serial_ports.json`.
- **Uno protocol:** `CARD:UID` to the PC; `OK`, `WRONG`, `RESET` back to the board.
- **Mega protocol:** `KEY:1:2___`, `KEY:2:20__`, `KEY:3:2012`, `UNLOCKED`, `WRONG`, `RESET`.
- **Requirements:** pyserial, Tkinter; MFRC522, LedControl, Adafruit GFX, ST7735/ST7789, SH110X, and their dependencies.

| Module | Wiring |
| --- | --- |
| RC522 on Uno | 3.3V → 3.3V, GND → GND, SS/SDA → D10, RST → D9, SCK → D13, MOSI → D11, MISO → D12; leave IRQ unconnected |
| MAX7219 on Uno | VCC → 5V, GND → GND, DIN → D6, CLK → D5, CS → D7 |
| ST7789 on Mega | VCC/BLK → 3.3V, GND → GND, MOSI → D51, SCK → D52, DC → D9, RST → D8; no CS |
| SH1106 on Mega | SDA → D20, SCL → D21, GND → GND, address 0x3C; supply voltage depends on the module |

Power the RC522 at 3.3V and level-shift its inputs from the 5V Uno.
Also level-shift TFT inputs if the module lacks built-in level shifters.
I2C voltage must match the OLED module.
Connect both boards with separate USB cables; there is no additional data
link between them. If changing the revealed code, also update the fixed
`KEY:` commands in the Mega sketch.

Upload both sketches and run `NFC_code_Driver.py`.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
