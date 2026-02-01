#!/usr/bin/env python3
"""
Command-line interface for DictWhisperer.
"""

import argparse
import sys
import os
import time
from .dictwhisperer import (
    DictationSession,
    DEFAULT_VAULT_PATH,
    DEFAULT_MODEL_SIZE,
    DEFAULT_CHUNK_DURATION,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Dictate to Obsidian via Whisper - Real-time voice transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vault-path ~/Documents/ObsidianVault
  %(prog)s --model-size small --chunk-duration 10

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
        help="Whisper model size (default: base)",
        choices=["tiny", "base", "small", "medium", "large"],
        default=os.environ.get("DICTWHISPERER_MODEL_SIZE", DEFAULT_MODEL_SIZE),
    )

    parser.add_argument(
        "--chunk-duration",
        type=int,
        help="Recording chunk duration in seconds (default: 20)",
        default=int(
            os.environ.get("DICTWHISPERER_CHUNK_DURATION", DEFAULT_CHUNK_DURATION)
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the application."""
    args = parse_args()

    # Callbacks for CLI output
    def on_status_change(msg: str):
        print(f"[dictwhisperer] {msg}")

    def on_progress(msg: str):
        # Overwrite the current line for progress
        sys.stdout.write(f"\r[dictwhisperer] {msg}   ")
        sys.stdout.flush()

    def on_transcription(text: str):
        # Clear the progress line before printing result
        sys.stdout.write("\r") 
        print(f"[dictwhisperer] Added: {text}")

    def on_error(msg: str):
        print(f"\n[dictwhisperer] Error: {msg}")

    print("[dictwhisperer] Starting CLI...")

    session = DictationSession(
        vault_path=args.vault_path,
        model_size=args.model_size,
        chunk_duration=args.chunk_duration,
        on_status_change=on_status_change,
        on_progress=on_progress,
        on_transcription=on_transcription,
        on_error=on_error,
    )

    try:
        session.initialize()
        print(f"[dictwhisperer] Recording in {args.chunk_duration}-second chunks.")
        print("[dictwhisperer] Press Ctrl+C to stop.\n")
        
        session.start()
        
        # Keep main thread alive
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[dictwhisperer] Stopping...")
        session.stop()
        print("[dictwhisperer] Session ended.")
    except Exception as e:
        print(f"[dictwhisperer] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
