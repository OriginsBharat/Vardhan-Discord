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

            # This is now the single point of entry for simulation.
            # It will block and run the primordial simulation on the first run,
            # or run a quick catch-up on subsequent runs.
            # It returns True only if the primordial (first-run) simulation was executed.
            is_first_run = await self.simulation_manager.run_simulation()

            # If it wasn't the first run, we still need to check if we should post command lists,
            # in case they were deleted.
            if not is_first_run and self.guilds:
                guild = self.guilds[0]
                control_panel_channel = discord.utils.get(guild.text_channels, name='control-panel')
                # Check if the channel exists and is empty
                if control_panel_channel and not any(await control_panel_channel.history(limit=1).flatten()):
                    await self.post_command_lists(guild)

            # The live scheduler for real-time events always starts after the simulation is complete.
            self.scheduler.start()

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
        """Creates the full server structure, completely visible from the start."""
        print("Performing first-time setup for guild... This may take a moment.")
        # Clean slate
        for channel in await guild.fetch_channels(): await channel.delete()
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed: await role.delete()

        master_member = guild.get_member(MASTER_ID)
        if not master_member:
            print(f"CRITICAL: Master with ID {MASTER_ID} not found. Aborting.")
            return

        # Permissions for the Master's private channels
        master_only_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            master_member: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        print("Creating server roles...")
        for persona in self.persona_manager.get_all_personas():
            role = await guild.create_role(name=persona.name, colour=discord.Colour(persona.aura_color), mentionable=True)
            persona.role_id = role.id
            # Assign role to Master for easy pinging
            if master_member:
                await master_member.add_roles(role)

        print("Creating server categories and channels...")
        # Public Categories
        citadel = await guild.create_category("THE CITADEL")
        await citadel.create_text_channel("announcements")
        await citadel.create_text_channel("world-events")
        await citadel.create_text_channel("bot-commands-list")
        await citadel.create_voice_channel("The Forum")

        homes = await guild.create_category("CHARACTER HOMES")
        for persona in self.persona_manager.get_all_personas():
            await homes.create_text_channel(f"{persona.name.lower()}-s-chamber")

        market = await guild.create_category("THE MARKET DISTRICT")
        await market.create_text_channel("the-market-square")
        await market.create_text_channel("the-auction-house")
        await market.create_text_channel("job-board")
        await market.create_text_channel("bot-owned-shops")
        await market.create_voice_channel("The Exchange")

        velvet = await guild.create_category("THE VELVET DISTRICT")
        velvet_lounge = await velvet.create_text_channel("the-velvet-lounge")
        await velvet_lounge.edit(nsfw=True)
        red_lantern = await velvet.create_text_channel("the-red-lantern-brothel")
        await red_lantern.edit(nsfw=True)
        erotica_library = await velvet.create_text_channel("erotica-library")
        await erotica_library.edit(nsfw=True)
        await velvet.create_voice_channel("The Whisper Room")

        creative = await guild.create_category("CREATIVE WORKS")
        await creative.create_text_channel("art-gallery")
        nsfw_art_gallery = await creative.create_text_channel("nsfw-art-gallery")
        await nsfw_art_gallery.edit(nsfw=True)
        await creative.create_voice_channel("The Studio")

        # Master's chambers are created last and are private.
        master_chambers = await guild.create_category("MASTER'S PRIVATE CHAMBERS", overwrites=master_only_overwrites)
        await master_chambers.create_text_channel("control-panel")
        await master_chambers.create_text_channel("maya-s-daily-journal")
        await master_chambers.create_text_channel("director-s-whispers")

        print("Initial guild structure created.")

    async def post_command_lists(self, guild):
        """Generates, posts, and pins lists of available commands."""
        print("Posting and pinning command lists...")
        control_panel_channel = discord.utils.get(guild.text_channels, name='control-panel')
        commands_list_channel = discord.utils.get(guild.text_channels, name='bot-commands-list')

        await commands_list_channel.set_permissions(guild.get_member(MASTER_ID), read_messages=True)

        master_commands = []
        general_commands = []
        for cmd in self.commands:
            if cmd.cog and hasattr(cmd.cog, 'cog_check'): master_commands.append(cmd)
            else: general_commands.append(cmd)

        master_embed = discord.Embed(title="Master Control Panel Commands", color=0xE74C3C)
        master_text = ""
        for cmd in sorted(master_commands, key=lambda c: c.name):
            help_text = (cmd.help or "No description provided.").split('[MASTER ONLY] ')[-1]
            master_text += f"**`{self.command_prefix}{cmd.name}`**: {help_text}\n"
        master_embed.description = master_text
        msg = await control_panel_channel.send(embed=master_embed)
        await msg.pin()

        general_embed = discord.Embed(title="General Commands", color=0x2ECC71)
        general_text = ""
        for cmd in sorted(general_commands, key=lambda c: c.name):
            general_text += f"**`{self.command_prefix}{cmd.name}`**: {cmd.help or 'No description provided.'}\n"
        general_embed.description = general_text
        msg = await commands_list_channel.send(embed=general_embed)
        await msg.pin()
        print("Command lists posted.")

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