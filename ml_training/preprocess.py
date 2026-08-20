import numpy as np
import scipy.signal as signal
import torch

# Target audio configuration
SAMPLE_RATE = 16000
CLIP_DURATION = 2.0  # seconds
TARGET_SAMPLES = int(SAMPLE_RATE * CLIP_DURATION)  # 32,000 samples
N_MELS = 64
TIME_FRAMES = 64

def pcm_to_float(audio_bytes: bytes) -> np.ndarray:
    """Convert raw 16-bit or 32-bit PCM audio bytes to float32 numpy array [-1.0, 1.0]."""
    if not audio_bytes:
        return np.zeros(TARGET_SAMPLES, dtype=np.float32)
    
    # Check if 32-bit int from ESP32 or 16-bit int standard WAV
    if len(audio_bytes) % 4 == 0 and len(audio_bytes) >= TARGET_SAMPLES * 2:
        try:
            arr = np.frombuffer(audio_bytes, dtype=np.int32).astype(np.float32)
            arr = arr / (2.0 ** 31)
        except Exception:
            arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif len(audio_bytes) % 2 == 0:
        arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        arr = np.frombuffer(audio_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
        
    return arr

def pad_or_crop(audio: np.ndarray, target_length: int = TARGET_SAMPLES) -> np.ndarray:
    """Ensure audio signal is exactly target_length samples long."""
    if len(audio) == target_length:
        return audio
    elif len(audio) > target_length:
        return audio[:target_length]
    else:
        pad_width = target_length - len(audio)
        return np.pad(audio, (0, pad_width), mode='constant')

def hz_to_mel(hz):
    return 2595.0 * np.log10(1.0 + hz / 700.0)

def mel_to_hz(mel):
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

def create_mel_filterbank(sr=16000, n_fft=512, n_mels=64):
    """Generate Mel-scale filterbank matrix (n_mels, n_fft//2 + 1)."""
    n_freqs = n_fft // 2 + 1
    low_mel = hz_to_mel(80)
    high_mel = hz_to_mel(sr / 2)
    mel_points = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    fbank = np.zeros((n_mels, n_freqs), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]

        for k in range(f_m_minus, f_m):
            if f_m != f_m_minus:
                fbank[m - 1, k] = (k - bin_points[m - 1]) / (f_m - f_m_minus)
        for k in range(f_m, f_m_plus):
            if f_m_plus != f_m:
                fbank[m - 1, k] = (bin_points[m + 1] - k) / (f_m_plus - f_m)
                
    return fbank

_MEL_FILTERBANK = create_mel_filterbank(sr=SAMPLE_RATE, n_fft=512, n_mels=N_MELS)

def extract_log_mel_spectrogram(audio: np.ndarray, augment: bool = False) -> np.ndarray:
    """
    Extract Log-Mel Spectrogram (64 mels x 64 time frames) from audio waveform.
    Supports audio data augmentation (pitch/speed variation) for Indian student accents.
    """
    audio = pad_or_crop(audio, TARGET_SAMPLES)
    
    # Indian Accent Data Augmentation (during training phase)
    if augment:
        # Speed stretch simulation via resampling
        speed_factor = np.random.uniform(0.88, 1.12)
        if speed_factor != 1.0:
            indices = np.round(np.arange(0, len(audio), speed_factor)).astype(int)
            indices = indices[indices < len(audio)]
            audio = audio[indices]
            audio = pad_or_crop(audio, TARGET_SAMPLES)
            
        # Micro pitch tremor / noise injection
        if np.random.rand() > 0.5:
            noise = np.random.normal(0, 0.005, size=audio.shape)
            audio = audio + noise

    # Compute STFT
    n_fft = 512
    hop_length = (len(audio) - n_fft) // (TIME_FRAMES - 1)
    if hop_length <= 0:
        hop_length = 500
        
    _, _, stft_matrix = signal.stft(audio, fs=SAMPLE_RATE, nperseg=n_fft, noverlap=n_fft - hop_length)
    power_spec = np.abs(stft_matrix[:, :TIME_FRAMES]) ** 2
    
    if power_spec.shape[1] < TIME_FRAMES:
        pad_t = TIME_FRAMES - power_spec.shape[1]
        power_spec = np.pad(power_spec, ((0, 0), (0, pad_t)), mode='edge')
    elif power_spec.shape[1] > TIME_FRAMES:
        power_spec = power_spec[:, :TIME_FRAMES]

    # Apply Mel filterbank
    mel_spec = np.dot(_MEL_FILTERBANK, power_spec[:_MEL_FILTERBANK.shape[1], :])
    
    # Log-dB scaling
    log_mel = np.log10(np.maximum(mel_spec, 1e-10))
    
    # Normalization (zero mean, unit variance)
    mean = np.mean(log_mel)
    std = np.std(log_mel) + 1e-6
    normalized_spec = (log_mel - mean) / std
    
    return normalized_spec.astype(np.float32)

def audio_bytes_to_tensor(audio_bytes: bytes, augment: bool = False) -> torch.Tensor:
    """Preprocess audio bytes directly into a 3D PyTorch Tensor (1, 64, 64)."""
    audio = pcm_to_float(audio_bytes)
    spec = extract_log_mel_spectrogram(audio, augment=augment)
    tensor = torch.tensor(spec, dtype=torch.float32).unsqueeze(0)  # Shape: (1, 64, 64)
    return tensor
