import argparse
import os
import sys
import datetime
from pathlib import Path

from .dictwhisperer import (
    ensure_ffmpeg,
    check_audio_devices,
    record_audio,
    transcribe_and_append,
    load_whisper_model,
    DEFAULT_VAULT_PATH,
    DEFAULT_MODEL_SIZE,
    DEFAULT_CHUNK_DURATION,
)

try:
    import whisper
except ImportError:
    print("Error: openai-whisper is not installed.")
    print("Install it in your (supported) virtual environment with:")
    print()
    print("  pip install openai-whisper")
    sys.exit(1)


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
        help="Recording chunk duration in seconds (default: 20)",
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
        print(
            "  3. Set environment variable: "
            "export DICTWHISPERER_VAULT_PATH=/path/to/vault"
        )
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
                f"*Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
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
