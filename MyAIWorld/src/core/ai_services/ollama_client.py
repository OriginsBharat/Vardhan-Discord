import requests
import json
import asyncio
import time

class OllamaClient:
    def __init__(self, host="http://127.0.0.1:11434"):
        self.host = host
        self.chat_url = f"{host}/api/chat"

    async def wait_for_server_ready(self, timeout=60):
        print("[Health Check] Waiting for Ollama server...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await asyncio.to_thread(requests.get, self.host, timeout=2)
                if response.status_code == 200:
                    print("[Health Check] Ollama server is online.")
                    return True
            except requests.exceptions.RequestException:
                pass
            await asyncio.sleep(2)
        print(f"[Health Check] Ollama server did not respond within {timeout} seconds.")
        return False

    def generate_text(self, model: str, prompt: str, system_prompt: str = None):
        messages = [{"role": "system", "content": system_prompt or "You are a helpful assistant."}, {"role": "user", "content": prompt}]
        payload = { "model": model, "messages": messages, "stream": False }
        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "").strip()
        except requests.exceptions.RequestException:
            return "Error: Could not connect to Ollama."
        except json.JSONDecodeError:
            return "Error: Invalid response from Ollama."