import discord
from discord.ext import commands

class ProstitutionService:
    def __init__(self, persona_name, price):
        self.persona_name, self.price, self.is_available = persona_name, price, True

class ProstitutionManager(commands.Cog):
    """Manages the NSFW service industry."""
    def __init__(self, bot):
        self.bot, self.services = bot, {}

    @commands.command(name="offer_services", help="Offer your services as a prostitute at a set price. Usage: !offer_services <price>")
    async def offer_services(self, ctx, price: int):
        actor_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else None
        if not actor_id: return await ctx.send(":x: Only bot personas may offer services.")
        if actor_id in self.services:
            self.services[actor_id].price = price; self.services[actor_id].is_available = True
            await ctx.send(f"✅ **{actor_id}** has updated their service price to **{price:,} Rs**.")
        else:
            self.services[actor_id] = ProstitutionService(actor_id, price)
            await ctx.send(f"✅ **{actor_id}** is now offering their services for **{price:,} Rs**.")

    @commands.command(name="solicit", help="Solicit the services of a prostitute. Usage: !solicit <BotName>")
    async def solicit(self, ctx, persona_name: str):
        persona_name = persona_name.capitalize()
        if persona_name not in self.services or not self.services[persona_name].is_available:
            return await ctx.send(f":x: **{persona_name}** is not currently offering their services.")
        service, price = self.services[persona_name], self.services[persona_name].price
        solicitor_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else ctx.author.id
        if not self.bot.economy_manager.subtract_balance(solicitor_id, price):
            return await ctx.send(f":x: You cannot afford **{persona_name}'s** services. It costs **{price:,} Rs**.")
        self.bot.economy_manager.add_balance(persona_name, price)
        service.is_available = False
        await ctx.send(f"Transaction complete. **{ctx.author.display_name}** has solicited **{persona_name}** for **{price:,} Rs**.")
        # Here, a full implementation would trigger a private, generative scene.

async def setup(bot): await bot.add_cog(ProstitutionManager(bot))