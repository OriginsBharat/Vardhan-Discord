import sys
import os
import asyncio

# Add the root directory to the Python path to allow for clean imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot import MyAIWorldBot
from src.config import DISCORD_TOKEN

async def main():
    """
    The main entry point for the My AI World bot.
    """
    if not DISCORD_TOKEN:
        print("FATAL: DISCORD_TOKEN is not set in the .env file.")
        print("Please run the SETUP_THE_WORLD.py script to configure your world.")
        return

    bot = MyAIWorldBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down gracefully.")