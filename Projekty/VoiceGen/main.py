"""VoiceGen: české hlášení pro únikovou hru s efektem rozhlasu a alarmy.

Požadavky: Python 3.12, edge-tts, internet a FFmpeg v PATH.
Výstup: EMERGENCY.wav vedle tohoto skriptu, mono / 44100 Hz.
Texty jsou v main(), hlas a tempo v konfiguraci níže. Bez Arduino zapojení.
Instalace a spuštění: README.md v této složce.
"""

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

import edge_tts


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = Path(__file__).with_name("EMERGENCY.wav")

VOICE = "cs-CZ-AntoninNeural"

# Try:
# -5%   normal-ish
# -12%  serious
# -18%  very deliberate
RATE = "-18%"

# Slightly lower voice
PITCH = "-0Hz"

SAMPLE_RATE = 44100


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def run(command):
    """Run FFmpeg command."""

    print("\nFFmpeg:")
    print(" ".join(str(x) for x in command))

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL
    )


def check_ffmpeg():
    """Check whether FFmpeg is installed."""

    if shutil.which("ffmpeg") is None:
        print()
        print("==========================================")
        print("ERROR: FFmpeg nebyl nalezen.")
        print("==========================================")
        print()
        print("Nainstaluj FFmpeg a přidej ho do PATH.")
        print()
        print("Potom v terminálu zkus:")
        print()
        print("    ffmpeg -version")
        print()

        raise SystemExit(1)


# ============================================================
# TEXT TO SPEECH
# ============================================================

async def generate_tts(text, filename):

    print()
    print("TTS:")
    print(text)

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        pitch=PITCH
    )

    await communicate.save(filename)


# ============================================================
# PA / INTERCOM EFFECT
# ============================================================

def make_intercom(input_file, output_file):

    filters = ",".join([

        # Remove deep bass
        "highpass=f=280",

        # Remove highs = cheap PA speaker
        "lowpass=f=3800",

        # Presence / intelligibility
        "equalizer=f=1800:t=q:w=1.2:g=4",

        # Slight emphasis around 900 Hz
        "equalizer=f=900:t=q:w=1:g=2",

        # Compression
        (
            "acompressor="
            "threshold=0.12:"
            "ratio=4:"
            "attack=5:"
            "release=80:"
            "makeup=1.5"
        ),

        # Tiny PA echo
        "aecho=0.8:0.25:65:0.10",

        # Prevent clipping
        "alimiter=limit=0.90"
    ])

    run([
        "ffmpeg",
        "-y",

        "-i", input_file,

        "-af", filters,

        "-ar", str(SAMPLE_RATE),
        "-ac", "1",

        output_file
    ])


# ============================================================
# SILENCE
# ============================================================

def create_silence(filename, seconds):

    run([
        "ffmpeg",
        "-y",

        "-f", "lavfi",

        "-i",
        f"anullsrc=r={SAMPLE_RATE}:cl=mono",

        "-t", str(seconds),

        filename
    ])


# ============================================================
# BEEP
# ============================================================

def create_beep(filename, frequency=1000, duration=0.4):

    run([
        "ffmpeg",
        "-y",

        "-f", "lavfi",

        "-i",
        (
            f"sine=frequency={frequency}:"
            f"duration={duration}:"
            f"sample_rate={SAMPLE_RATE}"
        ),

        "-af",
        "volume=0.25",

        filename
    ])


# ============================================================
# STATIC
# ============================================================

def create_static(filename, duration=0.5):

    run([
        "ffmpeg",
        "-y",

        "-f", "lavfi",

        "-i",
        (
            f"anoisesrc="
            f"color=white:"
            f"duration={duration}:"
            f"sample_rate={SAMPLE_RATE}:"
            f"amplitude=0.15"
        ),

        "-af",
        (
            "highpass=f=600,"
            "lowpass=f=6000,"
            "volume=0.35"
        ),

        filename
    ])


# ============================================================
# EMERGENCY SIREN
# ============================================================

def create_siren(filename, duration=4):

    #
    # Alternating 720 Hz / 960 Hz emergency alarm.
    #

    segment = 0.45

    with tempfile.TemporaryDirectory() as temp:
        piece_file = str(Path(temp) / "siren_piece.wav")

        run([
            "ffmpeg",
            "-y",

            "-f", "lavfi",
            "-i",
            (
                f"sine=frequency=720:"
                f"duration={segment}:"
                f"sample_rate={SAMPLE_RATE}"
            ),

            "-f", "lavfi",
            "-i",
            (
                f"sine=frequency=960:"
                f"duration={segment}:"
                f"sample_rate={SAMPLE_RATE}"
            ),

            "-filter_complex",
            (
                "[0:a][1:a]"
                "concat=n=2:v=0:a=1,"
                "volume=0.18"
                "[alarm]"
            ),

            "-map", "[alarm]",

            piece_file
        ])

        # Loop alarm
        run([
            "ffmpeg",
            "-y",

            "-stream_loop", "-1",

            "-i", piece_file,

            "-t", str(duration),

            "-af",
            "afade=t=in:st=0:d=0.1,"
            f"afade=t=out:st={max(0, duration - 0.3)}:d=0.3",

            filename
        ])


# ============================================================
# CONCATENATE AUDIO
# ============================================================

def concatenate(files, output):

    with tempfile.TemporaryDirectory() as temp:
        list_file = str(Path(temp) / "audio_list.txt")

        with open(
            list_file,
            "w",
            encoding="utf-8"
        ) as f:

            for filename in files:

                absolute = Path(filename).resolve()

                path = str(absolute).replace(
                    "\\",
                    "/"
                )

                f.write(
                    "file '" + path.replace("'", "'\\''") + "'\n"
                )

        run([
            "ffmpeg",
            "-y",

            "-f", "concat",
            "-safe", "0",

            "-i", list_file,

            "-ar", str(SAMPLE_RATE),
            "-ac", "1",

            output
        ])


# ============================================================
# BROADCAST BUILDER
# ============================================================

class Broadcast:

    def __init__(self, directory):

        self.directory = Path(directory)

        self.files = []

        self.counter = 0


    def new_file(self, name):

        self.counter += 1

        return str(
            self.directory /
            f"{self.counter:03d}_{name}.wav"
        )


    # --------------------------------------------------------
    # SPEECH
    # --------------------------------------------------------

    async def say(self, text):

        mp3 = str(
            self.directory /
            f"tts_{self.counter:03d}.mp3"
        )

        wav = self.new_file("speech")

        await generate_tts(
            text,
            mp3
        )

        make_intercom(
            mp3,
            wav
        )

        self.files.append(wav)


    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    def pause(self, seconds):

        filename = self.new_file(
            "pause"
        )

        create_silence(
            filename,
            seconds
        )

        self.files.append(filename)


    # --------------------------------------------------------
    # STATIC
    # --------------------------------------------------------

    def static(self, seconds=0.5):

        filename = self.new_file(
            "static"
        )

        create_static(
            filename,
            seconds
        )

        self.files.append(filename)


    # --------------------------------------------------------
    # BEEP
    # --------------------------------------------------------

    def beep(
        self,
        frequency=1000,
        duration=0.4
    ):

        filename = self.new_file(
            "beep"
        )

        create_beep(
            filename,
            frequency,
            duration
        )

        self.files.append(filename)


    # --------------------------------------------------------
    # WARNING SIGNAL
    # --------------------------------------------------------

    def warning_signal(self):

        for i in range(3):

            self.beep(
                frequency=950,
                duration=0.45
            )

            if i < 2:
                self.pause(0.18)


    # --------------------------------------------------------
    # SIREN
    # --------------------------------------------------------

    def siren(self, seconds=4):

        filename = self.new_file(
            "siren"
        )

        create_siren(
            filename,
            seconds
        )

        self.files.append(filename)


    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    def export(self, filename):

        concatenate(
            self.files,
            filename
        )


# ============================================================
# MAIN ESCAPE ROOM SCRIPT
# ============================================================

async def main():

    print()
    print("==========================================")
    print("   CZECH EMERGENCY BROADCAST GENERATOR")
    print("==========================================")
    print()

    check_ffmpeg()

    with tempfile.TemporaryDirectory() as temp:

        broadcast = Broadcast(temp)


        # ====================================================
        # RADIO / PA SYSTEM ACTIVATES
        # ====================================================

        broadcast.static(0.6)

        broadcast.pause(0.3)


        # ====================================================
        # WARNING TONES
        # ====================================================

        broadcast.warning_signal()

        broadcast.pause(1.2)


        # ====================================================
        # FIRST ANNOUNCEMENT
        # ====================================================

        await broadcast.say(
            "Pozor."
        )

        broadcast.pause(0.7)

        await broadcast.say(
            "Byl vyhlášen stav laboratorní nouze."
        )

        broadcast.pause(1)

        await broadcast.say(
            "V sektoru B byla zaznamenána "
            "kritická porucha bezpečnostního systému."
        )

        broadcast.pause(1)


        # ====================================================
        # ALARM
        # ====================================================

        broadcast.siren(3.5)

        broadcast.pause(0.8)


        # ====================================================
        # LOCKDOWN
        # ====================================================

        await broadcast.say(
            "Automatické uzavření objektu "
            "bylo zahájeno."
        )

        broadcast.pause(0.8)

        await broadcast.say(
            "Všechny bezpečnostní dveře "
            "jsou nyní uzamčeny."
        )

        broadcast.pause(0.8)

        await broadcast.say(
            "Nepokoušejte se objekt opustit."
        )

        broadcast.pause(0.7)

        await broadcast.say(
            "Nepokoušejte se dveře "
            "otevřít silou."
        )

        broadcast.pause(1.5)


        # ====================================================
        # RADIO INTERRUPTION
        # ====================================================

        broadcast.static(0.35)

        broadcast.pause(0.15)

        broadcast.static(0.2)

        broadcast.pause(0.8)


        # ====================================================
        # SYSTEM MESSAGE
        # ====================================================

        await broadcast.say(
            "Pozor."
        )

        broadcast.pause(0.5)

        await broadcast.say(
            "Nouzový protokol nelze "
            "automaticky ukončit."
        )

        broadcast.pause(1)

        await broadcast.say(
            "K obnovení kontroly nad systémem "
            "je vyžadován autorizační kód."
        )

        broadcast.pause(1.2)

        await broadcast.say(
            "Vyhledejte hlavní řídicí terminál."
        )

        broadcast.pause(1.5)


        # ====================================================
        # SECOND WARNING
        # ====================================================

        broadcast.beep(
            frequency=1250,
            duration=0.25
        )

        broadcast.pause(0.15)

        broadcast.beep(
            frequency=1250,
            duration=0.25
        )

        broadcast.pause(0.8)


        # ====================================================
        # COUNTDOWN WARNING
        # ====================================================

        await broadcast.say(
            "Upozornění."
        )

        broadcast.pause(0.5)

        await broadcast.say(
            "Na dokončení bezpečnostní procedury "
            "máte omezený čas."
        )

        broadcast.pause(1)

        await broadcast.say(
            "Po vypršení časového limitu "
            "přejde systém do režimu "
            "úplného uzamčení."
        )

        broadcast.pause(1.5)


        # ====================================================
        # FINAL WARNING
        # ====================================================

        broadcast.warning_signal()

        broadcast.pause(1)

        await broadcast.say(
            "Toto není cvičení."
        )

        broadcast.pause(1)

        await broadcast.say(
            "Opakuji."
        )

        broadcast.pause(0.7)

        await broadcast.say(
            "Toto není cvičení."
        )

        broadcast.pause(1.2)


        # ====================================================
        # FINAL SYSTEM MESSAGE
        # ====================================================

        broadcast.static(0.25)

        broadcast.pause(0.3)

        await broadcast.say(
            "Nouzový protokol je aktivní."
        )

        broadcast.pause(1)

        await broadcast.say(
            "Čekám na autorizaci."
        )

        broadcast.pause(1)


        # ====================================================
        # END TONE
        # ====================================================

        broadcast.beep(
            frequency=1300,
            duration=0.18
        )

        broadcast.pause(0.12)

        broadcast.beep(
            frequency=1600,
            duration=0.18
        )

        broadcast.pause(0.4)

        broadcast.static(0.6)


        # ====================================================
        # EXPORT
        # ====================================================

        print()
        print("Creating final broadcast...")

        broadcast.export(
            OUTPUT_FILE
        )


    print()
    print("==========================================")
    print("HOTOVO")
    print("==========================================")
    print()

    print(
        "Soubor:",
        Path(OUTPUT_FILE).resolve()
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())
