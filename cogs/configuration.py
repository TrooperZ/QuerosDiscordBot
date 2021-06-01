import os
import random
import sys
import secrets

import discord
import pymongo
from discord.ext import commands, tasks
from dotenv import load_dotenv
from captcha.image import ImageCaptcha

load_dotenv()

MONGO_PASS = os.getenv("MONGO_PASS")
myclient = pymongo.MongoClient(
    "mongodb+srv://queroscode:"
    + MONGO_PASS
    + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority"
)
mydb = myclient["data"]
modcol = mydb["moderation"]
configcol = mydb["configs"]
balcol = mydb["balances"]


class Configuration(commands.Cog):
    """Configure bot server settings"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def togglecommand(self, ctx, cmd: str, yN: str):
        """Toggles commands, currently moderation does not have this ability."""
        if yN not in ("on", "off"):
            await ctx.send("Please choose a valid level, on or off.")
            return

        if yN == "off":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            listcmd = []
            for i in logging:
                listcmd.extend(i["commands"])
            listcmd.append(cmd)
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]},
                {
                    "$set": {
                        "cfg_type": "cmdsoff",
                        "guild": ctx.guild.id,
                        "commands": listcmd,
                    }
                },
                upsert=True,
            )
            await ctx.send(f"Added **{cmd}** to off list.")

        if yN == "on":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            for i in logging:
                listcmd = []
                listcmd.extend(i["commands"])
            listcmd.remove(cmd)
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]},
                {
                    "$set": {
                        "cfg_type": "cmdsoff",
                        "guild": ctx.guild.id,
                        "commands": listcmd,
                    }
                },
                upsert=True,
            )
            await ctx.send(f"Removed **{cmd}** from off list.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def togglechannel(self, ctx, channel: discord.TextChannel, yN: str):
        """Toggles which channel the bot to ignore, currently moderation does not have this ability."""
        if yN not in ("on", "off"):
            await ctx.send("Please choose a valid level, on or off.")
            return
        if yN == "off":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
            )
            channels = []
            for i in logging:
                channels.extend(i["channels"])
            channels.append(channel.id)
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]},
                {
                    "$set": {
                        "cfg_type": "channeloff",
                        "guild": ctx.guild.id,
                        "channels": channels,
                    }
                },
                upsert=True,
            )
            await ctx.send(f"Added **{channel}** to off list.")

        if yN == "on":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
            )
            for i in logging:
                channels = []
                channels.extend(i["channels"])
            channels.remove(channel.id)
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]},
                {
                    "$set": {
                        "cfg_type": "channeloff",
                        "guild": ctx.guild.id,
                        "channels": channels,
                    }
                },
                upsert=True,
            )
            await ctx.send(f"Removed **{channel}** from off list.")

   
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def captchaconfig(self, ctx, toggle: str):
        """Configures captcha."""
        if toggle not in ("on", "off"):
            await ctx.send("Choose a valid option, on or off")
            return
        if toggle == "off":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]}
            )
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]},
                {
                    "$set": {
                        "cfg_type": "captcha",
                        "guild": ctx.guild.id,
                        "status": toggle,
                    }
                },
                upsert=True,
            )
            await ctx.send(f"Disabled captcha.")

        if toggle == "on":
            logging = configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]}
            )
            configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]},
                {
                    "$set": {
                        "cfg_type": "captcha",
                        "guild": ctx.guild.id,
                        "status": toggle,
                    }
                },
                upsert=True,
            )
            await ctx.send("Enabled captcha. Users will need to enable DMs and complete captcha to get the Captcha Verified role. Make sure to give the everyone role no permission to send messages.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log = configcol.find(
            {"$and": [{"guild": member.guild.id}, {"cfg_type": "captcha"}]}
        )
        capStat = 'off'
        for i in log:
            capStat = i['status']
        if capStat == 'off':
            return
        msg = await member.send(f"Hey there {member}, we just need to do one little thing to make sure you're a human and not anything malicious... Please complete this captcha (note, you have 1 try, if it is not correct, you will have to rejoin.):")
        image = ImageCaptcha()
        captchaAMT = secrets.token_urlsafe(4)
        data = image.generate(captchaAMT)
        image.write(captchaAMT, f"{captchaAMT}CAPTCHA.png")
        await member.send(file=discord.File(f"{captchaAMT}CAPTCHA.png"))

        def check(m):
            return m.content == captchaAMT and m.guild is None

        await self.bot.wait_for('message', check=check)
        await member.send("Captcha verified. Giving you access...")

        if discord.utils.get(member.guild.roles, name="Captcha Verified"):
            role = discord.utils.get(member.guild.roles, name="Captcha Verified")

            await member.add_roles(role)

            for channel in member.guild.channels:
                await channel.set_permissions(role, send_messages=True)

        else:
            perms = discord.Permissions(send_messages=True)
            await member.guild.create_role(name="Captcha Verified", permissions=perms)

            role = discord.utils.get(member.guild.roles, name="Captcha Verified")
            await role.edit(position=1)
            await member.add_roles(role)

            for channel in member.guild.channels:
                await channel.set_permissions(role, send_messages=True)


# setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
    bot.add_cog(Configuration(bot))
