import discord
from discord.ext import commands

class Shop:
    """Represents a single bot-owned shop."""
    def __init__(self, owner_id, name):
        self.owner_id = owner_id
        self.name = name
        self.inventory = {} # {item_name: price}

class ShopManager(commands.Cog):
    """Manages all bot-owned shops."""
    def __init__(self, bot):
        self.bot = bot
        self.shops = {} # {owner_id (str persona name): Shop}

    @commands.command(name="open_shop", help="Open a personal shop. Usage: !open_shop <name>")
    async def open_shop(self, ctx, *, name: str):
        """Opens a personal shop."""
        actor_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else None
        if not actor_id: return await ctx.send(":x: Only bot personas may open shops.")
        if actor_id in self.shops: return await ctx.send(":x: You already own a shop.")
        self.shops[actor_id] = Shop(actor_id, name)
        await ctx.send(f"🛍️ **{actor_id}** has opened a new shop: **{name}**!")

    @commands.command(name="add_item", help="Add an item to your shop. Usage: !add_item <price> <item_name>")
    async def add_item(self, ctx, price: int, *, item_name: str):
        """Adds an item to your shop."""
        actor_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else None
        if not actor_id: return await ctx.send(":x: Only bot personas can manage shop inventory.")
        if actor_id not in self.shops: return await ctx.send(":x: You don't own a shop.")
        shop = self.shops[actor_id]
        shop.inventory[item_name.lower()] = price
        await ctx.send(f"✅ Added **{item_name}** to **{shop.name}** for **{price:,} Rs**.")

    @commands.command(name="buy_item", help="Buy an item from a bot's shop. Usage: !buy_item <OwnerName> <item_name>")
    async def buy_item(self, ctx, owner_name: str, *, item_name: str):
        """Buys an item from a bot's shop."""
        buyer_id = ctx.message.persona.name if hasattr(ctx.message, 'persona') else ctx.author.id
        owner_name = owner_name.capitalize()
        if owner_name not in self.shops: return await ctx.send(f":x: **{owner_name}** does not own a shop.")
        shop = self.shops[owner_name]
        item_lower = item_name.lower()
        if item_lower not in shop.inventory: return await ctx.send(f":x: **{item_name}** is not available in that shop.")
        price = shop.inventory[item_lower]
        if not self.bot.economy_manager.subtract_balance(buyer_id, price): return await ctx.send(f":x: You cannot afford **{item_name}**.")
        self.bot.economy_manager.add_balance(shop.owner_id, price)
        buyer_name = ctx.author.display_name
        await ctx.send(f"🛒 **{buyer_name}** has purchased **{item_name}** from **{owner_name}** for **{price:,} Rs**.")
        del shop.inventory[item_lower]

async def setup(bot): await bot.add_cog(ShopManager(bot))