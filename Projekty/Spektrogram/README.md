# Spectrogram

The GUI converts images into audio that reproduces the image in a
spectrogram, reads WAV files, and supports recording/playback.
This project has no Arduino counterpart.

- **Run:** `python Spectogram.py`.
- **Requirements:** Tkinter, numpy, Pillow; sounddevice for microphone input and playback.
- **Connections:** computer audio input/output and an optional microphone; no GPIO.
- **Working directory:** this project's folder; create the environment using the [shared guide](../README.md).
- **Install:** `python -m pip install -r requirements.txt`.
- **WAV:** 8/16-bit PCM; internal sample rate 44100 Hz.
- **Window:** F11 toggles fullscreen; Esc exits fullscreen.
