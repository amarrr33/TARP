import os
import torch
import torchaudio
import torchaudio.transforms as T
import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 16000
N_MELS = 64
N_FFT = 512
HOP_LENGTH = 160
TARGET_SAMPLES = 48000  # 3.0 seconds at 16kHz

# 1. Log-Mel Spectrogram Transform (PyTorch)
mel_spectrogram_transform = T.MelSpectrogram(
    sample_rate=SAMPLE_RATE,
    n_fft=N_FFT,
    win_length=N_FFT,
    hop_length=HOP_LENGTH,
    n_mels=N_MELS,
    power=2.0
)
amplitude_to_db = T.AmplitudeToDB(top_db=80)

# 2. MFCC Transform for SVM Baseline
mfcc_transform = T.MFCC(
    sample_rate=SAMPLE_RATE,
    n_mfcc=20,
    melkwargs={"n_fft": N_FFT, "hop_length": HOP_LENGTH, "n_mels": 40}
)
compute_deltas = T.ComputeDeltas()

def load_and_preprocess_audio(audio_path_or_array, sample_rate=16000):
    """
    Standard audio loader and preprocessor:
    - Mono 16kHz
    - Padded/truncated to exactly 48,000 samples (3.0s)
    - Peak-normalized float32 in [-1.0, 1.0]
    """
    if isinstance(audio_path_or_array, (str, os.PathLike)):
        sr, audio = wavfile.read(str(audio_path_or_array))
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        else:
            audio = audio.astype(np.float32)

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sr != SAMPLE_RATE:
            import scipy.signal as sig
            num_samples = int(len(audio) * SAMPLE_RATE / sr)
            audio = sig.resample(audio, num_samples)
    else:
        audio = np.array(audio_path_or_array, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != SAMPLE_RATE:
            import scipy.signal as sig
            num_samples = int(len(audio) * SAMPLE_RATE / sample_rate)
            audio = sig.resample(audio, num_samples)

    # Pad or truncate to TARGET_SAMPLES
    if len(audio) < TARGET_SAMPLES:
        audio = np.pad(audio, (0, TARGET_SAMPLES - len(audio)))
    else:
        audio = audio[:TARGET_SAMPLES]

    # Normalize amplitude
    max_val = np.max(np.abs(audio))
    if max_val > 1e-6:
        audio = audio / max_val

    return audio

def extract_log_mel_spectrogram(audio_np):
    """
    Extracts Log-Mel Spectrogram for CNN and CNN-GRU.
    Returns torch.Tensor of shape (1, N_MELS, T)
    """
    audio_tensor = torch.from_numpy(audio_np).unsqueeze(0)  # (1, 48000)
    mel = mel_spectrogram_transform(audio_tensor)
    log_mel = amplitude_to_db(mel)
    # Standardize mean and std
    mean = log_mel.mean()
    std = log_mel.std() + 1e-6
    norm_log_mel = (log_mel - mean) / std
    return norm_log_mel  # (1, 64, ~301)

def extract_mfcc_statistical_features(audio_np):
    """
    Extracts 20 MFCCs + Deltas + Delta-Deltas.
    Computes mean, std, min, max across time frames.
    Returns 1D numpy array of shape (240,)
    """
    audio_tensor = torch.from_numpy(audio_np).unsqueeze(0)
    mfcc = mfcc_transform(audio_tensor)  # (1, 20, T)
    delta = compute_deltas(mfcc)         # (1, 20, T)
    delta2 = compute_deltas(delta)       # (1, 20, T)

    features = []
    for feat in [mfcc, delta, delta2]:
        f_np = feat.squeeze(0).numpy()  # (20, T)
        mean = np.mean(f_np, axis=1)
        std = np.std(f_np, axis=1)
        f_min = np.min(f_np, axis=1)
        f_max = np.max(f_np, axis=1)
        features.extend([mean, std, f_min, f_max])

    return np.concatenate(features)  # 20 * 4 * 3 = 240 features
