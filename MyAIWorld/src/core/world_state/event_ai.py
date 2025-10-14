import discord
import random
from discord.ext import commands

class EventAI(commands.Cog):
    """The 'Director' bot that autonomously generates server-wide events."""
    def __init__(self, bot):
        self.bot = bot
        self.event_themes = [
            "economic boom/bust", "a political intrigue", "a magical anomaly",
            "a cultural festival", "a natural disaster", "a 'Whisper of Madness'",
            "a divine blessing/curse", "a criminal underground power shift"
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

        await self.create_event_command(event_idea, announcements_channel)

    async def create_event_command(self, event_idea: str, channel: discord.TextChannel):
        """Creates a dynamic command related to the generated event."""
        self.bot.command_factory.remove_all_created_commands()

        cmd_prompt = f"Based on the event '{event_idea}', generate a short, one-word command name (lowercase_snake_case) and a brief help description for a command a player could use to interact with this event. Format it as: command_name;description"
        cmd_details = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", cmd_prompt)
        if "Error:" in cmd_details or ';' not in cmd_details: return
            
        name, description = cmd_details.split(';', 1)

        async def event_command_callback(ctx):
            response_prompt = f"As the world's narrator, describe the outcome of a player trying to '{name}' during the '{event_idea}' event."
            response_text = self.bot.ollama_client.generate_text("dolphin-2.2.1-mistral:7b-q4_K_M", response_prompt)
            await ctx.send(f"*{response_text}*")

        self.bot.command_factory.create_command(name.strip(), description.strip(), event_command_callback)
        
        cmd_list_channel = discord.utils.get(self.bot.guilds[0].text_channels, name='bot-commands-list')
        if cmd_list_channel:
            await cmd_list_channel.send(f"**New Event Command Created:**\n- `!{name.strip()}`: {description.strip()}")

async def setup(bot):
    bot.event_ai = EventAI(bot)
    await bot.add_cog(bot.event_ai)