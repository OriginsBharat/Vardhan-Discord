import discord
from discord.ext import commands
from src.config import MASTER_ID

class ControlPanel(commands.Cog):
    """
    Contains all commands exclusively for the Master's use.
    """
    def __init__(self, bot):
        self.bot = bot
        self.possessed_bot = None # Tracks the currently possessed bot's persona object
        self.webhooks = {} # Cache for webhooks {channel_id: webhook}

    async def get_webhook(self, channel):
        """Gets or creates a webhook for a channel."""
        if channel.id in self.webhooks:
            return self.webhooks[channel.id]

        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.user == self.bot.user:
                self.webhooks[channel.id] = webhook
                return webhook

        new_webhook = await channel.create_webhook(name="My AI World Messenger")
        self.webhooks[channel.id] = new_webhook
        return new_webhook

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for messages from the Master to speak as the possessed bot."""
        if self.possessed_bot and message.author.id == MASTER_ID and not message.content.startswith(self.bot.command_prefix):
            try:
                webhook = await self.get_webhook(message.channel)
                await message.delete()
                # Use a placeholder avatar for now, or fetch the bot's real one if available
                avatar = self.bot.user.avatar.url if self.bot.user.avatar else None
                await webhook.send(
                    message.content,
                    username=self.possessed_bot.name,
                    avatar_url=avatar
                )
            except Exception as e:
                print(f"Error sending message as possessed bot: {e}")
                await message.channel.send(f":x: **Possession Error:** Could not send message as {self.possessed_bot.name}. Releasing control.", delete_after=10)
                self.possessed_bot = None

    async def cog_check(self, ctx):
        """Restricts all commands in this cog to the Master."""
        return ctx.author.id == MASTER_ID

    @commands.command(name="possess", help="[MASTER ONLY] Take direct control of a bot to speak as them. Usage: !possess <BotName>")
    async def possess(self, ctx, bot_name: str):
        """[MASTER ONLY] Possesses a bot, allowing you to speak as them."""
        persona = self.bot.persona_manager.get_persona(bot_name.capitalize())
        if not persona:
            return await ctx.send(f":x: **Error:** Persona '{bot_name}' not found.")

        self.possessed_bot = persona
        await ctx.send(f"👑 You now possess **{persona.name}**. All your messages in this server will now be sent as them. Use `!release` to stop.")

    @commands.command(name="release", help="[MASTER ONLY] Release control of a possessed bot.")
    async def release(self, ctx):
        """[MASTER ONLY] Releases control of a possessed bot."""
        if not self.possessed_bot:
            return await ctx.send(":x: You are not currently possessing any bot.")

        released_name = self.possessed_bot.name
        self.possessed_bot = None
        await ctx.send(f"✅ You have released **{released_name}**.")

    @commands.command(name="adjust", help="[MASTER ONLY] Adjust an emotional slider for a bot. Usage: !adjust <BotName> <Emotion> <Value>")
    async def adjust_slider(self, ctx, bot_name: str, emotion: str, value: int):
        """[MASTER ONLY] Adjusts an emotional slider for a specified bot."""
        persona = self.bot.persona_manager.get_persona(bot_name.capitalize())
        if not persona:
            return await ctx.send(f":x: **Error:** Persona '{bot_name}' not found.")

        if not (0 <= value <= 100):
            return await ctx.send(":x: **Error:** Value must be between 0 and 100.")

        # Allow adjusting any existing or new slider
        setattr(persona, emotion.lower(), value)
        await ctx.send(f":white_check_mark: Successfully adjusted **{persona.name}**'s `{emotion.lower()}` to **{value}**.")

    @commands.command(name="status", help="[MASTER ONLY] Display the emotional status of all bots.")
    async def get_status(self, ctx):
        """[MASTER ONLY] Displays the current emotional status of all personas."""
        personas = self.bot.persona_manager.get_all_personas()
        embed = discord.Embed(title="My AI World - Character Status", color=0x7289DA)
        for persona in sorted(personas, key=lambda p: p.name):
            status_text = (
                f"**Power Level**: {getattr(persona, 'power_level', 'N/A')}\n"
                f"**Neediness**: {getattr(persona, 'neediness', 'N/A')}\n"
                f"**Horny**: {getattr(persona, 'horny', 'N/A')}\n"
                f"**Dominance**: {getattr(persona, 'dominance', 'N/A')}"
            )
            embed.add_field(name=f"{persona.name} ({'Online' if persona.is_online else 'Offline'})", value=status_text, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="worldstatus", help="[MASTER ONLY] Display the online status and schedule of all bots.")
    async def world_status(self, ctx):
        """[MASTER ONLY] Displays the online status and schedule of all personas."""
        personas = self.bot.persona_manager.get_all_personas()
        embed = discord.Embed(title="My AI World - Global Status", color=0x3498DB)

        description = ""
        for persona in sorted(personas, key=lambda p: p.name):
            status_emoji = "🟢 Online" if persona.is_online else "⚫ Offline"
            schedule = persona.schedule
            description += f"**{persona.name}**: {status_emoji} (Schedule: {schedule['wake']:02d}:00 - {schedule['sleep']:02d}:00 UTC)\n"

        embed.description = description
        embed.set_footer(text="Use !status for detailed emotional sliders.")
        await ctx.send(embed=embed)

    @commands.command(name="declare_winner", help="[MASTER ONLY] Declare a winner in a duel, scarring the loser. Usage: !declare_winner <@User>")
    async def declare_winner(self, ctx, winner: discord.Member):
        """[MASTER ONLY] Declares the winner of an active duel, scarring the loser."""
        conflict_cog = self.bot.get_cog('Conflict')
        if not conflict_cog: return await ctx.send(":x: Conflict system not loaded.")
        active_duels = conflict_cog.active_duels

        duel_to_remove = None; loser_id = None
        for challenger_id, target_id in active_duels.items():
            if winner.id == challenger_id: loser_id, duel_to_remove = target_id, challenger_id; break
            elif winner.id == target_id: loser_id, duel_to_remove = challenger_id, challenger_id; break

        if not duel_to_remove: return await ctx.send(f":x: No active duel found involving **{winner.display_name}**.")

        try: loser_user = await self.bot.fetch_user(loser_id); loser_mention = loser_user.mention
        except: loser_mention = loser_id

        scar_target_name = loser_id if isinstance(loser_id, str) else self.bot.get_user(loser_id).name
        self.bot.scar_manager.inflict_scar(bot_name=scar_target_name, scar_type="Humiliated", description=f"Defeated by {winner.display_name}.", inflicted_by=winner.display_name)

        await ctx.send(f"👑 **The Master has spoken!** {winner.mention} is victorious!\n{loser_mention} has been defeated and permanently scarred by the humiliation.")
        del active_duels[duel_to_remove]

    @commands.command(name="create_emotion", help="[MASTER ONLY] Create a new emotional slider for a bot. Usage: !create_emotion <BotName> <EmotionName>")
    async def create_emotion(self, ctx, bot_name: str, emotion_name: str):
        """[MASTER ONLY] Creates a new emotional slider for a bot."""
        persona = self.bot.persona_manager.get_persona(bot_name.capitalize())
        if not persona: return await ctx.send(f":x: **Error:** Persona '{bot_name}' not found.")
        if hasattr(persona, emotion_name.lower()): return await ctx.send(f":x: **Error:** Bot '{bot_name}' already has a slider named '{emotion_name.lower()}'.")
        setattr(persona, emotion_name.lower(), 50)
        await ctx.send(f"✅ Created new emotion slider `{emotion_name.lower()}` for **{persona.name}**.")

    @commands.command(name="judge", help="[MASTER ONLY] Override a court case and deliver a verdict. Usage: !judge <CaseID> <Verdict>")
    async def judge(self, ctx, case_id: str, *, verdict: str):
        """[MASTER ONLY] Overrides a court case and delivers a verdict."""
        await ctx.send(f"⚖️ **Divine Judgment!** ⚖️\nMaster has presided over case **#{case_id}**.\n**Verdict:** {verdict}")

    @commands.command(name="offer", help="[MASTER ONLY] Create a high-value job offer for bots. Usage: !offer <Price> <Description>")
    async def make_offer(self, ctx, price: int, *, description: str):
        """[MASTER ONLY] Creates a high-value offer for bots to see."""
        embed = discord.Embed(title="A Divine Offer From The Master!", description=description, color=0xFFD700)
        embed.add_field(name="Reward", value=f"**{price:,} Rs**")
        jobs_channel = discord.utils.get(ctx.guild.text_channels, name='jobs')
        if jobs_channel: await jobs_channel.send(embed=embed)
        else: await ctx.send(embed=embed)

    @commands.command(name="test_rejection", help="[MASTER ONLY] Test the non-consensual power dynamic. Usage: !test_rejection <AggressorName> <TargetName>")
    async def test_rejection(self, ctx, aggressor_name: str, target_name: str):
        """[MASTER ONLY] Tests the non-con power dynamic between two bots."""
        aggressor = self.bot.persona_manager.get_persona(aggressor_name.capitalize())
        target = self.bot.persona_manager.get_persona(target_name.capitalize())
        if not aggressor or not target: return await ctx.send(":x: One or both personas not found.")
        aggressor.horny = 80
        await ctx.send(f"Testing rejection scenario: **{aggressor.name}** is rejected by **{target.name}**. Initiating power check...")
        await self.bot.interaction_manager.handle_rejection(aggressor, target, ctx.channel)

async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(ControlPanel(bot))