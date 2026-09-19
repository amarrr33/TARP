import os
import json
import torch
import numpy as np
from pathlib import Path

from configs.config import MODEL_CONFIG
from ml.features.extraction import (
    load_and_preprocess_audio,
    extract_log_mel_spectrogram,
    extract_mfcc_statistical_features
)
from ml.models.cnn_model import VoxFlowCNN
from ml.models.cnn_gru_model import VoxFlowCNNGRU
from ml.models.wav2vec2_classifier import VoxFlowWav2Vec2Classifier
from ml.models.svm_baseline import SVMBaseline

LABEL_TO_IDX = {"Fluent": 0, "Repetition": 1, "Prolongation": 2, "Block": 3}
IDX_TO_LABEL = {0: "Fluent", 1: "Repetition", 2: "Prolongation", 3: "Block"}

class VoxFlowInferenceEngine:
    _instance = None

    def __init__(self):
        self.model = None
        self.model_type = None
        self.metadata = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_model()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        model_dir = MODEL_CONFIG['save_dir']
        meta_file = model_dir / "model_metadata.json"
        
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "model_version": MODEL_CONFIG['version'],
                "winning_architecture": "CNN-GRU",
                "sample_rate": 16000
            }

        pt_file = model_dir / "voxflow_model_v1.0.pt"
        joblib_file = model_dir / "voxflow_model_v1.0.joblib"

        if os.path.exists(pt_file):
            checkpoint = torch.load(pt_file, map_location=self.device)
            self.model_type = checkpoint.get("model_type", "cnn_gru")
            if self.model_type == "cnn_gru":
                self.model = VoxFlowCNNGRU(num_classes=4).to(self.device)
            elif self.model_type == "cnn":
                self.model = VoxFlowCNN(num_classes=4).to(self.device)
            elif self.model_type == "w2v":
                self.model = VoxFlowWav2Vec2Classifier(num_classes=4, pretrained=False).to(self.device)
            
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model.eval()
            print(f"Loaded PyTorch inference model ({self.model_type}) from {pt_file}")

        elif os.path.exists(joblib_file):
            self.model_type = "svm"
            self.model = SVMBaseline().load(joblib_file)
            print(f"Loaded SVM inference model from {joblib_file}")
        else:
            # Fallback initialization before training completes
            self.model_type = "cnn_gru"
            self.model = VoxFlowCNNGRU(num_classes=4).to(self.device)
            self.model.eval()
            print("Initialized default VoxFlowCNNGRU (awaiting trained weights)")

    def predict_window(self, audio_or_path, sample_rate=16000):
        """
        Inference interface for a single 3.0s window:
        Returns:
          predicted_class, fluent_probability, repetition_probability,
          prolongation_probability, block_probability, confidence, model_version
        """
        audio_np = load_and_preprocess_audio(audio_or_path, sample_rate=sample_rate)

        # Check for silence: if RMS is near zero, classify as Fluent with high confidence
        rms = np.sqrt(np.mean(audio_np ** 2))
        if rms < 1e-4:
            return {
                "predicted_class": "Fluent",
                "fluent_probability": 0.99,
                "repetition_probability": 0.003,
                "prolongation_probability": 0.003,
                "block_probability": 0.004,
                "confidence": 0.99,
                "model_version": self.metadata.get("model_version", MODEL_CONFIG['version'])
            }

        if self.model_type == "svm":
            feat = extract_mfcc_statistical_features(audio_np)
            probs = self.model.predict_proba(np.array([feat]))[0]
        elif self.model_type in ["cnn", "cnn_gru"]:
            feat = extract_log_mel_spectrogram(audio_np).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(feat)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        elif self.model_type == "w2v":
            wave = torch.from_numpy(audio_np).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(wave)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        else:
            probs = np.array([0.25, 0.25, 0.25, 0.25])

        pred_idx = int(np.argmax(probs))
        pred_class = IDX_TO_LABEL[pred_idx]
        confidence = float(probs[pred_idx])

        return {
            "predicted_class": pred_class,
            "fluent_probability": float(probs[0]),
            "repetition_probability": float(probs[1]),
            "prolongation_probability": float(probs[2]),
            "block_probability": float(probs[3]),
            "confidence": confidence,
            "model_version": self.metadata.get("model_version", MODEL_CONFIG['version'])
        }

def predict_window(audio_or_path, sample_rate=16000):
    engine = VoxFlowInferenceEngine.get_instance()
    return engine.predict_window(audio_or_path, sample_rate=sample_rate)
