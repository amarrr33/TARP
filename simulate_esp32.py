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

def generate_chunk_wav_bytes(duration_sec=0.5, sample_rate=16000, chunk_num=1):
    """Generates a 0.5-second 16kHz 16-bit Mono PCM audio chunk simulating ESP32 INMP441 micro-uploads."""
    num_samples = int(duration_sec * sample_rate)
    samples = []
    f0 = 220.0 + (chunk_num * 30.0) # Dynamic pitch variation across chunks
    for i in range(num_samples):
        t = float(i) / sample_rate
        sine_val = math.sin(2.0 * math.pi * f0 * t)
        noise_val = random.uniform(-0.08, 0.08)
        sample_val = int((sine_val * 0.5 + noise_val) * 32767.0)
        sample_val = max(-32768, min(32767, sample_val))
        samples.append(struct.pack('<h', sample_val))
    return b''.join(samples)

def simulate_esp32_post(num_chunks=6):
    print(f"\n========================================================")
    print(f" [ESP32 HARDWARE SIMULATOR] Streaming {num_chunks} x 0.5s Audio Chunks")
    print(f" Target Host REST API: {SERVER_URL}")
    print(f"========================================================\n")
    
    for i in range(1, num_chunks + 1):
        chunk_bytes = generate_chunk_wav_bytes(duration_sec=0.5, chunk_num=i)
        print(f"[Chunk {i}/{num_chunks}] ESP32 sending 0.5s audio chunk ({len(chunk_bytes)} bytes) over Wi-Fi...")
        
        try:
            files = {'audio': (f'chunk_{i}.wav', chunk_bytes, 'audio/wav')}
            data = {'user_id': '1', 'chunk_num': str(i)}
            response = requests.post(SERVER_URL, files=files, data=data, timeout=5)
            
            if response.status_code == 200:
                res = response.json()
                pipe_status = res.get('pipeline_status')
                score = res.get('fluency_score')
                stutter = res.get('stutter_detected')
                stutter_type = res.get('stutter_type')
                buf_sec = res.get('buffer_sec')
                
                print(f"   -> [Server Response] Pipeline Status: {pipe_status.upper()} | Rolling Buffer: {buf_sec}s")
                print(f"   -> [OLED Display] '{res.get('display_message')}'")
                print(f"   -> [ESP32 LED Indicator] {'RED (Disfluency Alert)' if stutter else 'GREEN (Fluent)'}\n")
            else:
                print(f"   -> [Error Response] HTTP {response.status_code}: {response.text}\n")
                
        except Exception as e:
            print(f"[ESP32 SIMULATOR ERROR] Connection failed: {e}")
            print("Make sure Flask server is running on http://localhost:5000 (`python server.py`)\n")
            break
            
        time.sleep(0.4) # Simulate 400ms Wi-Fi upload delay between 0.5s hardware sampling cycles

def test_realtime_training():
    print(f"\n========================================================")
    print(f" [ONLINE LEARNING ENGINE] Triggering Real-Time Retraining")
    print(f" Target Host REST API: http://localhost:5000/api/v1/model/retrain")
    print(f"========================================================\n")
    try:
        # 1. Fetch current status
        status_res = requests.get("http://localhost:5000/api/v1/model/status", timeout=5)
        if status_res.status_code == 200:
            st = status_res.json()
            print(f"-> Current Model Version: {st.get('version')} | Benchmark Accuracy: {st.get('benchmark_accuracy')}")
            
        # 2. Trigger real-time retraining
        print("-> Posting real-time online fine-tuning request (3 epochs)...")
        retrain_res = requests.post("http://localhost:5000/api/v1/model/retrain", json={"epochs": 3}, timeout=15)
        
        if retrain_res.status_code == 200:
            res = retrain_res.json()
            print(f"-> RETRAINING SUCCESS: {res.get('message')}")
            print(f"-> New Model Version : {res.get('new_version')}")
            print(f"-> Fine-Tune Accuracy: {res.get('fine_tune_accuracy')} | Loss: {res.get('final_loss')}")
        else:
            print(f"-> Retraining failed: {retrain_res.text}")
            
    except Exception as e:
        print(f"[RETRAINING TEST ERROR] Server connection failed: {e}\n")

if __name__ == "__main__":
    simulate_esp32_post()
    test_realtime_training()
