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
        # The correct endpoint for chat-like generation is /api/chat.
        self.api_url = f"{host}/api/chat"
        # The health check endpoint remains the same, as it's a good indicator of the server being up.
        self.health_check_url = f"{host}/api/tags"

    async def wait_for_server_ready(self, timeout=60):
        """
        Waits for the Ollama server's API to be responsive. Simplified and faster.
        """
        print("[Health Check] Waiting for Ollama API to become available...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await asyncio.to_thread(requests.get, self.health_check_url, timeout=2)
                if response.status_code == 200:
                    print("[Health Check] Ollama API is online and ready.")
                    return True
            except requests.exceptions.RequestException:
                pass
            await asyncio.sleep(2)

        print(f"[Health Check] CRITICAL: Ollama API did not become available within {timeout} seconds.")
        return False

    def generate_text(self, model: str, prompt: str, system_prompt: str = None, stream: bool = False):
        """
        Generates text using the /api/chat endpoint, which is the correct endpoint for this task.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()

            # The response structure for /api/chat is different.
            response_data = response.json()
            # The actual message content is nested inside the 'message' object.
            return response_data.get("message", {}).get("content", "").strip()

        except requests.exceptions.RequestException as e:
            error_message = f"Error connecting to Ollama server at {self.host}: {e}"
            print(error_message)
            return f"Error: Could not connect to the Ollama text generation server. Please ensure it is running."
        except json.JSONDecodeError:
            error_message = f"Error decoding JSON from Ollama response: {response.text}"
            print(error_message)
            return "Error: Received an invalid response from the text generation server."