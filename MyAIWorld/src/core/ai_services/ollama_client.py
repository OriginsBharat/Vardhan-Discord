import requests
import json

class OllamaClient:
    """
    Client for interacting with a local Ollama server.
    """
    def __init__(self, host="http://127.0.0.1:11434"):
        self.host = host
        self.api_url = f"{host}/api/generate"

    def generate_text(self, model: str, prompt: str, system_prompt: str = None, stream: bool = False):
        """
        Generates text using a specified model and prompt.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(self.api_url, json=payload, timeout=120) # 120-second timeout
            response.raise_for_status()
            
            response_data = response.json()
            return response_data.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            error_message = f"Error connecting to Ollama server at {self.host}: {e}"
            print(error_message)
            return f"Error: Could not connect to the Ollama text generation server. Please ensure it is running."
        except json.JSONDecodeError:
            error_message = f"Error decoding JSON from Ollama response: {response.text}"
            print(error_message)
            return "Error: Received an invalid response from the text generation server."