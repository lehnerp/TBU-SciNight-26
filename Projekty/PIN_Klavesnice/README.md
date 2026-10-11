# PIN and LED Rings

The keypad verifies PIN `2012`, and the LCD reveals key `TEST`.
Python displays progress and controls three LED rings.
`*` deletes a digit; `#` confirms the PIN.

- **Pair 1:** Mega `KeyPin_Driver_Part/KeyPin_Driver_Part.ino` ↔ `KeyPad_code_driver.py`.
- **Pair 2:** a separate board running `Circles_Breathing_Driver/Circles_Breathing_Driver.ino` ↔ the same Python application.
- **USB:** 9600 baud; `keypad` (COM11) and `neopixel` (COM12) in `serial_ports.json`.
- **Events:** `PIN:KEY:digit:length`, `PIN:BACKSPACE:length`, `PIN:OK`, `PIN:WRONG`, `PIN:RESET`.
- **LED commands:** `STEP:1/2/3`, `SUCCESS`, `ERROR`, `RESET`.
- **Requirements:** Windows, pyserial, Tkinter, built-in winsound; LiquidCrystal_I2C, Keypad, Adafruit NeoPixel.

| Module | Wiring |
| --- | --- |
| 16×2 LCD on Mega | VCC → 5V, GND → GND, SDA → D20, SCL → D21; address 0x27 |
| 4×4 keypad on Mega | R1–R4 → D2/D3/D4/D5, C1–C4 → D6/D7/D8/D9 |
| Three rings, 12 LEDs each | Ring 1/2/3 DIN → D2/D3/D4 on the second board; VCC → external 5V, GND connected to that board's GND |

Use an approximately 330 Ω series resistor in each NeoPixel data line and
size the power supply for the LEDs. Do not supply ring current through GPIO.
Sound files `xp_error.wav` and `vista_login.wav` are next to the Python file.
Change the PIN and key in the `KeyPin_Driver_Part` sketch.

Upload both sketches and run `KeyPad_code_driver.py`.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
