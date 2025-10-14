import requests
import json
import asyncio
import time

class OllamaClient:
    """
    Client for interacting with a local Ollama server.
    """
    def __init__(self, host="http://127.0.0.1:11434"):
        self.host = host
        self.api_url = f"{host}/api/generate"
        self.health_check_url = f"{host}/"

    async def wait_for_server_ready(self, timeout=120):
        """
        Waits for the Ollama server to be responsive by polling its root endpoint.
        """
        print("[Health Check] Waiting for Ollama server to become available...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Run the synchronous requests.get in a separate thread
                response = await asyncio.to_thread(
                    requests.get, self.health_check_url, timeout=2
                )
                if response.status_code == 200:
                    print("[Health Check] Ollama server is online.")
                    return True
            except requests.exceptions.RequestException:
                # This is expected if the server is not up yet, so we just wait and retry.
                pass

            await asyncio.sleep(3)

        print(f"[Health Check] CRITICAL: Ollama server did not become available within {timeout} seconds.")
        return False

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
            response = requests.post(self.api_url, json=payload, timeout=120)
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