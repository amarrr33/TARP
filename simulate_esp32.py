import requests
import wave
import struct
import math
import time
import random

SERVER_URL = "http://localhost:5000/api/v1/audio/upload"
WAV_PATH = r"c:\Users\amare\Downloads\TARP\simulated_esp32_audio.wav"

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

def simulate_esp32_post():
    filename = generate_sample_wav()
    print(f"\n[ESP32 SIMULATOR] Transmitting Wi-Fi HTTP POST audio payload to: {SERVER_URL} ...")
    
    try:
        with open(filename, 'rb') as f:
            files = {'audio': (filename, f, 'audio/wav')}
            data = {'user_id': '1'}
            response = requests.post(SERVER_URL, files=files, data=data, timeout=5)
            
        print(f"[ESP32 SIMULATOR] HTTP Response Status Code: {response.status_code}")
        print(f"[ESP32 SIMULATOR] Response JSON Body:\n{response.text}")
        
        if response.status_code == 200:
            res_json = response.json()
            score = res_json.get('fluency_score')
            stutter = res_json.get('stutter_detected')
            print(f"\n>>> [ESP32 HARDWARE DISPLAY] OLED: '{res_json.get('display_message')}' | LED: {'RED (Stutter Alert)' if stutter else 'GREEN (Fluent)'}")
            
    except Exception as e:
        print(f"[ESP32 SIMULATOR ERROR] Server connection failed: {e}")
        print("Make sure Flask server is running on http://localhost:5000 (`python server.py`)")

if __name__ == "__main__":
    simulate_esp32_post()
