import os
import sys
import unittest
import numpy as np
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.features.extraction import (
    load_and_preprocess_audio,
    extract_log_mel_spectrogram,
    extract_mfcc_statistical_features
)
from app.services.event_aggregator import aggregate_window_events
from app.services.session_summary import calculate_session_summary
from app.db.database import (
    init_db,
    save_session_record,
    save_session_analysis,
    get_session,
    get_all_sessions
)

class TestVoxFlowCoreComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_audio_preprocessing_shape_and_range(self):
        # Generate 2.0s sine wave at 8000Hz (should be upsampled to 16000Hz and padded to 48000 samples)
        t = np.linspace(0, 2.0, 16000)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        processed = load_and_preprocess_audio(audio, sample_rate=8000)

        self.assertEqual(len(processed), 48000)
        self.assertLessEqual(np.max(np.abs(processed)), 1.0)
        self.assertGreater(np.max(np.abs(processed)), 0.0)

    def test_feature_extraction_dimensions(self):
        dummy_audio = np.random.randn(48000).astype(np.float32)
        # Log-Mel
        mel = extract_log_mel_spectrogram(dummy_audio)
        self.assertEqual(mel.shape[0], 1)
        self.assertEqual(mel.shape[1], 64)
        self.assertGreater(mel.shape[2], 250)

        # MFCC Stats
        mfcc_stats = extract_mfcc_statistical_features(dummy_audio)
        self.assertEqual(mfcc_stats.ndim, 1)
        self.assertEqual(len(mfcc_stats), 240)

    def test_event_aggregation_prevents_double_counting(self):
        # Three consecutive overlapping repetition windows: [0-3, 1-4, 2-5]
        windows = [
            {"start_time": 0.0, "end_time": 3.0, "predicted_class": "Repetition", "confidence": 0.85},
            {"start_time": 1.0, "end_time": 4.0, "predicted_class": "Repetition", "confidence": 0.88},
            {"start_time": 2.0, "end_time": 5.0, "predicted_class": "Repetition", "confidence": 0.82},
            {"start_time": 3.0, "end_time": 6.0, "predicted_class": "Fluent", "confidence": 0.90},
            {"start_time": 4.0, "end_time": 7.0, "predicted_class": "Block", "confidence": 0.75}
        ]

        events = aggregate_window_events("test_sess", windows)
        # The 3 overlapping repetitions must be aggregated into exactly 1 event region: 0.0s to 5.0s
        rep_events = [e for e in events if e['event_type'] == 'Repetition']
        self.assertEqual(len(rep_events), 1)
        self.assertEqual(rep_events[0]['start_time'], 0.0)
        self.assertEqual(rep_events[0]['end_time'], 5.0)
        self.assertEqual(rep_events[0]['supporting_window_count'], 3)

        # Block event must remain separate
        block_events = [e for e in events if e['event_type'] == 'Block']
        self.assertEqual(len(block_events), 1)
        self.assertEqual(block_events[0]['start_time'], 4.0)

    def test_fluency_ratio_calculation(self):
        windows = [
            {"predicted_class": "Fluent"},
            {"predicted_class": "Fluent"},
            {"predicted_class": "Repetition"},
            {"predicted_class": "Fluent"}
        ]
        events = [{"event_type": "Repetition"}]
        summary = calculate_session_summary("sess_test", 10.0, windows, events, "v1.0")

        self.assertEqual(summary['total_windows'], 4)
        self.assertEqual(summary['valid_windows'], 4)
        self.assertEqual(summary['fluent_windows'], 3)
        self.assertEqual(summary['repetition_events'], 1)
        self.assertEqual(summary['fluency_ratio'], 0.75)

    def test_database_crud_and_persistence(self):
        from datetime import datetime
        sess_id = "test_db_persistence_001"
        now_str = datetime.utcnow().isoformat()
        save_session_record(
            session_id=sess_id,
            user_id="user_default",
            started_at=now_str,
            ended_at=now_str,
            duration=45.0,
            audio_path="dummy.wav",
            model_version="voxflow-model-v1.0",
            status="ANALYZED"
        )
        dummy_windows = [{
            "start_time": 0.0, "end_time": 3.0, "predicted_class": "Fluent",
            "fluent_probability": 0.95, "repetition_probability": 0.02,
            "prolongation_probability": 0.01, "block_probability": 0.02, "confidence": 0.95
        }]
        dummy_events = []
        dummy_summary = {
            "valid_windows": 1, "fluent_windows": 1, "repetition_events": 0,
            "prolongation_events": 0, "block_events": 0, "fluency_ratio": 1.0
        }
        save_session_analysis(sess_id, dummy_windows, dummy_events, dummy_summary)

        retrieved = get_session(sess_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['duration'], 45.0)
        self.assertEqual(retrieved['summary']['fluency_ratio'], 1.0)
        self.assertEqual(len(retrieved['windows']), 1)

if __name__ == '__main__':
    unittest.main()
