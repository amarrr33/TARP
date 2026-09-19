import os
import sys
import time
import json
import pathlib
import unittest
import numpy as np
from scipy.io import wavfile

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.config import MODEL_CONFIG, DB_CONFIG, SESSION_CONFIG
from app.db.database import init_db, get_session, get_db_connection
from server import app

class TestFullIntegrationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()
        cls.test_wav_path = ROOT_DIR / "data" / "integration_test_35s.wav"

        # Create a valid 35.0-second test WAV file with speech-like harmonic signal
        sr = 16000
        duration = 35.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        # 200 Hz tone with varying amplitude to simulate speech
        audio = 0.3 * np.sin(2 * np.pi * 200 * t) * (1.0 + 0.5 * np.sin(2 * np.pi * 2 * t))
        pcm16 = (audio * 32767.0).astype(np.int16)
        wavfile.write(cls.test_wav_path, sr, pcm16)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_wav_path):
            try:
                os.remove(cls.test_wav_path)
            except Exception:
                pass

    def test_end_to_end_session_flow(self):
        # 1. Start session via Flask
        start_res = self.client.post('/api/v1/session/start', json={'user_id': 'user_default'})
        self.assertEqual(start_res.status_code, 201)
        start_data = start_res.get_json()
        session_id = start_data['session_id']
        self.assertTrue(session_id.startswith('sess_'))

        # 2. Upload valid audio bytes
        with open(self.test_wav_path, 'rb') as f:
            audio_bytes = f.read()
        upload_res = self.client.post(
            f'/api/v1/session/{session_id}/audio',
            data=audio_bytes,
            content_type='application/octet-stream'
        )
        self.assertEqual(upload_res.status_code, 200)

        # 3. Stop session
        stop_res = self.client.post(f'/api/v1/session/{session_id}/stop')
        self.assertEqual(stop_res.status_code, 200)

        # 4. Analyze session
        analyze_res = self.client.post(f'/api/v1/session/{session_id}/analyze')
        self.assertEqual(analyze_res.status_code, 200)
        analyze_data = analyze_res.get_json()
        self.assertEqual(analyze_data['status'], 'success')
        self.assertAlmostEqual(analyze_data['duration'], 35.0, delta=0.5)

        # 5. Verify windows and probabilities
        summary = analyze_data['summary']
        self.assertGreater(summary['valid_windows'], 30)  # 35s audio has ~33 overlapping 3s windows
        self.assertIn('fluency_ratio', summary)
        self.assertGreaterEqual(summary['fluency_ratio'], 0.0)
        self.assertLessEqual(summary['fluency_ratio'], 1.0)

        # 6. Verify SQLite records directly
        db_session = get_session(session_id)
        self.assertIsNotNone(db_session)
        self.assertEqual(db_session['status'], 'ANALYZED')
        self.assertEqual(len(db_session['windows']), summary['valid_windows'])
        self.assertEqual(db_session['model_version'], MODEL_CONFIG['version'])

        # Verify probabilities in windows
        first_win = db_session['windows'][0]
        prob_sum = (
            first_win['fluent_probability'] +
            first_win['repetition_probability'] +
            first_win['prolongation_probability'] +
            first_win['block_probability']
        )
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

        # 7. Retrieve session through Flask GET route
        get_res = self.client.get(f'/api/v1/session/{session_id}')
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()
        self.assertEqual(get_data['session']['id'], session_id)

        # 8. Retrieve latest session endpoint
        latest_res = self.client.get('/api/v1/session/latest')
        self.assertEqual(latest_res.status_code, 200)
        self.assertEqual(latest_res.get_json()['session']['id'], session_id)

        print("\n>>> End-to-End Automated Integration Test PASSED Successfully! <<<")

if __name__ == '__main__':
    unittest.main()
