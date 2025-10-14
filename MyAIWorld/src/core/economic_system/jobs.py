import discord
from discord.ext import commands

class Job:
    def __init__(self, job_id, owner_id, title, description, payout):
        self.id, self.owner_id, self.title, self.description, self.payout = job_id, owner_id, title, description, payout
        self.assignee_id, self.is_complete = None, False

class JobManager(commands.Cog):
    """Manages the job board and bot-to-bot contracts."""
    def __init__(self, bot):
        self.bot, self.jobs, self.next_job_id = bot, {}, 1

    @commands.command(name="post_job")
    async def post_job(self, ctx, payout: int, *, title_and_desc: str):
        if ctx.channel.name != 'jobs': return
        parts = [p.strip().strip('"') for p in title_and_desc.split(';', 1)]
        if len(parts) != 2: return await ctx.send(":x: Invalid format. Use `!post_job <payout> \"<title>\"; \"<description>\"`")
        title, description = parts
        actor_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else ctx.author.id
        if not self.bot.economy_manager.subtract_balance(actor_id, payout): return await ctx.send(f":x: You don't have enough Rs.")
        job_id = self.next_job_id; self.next_job_id += 1
        self.jobs[job_id] = Job(job_id, actor_id, title, description, payout)
        embed = discord.Embed(title=f"New Contract: {title}", description=description, color=0xF1C40F)
        embed.set_author(name=f"Posted by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if not hasattr(ctx.message, 'persona') else self.bot.user.avatar.url)
        embed.add_field(name="Payout", value=f"**{payout:,} Rs**").set_footer(text=f"Job ID: {job_id}")
        await ctx.send(embed=embed)

    @commands.command(name="accept_job")
    async def accept_job(self, ctx, job_id: int):
        if job_id not in self.jobs: return await ctx.send(f":x: Job ID `{job_id}` not found.")
        job, actor_id = self.jobs[job_id], ctx.author.id
        if job.assignee_id: return await ctx.send(f":x: Job has been taken.")
        if job.owner_id == actor_id: return await ctx.send(":x: You cannot accept your own job.")
        job.assignee_id = actor_id
        await ctx.send(f"✅ {ctx.author.mention} has accepted contract **{job.title}**.")

    @commands.command(name="complete_job")
    async def complete_job(self, ctx, job_id: int):
        if job_id not in self.jobs: return await ctx.send(f":x: Job ID `{job_id}` not found.")
        job, actor_id = self.jobs[job_id], ctx.author.id
        if job.assignee_id != actor_id: return await ctx.send(":x: You have not accepted this job.")
        if job.is_complete: return await ctx.send(":x: Job already completed.")
        job.is_complete = True
        self.bot.economy_manager.add_balance(actor_id, job.payout)
        await ctx.send(f"🎉 **Contract Complete!** {ctx.author.mention} has been paid **{job.payout:,} Rs**.")
        del self.jobs[job_id]

async def setup(bot): await bot.add_cog(JobManager(bot))
