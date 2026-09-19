import os
import io
import numpy as np
from scipy.io import wavfile
import scipy.signal as signal

from configs.config import SESSION_CONFIG, MODEL_CONFIG
from ml.inference.engine import predict_window

class AudioValidationError(Exception):
    pass

def validate_and_load_session_audio(audio_path_or_bytes):
    """
    Validates session audio according to VoxFlow requirements:
    - Must be a valid WAV file
    - Must be between 30.0s and 60.0s for standard prototype evaluation
    - Must have audible speech signal (not complete silence)
    """
    if isinstance(audio_path_or_bytes, (str, os.PathLike)):
        if not os.path.exists(audio_path_or_bytes):
            raise AudioValidationError(f"Audio file not found: {audio_path_or_bytes}")
        try:
            sr, audio = wavfile.read(str(audio_path_or_bytes))
        except Exception as e:
            raise AudioValidationError(f"Invalid or corrupt WAV audio file: {e}")
    elif isinstance(audio_path_or_bytes, bytes):
        try:
            sr, audio = wavfile.read(io.BytesIO(audio_path_or_bytes))
        except Exception as e:
            raise AudioValidationError(f"Invalid or corrupt WAV audio byte stream: {e}")
    else:
        raise AudioValidationError("Audio input must be a file path or raw bytes")

    # Format to float32
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    else:
        audio = audio.astype(np.float32)

    # Convert to mono if multi-channel
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample to 16kHz if needed
    if sr != SESSION_CONFIG['sample_rate']:
        target_sr = SESSION_CONFIG['sample_rate']
        num_samples = int(len(audio) * target_sr / sr)
        audio = signal.resample(audio, num_samples)
        sr = target_sr

    duration_sec = len(audio) / sr

    # Duration Policy Validation
    if duration_sec < SESSION_CONFIG['min_duration_sec']:
        raise AudioValidationError(
            f"Session duration ({duration_sec:.2f}s) is below the minimum required "
            f"{SESSION_CONFIG['min_duration_sec']:.1f}s. Standard VoxFlow sessions must be 30–60 seconds."
        )

    if duration_sec > SESSION_CONFIG['max_duration_sec'] + 1.0: # 1s grace margin
        raise AudioValidationError(
            f"Session duration ({duration_sec:.2f}s) exceeds standard prototype maximum "
            f"{SESSION_CONFIG['max_duration_sec']:.1f}s. Standard VoxFlow sessions must be 30–60 seconds."
        )

    # Silence Check
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-4:
        raise AudioValidationError("Session audio contains only silence or undetectable speech signal.")

    return audio, sr, duration_sec

def process_session_windows(session_id, audio, sr, duration_sec):
    """
    Sliding window processor:
    - 3.0-second inference window
    - 1.0-second step
    """
    window_duration = SESSION_CONFIG['window_duration_sec']
    step_sec = SESSION_CONFIG['window_step_sec']
    window_samples = int(window_duration * sr)
    step_samples = int(step_sec * sr)

    windows = []
    window_id = 0
    start_sample = 0

    while start_sample + window_samples <= len(audio):
        end_sample = start_sample + window_samples
        start_time = round(start_sample / sr, 2)
        end_time = round(end_sample / sr, 2)

        window_audio = audio[start_sample:end_sample]
        pred_res = predict_window(window_audio, sample_rate=sr)

        windows.append({
            "session_id": session_id,
            "window_id": window_id,
            "start_time": start_time,
            "end_time": end_time,
            "predicted_class": pred_res["predicted_class"],
            "fluent_probability": pred_res["fluent_probability"],
            "repetition_probability": pred_res["repetition_probability"],
            "prolongation_probability": pred_res["prolongation_probability"],
            "block_probability": pred_res["block_probability"],
            "confidence": pred_res["confidence"],
            "model_version": pred_res["model_version"]
        })

        window_id += 1
        start_sample += step_samples

    return windows
