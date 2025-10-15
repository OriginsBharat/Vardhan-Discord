import requests
import os

class XTTSClient:
    def __init__(self, host="http://127.0.0.1:8020"):
        self.api_url = f"{host}/tts_to_audio/"

    def generate_speech(self, text: str, speaker_wav_path: str):
        if not os.path.exists(speaker_wav_path):
            print(f"[XTTS] Error: Speaker WAV not found at {speaker_wav_path}")
            return None
        try:
            with open(speaker_wav_path, "rb") as f:
                speaker_wav_content = f.read()

            payload = {"text": text, "language": "en"}
            files = {"speaker_wav": ("speaker.wav", speaker_wav_content, "audio/wav")}

            response = requests.post(self.api_url, data=payload, files=files, timeout=120)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException:
            print(f"[XTTS] Error connecting to XTTS server.")
            return None
        except Exception as e:
            print(f"[XTTS] An unexpected error occurred: {e}")
            return None