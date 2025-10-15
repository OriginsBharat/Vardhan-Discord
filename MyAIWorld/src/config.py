import os
from dotenv import load_dotenv

# Load environment variables from the .env file you will create during setup
load_dotenv()

# --- Discord ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MASTER_ID = int(os.getenv("MASTER_ID", 0))

# --- Pinecone ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

# --- Paths ---
OLLAMA_PATH = os.getenv("OLLAMA_PATH")
COMFYUI_PATH = os.getenv("COMFYUI_PATH")
XTTS_PATH = os.getenv("XTTS_PATH")

# --- Bot Settings ---
BOT_PREFIX = "!"

# --- Voice Paths ---
# This will be populated dynamically from the .env file
VOICE_PATHS = {
    name.replace('VOICE_', ''): os.getenv(name)
    for name in os.environ if name.startswith('VOICE_')
}

def get_voice_path(character_name: str) -> str | None:
    """Returns the voice path for a given character, case-insensitively."""
    for name, path in VOICE_PATHS.items():
        if name.lower() == character_name.lower():
            return path
    return None