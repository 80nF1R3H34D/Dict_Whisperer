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
from typing import Optional, Any, Callable

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


class DictationSession:
    """
    Manages a dictation session, handling audio recording and transcription.
    """

    def __init__(
        self,
        vault_path: str,
        model_size: str = DEFAULT_MODEL_SIZE,
        chunk_duration: int = DEFAULT_CHUNK_DURATION,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the dictation session.

        Args:
            vault_path: Path to the Obsidian vault.
            model_size: Whisper model size.
            chunk_duration: Duration of each recording chunk in seconds.
            on_status_change: Callback for general status messages.
            on_progress: Callback for progress updates (e.g., countdown).
            on_transcription: Callback when text is successfully transcribed.
            on_error: Callback for error messages.
        """
        self.vault_path = Path(os.path.expanduser(vault_path)).resolve()
        self.model_size = model_size
        self.chunk_duration = chunk_duration
        self.on_status_change = on_status_change or (lambda x: None)
        self.on_progress = on_progress or (lambda x: None)
        self.on_transcription = on_transcription or (lambda x: None)
        self.on_error = on_error or (lambda x: None)

        self.model = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.md_filename = None

    def initialize(self):
        """Perform pre-flight checks and load the model."""
        self.on_status_change("Initializing...")
        self.on_progress("Initializing: Checking system...")
        
        # System checks
        self._ensure_ffmpeg()
        self._check_audio_devices()

        # Validate vault
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Obsidian vault path does not exist: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise NotADirectoryError(f"Vault path is not a directory: {self.vault_path}")

        # Create session file
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.md_filename = self.vault_path / f"LiveDictation_{timestamp}.md"
        try:
            with open(self.md_filename, "w", encoding="utf-8") as f:
                f.write(f"# Live Dictation - {timestamp}\n\n")
                f.write(f"*Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            self.on_status_change(f"Created file: {self.md_filename.name}")
        except Exception as e:
            raise IOError(f"Cannot write to vault path: {e}")

        # Download Model if needed
        self._ensure_model_downloaded()

        # Load model
        self.on_status_change(f"Loading Whisper model '{self.model_size}' into memory...")
        self.on_progress("Loading model...")
        self.model = self._load_whisper_model(self.model_size)
        self.on_status_change("Ready.")
        self.on_progress("Ready to dictate.")

    def _ensure_model_downloaded(self):
        """Check if model exists, if not, download with progress."""
        project_root = Path(__file__).resolve().parent.parent
        model_dir = project_root / "models"
        model_dir.mkdir(exist_ok=True)
        
        # Whisper stores models as "name.pt" usually, but let's check standard behavior.
        # We will use whisper's internal logic to get the URL, but handle download manually.
        try:
            import urllib.request
            url = whisper._MODELS[self.model_size]
            filename = url.split("/")[-1]
            target_path = model_dir / filename
            
            if target_path.exists():
                # We could check SHA256 here, but for now assume existence is enough for speed
                # or let whisper verify it later.
                return

            self.on_status_change(f"Downloading model '{self.model_size}'...")
            
            def report_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = (block_num * block_size * 100) / total_size
                    self.on_progress(f"Downloading: {percent:.1f}%")
            
            print(f"[dictwhisperer] Downloading {url} to {target_path}")
            urllib.request.urlretrieve(url, target_path, reporthook=report_hook)
            self.on_progress("Download complete.")
            
        except Exception as e:
            # Fallback to default whisper download if manual fails
            print(f"Manual download failed: {e}. Falling back to default.")
            pass

    def _load_whisper_model(self, model_size: str) -> Any:
        try:
            project_root = Path(__file__).resolve().parent.parent
            model_dir = project_root / "models"
            model_dir.mkdir(exist_ok=True)
            return whisper.load_model(model_size, download_root=str(model_dir))
        except Exception as e:
            raise RuntimeError(f"Error loading Whisper model: {e}")

    def start(self):
        """Start the dictation loop in a background thread."""
        if self.is_running:
            return

        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.on_status_change("Dictation started.")

    def stop(self):
        """Stop the dictation loop."""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        self.on_status_change("Dictation stopped.")

    def _run_loop(self):
        """Main recording loop."""
        try:
            while self.is_running and not self.stop_event.is_set():
                audio_data = self._record_audio(duration=self.chunk_duration)
                if self.stop_event.is_set():
                    break
                self._transcribe_and_append(audio_data)
        except Exception as e:
            self.on_error(f"Error in dictation loop: {e}")
            self.is_running = False

    def _record_audio(self, duration: int, samplerate: int = DEFAULT_SAMPLE_RATE, channels: int = DEFAULT_CHANNELS) -> np.ndarray:
        """Record audio with progress updates."""
        try:
            start_time = time.time()
            
            # Start recording
            audio = sd.rec(
                int(duration * samplerate),
                samplerate=samplerate,
                channels=channels,
                dtype="int16",
            )
            
            # Progress loop while recording
            while time.time() - start_time < duration:
                if self.stop_event.is_set():
                    sd.stop()
                    return np.array([]) # Return empty array on stop

                elapsed = time.time() - start_time
                remaining = max(0, duration - elapsed)
                self.on_progress(f"Recording: {int(np.ceil(remaining))}s")
                time.sleep(0.1)
                
            sd.wait()
            self.on_progress("Processing...")
            return audio

        except Exception as e:
            self.on_error(f"Error recording audio: {e}")
            raise

    def _transcribe_and_append(self, audio_data: np.ndarray) -> None:
        """Transcribe audio and append to file."""
        if audio_data.size == 0:
            return

        try:
            # Whisper expects a 1D float array normalized between -1 and 1
            audio_float = audio_data.flatten().astype(np.float32) / 32768.0

            # Simple Voice Activity Detection (VAD) based on RMS amplitude
            rms = np.sqrt(np.mean(audio_float**2))
            threshold = 0.005  # Silence threshold

            if rms < threshold:
                # self.on_status_change(f"Silence detected (RMS: {rms:.4f}). Skipping.")
                return

            self.on_status_change("Transcribing...")
            
            # Explicitly disable fp16 to avoid warnings on CPU
            result = self.model.transcribe(audio_float, fp16=False)
            text = result["text"].strip()

            if text:
                with open(self.md_filename, "a", encoding="utf-8") as f:
                    f.write(f" {text}")
                self.on_transcription(text)
                self.on_status_change("Transcribed.")
            # else:
            #     self.on_status_change("No speech detected.")

        except Exception as e:
            self.on_error(f"Error during transcription: {e}")

    def _ensure_ffmpeg(self) -> None:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found in PATH. Whisper requires ffmpeg.")

    def _check_audio_devices(self) -> None:
        try:
            devices = sd.query_devices()
            if not devices:
                raise RuntimeError("No audio devices found.")
            has_input = any(d["max_input_channels"] > 0 for d in devices)
            if not has_input:
                raise RuntimeError("No audio input devices (microphones) found.")
        except Exception as e:
            raise RuntimeError(f"Error checking audio devices: {e}")


# Backwards compatibility wrappers for direct module usage if needed, 
# though CLI should use the class now.
def ensure_ffmpeg():
    DictationSession(".")._ensure_ffmpeg()

def check_audio_devices():
    DictationSession(".")._check_audio_devices()
