#!/usr/bin/python
# -*- coding: utf-8 -*-
# Utillity cog for main bot.
import asyncio
import datetime
import os
import sys
import time
import traceback

import discord
import psutil
from discord.ext import commands

bot_launch_time = datetime.datetime.now()  # bot launch time for uptime command


class BotInfo(commands.Cog):
    """General commands that can help you with things."""

    def __init__(self, bot):
        # Initalizes bot.
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def botlink(self, ctx):
        """My link!"""
        await ctx.send(
            "Add Queros to your server today!\nhttps://discord.com/oauth2/authorize?client_id=760856635425554492&permissions=2146954871&scope=bot"
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def support(self, ctx):
        """Help for the bot"""
        await ctx.send(
            "Join this server for bot support: https://discord.gg/7qvsUCBZ8W"
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def website(self, ctx):
        """Bot's website"""
        await ctx.send("http://queros.live/index.html?i=1")

    @commands.command()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def botinfo(self, ctx):
        """General bot info"""
        delta_uptime = datetime.datetime.now() - bot_launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        memory = psutil.virtual_memory()

        uptime = f"{days}d, {hours}h, {minutes}m, {seconds}s"
        embed = discord.Embed(
            title="Queros Information", description="Info about creator and bot status"
        )
        embed.add_field(name="Uptime:", value=uptime, inline=True)
        embed.add_field(name="Creator:", value="TrooperZ", inline=True)
        embed.add_field(
            name="Total Users", value=str(len(set(self.bot.users))), inline=True
        )
        embed.add_field(
            name="Total Servers", value=str(len(self.bot.guilds)), inline=True
        )
        embed.add_field(
            name="Language Used", value="Python, using discord.py", inline=True
        )
        embed.add_field(name="Version", value="v1.1", inline=True)
        embed.add_field(
            name="CPU", value=f"{psutil.cpu_percent(percpu=False)} %", inline=True
        )
        embed.add_field(
            name="Memory",
            value=f"{round(memory.used/1024**2)} MiB used, {round(memory.total/1024**2)} MiB total.",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def donate(self, ctx):
        """How to donate to bot?"""
        await ctx.send(
            "You can donate via Monero (XMR) or via Ethereum (ETH) cryptocurrency\nXMR: 454KvhmqG7jKkf5LQ4zWbKdfN9iCW3fKuZbzz546i6PHDFJPvrNLKvP3oUqBPwBEWEP2YPvLACmorVp9KeqRRW5HShzrzBM\nETH: 0x7dce61d6b52c83a0c0d125787e081a841c52f2b4"
        )


# setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
    bot.add_cog(BotInfo(bot))
