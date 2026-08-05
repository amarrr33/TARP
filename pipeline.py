import os
import random
import time
import numpy as np

class AudioReceiver:
    def __init__(self, buffer_dir=r"c:\Users\amare\Downloads\TARP\audio_buffer"):
        self.buffer_dir = buffer_dir
        os.makedirs(self.buffer_dir, exist_ok=True)

    def stage_file(self, file_obj, filename):
        file_path = os.path.join(self.buffer_dir, filename)
        file_obj.save(file_path)
        return file_path

class NoiseFilter:
    def denoise(self, audio_path):
        # Simulates spectral gating noise removal
        time.sleep(0.05)
        snr_db = round(random.uniform(18.0, 32.0), 1)
        return {"status": "denoised", "snr_db": snr_db}

class SpeakerVerifier:
    def verify(self, audio_path, user_id):
        # Simulates cosine similarity speaker matching against baseline
        time.sleep(0.04)
        similarity = round(random.uniform(0.88, 0.97), 3)
        is_match = similarity >= 0.85
        return {"verified": is_match, "similarity": similarity}

class FeatureExtractor:
    def extract_mfccs(self, audio_path):
        # Simulates 13 MFCC + Delta + Delta-Delta extraction (39 dimensions)
        time.sleep(0.05)
        num_frames = 150
        features = np.random.randn(num_frames, 39)
        return features

class FluencyPredictor:
    def predict(self, features):
        # Simulates CNN-LSTM fluency classification pass
        time.sleep(0.08)
        score = round(random.uniform(65.0, 96.0), 1)
        if score >= 82.0:
            stutter_type = "Fluent"
        else:
            stutter_type = random.choice(["Block", "Repetition", "Prolongation"])
        confidence = round(random.uniform(0.89, 0.98), 2)
        return {
            "fluency_score": score,
            "is_disfluent": stutter_type != "Fluent",
            "stutter_type": stutter_type,
            "confidence": confidence
        }

class PipelineRunner:
    def __init__(self):
        self.receiver = AudioReceiver()
        self.noise_filter = NoiseFilter()
        self.verifier = SpeakerVerifier()
        self.extractor = FeatureExtractor()
        self.predictor = FluencyPredictor()

    def process(self, file_path, user_id=1):
        # Step 1: Denoise
        denoise_res = self.noise_filter.denoise(file_path)
        # Step 2: Speaker Verify
        verify_res = self.verifier.verify(file_path, user_id)
        if not verify_res["verified"]:
            return {"status": "rejected", "reason": "Speaker verification failed"}
        # Step 3: Feature Extraction
        features = self.extractor.extract_mfccs(file_path)
        # Step 4: AI Model Prediction
        prediction = self.predictor.predict(features)
        return prediction

pipeline_runner = PipelineRunner()
