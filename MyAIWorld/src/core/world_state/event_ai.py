import discord
import random
from discord.ext import commands

class EventAI(commands.Cog):
    """The 'Director' bot that autonomously generates server-wide events."""
    def __init__(self, bot):
        self.bot = bot
        self.event_themes = [
            "a sudden economic boom", "a political conspiracy", "a strange magical anomaly",
            "a forgotten cultural festival", "a minor natural disaster", "a whisper of madness spreading through the populace",
            "a divine blessing from a forgotten god", "a shift in the criminal underground"
        ]

    async def generate_event(self):
        """Generates and announces a new world event."""
        guild = self.bot.guilds[0]
        announcements_channel = discord.utils.get(guild.text_channels, name='announcements')
        if not announcements_channel: return

        theme = random.choice(self.event_themes)
        idea_prompt = f"You are the 'Director' of a dark fantasy world. Generate a single, concise, creative event idea based on the theme: '{theme}'. Just the core idea, one sentence."
        event_idea = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", idea_prompt)
        if "Error:" in event_idea or not event_idea: return

        announcement_prompt = f"You are the 'Director' of a dark fantasy world. Write a short, immersive announcement for this server event: '{event_idea}'. Make it dramatic and mysterious."
        description = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", announcement_prompt)
        if "Error:" in description: return

        embed = discord.Embed(title="🌐 A World Event is Unfolding...", description=description, color=0x9B59B6)
        await announcements_channel.send(embed=embed)
        print(f"[EventAI] Generated new world event: {event_idea}")

async def setup(bot):
    await bot.add_cog(EventAI(bot))