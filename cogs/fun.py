#!/usr/bin/python
# -*- coding: utf-8 -*-
# Fun command category
import asyncio
import datetime
import json
import os
import random
import re
import sys


import aiofiles
import aiohttp
import asyncdagpi
import asyncpraw
import deeppyer
import discord
import PIL.Image
from bs4 import BeautifulSoup
from discord.ext import commands

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_API_KEY"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent="QuerosDiscordBot accessAPI:v0.0.1 (by /u/Troopr_Z)",
    username=os.getenv("REDDIT_USERNAME"),
)


class Fun(commands.Cog):
    """Have lots of laughs with these commands!"""

    def __init__(self, bot):
        self.bot = bot
        self.configcol = self.bot.mongodatabase["configs"]
        self.bot.dagpi = bot.dagpi
        self.bot.snipes = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.bot.snipes[message.channel.id] = message

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def pickupline(self, ctx):
        """Generates a pickup line, may be NSFW"""
        line = await self.bot.dagpi.pickup_line()
        await ctx.send(line.line)

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def joke(self, ctx):
        """Generates a joke, may be NSFW"""
        await ctx.send(await self.bot.dagpi.joke())

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def roast(self, ctx):
        """Generates a roast, may be NSFW"""
        await ctx.send(await self.bot.dagpi.roast())

    @commands.command()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def yomama(self, ctx):
        """Generates a roast, may be NSFW"""
        await ctx.send(await self.bot.dagpi.yomama())

    @commands.command()
    async def snipe(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        try:
            msg = self.bot.snipes[channel.id]
        except KeyError:
            return await ctx.send("Nothing to snipe!")
        embed = discord.Embed(
            description=msg.content, color=msg.author.color
        ).set_author(name=str(msg.author), icon_url=str(msg.author.avatar_url))
        imgURL = None
        for attachment in msg.attachments:
            imgURL = attachment.proxy_url
        if imgURL is not None:
            embed.set_image(url=imgURL)
        await ctx.send(embed=embed)

    @commands.command(aliases=["murder"])
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def kill(self, ctx, user: discord.Member):
        """Eliminates a user of your choice."""
        kill_choices = [
            f"{user.name} just got 360 noscoped by {ctx.message.author.name}, let's gooooooo!",
            f"{user.name} drank expired milk and died.",
            f"{user.name} tripped and fell in the industrial blender.",
            f"{user.name} got poisoned by {ctx.message.author.name}",
            f"{user.name} has been eliminated. Well done Agent 47, proceed to the extraction point.",
            f"*chk chik* **BOOM!** {user.name}'s guts just got splattered on the wall by {ctx.message.author.name}",
            f"{user.name} was skooter ankled.",
        ]

        await ctx.send(random.choice(kill_choices))

    # @commands.command()
    # @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    # async def redditgrab(self, ctx, subreddit: str, spoiler="no"):
    #    """Grabs a post from reddit subreddit, add tag spoiler to add a spoiler."""
    #    await ctx.channel.trigger_typing()
    #    try:
    #        subredditGrabbed = await reddit.subreddit(subreddit)
    #    except Exception as e:
    #        await ctx.send("Hmm, there was an issue getting that subreddit. Make sure to type the subreddit without the r/.")
    #        print(e)
    #    Listposts = []
    #    randomPost = random.randint(1, 120)
    #    async for post in subredditGrabbed.hot(limit=60):
    #        Listposts.append(post)
    #    post = Listposts[randomPost]

    #    if post.over_18:
    #        if ctx.channel.is_nsfw():
    #            if spoiler == "spoiler":
    #                imgId = random.randint(1,10000)
    #                async with aiohttp.ClientSession() as session:
    #                    async with session.get(post.url) as resp:
    #                        if resp.status == 200:
    #                            f = await aiofiles.open(f'SPOILER_imageNSFW{imgId}.jpg', mode='wb')
    #                            await f.write(await resp.read())
    #                            await f.close()
    #                with open(f'SPOILER_imageNSFW{imgId}.jpg', 'rb') as f:
    #                        picture = discord.File(f)
    #                        await ctx.send(file=picture)

    #            embed = discord.Embed(
    #                title=post.title,
    #                description="Posted by: " + str(post.author),
    #                url="https://www.reddit.com" + post.permalink,
    #                color=0xFF4000,
    #            )
    #            embed.set_author(name=f"Post from r/{subreddit}")
    #            if post.is_self:
    #                embed.add_field(name="** **", value=post.selftext)
    #            else:
    #                embed.set_image(url=post.url)
    #            embed.set_footer(text=f"Upvotes: {post.score}")
    #            await ctx.send(embed=embed)

    #        else:
    #            await ctx.send("Content is NSFW, this channel is not NSFW, content will not be loaded.")

    #    if post.over_18 == False:
    #        if spoiler == "spoiler":
    #            imgId = random.randint(1,10000)
    #            async with aiohttp.ClientSession() as session:
    #                async with session.get(post.url) as resp:
    #                    if resp.status == 200:
    #                        f = await aiofiles.open(f'SPOILER_image{imgId}.jpg', mode='wb')
    #                        await f.write(await resp.read())
    #                        await f.close()
    #            with open(f'SPOILER_image{imgId}.jpg', 'rb') as f:
    #                    picture = discord.File(f)
    #                    await ctx.send(file=picture)
    #            return
    #        embed = discord.Embed(
    #            title=post.title,
    #            description="Posted by: " + str(post.author),
    #            url="https://www.reddit.com" + post.permalink,
    #            color=0xFF4000,
    #        )
    #        embed.set_author(name=f"Post from r/{subreddit}")
    #        if post.is_self:
    #            embed.add_field(name="** **", value=post.selftext)
    #        else:
    #            embed.set_image(url=post.url)
    #        embed.set_footer(text=f"Upvotes: {post.score}")
    #        await ctx.send(embed=embed)

    @commands.command(aliases=["8ball"])
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def eightb(self, ctx: commands.Context, *, query: str):
        """Eight Ball shall tell your future"""
        if query.endswith("?") != True:
            await ctx.send("Ask me a yes or no question that ends with a question mark.")
            return

        valuE = 0

        for letter in query:
            valuE = valuE + (ord(letter) * ord(letter))
            if (valuE % 5) == 0:
                resultNeu = [
                    "I cannot predict that",
                    "Only time will tell",
                    "Ask me later",
                    "That question is beyond my knowledge",
                ]
                await ctx.send(random.choice(resultNeu))
                return

            if (valuE % 2) > 0:
                resultPos = [
                    "Most likely",
                    "My sources point to yes",
                    "High chance",
                    "I think yes",
                ]
                await ctx.send(random.choice(resultPos))
                return

            if (valuE % 2) == 0:
                resultNo = [
                    "Not likely",
                    "High chance of no",
                    "I don't think it is a yes...",
                    "Sources point to no",
                ]
                await ctx.send(random.choice(resultNo))
                return


# setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
    bot.add_cog(Fun(bot))
