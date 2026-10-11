# TBU-SciNight-26 – Project Overview

Each active project has its own subfolder in `Projekty/` containing source files,
`requirements.txt`, and a requirements guide. Hardware stations include
Arduino sketches and wiring instructions. Upload each `.ino` separately
to its board; Python connects the boards over USB.
RGB Filter, Spectrogram, and VoiceGen work without Arduino.
Application interfaces and generated speech are intended for Czech users.

| Project | Description | Arduino ↔ Python |
| --- | --- | --- |
| [RFID and TV](Projekty/RFID_TV/README.md) | A valid card reveals a QR code; Python then prepares the TV image. | `TV_RFID_PART` ↔ `RFID_code_Driver.py` |
| [NFC Sequence](Projekty/NFC_Sekvence/README.md) | Three cards in the correct order reveal code 2012. | `NFC_Smiley_Parat` + `Displays_Driver_part` ↔ `NFC_code_Driver.py` |
| [PIN and LED Rings](Projekty/PIN_Klavesnice/README.md) | Keypad, LCD, GUI, and lighting feedback for PIN entry. | `KeyPin_Driver_Part` + `Circles_Breathing_Driver` ↔ `KeyPad_code_driver.py` |
| [Dino Game](Projekty/Dino_Hra/README.md) | A game on three LED matrices; clearing five obstacles reveals a code. | `Dino_Driver_part` ↔ `DinoRun_Driver.py` |
| [Morse Code](Projekty/Morseovka/README.md) | IR and RGB lights transmit UTB/FAI; Python displays the characters. | `Morse_Part_Driver` ↔ `Morse_Driver.py` |
| [BLE Radar](Projekty/BLE_Radar/README.md) | A radar combines BLE data from an ESP32-C3 and a laptop. | `Detector_Driver_ESP32C3` + `Transmitterr_ESP32CV` transmitter ↔ `BLE_Scan.py` |
| [RGB Filter](Projekty/RGB_Filtr/README.md) | Generate and export text/QR codes in colored layers. | `main.py`, `Filter_Text_QE.py`; no Arduino |
| [Spectrogram](Projekty/Spektrogram/README.md) | Encode an image into audio and display its spectrum. | `Spectogram.py`; no Arduino |
| [VoiceGen](Projekty/VoiceGen/README.md) | Generate Czech announcements with PA effects and alarms as a WAV file. | `main.py`, edge-tts + FFmpeg; no Arduino |

## Archived Prototypes

[Old_Prototypes](Projekty/Old_Prototypes/README.md) contains earlier standalone keypad
and NFC sketches. These prototypes are no longer used in the current setup
and are kept only as historical references. They are not required to install
or run any active project. Use the current PIN and NFC projects listed above.

## Installation and Running

All active project files and dependency lists are in `Projekty/`. Each project uses
its own `requirements.txt`; installation does not require shared files
or libraries in the `Noc` root folder.

Use Python 3.12 with Tkinter for the GUI applications.
The PIN station requires Windows because it uses `winsound`.
For Arduino, use Arduino IDE with Arduino AVR Boards for Uno/Mega,
or the ESP32 core for BLE boards. Install the libraries listed in each
project's guide through the Arduino IDE Library Manager.

Dino example: run the following commands from the `Noc` root folder.
For another station, change the folder and Python filename.

```powershell
cd Projekty\Dino_Hra
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m serial.tools.list_ports
.\.venv\Scripts\python.exe DinoRun_Driver.py
```

The virtual environment is created inside the selected project.
Tkinter, `winsound`, and other standard-library modules are not installed
through pip. Install FFmpeg (RFID/TV and VoiceGen) and HackTV (RFID/TV)
separately. VoiceGen requires internet access for edge-tts speech synthesis.

## Connecting Boards

Set the actual COM ports in each project's `serial_ports.json`.
RFID/TV, Dino, and the NFC display use COM7 by default;
assign a separate port to each board when running stations simultaneously.
Baud rates in `connection_config.py` match the sketches.
Close Serial Monitor before starting Python.
NFC and PIN each require two USB boards; messages are text lines ending in `\n`.

The BLE transmitter sends advertising packets to the detector or the laptop's
Bluetooth adapter; Python does not open its COM port.
See the individual guides for protocols, pin assignments, and other requirements.
