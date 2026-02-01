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
*   **Visual Interface (GUI):** A clean interface built with PyQt6 to control dictation, view live transcripts, and manage settings.
*   **Configurable:** Adjust recording duration, model size (speed vs. accuracy), and vault location.

---

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.10 - 3.13:** (Note: Python 3.14 is not yet supported by Whisper).
2.  **FFmpeg:** Required for audio processing.
    *   **Windows:** [Install Guide](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)
    *   **macOS:** `brew install ffmpeg`
    *   **Linux:** `sudo apt install ffmpeg` or `sudo dnf install ffmpeg`
3.  **Git:** To download this repository.

### Installation & Usage (The Easy Way)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/80nF1R3H34D/Dict_Whisperer.git
    cd Dict_Whisperer
    ```

2.  **Run the automated setup script:**
    ```bash
    chmod +x run_dictwhisperer.sh
    ./run_dictwhisperer.sh
    ```
    This script will automatically:
    *   Create a virtual environment (`.venv`) if it doesn't exist.
    *   Install all dependencies (including PyQt6 and Whisper).
    *   Launch the GUI.

---

## 🎙️ Manual Usage

If you prefer to manage the environment yourself or use the CLI:

### 1. Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2. Run GUI
```bash
python -m dictwhisperer.gui
```

### 3. Run CLI
```bash
python -m dictwhisperer.cli --vault-path "/path/to/your/Obsidian/Vault"
```

---

## ⚙️ Configuration

You can customize DictWhisperer using the GUI settings or command-line arguments.

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--vault-path` | (Required*) | Path to your Obsidian vault. |
| `--model-size` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). |
| `--chunk-duration` | `20` | Duration (in seconds) of each recording segment. |

*\*Can be set via environment variable `DICTWHISPERER_VAULT_PATH`.*

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
