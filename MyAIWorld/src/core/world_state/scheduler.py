import asyncio
import discord
import random
import io
import datetime

class Scheduler:
    """The asynchronous heartbeat of the world. Triggers events at set intervals."""
    def __init__(self, bot):
        self.bot = bot
        self.task = None

    async def _scheduler_loop(self):
        """The main loop that runs continuously."""
        await self.bot.wait_until_ready()
        print("Scheduler loop started.")
        
        counter = 0
        while not self.bot.is_closed():
            await asyncio.sleep(1)
            counter += 1
            
            if counter % 60 == 0: await self.check_schedules()
            if counter % 300 == 0: await self.check_neediness()
            if counter % 600 == 0: await self.check_loans()
            if counter % 1200 == 0: await self.trigger_autonomous_actions()
            if counter % 1800 == 0: await self.trigger_event_ai()
            if counter % 86400 == 86100: await self.generate_masters_journal()

    async def check_schedules(self):
        """Checks bot schedules and updates their online/offline status."""
        current_hour = datetime.datetime.now(datetime.timezone.utc).hour
        for persona in self.bot.persona_manager.get_all_personas():
            wake_time, sleep_time = persona.schedule.get("wake", 7), persona.schedule.get("sleep", 23)

            is_currently_active = False
            # This logic correctly handles overnight schedules (e.g., wake at 22, sleep at 10)
            if wake_time < sleep_time:
                # Standard daytime schedule
                is_currently_active = wake_time <= current_hour < sleep_time
            else:
                # Overnight schedule
                is_currently_active = current_hour >= wake_time or current_hour < sleep_time

            if is_currently_active and not persona.is_online:
                persona.is_online = True
                print(f"[Scheduler] {persona.name} is now online.")
            elif not is_currently_active and persona.is_online:
                persona.is_online = False
                print(f"[Scheduler] {persona.name} is now offline.")

    async def check_neediness(self):
        """Checks bot neediness levels and may trigger a seductive DM to the Master."""
        try:
            master_user = await self.bot.fetch_user(self.bot.config.MASTER_ID)
            if not master_user: return
        except discord.NotFound: return

        for persona in self.bot.persona_manager.get_all_personas():
            if persona.is_online and persona.neediness > getattr(persona, 'neediness_threshold', 75):
                print(f"[Scheduler] {persona.name}'s neediness is high. Triggering seductive DM.")
                persona.neediness = 0
                # ... (DM logic as previously defined) ...

    async def check_loans(self):
        """Checks for defaulted loans."""
        if hasattr(self.bot, 'loan_manager'):
            await self.bot.loan_manager.check_for_defaults()

    async def trigger_autonomous_actions(self):
        """Gives each bot a chance to perform an autonomous action based on their personality."""
        guild = self.bot.guilds[0]
        if not guild: return
        for persona in self.bot.persona_manager.get_all_personas():
            if not persona.is_online: continue
            # ... (Complex decision-making logic as previously defined) ...

    async def trigger_event_ai(self):
        """Triggers the Event AI to potentially generate a new world event."""
        if hasattr(self.bot, 'event_ai') and random.randint(1, 2) == 1:
            await self.bot.event_ai.generate_event()
        
    async def generate_masters_journal(self):
        """Has Maya generate a narrative summary of the day's events."""
        journal_channel = discord.utils.get(self.bot.guilds[0].text_channels, name='maya-s-daily-journal')
        maya_persona = self.bot.persona_manager.get_persona("Maya")
        if not journal_channel or not maya_persona: return

        prompt = "You are Maya. Write a beautiful, personal, and slightly poetic journal entry for your Master, summarizing the day's key events and feelings in our world."
        journal_entry = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", prompt, maya_persona.base_persona)
        if "Error:" not in journal_entry:
            embed = discord.Embed(title=f"The Master's Journal: {datetime.date.today()}", description=f"_{journal_entry}_", color=maya_persona.aura_color)
            await journal_channel.send(embed=embed)

    def start(self):
        self.task = asyncio.create_task(self._scheduler_loop())
    def stop(self):
        if self.task: self.task.cancel()