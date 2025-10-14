import datetime
from discord.ext import commands

class Scar:
    """Represents a single psychological scar."""
    def __init__(self, scar_type: str, description: str, inflicted_by: str = "The World"):
        self.scar_type = scar_type
        self.description = description
        self.inflicted_by = inflicted_by
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return f"<Scar: {self.scar_type} - {self.description}>"

class ScarManager(commands.Cog):
    """
    Manages the infliction and tracking of psychological scars on personas.
    """
    def __init__(self, bot):
        self.bot = bot
        # In a real implementation, scars would be loaded from and saved to a persistent database.

    def inflict_scar(self, bot_name: str, scar_type: str, description: str, inflicted_by: str = "The World"):
        """
        Inflicts a new scar on a bot, modifying their persona.
        """
        persona = self.bot.persona_manager.get_persona(bot_name.capitalize())
        if not persona:
            print(f"Error: Could not inflict scar. Persona '{bot_name}' not found.")
            return None

        new_scar = Scar(scar_type, description, inflicted_by)
        persona.scars.append(new_scar)
        
        # This is the core mechanic: the trauma permanently changes them by altering their base prompt.
        scar_prompt_addition = f"\n\n[Psychological Scar: {scar_type}] - {description} This event has left a permanent mark on your soul, forever influencing your thoughts and actions."
        persona.base_persona += scar_prompt_addition
        
        print(f"Successfully inflicted scar '{scar_type}' on {bot_name}.")
        # Here you would save the updated persona state to the database.
        
        return new_scar

async def setup(bot):
    """Adds the scar manager to the bot."""
    bot.scar_manager = ScarManager(bot)
    await bot.add_cog(bot.scar_manager)