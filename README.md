# DictWhisperer: Real-Time Voice Notes for Obsidian

DictWhisperer listens to your microphone, uses the powerful Whisper AI to transcribe your speech, and saves the text directly into a new note in your [Obsidian](https://obsidian.md/) vault. It's perfect for brainstorming, journaling, or capturing ideas without typing.

<br>

## How It Works (The Simple Version)

1.  You run the script from your computer's command line.
2.  It listens for you to speak, recording in 30-second chunks (this is adjustable!).
3.  Each chunk is instantly converted to text.
4.  The text is added to a new timestamped note in your Obsidian vault.
5.  When you're done, you press `Ctrl+C` to stop, and your note is saved.

<br>

---

## The Ultimate Beginner's Guide to a Working Setup

This guide is designed to be as simple as possible. Follow these steps exactly, and you'll have a working setup.

### Step 1: Install the Prerequisites

Before you can use the script, your computer needs three things.

<details>
<summary><strong>► Click here for instructions on how to install Git</strong></summary>

Git is a tool for downloading code. You may already have it. Open your terminal (on Mac, it's called Terminal; on Windows, PowerShell; on Linux, it may be called Terminal, Konsole, or similar) and type `git --version`. If you see a version number, you can skip to the next prerequisite. If not, follow these steps:

*   **Windows:** [Download and install Git for Windows](https://git-scm.com/download/win).
*   **macOS:** Open the Terminal app and run `xcode-select --install`.
*   **Linux (Ubuntu/Debian):** Open a terminal and run `sudo apt update && sudo apt install git`.
*   **Linux (Fedora/CentOS/RHEL):** Open a terminal and run `sudo dnf install git`.

</details>

<details>
<summary><strong>► Click here for instructions on how to install Python 3.13</strong></summary>

This project **requires Python version 3.13**. It will not work with other versions like 3.14. You may already have it. Open your terminal and type `python3.13 --version`. If you see "Python 3.13.x", you can skip to the next prerequisite.

*   **Windows:** [Download and install Python 3.13 from the official website](https://www.python.org/downloads/windows/). **Important:** During installation, make sure to check the box that says "Add Python to PATH".
*   **macOS:** The easiest way is using Homebrew. Open the Terminal app and run `brew install python@3.13`.
*   **Linux (Ubuntu/Debian):** You may need to add a special repository.
    ```bash
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.13 python3.13-venv
    ```
*   **Linux (Fedora/CentOS/RHEL):** Open a terminal and run `sudo dnf install python3.13`.

</details>

<details>
<summary><strong>► Click here for instructions on how to install FFmpeg</strong></summary>

FFmpeg is a required audio processing tool. You may already have it. Open your terminal and type `ffmpeg --version`. If you see version information, you are all set.

*   **Windows:** Follow this detailed [guide for installing FFmpeg on Windows](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/).
*   **macOS:** Open the Terminal app and run `brew install ffmpeg`.
*   **Linux (Ubuntu/Debian):** Open a terminal and run `sudo apt install ffmpeg`.
*   **Linux (Fedora/CentOS/RHEL):** Open a terminal and run `sudo dnf install ffmpeg`.

</details>

<br>

### Step 2: Download and Set Up the Project

Now, follow these 5 steps precisely. Open your terminal and run these commands one by one.

1.  **Download the Code:**
    This command copies the project files to your computer.
    ```bash
    git clone https://github.com/glozinc/Dict_Whisperer.git
    ```

2.  **Go Into the Project Directory:**
    ```bash
    cd Dict_Whisperer
    ```

3.  **Create a "Sandbox" Environment:**
    This command creates an isolated sandbox (called a virtual environment) so the project's dependencies don't interfere with your system.
    ```bash
    python3.13 -m venv .venv
    ```

4.  **Activate the Sandbox:**
    This "enters" the sandbox. You'll need to do this every time you open a new terminal to run the script. Your terminal prompt should change to show `(.venv)`.

    *   If you are on **macOS or Linux**:
        ```bash
        source .venv/bin/activate
        ```
    *   If you are on **Windows**:
        ```bash
        .venv\Scripts\activate
        ```

5.  **Install the Python Dependencies:**
    This command reads `requirements.txt` and installs all the necessary Python packages into your sandbox.
    ```bash
    python -m pip install -r requirements.txt
    ```

<br>

---

## Running the Application

Once you have completed all the setup steps, you can run the application.

1.  **Open a new terminal** and navigate to the project directory:
    ```bash
    cd path/to/your/Dict_Whisperer
    ```

2.  **Activate the virtual environment**:
    *   On macOS/Linux: `source .venv/bin/activate`
    *   On Windows: `.venv\Scripts\activate`

3.  **Run the script with the following command:**
    Be sure to replace `/path/to/your/Obsidian/Vault` with the actual, full path to your vault.
    ```bash
    python -m dictwhisperer.cli --vault-path "/path/to/your/Obsidian/Vault"
    ```
    *   **How to find your vault path:** In Obsidian, open Settings > About. You will see the "Vault path" listed there. You can copy it directly.

The script is now running! It will print status messages in the terminal. Start talking, and it will begin transcribing your speech into a new Markdown file in your vault.

### How to Stop the Script
The script will run forever until you stop it manually. To stop it, click on the terminal window where it is running and press the **`Ctrl+C`** keys on your keyboard.

<br>

---

## Customizing Your Dictation

You can change the behavior of the script by adding optional arguments to the run command.

### Choosing the Right AI Model (Speed vs. Accuracy)

Whisper offers several AI models with a trade-off between how fast they are and how accurate they are. You can choose a model using the `--model-size` argument. The default is `medium`.

**Example:** To use the faster `base` model, run:
```bash
python -m dictwhisperer.cli --vault-path "/path/to/your/Vault" --model-size base
```

Here are the available models:

| Model | Approx. Size | Speed | Accuracy | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `tiny` | ~75 MB | Very Fast | Basic | Good for quick notes if you speak clearly. |
| `base` | ~142 MB | Fast | Good | A great balance for most users. |
| `small` | ~466 MB | Moderate | Better | Good for transcribing with background noise. |
| `medium`| ~1.4 GB | Slow | **Great (Default)** | For when accuracy is critical (transcribing meetings, etc). |
| `large` | ~2.8 GB | Very Slow | Best | The most accurate model, requires a powerful computer. |

**Note:** The first time you use a new model, it will be downloaded automatically. This can take a while for the larger models.

### Adjusting the Recording Time (Chunk Size)

By default, the script records in 30-second chunks. You can change this with the `--chunk-duration` argument.

**Example:** To record in 10-second chunks, run:
```bash
python -m dictwhisperer.cli --vault-path "/path/to/your/Vault" --chunk-duration 10
```

*   **Shorter Duration (e.g., `3`)**
    *   **Advantage:** You see the transcribed text appear in your notes more quickly, feeling more "real-time".
    *   **Disadvantage:** Less context for the AI, which can sometimes reduce accuracy. More frequent processing can use more system resources.

*   **Longer Duration (e.g., `10` or `15`)**
    *   **Advantage:** Gives the AI more audio context, which can lead to more accurate and coherent transcriptions. More efficient processing.
    *   **Disadvantage:** You have to wait longer to see your speech appear in the note.

### Saving Notes to a Specific Folder

You can save your dictation notes into a specific folder inside your Obsidian vault (e.g., a "Journal" or "Inbox" folder).

To do this, simply add the folder's name to the end of your vault path. The folder **must already exist** in Obsidian.

**Example:**
Imagine your vault path is `/home/user/MyVault` and you have a folder inside it named `Daily Dictations`.

To save notes there, you would use this path:
```bash
python -m dictwhisperer.cli --vault-path "/home/user/MyVault/Daily Dictations"
```

---

## Troubleshooting

<details>
<summary><strong>► Error about "SHA256 checksum does not match" during model download?</strong></summary>

This means your internet connection was interrupted while downloading the AI model, and the file is now corrupt. The program may try to re-download it and fail again. If this happens repeatedly, you may need to download the model manually.

1.  **Download the file from this URL** using your web browser:
    *   [https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt](https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt)

2.  **Find the file** in your computer's `Downloads` folder. It should be named `base.pt`.

3.  **Move the `base.pt` file** into the whisper cache folder.
    *   The cache folder is hidden. On most systems, it is located at `~/.cache/whisper/`. You can navigate there by opening your file browser and selecting "Go to Folder" and pasting in that path.
    *   Place `base.pt` inside the `whisper` folder.

4.  **Run the application again.** It should now find the model locally and start right away.

</details>

<details>
<summary><strong>► Command `python3.13` not found?</strong></summary>
This means Python 3.13 is not installed or not available in your system's PATH. Please carefully follow the prerequisite instructions for installing Python 3.13 for your operating system.
</details>

<br>

Happy dictating! 🎙️
