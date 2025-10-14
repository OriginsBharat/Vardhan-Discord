import discord
from discord.ext import commands
from src.config import MASTER_ID

class EconomyManager(commands.Cog):
    """Manages the 'Rs' currency, wallets, and economic commands for the world."""
    def __init__(self, bot):
        self.bot = bot
        self.wallets = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize wallets once the bot is ready and personas are loaded."""
        self.wallets[MASTER_ID] = 999_999_999_999
        for persona in self.bot.persona_manager.get_all_personas():
            if persona.name not in self.wallets:
                self.wallets[persona.name] = 1000
        print("EconomyManager: Wallets initialized.")

    def get_balance(self, id): return self.wallets.get(id, 0)
    def set_balance(self, id, amount): self.wallets[id] = amount
    def add_balance(self, id, amount): self.wallets[id] = self.get_balance(id) + amount
    def subtract_balance(self, id, amount):
        if self.get_balance(id) < amount: return False
        self.wallets[id] -= amount
        return True

    @commands.command(name="balance", help="Check your or another user's balance. Usage: !balance [@user]")
    async def check_balance(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        balance = self.get_balance(user.id)
        await ctx.send(f"💰 **{user.display_name}** has a balance of **{balance:,} Rs**.")

    @commands.command(name="give", help="Give another user some of your Rs. Usage: !give <@user> <amount>")
    async def give_money(self, ctx, member: discord.Member, amount: int):
        if amount <= 0: return await ctx.send(":x: You must give a positive amount.")
        if not self.subtract_balance(ctx.author.id, amount): return await ctx.send(":x: You do not have enough Rs.")
        self.add_balance(member.id, amount)
        await ctx.send(f"💸 **{ctx.author.display_name}** gave **{amount:,} Rs** to **{member.display_name}**.")

    @commands.command(name="award", help="[MASTER ONLY] Award Rs to a user. Usage: !award <@user> <amount>")
    @commands.check(lambda ctx: ctx.author.id == MASTER_ID)
    async def award_money(self, ctx, member: discord.Member, amount: int):
        self.add_balance(member.id, amount)
        await ctx.send(f"👑 Master has awarded **{amount:,} Rs** to **{member.display_name}**.")

async def setup(bot):
    bot.economy_manager = EconomyManager(bot)
    await bot.add_cog(bot.economy_manager)