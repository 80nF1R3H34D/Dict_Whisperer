
import unittest
from unittest.mock import MagicMock, patch
import threading
import time
import os
import shutil
import numpy as np

# Mock dependencies before importing the module
sys_modules_patch = patch.dict('sys.modules', {
    'sounddevice': MagicMock(),
    'whisper': MagicMock(),
})
sys_modules_patch.start()

# Now import the class
from dictwhisperer.dictwhisperer import DictationSession

class TestDictationSession(unittest.TestCase):
    def setUp(self):
        self.mock_vault = "/tmp/test_vault"
        os.makedirs(self.mock_vault, exist_ok=True)
        self.session = DictationSession(
            vault_path=self.mock_vault,
            model_size="tiny",
            chunk_duration=1
        )
        # Mock internal helpers to avoid system checks
        self.session._ensure_ffmpeg = MagicMock()
        self.session._check_audio_devices = MagicMock()
        self.session._load_whisper_model = MagicMock()
        
        # Mock callbacks
        self.session.on_status_change = MagicMock()
        self.session.on_progress = MagicMock()
        self.session.on_transcription = MagicMock()
        self.session.on_error = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.mock_vault, ignore_errors=True)
        sys_modules_patch.stop()

    def test_initialize(self):
        self.session.initialize()
        self.session._ensure_ffmpeg.assert_called_once()
        self.session.on_status_change.assert_any_call("Ready.")
        self.assertTrue(os.path.exists(self.session.md_filename))

    @patch('dictwhisperer.dictwhisperer.sd')
    def test_record_loop(self, mock_sd):
        self.session.initialize()
        
        # Setup mock recording
        mock_sd.rec.return_value = np.zeros(16000, dtype='int16') # 1 sec silence
        mock_sd.get_status().active = False # Finish immediately
        
        # Start in thread
        self.session.start()
        time.sleep(0.5)
        self.assertTrue(self.session.is_running)
        
        # Stop
        self.session.stop()
        self.assertFalse(self.session.is_running)
        
        # Check callbacks
        # Since we mocked silence, it might not transcribe, depending on threshold.
        # But start/stop status should be logged.
        self.session.on_status_change.assert_any_call("Dictation started.")
        self.session.on_status_change.assert_any_call("Dictation stopped.")

if __name__ == '__main__':
    unittest.main()
