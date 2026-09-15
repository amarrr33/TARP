import sounddevice as sd
import numpy as np
import requests
import time
import sys

SERVER_URL = "http://localhost:5000/api/v1/audio/upload"
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5 # seconds
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

def get_manga_stutter_text(stutter_type, confidence, fluency_score):
    if stutter_type == "Repetition":
        return f"“H-h-hello... w-w-what did you s-say?” (Confidence: {confidence*100:.0f}%)"
    elif stutter_type == "Prolongation":
        return f"“Sssss-sometimes I g-g-get stuck...” (Confidence: {confidence*100:.0f}%)"
    elif stutter_type == "Block":
        return f"“I want to ... [Tense Silent Block 1.2s] ... speak!” (Confidence: {confidence*100:.0f}%)"
    elif stutter_type == "Idle / Silence":
        return "“[Microphone listening... Waiting for voice input]”"
    else:
        return f"“Speech flowing smoothly and naturally!” (Fluency: {fluency_score:.1f}%)"

def main():
    print("=" * 72)
    print("      🎙️ VOXFLOW LAPTOP MICROPHONE REAL-TIME SPEECH STREAMER")
    print("  Streams live audio from your laptop mic directly to the AI model!")
    print("  Destination Host: " + SERVER_URL)
    print("=" * 72)

    try:
        health = requests.get("http://localhost:5000/api/v1/health", timeout=3)
        if health.status_code != 200:
            print("[ERROR] Server not reachable. Make sure `python server.py` is running!")
            return
    except Exception:
        print("[ERROR] Server is not running on port 5000! Start `python server.py` first.")
        return

    print("\n[ACTIVE] Listening to your laptop microphone. Speak or simulate a stutter now!")
    print("Press Ctrl+C to stop streaming.\n")
    print("-" * 72)

    chunk_count = 1
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
            while True:
                # Read 0.5 seconds of PCM audio from laptop mic
                audio_data, overflowed = stream.read(CHUNK_SAMPLES)
                raw_bytes = audio_data.tobytes()

                # Post to server
                files = {'audio': (f'laptop_mic_{chunk_count}.wav', raw_bytes, 'audio/wav')}
                data = {'user_id': '1', 'chunk_num': str(chunk_count)}
                
                try:
                    resp = requests.post(SERVER_URL, files=files, data=data, timeout=5)
                    if resp.status_code == 200:
                        r = resp.json()
                        score = r.get('fluency_score', 0.0)
                        stutter_type = r.get('stutter_type', 'Fluent')
                        is_stutter = r.get('stutter_detected', False)
                        conf = r.get('confidence', 0.9)
                        
                        manga_text = get_manga_stutter_text(stutter_type, conf, score)
                        
                        if is_stutter:
                            badge = "🔴 [STUTTER ALERT!]"
                        elif stutter_type == "Idle / Silence":
                            badge = "⚪ [IDLE / SILENCE]"
                        else:
                            badge = "🟢 [FLUENT SPEECH ]"
                            
                        print(f"[{chunk_count:03d}] {badge} Score: {score:>5.1f}% | Type: {stutter_type:<16} | Manga: {manga_text}")
                except Exception as ex:
                    print(f"[{chunk_count:03d}] Upload error: {ex}")
                    
                chunk_count += 1
                
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Microphone streaming stopped by user.")
    except Exception as e:
        print(f"\n[DEVICE ERROR] Could not access microphone: {e}")

if __name__ == "__main__":
    main()
