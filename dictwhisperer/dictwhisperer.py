#!/usr/bin/env python3
"""
dictwhisperer - Real-time voice dictation to Obsidian using OpenAI Whisper.

This module contains the core functionality for recording audio, processing it,
and transcribing it using the Whisper model.
"""

import itertools
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Any

import numpy as np
import sounddevice as sd

# ---------------------------------------------------------------------------
# Python version check
# ---------------------------------------------------------------------------
MIN_SUPPORTED = (3, 10)
MAX_SUPPORTED = (3, 14)

if not (MIN_SUPPORTED <= sys.version_info < MAX_SUPPORTED):
    print("Error: Unsupported Python version for Whisper/numba.")
    print(f"Current version : {sys.version.split()[0]}")
    print("Supported range : >=3.10,<3.14")
    sys.exit(1)

try:
    import whisper
except ImportError:
    print("Error: openai-whisper is not installed.")
    print("Install it via pip install openai-whisper")
    sys.exit(1)


# Default configuration
DEFAULT_VAULT_PATH = "/path/to/your/Obsidian/Vault"
DEFAULT_MODEL_SIZE = "base"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_DURATION = 20  # seconds


def load_whisper_model(model_size: str) -> Any:
    """
    Load a Whisper model, downloading it to a persistent directory if needed.

    Args:
        model_size (str): Size of the model (tiny, base, small, medium, large).

    Returns:
        The loaded Whisper model instance.
    """
    project_root = Path(__file__).resolve().parent.parent
    model_dir = project_root / "models"
    model_dir.mkdir(exist_ok=True)

    model_file = model_dir / f"{model_size}.pt"
    
    print(f"[dictwhisperer] Loading Whisper model '{model_size}'...")
    if not model_file.exists():
        print(f"[dictwhisperer] (First run for '{model_size}' will download the model to {model_dir})")
    
    try:
        # download_root directs where the model file is stored/looked for
        return whisper.load_model(model_size, download_root=str(model_dir))
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        sys.exit(1)


def ensure_ffmpeg() -> None:
    """
    Check if ffmpeg is available in the system PATH.
    Terminates execution if not found.
    """
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found in PATH.")
        print("Whisper requires ffmpeg for audio processing.")
        sys.exit(1)


def check_audio_devices() -> None:
    """
    Check if any audio input devices are available.
    Terminates execution if no input devices are found.
    """
    try:
        devices = sd.query_devices()
        if not devices:
            print("Error: No audio devices found.")
            sys.exit(1)

        has_input = any(d["max_input_channels"] > 0 for d in devices)
        if not has_input:
            print("Error: No audio input devices (microphones) found.")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking audio devices: {e}")
        sys.exit(1)


def countdown_animation(duration: int, stop_event: threading.Event) -> None:
    """
    Display a countdown timer matching the recording duration.

    Args:
        duration (int): The total duration in seconds.
        stop_event (threading.Event): Event to signal when to stop the animation.
    """
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
    Record audio from the default microphone.

    Args:
        duration (int): Recording duration in seconds.
        samplerate (int): Audio sample rate in Hz.
        channels (int): Number of audio channels.

    Returns:
        np.ndarray: Recorded audio data.
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
        sd.stop()
        stop_event.set()
        print("\n[dictwhisperer] Recording interrupted.")
        raise
    except Exception as e:
        sd.stop()
        stop_event.set()
        print(f"\n[dictwhisperer] Error recording audio: {e}")
        raise


def transcribe_and_append(audio_data: np.ndarray, md_filename: Path, model: Any) -> None:
    """
    Transcribe audio data and append the text to a Markdown file.

    Args:
        audio_data (np.ndarray): Audio data to transcribe.
        md_filename (Path): Path to the Markdown file.
        model (Any): Loaded Whisper model instance.
    """
    try:
        # Whisper expects a 1D float array normalized between -1 and 1
        audio_float = audio_data.flatten().astype(np.float32) / 32768.0

        # Simple Voice Activity Detection (VAD) based on RMS amplitude
        rms = np.sqrt(np.mean(audio_float**2))
        threshold = 0.005  # Silence threshold

        if rms < threshold:
            print(f"[dictwhisperer] Silence detected (RMS: {rms:.4f} < {threshold}). Skipping.")
            return

        print("[dictwhisperer] Transcribing... (App is NOT listening now)")
        
        # Explicitly disable fp16 to avoid warnings on CPU
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
