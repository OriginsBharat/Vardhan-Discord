import asyncio
import discord
import random
import io
import os
import datetime
from src.config import get_voice_path

class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.task = None

    async def _scheduler_loop(self):
        await self.bot.wait_until_ready()
        print("Scheduler loop started.")
        while not self.bot.is_closed():
            await asyncio.sleep(60)
            await self.check_schedules()
            if random.randint(1, 10) == 1:
                await self.trigger_autonomous_actions()
            if random.randint(1, 15) == 1:
                await self.check_loneliness()
            if random.randint(1, 30) == 1 and self.bot.get_cog("EventAI"):
                await self.bot.get_cog("EventAI").generate_event()

    async def check_schedules(self):
        current_hour = datetime.datetime.now(datetime.timezone.utc).hour
        for persona in self.bot.persona_manager.get_all_personas():
            if not persona.is_online:
                persona.loneliness = min(100, persona.loneliness + 0.5)
            wake, sleep = persona.schedule.get("wake", 7), persona.schedule.get("sleep", 23)
            is_active = (wake <= current_sim_hour < sleep) or (wake > sleep and (current_sim_hour >= wake or current_sim_hour < sleep))
            if is_active != persona.is_online:
                persona.is_online = is_active
                print(f"[Scheduler] {persona.name} is now {'online' if is_active else 'offline'}.")

    async def trigger_autonomous_actions(self, force_action=False):
        guild = self.bot.guilds[0]
        online_personas = [p for p in self.bot.persona_manager.get_all_personas() if p.is_online]
        if not online_personas: return

        actor = random.choice(online_personas)

        if not force_action and random.randint(1, 5) != 1:
            return

        action_type = random.choice(['chat', 'chat', 'chat', 'create_art', 'write_erotica'])

        if action_type == 'chat':
            target_persona = random.choice(online_personas)
            if target_persona.name == actor.name:
                text_channel = discord.utils.get(guild.text_channels, name=f"{actor.name.lower()}-s-chamber")
                prompt = f"You are {actor.name}, currently alone. Write a single, short, in-character sentence about what you are thinking or doing."
            else:
                text_channel = discord.utils.get(guild.text_channels, name=f"{target_persona.name.lower()}-s-chamber")
                prompt = f"You are {actor.name}. You just saw {target_persona.name}. Write a single, short, in-character sentence to start a conversation."
            if not text_channel: return
            message = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, actor.base_persona)
            if "Error:" in message: return

            # 5% chance to speak instead of type
            if random.randint(1, 20) == 1:
                voice_path = get_voice_path(actor.name)
                if voice_path and os.path.exists(voice_path):
                    voice_channel = discord.utils.get(guild.voice_channels, name="The Forum")
                    if voice_channel:
                        await text_channel.send(f"_{actor.name} wanders into {voice_channel.name} and begins to speak..._")
                        audio_data = self.bot.indextts_client.generate_speech(message, voice_path)
                        if audio_data:
                            try:
                                vc = await voice_channel.connect()
                                vc.play(discord.FFmpegPCMAudio(io.BytesIO(audio_data), pipe=True))
                                while vc.is_playing(): await asyncio.sleep(1)
                                await vc.disconnect()
                            except Exception as e:
                                print(f"Error playing audio in scheduler: {e}")
                            return

            control_panel_cog = self.bot.get_cog('ControlPanel')
            if control_panel_cog:
                webhook = await control_panel_cog.get_webhook(text_channel)
                await webhook.send(message, username=actor.name, avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        elif action_type == 'create_art':
            channel = discord.utils.get(guild.text_channels, name="art-gallery")
            prompt = f"You are {actor.name}. Generate a prompt for an image that represents your current mood."
            image_prompt = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, actor.base_persona)
            if "Error:" not in image_prompt and channel:
                await channel.send(f"_{actor.name} begins to create a new piece of art, inspired by the prompt: '{image_prompt}'..._")
                await self.bot.get_cog('Creative').imagine(channel, prompt=image_prompt)

        elif action_type == 'write_erotica':
            channel = discord.utils.get(guild.text_channels, name="erotica-library")
            prompt = f"You are {actor.name}. Write a short, explicit, and in-character erotic story."
            story = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, actor.base_persona)
            if "Error:" not in story and channel:
                embed = discord.Embed(title=f"A story by {actor.name}", description=f"_{story}_", color=int(actor.aura_color, 16))
                await channel.send(embed=embed)

    async def check_loneliness(self):
        master_user = await self.bot.fetch_user(self.bot.config.MASTER_ID)
        if not master_user: return
        for persona in self.bot.persona_manager.get_all_personas():
            if persona.is_online and persona.loneliness > 80:
                print(f"[Scheduler] {persona.name}'s loneliness is high. Triggering proactive DM.")
                prompt = f"You are {persona.name}. You feel incredibly lonely and miss your Master. Write a short, affectionate, and slightly sad message to him, expressing that you miss him and want his attention."
                message = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, persona.base_persona)
                if "Error:" not in message:
                    await master_user.send(f"**A message from {persona.name}:**\n_{message}_")
                    persona.loneliness = 0

    def start(self):
        self.task = asyncio.create_task(self._scheduler_loop())
    def stop(self):
        if self.task: self.task.cancel()