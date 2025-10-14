from discord.ext import commands

class Power:
    """
    Represents a specific power or ability a persona might have.
    This can be expanded to include cooldowns, effects, etc.
    """
    def __init__(self, name: str, description: str, power_level_modifier: int = 0):
        self.name = name
        self.description = description
        self.power_level_modifier = power_level_modifier

class PowerManager(commands.Cog):
    """
    A system for managing the powers of each persona.
    In a full implementation, this would load powers from a file or database.
    This cog primarily exists to be loaded and attached to the bot object.
    """
    def __init__(self, bot):
        self.bot = bot
        self.powers = {} # {persona_name: [Power, ...]}

    def grant_power(self, persona_name: str, power: Power):
        """Grants a new power to a persona."""
        if persona_name not in self.powers:
            self.powers[persona_name] = []
        
        self.powers[persona_name].append(power)
        
        # Optionally, adjust the persona's base power level
        persona = self.bot.persona_manager.get_persona(persona_name)
        if persona:
            persona.power_level += power.power_level_modifier

    def get_powers(self, persona_name: str):
        """Gets all powers for a specific persona."""
        return self.powers.get(persona_name, [])

async def setup(bot):
    """Adds the power manager to the bot."""
    bot.power_manager = PowerManager(bot)
    await bot.add_cog(bot.power_manager)