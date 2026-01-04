
#!/usr/bin/env python3
"""
dictwhisperer - Real-time voice dictation to Obsidian using OpenAI Whisper.

This script records audio from your microphone in chunks, transcribes it using
Whisper, and appends the text to a Markdown file in your Obsidian vault.
"""

import argparse
import datetime
import os
import shutil
import sys
import tempfile
import threading
import time
import wave
import itertools
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd

# ---------------------------------------------------------------------------
# Python version check: Whisper/numba currently supports >=3.10,<3.14
# ---------------------------------------------------------------------------

MIN_SUPPORTED = (3, 10)
MAX_SUPPORTED = (3, 14)  # strictly less than this

if not (MIN_SUPPORTED <= sys.version_info < MAX_SUPPORTED):
    print("Error: Unsupported Python version for Whisper/numba.")
    print(f"Current version : {sys.version.split()[0]}")
    print("Supported range : >=3.10,<3.14")
    print()
    print("Please create and activate a virtual environment with a supported")
    print("Python version. For example on Fedora (if python3.13 is available):")
    print()
    print("  python3.13 -m venv .venv")
    print("  source .venv/bin/activate")
    print("  pip install --upgrade pip")
    print("  pip install -r requirements.txt")
    print()
    print("If you already have a working environment (e.g. 'whisper-env'),")
    print("you can simply activate it and run this script inside it:")
    print()
    print("  source ~/whisper-env/bin/activate")
    print("  python dictwhisperer.py --vault-path /path/to/your/vault")
    sys.exit(1)

try:
    import whisper
except ImportError:
    print("Error: openai-whisper is not installed.")
    print("Install it in your (supported) virtual environment with:")
    print()
    print("  pip install openai-whisper")
    sys.exit(1)


# Default configuration
DEFAULT_VAULT_PATH = "/path/to/your/Obsidian/Vault"
DEFAULT_MODEL_SIZE = "base"  # Changed from medium to base for speed
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_DURATION = 20  # seconds per recording chunk


def load_whisper_model(model_size: str):
    """
    Load a Whisper model, downloading it to a persistent directory if needed.
    """
    project_root = Path(__file__).parent.parent
    model_dir = project_root / "models"
    model_dir.mkdir(exist_ok=True)

    model_file = model_dir / f"{model_size}.pt"
    
    print(f"[dictwhisperer] Loading Whisper model '{model_size}'...")
    if not model_file.exists():
        print(f"[dictwhisperer] (First run for '{model_size}' will download the model to {model_dir})")
    
    try:
        import whisper
        return whisper.load_model(model_size, download_root=str(model_dir))
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        sys.exit(1)


def ensure_ffmpeg() -> None:
    """Check if ffmpeg is available in PATH."""
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found in PATH.")
        print("Whisper requires ffmpeg for audio processing.")
        print()
        print("Install ffmpeg, for example:")
        print("  Fedora/RHEL : sudo dnf install ffmpeg")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS       : brew install ffmpeg")
        sys.exit(1)

def check_audio_devices() -> None:
    """Check if any audio input devices are available."""
    try:
        devices = sd.query_devices()
        if not devices:
            print("Error: No audio devices found.")
            sys.exit(1)

        # Check for input devices specifically
        has_input = any(d["max_input_channels"] > 0 for d in devices)
        if not has_input:
            print("Error: No audio input devices (microphones) found.")
            print("Please connect a microphone and try again.")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking audio devices: {e}")
        sys.exit(1)

def countdown_animation(duration: int, stop_event: threading.Event) -> None:
    """Display a countdown timer matching the recording duration."""
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        remaining = max(0, duration - elapsed)
        
        sys.stdout.write(f"\r[dictwhisperer] Recording: {int(np.ceil(remaining))}s...   ")
        sys.stdout.flush()
        
        time.sleep(0.1)
    
    sys.stdout.write("\r[dictwhisperer] Recording: Complete.   \n")
    sys.stdout.flush()

def record_audio(
    duration: int = DEFAULT_CHUNK_DURATION,
    samplerate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
) -> np.ndarray:
    """
    Record audio from the default microphone and return as a NumPy array.

    Args:
        duration: Recording duration in seconds
        samplerate: Audio sample rate in Hz
        channels: Number of audio channels (1 for mono, 2 for stereo)

    Returns:
        Audio data as a NumPy array
    """
    stop_event = threading.Event()
    try:
        # Start countdown thread
        timer_thread = threading.Thread(
            target=countdown_animation, args=(duration, stop_event)
        )
        timer_thread.daemon = True
        timer_thread.start()

        # Start recording
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=channels,
            dtype="int16",
        )
        
        # Wait for recording to finish
        sd.wait()

        stop_event.set()
        timer_thread.join()

        return audio

    except KeyboardInterrupt:
        sd.stop()  # Ensure recording stops immediately
        stop_event.set()
        print("\n[dictwhisperer] Recording interrupted.")
        raise
    except Exception as e:
        sd.stop()  # Ensure recording stops on error
        stop_event.set()
        print(f"\n[dictwhisperer] Error recording audio: {e}")
        raise

def transcribe_and_append(audio_data: np.ndarray, md_filename: str, model) -> None:
    """
    Transcribe an audio array using Whisper and append text to a Markdown file.

    Args:
        audio_data: Audio data as a NumPy array
        md_filename: Path to the Markdown file to append to
        model: Loaded Whisper model instance
    """
    try:
        # Whisper expects a 1D float array normalized between -1 and 1
        audio_float = audio_data.flatten().astype(np.float32) / 32768.0

        # Simple Voice Activity Detection (VAD) based on RMS amplitude
        rms = np.sqrt(np.mean(audio_float**2))
        threshold = 0.005  # Adjustable threshold for silence

        if rms < threshold:
            print(f"[dictwhisperer] Silence detected (RMS: {rms:.4f} < {threshold}). Skipping.")
            return

        print("[dictwhisperer] Transcribing... (App is NOT listening now)")
        result = model.transcribe(audio_float, fp16=False)
        text = result["text"].strip()

        if text:
            with open(md_filename, "a", encoding="utf-8") as f:
                f.write(f" {text}")
            print(f"[dictwhisperer] Added: {text}")
        else:
            print("[dictwhisperer] No speech detected in this chunk.")
    except Exception as e:
        print(f"[dictwhisperer] Error during transcription: {e}")

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Dictate to Obsidian via Whisper - real-time voice transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s --vault-path ~/Documents/ObsidianVault
  %(prog)s --model-size small --chunk-duration 3

Environment variables:
  DICTWHISPERER_VAULT_PATH     Path to Obsidian vault
  DICTWHISPERER_MODEL_SIZE     Whisper model size (tiny, base, small, medium, large)
  DICTWHISPERER_CHUNK_DURATION Recording chunk duration in seconds
        """,
    )

    parser.add_argument(
        "--vault-path",
        help="Path to your Obsidian vault (default: from env or config)",
        default=os.environ.get("DICTWHISPERER_VAULT_PATH", DEFAULT_VAULT_PATH),
    )

    parser.add_argument(
        "--model-size",
        help="Whisper model size: tiny, base, small, medium, large (default: base)",
        choices=["tiny", "base", "small", "medium", "large"],
        default=os.environ.get("DICTWHISPERER_MODEL_SIZE", DEFAULT_MODEL_SIZE),
    )

    parser.add_argument(
        "--chunk-duration",
        type=int,
        help="Recording chunk duration in seconds (default: 5)",
        default=int(
            os.environ.get("DICTWHISPERER_CHUNK_DURATION", DEFAULT_CHUNK_DURATION)
        ),
    )

    return parser.parse_args()

def main() -> None:
    """Main entry point for dictwhisperer."""
    args = parse_args()

    # Pre-flight checks
    print("[dictwhisperer] Starting pre-flight checks...")
    ensure_ffmpeg()
    check_audio_devices()

    # Validate vault path
    vault_path = os.path.expanduser(args.vault_path)
    if not os.path.exists(vault_path):
        print(f"Error: Obsidian vault path does not exist: {vault_path}")
        print()
        print("Please either:")
        print("  1. Edit the script and set DEFAULT_VAULT_PATH")
        print("  2. Use --vault-path /path/to/vault")
        print("  3. Set environment variable: "
              "export DICTWHISPERER_VAULT_PATH=/path/to/vault")
        sys.exit(1)

    if not os.path.isdir(vault_path):
        print(f"Error: Vault path is not a directory: {vault_path}")
        sys.exit(1)

    if not os.access(vault_path, os.W_OK):
        print(f"Error: Vault path is not writable: {vault_path}")
        sys.exit(1)

    # Prepare Markdown file
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    md_filename = Path(vault_path) / f"LiveDictation_{timestamp}.md"

    try:
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write("# Live Dictation\n\n")
            f.write(
                f"*Created: "
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            )
    except Exception as e:
        print(f"Error: Cannot write to vault path: {e}")
        sys.exit(1)

    print(f"[dictwhisperer] Markdown file created: {md_filename}")

    model = load_whisper_model(args.model_size)

    print("[dictwhisperer] Model loaded successfully!")
    print(f"[dictwhisperer] Recording in {args.chunk_duration}-second chunks.")
    print("[dictwhisperer] Press Ctrl+C to stop.\n")

    # Main recording loop
    try:
        while True:
            audio_data = record_audio(duration=args.chunk_duration)
            transcribe_and_append(audio_data, md_filename, model)

    except KeyboardInterrupt:
        print("\n\n[dictwhisperer] Dictation session ended.")
        print(f"[dictwhisperer] Final transcript saved at: {md_filename}")
    except Exception as e:
        print(f"\n[dictwhisperer] Unexpected error: {e}")
        print(f"[dictwhisperer] Partial transcript saved at: {md_filename}")
        sys.exit(1)


if __name__ == "__main__":
    main()
