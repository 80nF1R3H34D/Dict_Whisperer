# DictWhisperer: AI-Powered Voice Notes for Obsidian

DictWhisperer is a powerful, local-first voice dictation tool. It listens to your microphone, uses OpenAI's Whisper AI to transcribe your speech with high accuracy, and appends the text directly into a new note in your [Obsidian](https://obsidian.md/) vault.

It operates in **chunks** (default: 20 seconds), allowing for near real-time transcription while maintaining context for better accuracy.

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

*   **Local & Private:** Everything runs on your machine. No audio is sent to the cloud.
*   **Direct to Obsidian:** Creates a new Markdown file for each session and appends text as you speak.
*   **Smart Caching:** Whisper models are downloaded once and cached locally to `models/`.
*   **Silence Detection:** Automatically ignores quiet periods to prevent "hallucinations" (e.g., "Thanks for watching").
*   **Visual Feedback:** A live countdown timer shows you exactly when the app is recording and when it is processing.
*   **Configurable:** Adjust recording duration, model size (speed vs. accuracy), and vault location via command-line arguments or environment variables.

---

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.10 - 3.13:** (Note: Python 3.14 is not yet supported by Whisper).
2.  **FFmpeg:** Required for audio processing.
    *   **Windows:** [Install Guide](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)
    *   **macOS:** `brew install ffmpeg`
    *   **Linux:** `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`
3.  **Git:** To download this repository.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/80nF1R3H34D/Dict_Whisperer.git
    cd Dict_Whisperer
    ```

2.  **Create a virtual environment (Recommended):**
    ```bash
    # Linux/macOS
    python3.13 -m venv .venv
    source .venv/bin/activate

    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎙️ Usage

1.  **Activate your virtual environment** (if not already active).
2.  **Run the CLI tool:**

    ```bash
    python -m dictwhisperer.cli --vault-path "/path/to/your/Obsidian/Vault"
    ```

    *Replace `/path/to/your/Obsidian/Vault` with the actual path to your vault.*

3.  **Speak!** The app will record in 20-second chunks. A countdown will appear. When the countdown finishes, it transcribes and appends the text to your note.
4.  **Stop:** Press `Ctrl+C` to end the session.

---

## ⚙️ Configuration

You can customize DictWhisperer using command-line arguments.

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--vault-path` | (Required*) | Path to your Obsidian vault. |
| `--model-size` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). |
| `--chunk-duration` | `20` | Duration (in seconds) of each recording segment. |

*\*Can be set via environment variable `DICTWHISPERER_VAULT_PATH`.*

### Examples

**Use a faster, less accurate model:**
```bash
python -m dictwhisperer --model-size tiny --vault-path "..."
```

**Use a larger, more accurate model (slower):**
```bash
python -m dictwhisperer --model-size medium --vault-path "..."
```

**Record in 30-second chunks:**
```bash
python -m dictwhisperer --chunk-duration 30 --vault-path "..."
```

### Environment Variables

You can set these variables in your shell profile (e.g., `.bashrc`, `.zshrc`) to avoid typing them every time:

*   `DICTWHISPERER_VAULT_PATH`
*   `DICTWHISPERER_MODEL_SIZE`
*   `DICTWHISPERER_CHUNK_DURATION`

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
