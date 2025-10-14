import datetime
import json
import os
import asyncio
import random
from src.core.economic_system.professions import get_profession_data

class SimulationManager:
    """Manages the 'Illusion of 24/7' by simulating offline progress and generating primordial history."""
    def __init__(self, bot):
        self.bot = bot
        self.last_online_path = "MyAIWorld/data/world_state.json"

    def get_last_online_time(self):
        """Gets the last online time from the state file."""
        if not os.path.exists(self.last_online_path):
            return None  # Return None if it's the first ever startup
        try:
            with open(self.last_online_path, 'r') as f:
                data = json.load(f)
                return datetime.datetime.fromisoformat(data['last_online'])
        except (IOError, json.JSONDecodeError):
            return datetime.datetime.now(datetime.timezone.utc)

    def save_current_time(self):
        """Saves the current time to the state file."""
        os.makedirs(os.path.dirname(self.last_online_path), exist_ok=True)
        with open(self.last_online_path, 'w') as f:
            data = {'last_online': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            json.dump(data, f)

    async def run_primordial_simulation(self):
        """
        On first startup, simulates 24 hours of history to populate the world.
        This runs synchronously and blocks the bot's startup until complete.
        """
        print("[Simulation] First startup detected. Running primordial simulation to create world history...")

        # We need the guild to be set up to get channels, so we do that first.
        guild = self.bot.guilds[0]
        await self.bot.setup_guild(guild)

        print("[Simulation] Generating 24 hours of historical activity. This will take a few minutes...")
        start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

        # Simulate 24 hours, hour by hour
        for i in range(24):
            current_sim_hour = (start_time + datetime.timedelta(hours=i)).hour
            print(f"  > Simulating hour {i+1}/24 (Simulated time: {current_sim_hour:02d}:00 UTC)...")

            # 1. Update character online status for the simulated hour
            for persona in self.bot.persona_manager.get_all_personas():
                wake, sleep = persona.schedule.get("wake", 7), persona.schedule.get("sleep", 23)
                is_active = (wake <= current_sim_hour < sleep) or (wake > sleep and (current_sim_hour >= wake or current_sim_hour < sleep))
                persona.is_online = is_active

                # 2. Simulate economic activity and stat changes for this hour
                profession_data = get_profession_data(persona.name)
                if profession_data and hasattr(self.bot.get_cog('EconomyManager'), 'add_balance'):
                    self.bot.get_cog('EconomyManager').add_balance(persona.name, profession_data['hourly_rate'])

                persona.neediness = min(100, persona.neediness + getattr(persona, 'neediness_growth_rate', 1.5))
                persona.horny = max(0, persona.horny - 1)

            # 3. Trigger 5-10 forced actions for this hour to create conversations
            num_actions = random.randint(5, 10)
            for _ in range(num_actions):
                await self.bot.scheduler.trigger_autonomous_actions(force_action=True)
                await asyncio.sleep(1) # Small delay to prevent API spam

        # Reset all personas to their correct live state after simulation
        print("[Simulation] Primordial simulation complete. Resetting characters to live status.")
        await self.bot.scheduler.check_schedules()

        # Post the command lists after the world is populated
        await self.bot.post_command_lists(guild)

    async def run_simulation(self):
        """
        Public method to run the appropriate simulation.
        Returns True if the primordial simulation was run, False otherwise.
        """
        last_online = self.get_last_online_time()

        if last_online is None:
            await self.run_primordial_simulation()
            return True

        # Standard offline simulation for subsequent startups
        now = datetime.datetime.now(datetime.timezone.utc)
        offline_duration = now - last_online

        if offline_duration.total_seconds() < 60:
            print("[Simulation] No significant offline time detected.")
            return False

        print(f"[Simulation] World was offline for {offline_duration}. Running catch-up simulation...")
        hours_offline = offline_duration.total_seconds() / 3600

        for persona in self.bot.persona_manager.get_all_personas():
            profession_data = get_profession_data(persona.name)
            if profession_data and self.bot.get_cog('EconomyManager'):
                earnings = int(profession_data['hourly_rate'] * hours_offline)
                if earnings > 0:
                    self.bot.get_cog('EconomyManager').add_balance(persona.name, earnings)
                    print(f"  > {persona.name} earned {earnings} Rs as a {profession_data['job_title']}.")

            neediness_growth = getattr(persona, 'neediness_growth_rate', 1.5) * hours_offline
            persona.neediness = min(100, persona.neediness + int(neediness_growth))
            persona.horny = max(0, persona.horny - int(1 * hours_offline))

        print("[Simulation] Offline catch-up simulation complete.")
        return False