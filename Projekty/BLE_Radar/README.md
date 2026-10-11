# BLE Radar / AirWave

The Pygame radar combines BLE advertising data from an ESP32-C3 and the
laptop's Bluetooth adapter. An optional AirWave transmitter varies its power,
creating a changing RSSI signal. Radar angles are derived from MAC addresses;
they do not represent measured directions.

- **USB pair:** ESP32-C3 `Detector_Driver_ESP32C3/Detector_Driver_ESP32C3.ino` ↔ `BLE_Scan.py`.
- **Transmitter:** `Transmitterr_ESP32CV/Transmitterr_ESP32CV.ino` on a separate BLE-capable ESP32; advertised name `AirWave`.
- **Detector USB:** 460800 baud; `ble_detector` in `serial_ports.json` (COM15).
- **Detector output:** `BLE,MAC,RSSI,NAME`; a missing name is `-`.
- **Transmitter connection:** BLE advertising only; USB at 115200 baud is for diagnostics. Python does not open this COM port.
- **Requirements:** pyserial, pygame, bleak; NimBLE-Arduino 2.x and the ESP32 core.

Connect the detector to the PC over USB and power the transmitter over USB
as required by its board. No additional peripherals or GPIO connections
between boards are needed. For boards with native USB, enable USB CDC on boot
in the IDE settings if necessary. Enable laptop Bluetooth for the second data
source; Python can scan without the USB detector. Unsupported Bluetooth
results in a scanner error.

Upload the relevant sketches and run `BLE_Scan.py`; Esc closes the radar.
Run commands from this project's folder and create the environment using
the [shared guide](../README.md).
Install dependencies with `python -m pip install -r requirements.txt`.
