#!/usr/bin/env python3
"""
GUI for DictWhisperer using PyQt6.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QObject, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

from .dictwhisperer import (
    DictationSession,
    DEFAULT_VAULT_PATH,
    DEFAULT_MODEL_SIZE,
    DEFAULT_CHUNK_DURATION,
)


class MainWindow(QMainWindow):
    # Signals to update UI from background threads
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)
    transcription_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DictWhisperer")
        self.resize(600, 700)

        self.session = None
        self.is_recording = False

        # --- UI Setup ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Status Section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(16)
        status_font.setBold(True)
        self.lbl_status.setFont(status_font)
        status_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # 2. Transcription Log
        log_group = QGroupBox("Live Transcript")
        log_layout = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)

        # 3. Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()

        self.edt_vault_path = QLineEdit(
            os.environ.get("DICTWHISPERER_VAULT_PATH", DEFAULT_VAULT_PATH)
        )
        config_layout.addRow("Vault Path:", self.edt_vault_path)

        self.cmb_model_size = QComboBox()
        self.cmb_model_size.addItems(["tiny", "base", "small", "medium", "large"])
        default_model = os.environ.get("DICTWHISPERER_MODEL_SIZE", DEFAULT_MODEL_SIZE)
        self.cmb_model_size.setCurrentText(default_model)
        config_layout.addRow("Model Size:", self.cmb_model_size)

        self.edt_duration = QLineEdit(
            str(os.environ.get("DICTWHISPERER_CHUNK_DURATION", DEFAULT_CHUNK_DURATION))
        )
        config_layout.addRow("Chunk Duration (s):", self.edt_duration)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # 4. Controls
        controls_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Dictation")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.btn_start)

        self.btn_quit = QPushButton("Quit")
        self.btn_quit.setMinimumHeight(50)
        self.btn_quit.clicked.connect(QApplication.instance().quit)
        controls_layout.addWidget(self.btn_quit)

        main_layout.addLayout(controls_layout)

        # Connect Signals
        self.status_signal.connect(self.update_status)
        self.progress_signal.connect(self.update_progress)
        self.transcription_signal.connect(self.append_transcript)
        self.error_signal.connect(self.show_error)

    def toggle_recording(self):
        if self.is_recording:
            # Stop
            self.stop_session()
        else:
            # Start
            self.start_session()

    def start_session(self):
        vault_path = self.edt_vault_path.text()
        model_size = self.cmb_model_size.currentText()
        try:
            duration = int(self.edt_duration.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Chunk duration must be an integer.")
            return

        # Disable inputs
        self.enable_inputs(False)
        self.btn_start.setText("Stop Dictation")
        self.txt_log.clear()
        
        # Set indeterminate progress for initialization
        self.progress_bar.setRange(0, 0)

        self.session = DictationSession(
            vault_path=vault_path,
            model_size=model_size,
            chunk_duration=duration,
            on_status_change=self.status_signal.emit,
            on_progress=self.progress_signal.emit,
            on_transcription=self.transcription_signal.emit,
            on_error=self.error_signal.emit,
        )

        try:
            # Run initialize in a separate thread if it takes too long? 
            # For now, we'll risk a slight blocking for FFmpeg check, but download might block.
            # Ideally initialize should be async too. 
            # But the session.start() is async.
            # Loading model is heavy. Let's do it in the session start thread?
            # The refactoring had initialize() separate.
            # We will run initialize and start in a background thread to avoid freezing GUI during model load.
            
            import threading
            t = threading.Thread(target=self._background_start)
            t.daemon = True
            t.start()
            
        except Exception as e:
            self.show_error(str(e))
            self.reset_ui()

    def _background_start(self):
        try:
            self.status_signal.emit("Initializing & Loading Model...")
            if self.session:
                self.session.initialize()
                self.session.start()
                self.is_recording = True
        except Exception as e:
            self.error_signal.emit(str(e))
            # We can't call self.reset_ui() directly from thread
            # relying on error_signal connection

    def stop_session(self):
        self.status_signal.emit("Stopping...")
        if self.session:
            self.session.stop()
        
        self.is_recording = False
        self.reset_ui()

    def reset_ui(self):
        self.enable_inputs(True)
        self.btn_start.setText("Start Dictation")
        self.progress_bar.setValue(0)
        self.is_recording = False

    def enable_inputs(self, enabled: bool):
        self.edt_vault_path.setEnabled(enabled)
        self.cmb_model_size.setEnabled(enabled)
        self.edt_duration.setEnabled(enabled)

    @pyqtSlot(str)
    def update_status(self, msg: str):
        self.lbl_status.setText(msg)

    @pyqtSlot(str)
    def update_progress(self, msg: str):
        self.lbl_status.setText(msg)
        
        if "Recording" in msg:
            try:
                duration = int(self.edt_duration.text())
                # Switch to determinate progress
                self.progress_bar.setRange(0, duration)
                
                # msg format: "Recording: 15s" (meaning 15s remaining)
                # Find the number
                parts = msg.split() 
                for p in parts:
                    if "s" in p and p.replace('s','').isdigit():
                        remaining = int(p.replace('s',''))
                        # Fill the bar as time passes
                        self.progress_bar.setValue(duration - remaining)
                        break
            except:
                pass
        elif "Downloading" in msg:
            # Format: "Downloading: 45.2%"
            try:
                parts = msg.split()
                for p in parts:
                    if "%" in p:
                        val = float(p.replace('%', ''))
                        self.progress_bar.setRange(0, 100)
                        self.progress_bar.setValue(int(val))
                        break
            except:
                self.progress_bar.setRange(0, 0) # indeterminate if parsing fails
        elif "Processing" in msg or "Initializing" in msg or "Loading" in msg:
            # Indeterminate for processing/initialization
            self.progress_bar.setRange(0, 0)
        else:
            # Reset
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    @pyqtSlot(str)
    def append_transcript(self, text: str):
        self.txt_log.append(text)

    @pyqtSlot(str)
    def show_error(self, msg: str):
        QMessageBox.critical(self, "Error", msg)
        self.reset_ui()


def main():
    app = QApplication(sys.argv)
    
    # Optional: Set distinct style/palette if requested, but system default is usually best for Linux
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
