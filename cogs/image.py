import asyncio
import os
import random
import re
import sys

import asyncdagpi
import deeppyer
import discord
import PIL.Image
from bs4 import BeautifulSoup
from discord.ext import commands


class Image(commands.Cog):
    """Image manipulation commands."""

    def __init__(self, bot):
        self.bot = bot
        self.configcol = self.bot.mongodatabase["configs"]
        self.bot.dagpi = bot.dagpi

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def pixel(self, ctx, user=None):
        """Pixelates an image."""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "pixel" in cmdsList:
            return

        channelList = ["0"]
        channels = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
        )

        for i in channels:
            channeloff = i["channels"]
            channelList.extend(channeloff)
        if ctx.message.channel.id in channelList:
            return

        if user is None:
            for attachment in ctx.message.attachments:
                img = await self.bot.dagpi.image_process(
                    asyncdagpi.ImageFeatures.pixel(), attachment.proxy_url
                )
                file = discord.File(fp=img.image, filename=f"pixel.{img.format}")
                await ctx.send(file=file)

        else:
            userID = re.sub("[^0-9]", "", user)
            try:
                user = await ctx.guild.fetch_member(userID)
            except BaseException:
                await ctx.send("No user found.")
                return

            url = str(user.avatar_url_as(format="png", size=1024))
            img = await self.bot.dagpi.image_process(
                asyncdagpi.ImageFeatures.pixel(), url
            )
            file = discord.File(fp=img.image, filename=f"pixel.{img.format}")
            await ctx.send(file=file)

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def blur(self, ctx, user=None):
        """Blurs an image."""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "blur" in cmdsList:
            return

        channelList = ["0"]
        channels = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
        )

        for i in channels:
            channeloff = i["channels"]
            channelList.extend(channeloff)
        if ctx.message.channel.id in channelList:
            return

        if user is None:
            for attachment in ctx.message.attachments:
                img = await self.bot.dagpi.image_process(
                    asyncdagpi.ImageFeatures.blur(), attachment.proxy_url
                )
                file = discord.File(fp=img.image, filename=f"blur.{img.format}")
                await ctx.send(file=file)

        else:
            userID = re.sub("[^0-9]", "", user)
            try:
                user = await ctx.guild.fetch_member(userID)
            except BaseException:
                await ctx.send("No user found.")
                return

            url = str(user.avatar_url_as(format="png", size=1024))
            img = await self.bot.dagpi.image_process(
                asyncdagpi.ImageFeatures.blur(), url
            )
            file = discord.File(fp=img.image, filename=f"blur.{img.format}")
            await ctx.send(file=file)

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def deepfry(self, ctx, user=None):
        """Deepfries an image, must put command with uploaded image"""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "deepfry" in cmdsList:
            return

        channelList = ["0"]
        channels = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
        )

        for i in channels:
            channeloff = i["channels"]
            channelList.extend(channeloff)
        if ctx.message.channel.id in channelList:
            return

        if user is None:
            for attachment in ctx.message.attachments:
                imageID = random.randint(0, 1000000000)
                await attachment.save(f"image{imageID}.png")

                providedimage = PIL.Image.open(f"image{imageID}.png")
                image = await deeppyer.deepfry(providedimage, flares=False)
                image.save(f"imageDeepfried{imageID}.png")

                pic = discord.File(f"imageDeepfried{imageID}.png")
                await ctx.send(file=pic)
                return
        else:
            userID = re.sub("[^0-9]", "", user)
            try:
                user = await ctx.guild.fetch_member(userID)
            except BaseException:
                await ctx.send("No user found.")
                return

            img = user.avatar_url_as()
            imageID = random.randint(0, 1000000000)
            await img.save(f"imagePFP{imageID}.png")

            providedimage = PIL.Image.open(f"imagePFP{imageID}.png")
            image = await deeppyer.deepfry(providedimage, flares=False)
            image.save(f"imageDeepfried{imageID}.png")

            pic = discord.File(f"imageDeepfried{imageID}.png")
            await ctx.send(file=pic)

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def invert(self, ctx, user=None):
        """Inverts an image."""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "invert" in cmdsList:
            return

        channelList = ["0"]
        channels = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]}
        )

        for i in channels:
            channeloff = i["channels"]
            channelList.extend(channeloff)
        if ctx.message.channel.id in channelList:
            return

        if user is None:
            for attachment in ctx.message.attachments:
                img = await self.bot.dagpi.image_process(
                    asyncdagpi.ImageFeatures.invert(), attachment.proxy_url
                )
                file = discord.File(fp=img.image, filename=f"invert.{img.format}")
                await ctx.send(file=file)

        else:
            userID = re.sub("[^0-9]", "", user)
            try:
                user = await ctx.guild.fetch_member(userID)
            except BaseException:
                await ctx.send("No user found.")
                return

            url = str(user.avatar_url_as(format="png", size=1024))
            img = await self.bot.dagpi.image_process(
                asyncdagpi.ImageFeatures.invert(), url
            )
            file = discord.File(fp=img.image, filename=f"invert.{img.format}")
            await ctx.send(file=file)


def setup(bot):
    bot.add_cog(Image(bot))
