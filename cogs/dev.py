import discord
from discord.ext import commands
from discord.ext import tasks
import dotenv
import dbl
import os

dotenv.load_dotenv()

TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.premServercol = self.bot.mongodatabase["vipServers"]
        self.bot.dblpy = dbl.DBLClient(bot, TOPGG_TOKEN)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def addpremiumserver(self, ctx, serverid: int):
        self.premServercol.insert_one({"server": ctx.guild.id})
        await ctx.send("done")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def delpremiumserver(self, ctx, serverid: int):
        self.premServercol.delete_one({"server": ctx.guild.id})
        await ctx.send("done")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def getguilds(self, ctx):
        for i in self.bot.guilds:
            await ctx.send(i.name)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, msg):
        await ctx.send(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        try:
            self.bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(e)
        await ctx.send("done")

    @tasks.loop(seconds=360)
    async def statusLoop(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"to commands in {len(self.bot.guilds)} servers"))
        await self.bot.dblpy.post_guild_count()

    @statusLoop.before_loop  # basic loop handeling
    async def before_statusLoop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.statusLoop.start()


def setup(bot):
    bot.add_cog(Dev(bot))
