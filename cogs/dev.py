import discord
from discord.ext import commands
from discord.ext import tasks

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.premServercol = self.bot.mongodatabase["vipServers"]

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
            await asyncio.sleep(1)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, msg):
        await ctx.send(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        try:
            bot.reload_extension(cog)
        except Exception as e:
            await ctx.send(e)
        await ctx.send("done")

    @tasks.loop(seconds=360)
    async def statusLoop(self):
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="u.help in " + str(len(self.bot.guilds)) + " servers",
            )
        )

    @statusLoop.before_loop  # basic loop handeling
    async def before_statusLoop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.statusLoop.start()

def setup(bot):
    bot.add_cog(Dev(bot))