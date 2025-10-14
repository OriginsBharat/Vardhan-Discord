import requests
import os
import io

class XTTSClient:
    """
    Client for interacting with a local XTTSv2 API server.
    This implementation is based on a common API structure for such servers.
    """
    def __init__(self, host="http://127.0.0.1:8020"):
        self.host = host
        self.api_url = f"{host}/tts" 

    def generate_speech(self, text: str, speaker_wav_path: str, language: str = "en"):
        """
        Generates speech from text using a specific speaker voice file.

        :param text: The text to be converted to speech.
        :param speaker_wav_path: The full path to the reference speaker audio file (.wav).
        :param language: The language of the text.
        :return: A BytesIO object containing the generated .wav audio, or None on failure.
        """
        if not speaker_wav_path or not os.path.exists(speaker_wav_path):
            print(f"Error: Speaker wav file not found at '{speaker_wav_path}'")
            return None

        # The payload and files dictionary depends heavily on the specific API server implementation.
        # This is a common pattern.
        payload = {
            "text": text,
            "language": language,
        }
        files = {'speaker_wav': (os.path.basename(speaker_wav_path), open(speaker_wav_path, 'rb'), 'audio/wav')}
        
        try:
            response = requests.post(self.api_url, data=payload, files=files, timeout=120) # 120-second timeout
            response.raise_for_status()

            # The server should return the raw audio data in the response body
            return io.BytesIO(response.content)

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to XTTSv2 server at {self.host}: {e}")
            return None