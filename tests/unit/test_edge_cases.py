import os
import sys
import unittest
import numpy as np
import pathlib
from scipy.io import wavfile

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.session_engine import (
    validate_and_load_session_audio,
    AudioValidationError
)
from server import app

class TestVoxFlowEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.scratch_dir = ROOT_DIR / "data" / "scratch_tests"
        os.makedirs(cls.scratch_dir, exist_ok=True)

    def test_short_session_rejected(self):
        # 15.0 second audio (< 30.0s)
        sr = 16000
        audio = (0.2 * np.sin(2 * np.pi * 300 * np.linspace(0, 15.0, 15 * sr)) * 32767).astype(np.int16)
        path = self.scratch_dir / "short_15s.wav"
        wavfile.write(path, sr, audio)

        with self.assertRaises(AudioValidationError) as ctx:
            validate_and_load_session_audio(path)
        self.assertIn("below the minimum required", str(ctx.exception))

    def test_long_session_rejected(self):
        # 65.0 second audio (> 60.0s)
        sr = 16000
        audio = (0.2 * np.sin(2 * np.pi * 300 * np.linspace(0, 65.0, 65 * sr)) * 32767).astype(np.int16)
        path = self.scratch_dir / "long_65s.wav"
        wavfile.write(path, sr, audio)

        with self.assertRaises(AudioValidationError) as ctx:
            validate_and_load_session_audio(path)
        self.assertIn("exceeds standard prototype maximum", str(ctx.exception))

    def test_silence_rejected(self):
        # 35.0 seconds of dead silence
        sr = 16000
        audio = np.zeros(35 * sr, dtype=np.int16)
        path = self.scratch_dir / "silence_35s.wav"
        wavfile.write(path, sr, audio)

        with self.assertRaises(AudioValidationError) as ctx:
            validate_and_load_session_audio(path)
        self.assertIn("silence", str(ctx.exception).lower())

    def test_corrupt_file_rejected(self):
        path = self.scratch_dir / "corrupt.wav"
        with open(path, "wb") as f:
            f.write(b"NOT_A_VALID_RIFF_WAV_HEADER_DATA")

        with self.assertRaises(AudioValidationError):
            validate_and_load_session_audio(path)

    def test_api_missing_session_error(self):
        res = self.client.get('/api/v1/session/non_existent_session_id')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.get_json()['status'], 'error')

if __name__ == '__main__':
    unittest.main()
