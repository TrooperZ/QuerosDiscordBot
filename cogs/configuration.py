import os
import random
import sys
import string

import discord
import pymongo
from discord.ext import commands, tasks
from captcha.image import ImageCaptcha


class Configuration(commands.Cog):
    """Configure bot server settings"""

    def __init__(self, bot):
        self.bot = bot
        self.configcol = self.bot.mongodatabase["configuration"]


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def togglecommand(self, ctx, cmd: str, yN: str):
        """Toggles commands, currently moderation does not have this ability."""
        if yN not in ("on", "off"):
            await ctx.send("Please choose a valid level, on or off.")
            return

        if yN == "off":
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            listcmd = []
            for i in logging:
                listcmd.extend(i["commands"])
            listcmd.append(cmd)
            self.configcol.update_one(
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
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            for i in logging:
                listcmd = []
                listcmd.extend(i["commands"])
            listcmd.remove(cmd)
            self.configcol.update_one(
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
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
            )
            channels = []
            for i in logging:
                channels.extend(i["channels"])
            channels.append(channel.id)
            self.configcol.update_one(
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
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
            )
            for i in logging:
                channels = []
                channels.extend(i["channels"])
            channels.remove(channel.id)
            self.configcol.update_one(
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
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]}
            )
            self.configcol.update_one(
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
            role = discord.utils.get(ctx.guild.roles, name="Captcha Verified")

            for channel in member.guild.channels:
                await channel.set_permissions(role, send_messages=True, view_channel=True)
                await channel.set_permissions(ctx.guild.default_role, view_channel=True, send_messages=True)
            await ctx.send(f"Disabled captcha.")

        if toggle == "on":
            logging = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "captcha"}]}
            )
            self.configcol.update_one(
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
            perms = discord.Permissions(send_messages=True, view_channel=True)
            await ctx.guild.create_role(name="Captcha Verified", permissions=perms)

            role = discord.utils.get(ctx.guild.roles, name="Captcha Verified")

            for channel in member.guild.channels:
                await channel.set_permissions(role, send_messages=True, view_channel=True)
                await channel.set_permissions(ctx.guild.default_role, view_channel=False)

            await ctx.send("Enabled captcha. Users will need to enable DMs and complete captcha to get the Captcha Verified role. Make sure to give the everyone role no permission to send messages.")


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def profanitytext(self, ctx, mode, word, channel="all", location="any", punishment="none", punishdur="none"):
        if mode != "add" or mode != "remove":
            await ctx.send("Please set mode to `add` or `remove`")
            return

        log = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "profanity"}]}
        )

        if mode == "add":
            itemlist = ["0"]
            for i in log:
                itemlist.extend(i["words"])
            itemlist.extend((word, channel, punishment, punishdur))

            self.configcol.update_one(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "profanity"}]},
                {
                    "$set": {
                        "cfg_type": "profanity",
                        "guild": ctx.guild.id,
                        "words": itemlist,
                    }
                }, upsert=True)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        log = self.configcol.find(
            {"$and": [{"guild": member.guild.id}, {"cfg_type": "captcha"}]}
        )
        capStat = 'off'
        for i in log:
            capStat = i['status']
        if capStat == 'off':
            return


        msg = await member.send(f"Hey there {member}, we just need to do one little thing to make sure you're a human and not anything malicious... Please complete this captcha (rejoin to regenerate a captcha):")
        image = ImageCaptcha()
        captchaAMT = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        data = image.generate(captchaAMT)
        image.write(captchaAMT, f"{captchaAMT}CAPTCHA.png")
        await member.send(file=discord.File(f"{captchaAMT}CAPTCHA.png"))

        def check(m):
            return m.content == captchaAMT and m.guild is None

        await self.bot.wait_for('message', check=check)
        role = discord.utils.get(member.guild.roles, name="Captcha Verified")

        await member.add_roles(role)
        await member.send("Captcha verified. Giving you access...")



# setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
    bot.add_cog(Configuration(bot))
