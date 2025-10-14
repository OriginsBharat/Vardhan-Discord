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

        self.persona_manager = PersonaManager()
        self.simulation_manager = SimulationManager(self)
        self.scheduler = Scheduler(self)
        self.ollama_client = OllamaClient()

        self.ping_counts = {}
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
                        pass
                    except Exception as e:
                        print(f"Failed to load extension {extension}: {e}", file=sys.stderr)

        print("All cogs loaded.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        if not self.has_run_startup:
            await self.wait_until_ready()

            self.simulation_manager.run_offline_simulation()
            self.scheduler.start()

            if self.guilds:
                guild = self.guilds[0]
                # The trigger for setup is the absence of the 'control-panel' channel.
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

                webhook = await self.get_cog('ControlPanel').get_webhook(message.channel)
                await webhook.send(response_text, username=persona.name, avatar_url=self.user.avatar.url if self.user.avatar else None)

    async def setup_guild(self, guild):
        """Creates the full server structure as defined in the blueprint."""
        print(f"Performing first-time setup for guild: {guild.name}")

        # Delete all existing channels and roles to ensure a clean slate
        for channel in await guild.fetch_channels():
            await channel.delete()
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed:
                await role.delete()

        # --- PERMISSIONS ---
        master_member = guild.get_member(MASTER_ID)
        if not master_member:
            print(f"CRITICAL: Master with ID {MASTER_ID} not found in guild. Aborting setup.")
            return

        master_only_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            master_member: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        # --- CATEGORIES & CHANNELS ---
        # THE CITADEL (Admin & Info)
        citadel = await guild.create_category("THE CITADEL")
        await guild.create_text_channel("announcements", category=citadel)
        await guild.create_text_channel("world-events", category=citadel)
        await guild.create_text_channel("bot-commands-list", category=citadel, overwrites=master_only_overwrites)

        # CHARACTER HOMES
        homes = await guild.create_category("CHARACTER HOMES")
        for persona in self.persona_manager.get_all_personas():
            role = await guild.create_role(name=persona.name, colour=discord.Colour(int(persona.aura_color, 16)), mentionable=True)
            persona.role_id = role.id # Assign role ID back to persona object
            home_channel_name = f"{persona.name.lower()}-s-chamber"
            await guild.create_text_channel(home_channel_name, category=homes)
        await guild.create_voice_channel("The Living Quarters", category=homes)

        # THE MARKET DISTRICT (Economy)
        market = await guild.create_category("THE MARKET DISTRICT")
        await guild.create_text_channel("the-market-square", category=market)
        await guild.create_text_channel("the-auction-house", category=market)
        await guild.create_text_channel("job-board", category=market)
        await guild.create_text_channel("bot-owned-shops", category=market)

        # THE VELVET DISTRICT (NSFW)
        velvet = await guild.create_category("THE VELVET DISTRICT")
        velvet_lounge = await guild.create_text_channel("the-velvet-lounge", category=velvet)
        await velvet_lounge.edit(nsfw=True)
        red_lantern = await guild.create_text_channel("the-red-lantern-brothel", category=velvet)
        await red_lantern.edit(nsfw=True)
        erotica_library = await guild.create_text_channel("erotica-library", category=velvet)
        await erotica_library.edit(nsfw=True)

        # MASTER'S PRIVATE CHAMBERS
        master_chambers = await guild.create_category("MASTER'S PRIVATE CHAMBERS", overwrites=master_only_overwrites)
        await guild.create_text_channel("control-panel", category=master_chambers)
        await guild.create_text_channel("maya-s-daily-journal", category=master_chambers)
        await guild.create_text_channel("director-s-whispers", category=master_chambers)

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