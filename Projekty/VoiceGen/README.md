# VoiceGen

Generates Czech announcements for an escape room.
`edge-tts` creates speech; FFmpeg adds a PA/intercom effect and combines
it with pauses, static, beeps, and a siren.
The result is `EMERGENCY.wav` in the project folder (mono, 44100 Hz).
Running the script again overwrites this output file.

## Requirements and Running

- Python 3.12 and the `edge-tts` package from `requirements.txt`.
- Internet access for speech synthesis; text is sent to the TTS service.
- FFmpeg installed separately and available in PATH; check with `ffmpeg -version`.
- No Arduino or GPIO connections. Play the WAV file on a computer/speakers.

Run these commands directly from the `VoiceGen` folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

[Project overview](../README.md).

Edit the announcement text and effect order in `main()`.
Settings at the beginning of the script include `VOICE`
(default `cs-CZ-AntoninNeural`), `RATE` (`-18%`), `PITCH`,
`SAMPLE_RATE`, and the `OUTPUT_FILE` path.
Temporary audio files are cleaned up when the script finishes.
The script creates an audio file; it does not start playback or broadcasting.
