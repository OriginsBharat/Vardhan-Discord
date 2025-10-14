import discord
from discord.ext import commands, tasks
import asyncio
import datetime

class Auction:
    def __init__(self, item, seller_id, start_price, duration_minutes, msg_id, guild_id, channel_id):
        self.item, self.seller_id, self.start_price = item, seller_id, start_price
        self.end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=duration_minutes)
        self.current_bid, self.high_bidder_id = start_price, None
        self.message_id, self.guild_id, self.channel_id = msg_id, guild_id, channel_id
        self.is_active = True

class AuctionHouse(commands.Cog):
    """Manages the auction house system."""
    def __init__(self, bot):
        self.bot, self.auctions = bot, {}
        self.check_auctions.start()

    def cog_unload(self):
        self.check_auctions.cancel()

    @commands.command(name="start_auction", help="Start an auction for an item. Usage: !start_auction <start_price> <duration_minutes> <item_name>")
    async def start_auction(self, ctx, start_price: int, duration_minutes: int, *, item: str):
        if ctx.channel.name != 'the-auction-house': return
        msg = await ctx.send(embed=discord.Embed(title="Creating Auction..."))
        auction = Auction(item, ctx.author.id, start_price, duration_minutes, msg.id, ctx.guild.id, ctx.channel.id)
        self.auctions[msg.id] = auction
        await msg.edit(embed=self._create_embed(auction, ctx.author))

    @commands.command(name="bid", help="Place a bid on an active auction. Reply to the auction message to bid. Usage: !bid <amount>")
    async def bid(self, ctx, amount: int):
        if ctx.channel.name != 'the-auction-house' or not ctx.message.reference: return
        auction = self.auctions.get(ctx.message.reference.message_id)
        if not auction or not auction.is_active: return await ctx.send(":x: This auction is not active.", delete_after=10)
        if amount <= auction.current_bid: return await ctx.send(f":x: Bid must be higher than **{auction.current_bid:,} Rs**.", delete_after=10)
        if not self.bot.economy_manager.subtract_balance(ctx.author.id, amount): return await ctx.send(":x: You cannot afford this bid.", delete_after=10)
        if auction.high_bidder_id: self.bot.economy_manager.add_balance(auction.high_bidder_id, auction.current_bid)
        auction.current_bid, auction.high_bidder_id = amount, ctx.author.id
        msg = await ctx.channel.fetch_message(auction.message_id)
        seller = await self.bot.fetch_user(auction.seller_id)
        await msg.edit(embed=self._create_embed(auction, seller))
        await ctx.message.delete()

    @tasks.loop(seconds=15)
    async def check_auctions(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        for auction in list(self.auctions.values()):
            if auction.is_active and now >= auction.end_time:
                await self.finalize_auction(auction)

    async def finalize_auction(self, auction):
        auction.is_active = False
        guild = self.bot.get_guild(auction.guild_id)
        channel = guild.get_channel(auction.channel_id) if guild else None
        if not channel:
            del self.auctions[auction.message_id]
            return
        if auction.high_bidder_id:
            self.bot.economy_manager.add_balance(auction.seller_id, auction.current_bid)
            winner = await self.bot.fetch_user(auction.high_bidder_id)
            embed = discord.Embed(title="Auction Ended!", description=f"**{auction.item}** sold to {winner.mention} for **{auction.current_bid:,} Rs**.", color=0x2ECC71)
        else:
            embed = discord.Embed(title="Auction Ended!", description=f"**{auction.item}** received no bids.", color=0x99AAB5)
        await channel.send(embed=embed)
        del self.auctions[auction.message_id]

    def _create_embed(self, auction, seller):
        embed = discord.Embed(title=f"Auction: {auction.item}", color=0x1ABC9C).set_author(name=f"Seller: {seller.display_name}", icon_url=seller.avatar.url)
        embed.add_field(name="Current Bid", value=f"**{auction.current_bid:,} Rs**")
        high_bidder = self.bot.get_user(auction.high_bidder_id) if auction.high_bidder_id else "None"
        embed.add_field(name="High Bidder", value=high_bidder)
        embed.add_field(name="Ends", value=f"<t:{int(auction.end_time.timestamp())}:R>", inline=False)
        return embed

    @check_auctions.before_loop
    async def before_check(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(AuctionHouse(bot))