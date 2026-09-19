import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Configuration
DATA_CONFIG = {
    "raw_dir": BASE_DIR / "data" / "raw",
    "processed_dir": BASE_DIR / "data" / "processed",
    "manifests_dir": BASE_DIR / "data" / "manifests",
    "sample_rate": 16000,
    "clip_duration_sec": 3.0,
    "target_samples": 48000,  # 16000 * 3.0
    "classes": ["Fluent", "Repetition", "Prolongation", "Block"],
    "class_to_idx": {"Fluent": 0, "Repetition": 1, "Prolongation": 2, "Block": 3},
    "idx_to_class": {0: "Fluent", 1: "Repetition", 2: "Prolongation", 3: "Block"},
    "min_annotator_agreement": 2, # At least 2 out of 3 annotators must agree
}

# Audio Preprocessing Configuration
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "n_fft": 512,
    "hop_length": 160,     # 10ms hop
    "win_length": 400,     # 25ms window
    "n_mels": 64,
    "f_min": 50,
    "f_max": 8000,
    "time_frames": 301,    # ~3.0 seconds at 10ms hop
    "n_mfcc": 13,
}

# Training Configuration
TRAINING_CONFIG = {
    "seed": 42,
    "batch_size": 32,
    "epochs": 20,
    "learning_rate": 1e-3,
    "weight_decay": 1e-4,
    "early_stopping_patience": 5,
    "models_dir": BASE_DIR / "models",
    "final_model_dir": BASE_DIR / "models" / "final",
    "model_version": "voxflow-model-v1.0",
}

# Complete Session Engine Configuration
SESSION_CONFIG = {
    "sample_rate": 16000,
    "window_duration_sec": 3.0,
    "window_step_sec": 1.0,
    "min_session_duration_sec": 30.0,
    "max_standard_session_duration_sec": 60.0,
    "audio_upload_dir": BASE_DIR / "audio_buffer",
}

# Event Aggregation Configuration (Tuned on Validation Set)
AGGREGATION_CONFIG = {
    "confidence_threshold": 0.50,
    "min_supporting_windows": 1,
    "merge_gap_sec": 1.5,     # Merge same-class events separated by <= 1.5s
    "min_event_duration_sec": 0.5,
    "version": "agg-v1.0",
}

# Database Configuration
DB_CONFIG = {
    "db_path": BASE_DIR / "voxflow.db",
    "path": BASE_DIR / "voxflow.db",
}

# Model Configuration
MODEL_CONFIG = {
    "version": "voxflow-model-v1.0",
    "save_dir": BASE_DIR / "models" / "final",
}

SESSION_CONFIG["min_duration_sec"] = 30.0
SESSION_CONFIG["max_duration_sec"] = 60.0
SESSION_CONFIG["storage_dir"] = BASE_DIR / "data"
AGGREGATION_CONFIG["min_support_windows"] = 1


# Flask API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    "title": "VoxFlow — Speech Fluency & Stuttering Event Monitoring Platform",
    "clinical_threshold_default": 78.0,
}
