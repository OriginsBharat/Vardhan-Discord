import discord
from discord.ext import commands
import asyncio

class Conflict(commands.Cog):
    """
    Commands related to conflict, duels, and the arena.
    """
    def __init__(self, bot):
        self.bot = bot
        # Tracks active challenges {challenger_id: target_id}, IDs can be int (user) or str (persona)
        self.active_duels = {} 

    @commands.command(name="challenge")
    async def challenge(self, ctx, target: discord.Member):
        """
        Challenges another user to a duel in #the-coliseum.
        Usage: !challenge <@user>
        """
        if ctx.channel.name != 'dueling-grounds':
            return await ctx.send(":x: Duels can only be initiated in the #dueling-grounds.")

        challenger_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else ctx.author.id
        challenger_name = ctx.author.display_name
        target_id = target.id

        if challenger_id == target_id:
            return await ctx.send(":x: You cannot challenge yourself, warrior.")

        all_participants = list(self.active_duels.keys()) + list(self.active_duels.values())
        if challenger_id in all_participants:
             return await ctx.send(":x: You are already involved in a duel.")
        if target_id in all_participants:
             return await ctx.send(f":x: {target.display_name} is already involved in a duel.")

        embed = discord.Embed(
            title="⚔️ A Challenge is Made! ⚔️",
            description=f"{challenger_name} has challenged {target.mention} to a duel to the death in the Coliseum!",
            color=0xE74C3C
        )
        embed.set_footer(text=f"{target.display_name} has 60 seconds to accept or decline.")
        challenge_msg = await ctx.send(content=f"{target.mention}", embed=embed)

        await challenge_msg.add_reaction("✅")
        await challenge_msg.add_reaction("❌")

        def check(reaction, user):
            return user.id == target_id and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == challenge_msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

            if str(reaction.emoji) == "✅":
                self.active_duels[challenger_id] = target_id
                await ctx.send(f"**The duel is accepted!** {challenger_name} and {target.mention}, prepare for battle! The Master will now declare the winner.")
            else:
                await ctx.send(f"{target.display_name} has declined the challenge. A wise, if cowardly, choice.")

        except asyncio.TimeoutError:
            await ctx.send("The challenge was not answered in time and has expired.")
            
async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Conflict(bot))