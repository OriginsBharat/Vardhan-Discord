import discord
from discord.ext import commands
import asyncio
import os
import sys

# Core Systems
from src.core.personas import PersonaManager
from src.core.world_state.scheduler import Scheduler
from src.core.world_state.simulation import SimulationManager
from src.core.ai_services.ollama_client import OllamaClient

# Configuration
from src.config import BOT_PREFIX, MASTER_ID

class MyAIWorldBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        
        # Initialize core managers
        self.persona_manager = PersonaManager()
        self.simulation_manager = SimulationManager(self)
        self.scheduler = Scheduler(self)
        self.ollama_client = OllamaClient()
        
        self.ping_counts = {} # {persona_name: count}
        self.has_run_startup = False

    async def setup_hook(self):
        """Loads all command cogs from the src/commands and src/core directories."""
        print("Loading all cogs...")
        cog_paths = [
            'src/commands',
            'src/core/economic_system',
            'src/core'
        ]
        
        for path in cog_paths:
            for filename in os.listdir(f'./{path}'):
                if filename.endswith('.py') and not filename.startswith('__'):
                    extension = f'{path.replace("/", ".")}.{filename[:-3]}'
                    try:
                        await self.load_extension(extension)
                        print(f"  > Loaded cog: {extension}")
                    except (commands.ExtensionAlreadyLoaded, commands.NoEntryPointError):
                        # Ignore files that aren't cogs or are already loaded
                        pass
                    except Exception as e:
                        print(f"Failed to load extension {extension}: {e}", file=sys.stderr)
        
        print("All cogs loaded.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        # on_ready can be called multiple times. We use a simple flag to run setup only once.
        if not self.has_run_startup:
            await self.wait_until_ready()
            
            # This is a critical step. The simulation must run *after* cogs are loaded
            # so that managers like EconomyManager are available.
            self.simulation_manager.run_offline_simulation()

            self.scheduler.start()
            
            if self.guilds:
                guild = self.guilds[0]
                if not discord.utils.get(guild.text_channels, name='control-panel'):
                    await self.setup_guild(guild)
            
            self.add_listener(self.on_summon, 'on_message')
            self.has_run_startup = True

    async def on_summon(self, message):
        """Listener for the ping-based summoning mechanic using roles."""
        if message.author.id != MASTER_ID or not message.role_mentions:
            return

        for role in message.role_mentions:
            persona = next((p for p in self.persona_manager.get_all_personas() if p.role_id == role.id), None)
            if not persona: continue

            should_respond = False
            if persona.is_online:
                should_respond = True
                print(f"[Summon] Master summoned online bot {persona.name}. Responding.")
            else:
                self.ping_counts[persona.name] = self.ping_counts.get(persona.name, 0) + 1
                print(f"[Summon] Master pinged offline bot {persona.name}. Ping count: {self.ping_counts[persona.name]}.")
                if self.ping_counts[persona.name] >= 3:
                    should_respond = True
                    persona.is_online = True
                    print(f"[Summon] {persona.name} has been awakened by the Master's persistent call.")
                    del self.ping_counts[persona.name]

            if should_respond:
                response_prompt = f"You are {persona.name}. Your Master has summoned you. Write a short, in-character response acknowledging the summons and asking how you may serve."
                response_text = self.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", response_prompt, persona.base_persona)
                
                if "Error:" not in response_text:
                    webhook = await self.get_cog('ControlPanel').get_webhook(message.channel)
                    await webhook.send(response_text, username=persona.name, avatar_url=self.user.avatar.url)
                else:
                    await message.channel.send(f"*{persona.name} feels the Master's call but seems unable to respond clearly.*")

    async def setup_guild(self, guild):
        """Creates the server structure as defined in the blueprint."""
        print(f"Performing first-time setup for guild: {guild.name}")

        for channel in await guild.fetch_channels():
            await channel.delete()

        master_only_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_member(MASTER_ID): discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        # --- THE CITADEL ---
        citadel = await guild.create_category("THE CITADEL")
        await guild.create_text_channel("announcements", category=citadel)
        # ... (and all other channel creations as before) ...
        await guild.create_text_channel("bot-commands-list", category=citadel, overwrites=master_only_overwrites)

        # --- CHARACTER ROLES & HOMES ---
        homes = await guild.create_category("CHARACTER HOMES")
        for persona in self.persona_manager.get_all_personas():
            role = await guild.create_role(name=persona.name, colour=discord.Colour(persona.aura_color), mentionable=True)
            persona.role_id = role.id
            home_channel_name = f"{persona.name.lower()}-s-chamber"
            await guild.create_text_channel(home_channel_name, category=homes)
        await guild.create_voice_channel("The Living Quarters", category=homes)

        # ... (and all other category/channel creations) ...

        # --- MASTER'S PRIVATE CHAMBERS ---
        master_chambers = await guild.create_category("MASTER'S PRIVATE CHAMBERS")
        await guild.create_text_channel("control-panel", category=master_chambers, overwrites=master_only_overwrites)
        await guild.create_text_channel("maya-s-daily-journal", category=master_chambers, overwrites=master_only_overwrites)
        await guild.create_text_channel("director-s-whispers", category=master_chambers, overwrites=master_only_overwrites)

        print("Guild setup complete.")

    async def invoke_command_as_persona(self, persona_name: str, channel_id: int, command_string: str):
        guild = self.guilds[0]
        persona = self.persona_manager.get_persona(persona_name)
        member = guild.get_member(self.user.id)
        channel = self.get_channel(channel_id)
        if not all([persona, member, channel]): return

        class MockMessage(discord.Object):
            def __init__(self, *, id, channel, author, content, persona_ref):
                super().__init__(id=id)
                self.channel = channel; self.author = author; self.content = content; self.persona = persona_ref
        
        msg = MockMessage(id=0, channel=channel, author=member, content=self.command_prefix + command_string, persona_ref=persona)
        ctx = await self.get_context(msg, cls=commands.Context)
        await self.invoke(ctx)
        
    async def close(self):
        print("Shutting down...")
        if hasattr(self, 'simulation_manager'): self.simulation_manager.save_current_time()
        if hasattr(self, 'scheduler'): self.scheduler.stop()
        await super().close()