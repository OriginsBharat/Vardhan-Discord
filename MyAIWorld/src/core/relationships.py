import discord
from discord.ext import commands

class Relationship:
    """
    Tracks the feelings of one persona towards another entity (user or persona).
    """
    def __init__(self, source_name: str, target_id):
        self.source_name = source_name
        self.target_id = target_id
        # Feelings can be tracked on a -100 to 100 scale
        self.affection = 0
        self.trust = 0
        self.fear = 0
        self.rivalry = 0

class RelationshipManager(commands.Cog):
    """
    Manages the web of relationships between all personas.
    """
    def __init__(self, bot):
        self.bot = bot
        # {source_name: {target_id: Relationship}}
        self.relationships = {}

    def get_relationship(self, source_name: str, target_id):
        """Gets or creates a relationship object."""
        if source_name not in self.relationships:
            self.relationships[source_name] = {}
        
        if target_id not in self.relationships[source_name]:
            self.relationships[source_name][target_id] = Relationship(source_name, target_id)
            
        return self.relationships[source_name][target_id]

    def update_relationship(self, source_name: str, target_id, **kwargs):
        """
        Updates the feelings in a relationship.
        kwargs: affection=10, fear=-5, etc.
        """
        relationship = self.get_relationship(source_name, target_id)
        for feeling, value in kwargs.items():
            if hasattr(relationship, feeling):
                current_value = getattr(relationship, feeling)
                new_value = max(-100, min(100, current_value + value))
                setattr(relationship, feeling, new_value)
        print(f"[Relationship] Updated {source_name}'s feelings for {target_id}: {kwargs}")

    @commands.command(name="feelings")
    @commands.is_owner() # A check for the Master's ID would be better
    async def check_feelings(self, ctx, source: str, target: discord.Member):
        """
        [MASTER ONLY] Checks how one persona feels about a user.
        Usage: !feelings <PersonaName> <@User>
        """
        source_name = source.capitalize()
        persona = self.bot.persona_manager.get_persona(source_name)
        if not persona:
            return await ctx.send(f":x: Persona '{source_name}' not found.")

        relationship = self.get_relationship(source_name, target.id)
        
        embed = discord.Embed(
            title=f"Relationship Status: {source_name} -> {target.display_name}",
            color=persona.aura_color
        )
        embed.add_field(name="Affection", value=str(relationship.affection))
        embed.add_field(name="Trust", value=str(relationship.trust))
        embed.add_field(name="Fear", value=str(relationship.fear))
        embed.add_field(name="Rivalry", value=str(relationship.rivalry))
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Adds the relationship manager to the bot."""
    bot.relationship_manager = RelationshipManager(bot)
    await bot.add_cog(bot.relationship_manager)