import discord
from discord.ext import commands
import datetime

class Loan:
    def __init__(self, lender_id, borrower_id, amount, due_date):
        self.lender_id, self.borrower_id, self.amount, self.due_date = lender_id, borrower_id, amount, due_date
        self.is_defaulted = False

class LoanManager(commands.Cog):
    """Manages loans, debts, and defaults."""
    def __init__(self, bot):
        self.bot = bot; self.loans = []

    @commands.command(name="request_loan", help="Request a loan from other users in #bank-of-vardhan. Usage: !request_loan <amount> <days> <reason>")
    async def request_loan(self, ctx, amount: int, days: int, *, reason: str):
        if ctx.channel.name != 'bank-of-vardhan': return
        embed = discord.Embed(title=f"Loan Request: {amount:,} Rs for {days} days", description=f"**Reason:**\n> {reason}", color=0xE74C3C)
        embed.set_author(name=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.set_footer(text=f"Use !grant_loan {ctx.author.id} {amount} {days} to fund this loan.")
        await ctx.send(embed=embed)

    @commands.command(name="grant_loan", help="Grant a loan to another user. Usage: !grant_loan <@user> <amount> [days=7]")
    async def grant_loan(self, ctx, borrower: discord.Member, amount: int, days: int = 7):
        if ctx.channel.name != 'bank-of-vardhan': return
        lender_id = ctx.author.id
        if lender_id == borrower.id: return await ctx.send(":x: You cannot grant a loan to yourself.")
        if not self.bot.economy_manager.subtract_balance(lender_id, amount): return await ctx.send(f":x: You do not have enough Rs.")
        self.bot.economy_manager.add_balance(borrower.id, amount)
        due_date = datetime.datetime.now() + datetime.timedelta(days=days)
        self.loans.append(Loan(lender_id, borrower.id, amount, due_date))
        await ctx.send(f"✅ **Loan Granted!** {ctx.author.mention} has loaned **{amount:,} Rs** to {borrower.mention}, due on {due_date.strftime('%Y-%m-%d')}.")

    async def check_for_defaults(self):
        now = datetime.datetime.now()
        for loan in self.loans:
            if not loan.is_defaulted and now > loan.due_date:
                loan.is_defaulted = True
                # ... (Scarring and announcement logic) ...
                print(f"[LoanManager] Loan from {loan.lender_id} to {loan.borrower_id} has defaulted!")

async def setup(bot):
    bot.loan_manager = LoanManager(bot)
    await bot.add_cog(bot.loan_manager)