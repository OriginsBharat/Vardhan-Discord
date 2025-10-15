import discord
from discord.ext import commands
import asyncio
import os
import sys

from src.core.personas import PersonaManager
from src.core.world_state.scheduler import Scheduler
from src.core.world_state.simulation import SimulationManager
from src.core.ai_services.ollama_client import OllamaClient
from src.core.ai_services.xtts_client import XTTSClient
from src.core.command_factory import CommandFactory
from src.config import BOT_PREFIX, MASTER_ID

class MyAIWorldBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)

        self.persona_manager = PersonaManager()
        self.simulation_manager = SimulationManager(self)
        self.scheduler = Scheduler(self)
        self.ollama_client = OllamaClient()
        self.xtts_client = XTTSClient()
        self.command_factory = CommandFactory(self)
        self.has_run_startup = False

    async def setup_hook(self):
        print("Loading all cogs...")
        cog_paths = ['src/commands', 'src/core']
        for path in cog_paths:
            for root, _, files in os.walk(f'MyAIWorld/{path}'):
                for filename in files:
                    if filename.endswith('.py') and not filename.startswith('__'):
                        # Convert file path to module path
                        module_path = os.path.join(root, filename)
                        extension = module_path.replace(os.sep, '.')[:-3]
                        # Correct the module path for discord.py
                        extension = extension.replace('MyAIWorld.src.', 'src.')

                        try:
                            await self.load_extension(extension)
                            print(f"  > Loaded cog: {extension}")
                        except (commands.ExtensionAlreadyLoaded, commands.NoEntryPointError):
                            pass
                        except Exception as e:
                            print(f"Failed to load extension {extension}: {e}", file=sys.stderr)
        print("All cogs loaded.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        if not self.has_run_startup:
            await self.wait_until_ready()

            server_ready = await self.ollama_client.wait_for_server_ready()
            if not server_ready:
                print("CRITICAL: Ollama server did not become available. Aborting startup.")
                await self.close()
                return

            is_first_run = await self.simulation_manager.run_simulation()

            if not is_first_run and self.guilds:
                await self.post_command_lists(self.guilds[0])

            self.scheduler.start()
            self.has_run_startup = True

    async def setup_guild(self, guild):
        print("Performing first-time setup for guild...")
        for channel in await guild.fetch_channels(): await channel.delete()
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed: await role.delete()

        master_member = guild.get_member(MASTER_ID)
        if not master_member:
            print(f"CRITICAL: Master with ID {MASTER_ID} not found. Aborting.")
            return

        print("Creating server roles...")
        for persona in self.persona_manager.get_all_personas():
            await guild.create_role(name=persona.name, colour=discord.Colour(int(persona.aura_color, 16)), mentionable=True)

        print("Creating server categories and channels...")
        categories = {
            "THE CITADEL": ["announcements", "world-events", "bot-commands-list"],
            "CHARACTER HOMES": [f"{p.name.lower()}-s-chamber" for p in self.persona_manager.get_all_personas()],
            "THE MARKET DISTRICT": ["the-market-square", "the-auction-house", "job-board", "bot-owned-shops"],
            "THE VELVET DISTRICT": ["the-velvet-lounge", "the-red-lantern-brothel", "erotica-library"],
            "CREATIVE WORKS": ["art-gallery", "nsfw-art-gallery"]
        }
        voice_channels = {"THE CITADEL": "The Forum", "THE MARKET DISTRICT": "The Exchange", "THE VELVET DISTRICT": "The Whisper Room", "CREATIVE WORKS": "The Studio"}
        nsfw_text_channels = ["the-velvet-lounge", "the-red-lantern-brothel", "erotica-library", "nsfw-art-gallery"]

        for cat_name, text_channels in categories.items():
            category = await guild.create_category(cat_name)
            for name in text_channels:
                await category.create_text_channel(name, nsfw=(name in nsfw_text_channels))
            if cat_name in voice_channels:
                await category.create_voice_channel(voice_channels[cat_name])

        master_only_overwrites = { guild.default_role: discord.PermissionOverwrite(read_messages=False), master_member: discord.PermissionOverwrite(read_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True) }
        master_chambers = await guild.create_category("MASTER'S PRIVATE CHAMBERS", overwrites=master_only_overwrites)
        await master_chambers.create_text_channel("control-panel")
        await master_chambers.create_text_channel("maya-s-daily-journal")
        await master_chambers.create_text_channel("director-s-whispers")

        print("Initial guild structure created.")

    async def post_command_lists(self, guild):
        print("Posting and pinning command lists...")
        channel = discord.utils.get(guild.text_channels, name='bot-commands-list')
        if not channel: return

        all_commands = [cmd for cmd in self.commands if cmd.cog_name != 'DevTools']
        embed = discord.Embed(title="Command List", color=0x2ECC71, description="\n".join(f"**`{self.command_prefix}{cmd.name}`**: {cmd.help or 'No description.'}" for cmd in sorted(all_commands, key=lambda c: c.name)))

        await channel.send(embed=embed)
        print("Command lists posted.")

    async def close(self):
        print("Shutting down...")
        if hasattr(self, 'simulation_manager'): self.simulation_manager.save_current_time()
        if hasattr(self, 'scheduler'): self.scheduler.stop()
        await super().close()