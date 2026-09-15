import requests
import wave
import struct
import math
import time
import random

import os

SERVER_URL = "http://localhost:5000/api/v1/audio/upload"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV_PATH = os.path.join(BASE_DIR, "simulated_esp32_audio.wav")

def generate_sample_wav(filename=WAV_PATH, duration_sec=3.0, sample_rate=16000):
    """Generates a 3-second 16kHz 16-bit Mono WAV audio file simulating ESP32 INMP441 audio input."""
    num_samples = int(duration_sec * sample_rate)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2) # 16-bit PCM (2 bytes)
        wav_file.setframerate(sample_rate)
        
        # Generate 440Hz Sine Wave + White Noise
        for i in range(num_samples):
            t = float(i) / sample_rate
            sine_val = math.sin(2.0 * math.pi * 440.0 * t)
            noise_val = random.uniform(-0.1, 0.1)
            sample_val = int((sine_val * 0.5 + noise_val) * 32767.0)
            sample_val = max(-32768, min(32767, sample_val))
            data = struct.pack('<h', sample_val)
            wav_file.writeframesraw(data)
            
    print(f"Generated simulated audio WAV file: {filename}")
    return filename

def generate_chunk_audio(mode="fluent", chunk_num=1, duration_sec=0.5, sample_rate=16000):
    """
    Generates realistic 0.5s audio chunks representing real ESP32 INMP441 microphone inputs:
    - 'idle': Low-amplitude room ambient noise (energy < 0.003 RMS, silence/no speech).
    - 'fluent': Harmonic vocal cords with smooth cadence and mild natural variation.
    - 'repetition': Fast repeating syllables ('p-p-paper', 'b-b-bro').
    - 'prolongation': Stretched tense high-frequency formant ('ssss-snake', 'anteeee').
    """
    num_samples = int(duration_sec * sample_rate)
    samples = []
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    if mode == "idle":
        # Pure ambient microphone background noise (very low amplitude)
        signal = np.random.normal(0, 0.002, size=num_samples)
    elif mode == "fluent":
        # Clean speech harmonics (140Hz base + 280Hz + 420Hz formants)
        f0 = 150.0 + 10.0 * np.sin(2 * np.pi * 1.5 * t)
        vocal = 0.5 * np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(2 * np.pi * 2 * f0 * t)
        env = 0.5 + 0.4 * np.sin(2 * np.pi * 2.5 * t)
        signal = vocal * env + np.random.normal(0, 0.015, size=num_samples)
    elif mode == "repetition":
        # Rapid syllable repetitions (burst pulses at 5.5 Hz)
        f0 = 180.0
        vocal = 0.6 * np.sin(2 * np.pi * f0 * t)
        pulse = (np.sin(2 * np.pi * 5.5 * t) > 0.1).astype(np.float32)
        signal = vocal * pulse + np.random.normal(0, 0.03, size=num_samples)
    elif mode == "prolongation":
        # Prolonged sound (sustained 1100Hz formant)
        f0 = 160.0
        prolong_tone = 0.65 * np.sin(2 * np.pi * 1100.0 * t)
        signal = 0.35 * np.sin(2 * np.pi * f0 * t) + prolong_tone + np.random.normal(0, 0.02, size=num_samples)
    else:
        signal = np.random.normal(0, 0.002, size=num_samples)
        
    signal = np.clip(signal, -1.0, 1.0)
    int_samples = (signal * 32767.0).astype(np.int16)
    return int_samples.tobytes()

import numpy as np

def run_live_scenario_demo():
    print("=" * 68)
    print("      🎙️ VOXFLOW LIVE HARDWARE & SPEECH CLASSIFICATION DEMO")
    print("  Demonstrates: Idle (Silence) -> Fluent Speech -> Stutter -> Recovery")
    print("  Host Server Target: " + SERVER_URL)
    print("=" * 68)
    
    # Check if server is running
    try:
        health = requests.get("http://localhost:5000/api/v1/health", timeout=3)
        if health.status_code != 200:
            print("[ERROR] Server returned non-200. Make sure `python server.py` is running!")
            return
    except Exception:
        print("\n[ERROR] Flask server is NOT running on port 5000!")
        print("-> Please run `python server.py` in another terminal or launch `run_voxflow_system.bat`!\n")
        return

    scenario = [
        # Phase 1: 4 chunks (2.0s) of Idle / Silence
        ("idle", "Phase 1: IDLE / SILENCE (No one speaking, ambient room noise only)", 4),
        # Phase 2: 6 chunks (3.0s) of Smooth Fluent Speech
        ("fluent", "Phase 2: FLUENT SPEECH (Speaker talking smoothly: 'Hello, I am practicing today')", 6),
        # Phase 3: 6 chunks (3.0s) of Disfluency (Stuttering)
        ("repetition", "Phase 3: DISFLUENCY DETECTED (Speaker repeats syllables: 'p-p-paper, wh-wh-what')", 4),
        ("prolongation", "Phase 3 (cont): PROLONGATION (Speaker elongates vowel: 'ssss-sometimes')", 3),
        # Phase 4: 4 chunks (2.0s) of Recovery to Fluent
        ("fluent", "Phase 4: RECOVERY TO FLUENT (Speaker resumes fluent speech)", 5),
    ]

    total_chunk = 1
    for mode, phase_desc, num_chunks in scenario:
        print(f"\n>>> {phase_desc}")
        print("-" * 68)
        
        for i in range(1, num_chunks + 1):
            chunk_bytes = generate_chunk_audio(mode=mode, chunk_num=i)
            
            try:
                files = {'audio': (f'chunk_{total_chunk}.wav', chunk_bytes, 'audio/wav')}
                data = {'user_id': '1', 'chunk_num': str(total_chunk)}
                resp = requests.post(SERVER_URL, files=files, data=data, timeout=5)
                
                if resp.status_code == 200:
                    r = resp.json()
                    status = r.get('pipeline_status', '').upper()
                    stutter_type = r.get('stutter_type')
                    score = r.get('fluency_score')
                    is_stutter = r.get('stutter_detected')
                    buf = r.get('buffer_sec', 0.0)
                    
                    if is_stutter:
                        led_str = "🔴 RED LED (DISFLUENCY ALERT!)"
                    elif status == "IDLE":
                        led_str = "🟢 GREEN LED (Idle / Listening)"
                    else:
                        led_str = "🟢 GREEN LED (Fluent)"
                        
                    print(f"[{total_chunk:02d}] State: {mode.upper():<11} | Score: {score:>5.1f}% | Type: {stutter_type:<22} | LED: {led_str}")
                else:
                    print(f"[{total_chunk:02d}] Server error {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[{total_chunk:02d}] Connection failed: {e}")
                break
                
            total_chunk += 1
            time.sleep(0.5)  # Simulate 0.5s real-time cadence
            
    print("\n" + "=" * 68)
    print("  ✅ LIVE DEMO COMPLETED!")
    print("  Open Dashboard http://localhost:8501 to see all new sessions and graphs!")
    print("=" * 68)

if __name__ == "__main__":
    run_live_scenario_demo()
