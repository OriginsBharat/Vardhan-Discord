import datetime
import json
import os
import asyncio
import random

class SimulationManager:
    def __init__(self, bot):
        self.bot = bot
        self.last_online_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "world_state.json")

    def get_last_online_time(self):
        if not os.path.exists(self.last_online_path):
            return None
        try:
            with open(self.last_online_path, 'r') as f:
                return datetime.datetime.fromisoformat(json.load(f)['last_online'])
        except (IOError, json.JSONDecodeError):
            return datetime.datetime.now(datetime.timezone.utc)

    def save_current_time(self):
        os.makedirs(os.path.dirname(self.last_online_path), exist_ok=True)
        with open(self.last_online_path, 'w') as f:
            json.dump({'last_online': datetime.datetime.now(datetime.timezone.utc).isoformat()}, f)

    async def run_primordial_simulation(self):
        print("[Simulation] First startup. Running primordial simulation...")
        guild = self.bot.guilds[0]
        await self.bot.setup_guild(guild)

        print("[Simulation] Generating 24 hours of history...")
        start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        for i in range(24):
            current_sim_hour = (start_time + datetime.timedelta(hours=i)).hour
            print(f"  > Simulating hour {i+1}/24 ({current_sim_hour:02d}:00 UTC)...")
            for persona in self.bot.persona_manager.get_all_personas():
                wake, sleep = persona.schedule.get("wake", 7), persona.schedule.get("sleep", 23)
                persona.is_online = (wake <= current_sim_hour < sleep) or (wake > sleep and (current_sim_hour >= wake or current_sim_hour < sleep))

            num_actions = random.randint(10, 20)
            for _ in range(num_actions):
                await self.bot.scheduler.trigger_autonomous_actions(force_action=True)
                await asyncio.sleep(0.5)

        await self.bot.scheduler.check_schedules()
        await self.bot.post_command_lists(guild)
        print("[Simulation] Primordial simulation complete.")

    async def run_simulation(self):
        last_online = self.get_last_online_time()
        if last_online is None:
            await self.run_primordial_simulation()
            return True
        print("[Simulation] Existing world detected. Skipping primordial simulation.")
        return False