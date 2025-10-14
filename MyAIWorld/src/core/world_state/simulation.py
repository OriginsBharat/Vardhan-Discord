import datetime
import json
import os
from src.core.economic_system.professions import get_profession_data

class SimulationManager:
    """Manages the 'Illusion of 24/7' by simulating offline progress."""
    def __init__(self, bot):
        self.bot = bot
        self.last_online_path = "data/world_state.json"

    def get_last_online_time(self):
        if not os.path.exists(self.last_online_path):
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            with open(self.last_online_path, 'r') as f:
                data = json.load(f)
                return datetime.datetime.fromisoformat(data['last_online'])
        except (IOError, json.JSONDecodeError):
            return datetime.datetime.now(datetime.timezone.utc)

    def save_current_time(self):
        with open(self.last_online_path, 'w') as f:
            data = {'last_online': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            json.dump(data, f)

    def run_offline_simulation(self):
        """Calculates offline time and updates world state accordingly."""
        last_online = self.get_last_online_time()
        now = datetime.datetime.now(datetime.timezone.utc)
        offline_duration = now - last_online
        
        if offline_duration.total_seconds() < 60:
            print("[Simulation] No significant offline time detected.")
            return

        print(f"[Simulation] World was offline for {offline_duration}. Running simulation...")
        hours_offline = offline_duration.total_seconds() / 3600

        for persona in self.bot.persona_manager.get_all_personas():
            profession_data = get_profession_data(persona.name)
            if profession_data:
                earnings = int(profession_data['hourly_rate'] * hours_offline)
                if earnings > 0 and hasattr(self.bot, 'economy_manager'):
                    self.bot.economy_manager.add_balance(persona.name, earnings)
                    print(f"  > {persona.name} earned {earnings} Rs as a {profession_data['job_title']}.")

            neediness_growth = getattr(persona, 'neediness_growth_rate', 1.5) * hours_offline
            persona.neediness = min(100, persona.neediness + int(neediness_growth))
            persona.horny = max(0, persona.horny - int(1 * hours_offline))
            print(f"  > {persona.name}'s state updated: Neediness={persona.neediness}, Horny={persona.horny}.")

        print("[Simulation] Offline simulation complete.")