import websocket
import uuid
import json
import urllib.request
import urllib.parse
from PIL import Image
import io

class ComfyUIClient:
    """
    Client for interacting with a local ComfyUI server via WebSockets.
    """
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())

    def get_image(self, filename, subfolder, folder_type):
        """Retrieves a single image from the ComfyUI server."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
            return Image.open(io.BytesIO(response.read()))

    def get_history(self, prompt_id):
        """Gets the execution history for a given prompt ID."""
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def queue_prompt(self, prompt):
        """Queues a prompt for execution and waits for the resulting image."""
        try:
            ws = websocket.WebSocket()
            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            
            # The prompt is a dictionary with the workflow and our client ID
            prompt_to_send = {"prompt": prompt, "client_id": self.client_id}
            ws.send(json.dumps(prompt_to_send))
            
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        # Execution is complete when the node is None
                        if data['node'] is None and data['prompt_id'] == prompt_to_send['prompt']['prompt_id']:
                            break 
                else:
                    continue # Ignore binary data in this loop
            
            ws.close()
            
            history = self.get_history(prompt_to_send['prompt']['prompt_id'])
            history = history[prompt_to_send['prompt']['prompt_id']]
            
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    images_output = []
                    for image in node_output['images']:
                        image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                        images_output.append(image_data)
                    return images_output
        except Exception as e:
            print(f"Error communicating with ComfyUI: {e}")
            return None
        return None

    def create_simple_text_to_image_prompt(self, text_prompt: str, batch_size: int = 1, model: str = "sd_xl_base_1.0.safetensors"):
        """Creates a basic prompt workflow for SDXL text-to-image."""
        prompt = {
            "prompt_id": str(uuid.uuid4()),
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": random.randint(0, 999999999999999),
                    "steps": 25, "cfg": 8, "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
                    "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
                }
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": batch_size}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": text_prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "text, watermark, ugly, blurry", "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "MyAIWorld", "images": ["8", 0]}}
        }
        # A bit of a hack to get random seeds working inside the class
        import random
        prompt["3"]["inputs"]["seed"] = random.randint(0, 999999999999999)
        return prompt