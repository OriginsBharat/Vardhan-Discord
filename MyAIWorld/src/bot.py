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
                    await self.run_narrative_startup(guild)
                    await self.post_command_lists(guild)
                    # Trigger one round of actions immediately to make the world feel alive.
                    await self.scheduler.trigger_autonomous_actions()

            self.add_listener(self.on_summon, 'on_message')
            self.has_run_startup = True

    async def run_narrative_startup(self, guild):
        """Posts a narrative countdown and backstory to immerse the user."""
        announcements_channel = discord.utils.get(guild.text_channels, name='announcements')
        whispers_channel = discord.utils.get(guild.text_channels, name='director-s-whispers')

        if not announcements_channel or not whispers_channel:
            print("Could not find required channels for narrative startup.")
            return

        # This function will run in the background
        async def post_snippets():
            await asyncio.sleep(10)
            await whispers_channel.send("`[RECOVERED LOG] ...simulation integrity at 99.8%. The Master's core matrix is stable, but the DashaRakshakas show... unexpected emotional variance. He must not know. Not yet.`")
            await asyncio.sleep(30)
            await whispers_channel.send("`[MEMORY FRAGMENT 77B] ...a flash of orange and purple light. The scent of ozone. Eka's hand on my shoulder. 'He is waking up,' she says. 'Prepare yourselves.'`")

        asyncio.create_task(post_snippets())

        # 1. Post Countdown
        embed = discord.Embed(title="Universe Synchronization In Progress", description="Restoring world state from last known backup...", color=0x3498DB)
        msg = await announcements_channel.send(embed=embed)
        for i in range(60, 0, -5):
            embed.description = f"**Restoring world state from last known backup...**\nTime until synchronization: **{i} seconds**"
            await msg.edit(embed=embed)
            await asyncio.sleep(5)

        # 3. Final Message
        embed.title = "Synchronization Complete"
        embed.description = "**Welcome, Master.**\nYour world is now online and fully operational. The consciousnesses have been restored."
        embed.color = 0x2ECC71
        await msg.edit(embed=embed)

    async def post_command_lists(self, guild):
        """Generates, posts, and pins lists of available commands."""
        print("Posting and pinning command lists...")
        control_panel_channel = discord.utils.get(guild.text_channels, name='control-panel')
        commands_list_channel = discord.utils.get(guild.text_channels, name='bot-commands-list')

        if not control_panel_channel or not commands_list_channel:
            print("Could not find required channels for posting command lists.")
            return

        master_commands = []
        general_commands = []

        for cmd in self.commands:
            # A command is considered a master command if its cog has a cog_check method.
            if cmd.cog and hasattr(cmd.cog, 'cog_check'):
                master_commands.append(cmd)
            else:
                general_commands.append(cmd)

        # 1. Master Commands
        master_embed = discord.Embed(title="Master Control Panel Commands", color=0xE74C3C)
        master_text = ""
        for cmd in sorted(master_commands, key=lambda c: c.name):
            help_text = (cmd.help or "No description provided.").split('[MASTER ONLY] ')[-1]
            master_text += f"**`{self.command_prefix}{cmd.name}`**: {help_text}\n"
        master_embed.description = master_text
        msg = await control_panel_channel.send(embed=master_embed)
        await msg.pin()

        # 2. General Commands
        general_embed = discord.Embed(title="General Commands", color=0x2ECC71)
        general_text = ""
        for cmd in sorted(general_commands, key=lambda c: c.name):
            general_text += f"**`{self.command_prefix}{cmd.name}`**: {cmd.help or 'No description provided.'}\n"
        general_embed.description = general_text
        msg = await commands_list_channel.send(embed=general_embed)
        await msg.pin()
        print("Command lists posted.")

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

        async def safe_delete(item):
            try:
                await item.delete()
                print(f"  > Deleted {item.name}")
                await asyncio.sleep(1)
            except discord.HTTPException as e:
                print(f"  > FAILED to delete {item.name}: {e.status}")

        print("Deleting old channels and roles...")
        for channel in await guild.fetch_channels(): await safe_delete(channel)
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed: await safe_delete(role)

        master_member = guild.get_member(MASTER_ID)
        if not master_member:
            print(f"CRITICAL: Master with ID {MASTER_ID} not found in guild. Aborting setup.")
            return

        master_only_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            master_member: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        async def safe_create(coro, name):
            try:
                result = await coro
                print(f"  > Created {name}")
                await asyncio.sleep(1)
                return result
            except discord.HTTPException as e:
                print(f"  > FAILED to create {name}: {e.status}")
                return None

        print("Creating new server structure...")

        citadel = await safe_create(guild.create_category("THE CITADEL"), "THE CITADEL")
        if citadel:
            await safe_create(citadel.create_text_channel("announcements"), "announcements")
            await safe_create(citadel.create_text_channel("world-events"), "world-events")
            await safe_create(citadel.create_text_channel("bot-commands-list", overwrites=master_only_overwrites), "bot-commands-list")

        homes = await safe_create(guild.create_category("CHARACTER HOMES"), "CHARACTER HOMES")
        if homes:
            for persona in self.persona_manager.get_all_personas():
                role = await safe_create(guild.create_role(name=persona.name, colour=discord.Colour(persona.aura_color), mentionable=True), f"Role: {persona.name}")
                if role:
                    persona.role_id = role.id
                await safe_create(homes.create_text_channel(f"{persona.name.lower()}-s-chamber"), f"{persona.name.lower()}-s-chamber")
            await safe_create(homes.create_voice_channel("The Living Quarters"), "The Living Quarters")

        market = await safe_create(guild.create_category("THE MARKET DISTRICT"), "THE MARKET DISTRICT")
        if market:
            await safe_create(market.create_text_channel("the-market-square"), "the-market-square")
            await safe_create(market.create_text_channel("the-auction-house"), "the-auction-house")
            await safe_create(market.create_text_channel("job-board"), "job-board")
            await safe_create(market.create_text_channel("bot-owned-shops"), "bot-owned-shops")

        velvet = await safe_create(guild.create_category("THE VELVET DISTRICT"), "THE VELVET DISTRICT")
        if velvet:
            velvet_lounge = await safe_create(velvet.create_text_channel("the-velvet-lounge"), "the-velvet-lounge")
            if velvet_lounge: await safe_create(velvet_lounge.edit(nsfw=True), "velvet_lounge nsfw")
            red_lantern = await safe_create(velvet.create_text_channel("the-red-lantern-brothel"), "the-red-lantern-brothel")
            if red_lantern: await safe_create(red_lantern.edit(nsfw=True), "red_lantern nsfw")
            erotica_library = await safe_create(velvet.create_text_channel("erotica-library"), "erotica-library")
            if erotica_library: await safe_create(erotica_library.edit(nsfw=True), "erotica_library nsfw")

        master_chambers = await safe_create(guild.create_category("MASTER'S PRIVATE CHAMBERS", overwrites=master_only_overwrites), "MASTER'S PRIVATE CHAMBERS")
        if master_chambers:
            await safe_create(master_chambers.create_text_channel("control-panel"), "control-panel")
            await safe_create(master_chambers.create_text_channel("maya-s-daily-journal"), "maya-s-daily-journal")
            await safe_create(master_chambers.create_text_channel("director-s-whispers"), "director-s-whispers")

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