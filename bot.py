#!/usr/bin/python
# -*- coding: utf-8 -*-
# bot.py

import asyncio
import os

import discord
import pymongo
import wavelink
from asyncdagpi import Client as dagpiClient
from discord.ext import commands, tasks
from dotenv import load_dotenv
from pretty_help import PrettyHelp

load_dotenv()
mongoclient = pymongo.MongoClient(f"mongodb+srv://queroscode:{os.getenv('MONGO_PASS')}@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")

intervals = (
    ("weeks", 604800),  # 60 * 60 * 24 * 7
    ("days", 86400),  # 60 * 60 * 24
    ("hours", 3600),  # 60 * 60
    ("minutes", 60),
    ("seconds", 1),
)


def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append("{} {}".format(value, name))
    return ", ".join(result[:granularity])


bot = commands.Bot(command_prefix="u.", intents=discord.Intents.all(), help_command=PrettyHelp())

bot.help_command = PrettyHelp(color=0x6BD5FF, active=60, verify_checks=False)
bot.wavelink = wavelink.Client(bot=bot)
bot.mongodatabase = mongoclient["data"]
bot.dagpi = dagpiClient(os.getenv("DAGPI_TOKEN"))
configcol = bot.mongodatabase["configs"]

if __name__ == "__main__":
    for extension in [
        "cogs.utillity",
        "cogs.fun",
        "cogs.configuration",
        "cogs.moderation",
        "cogs.economy",
        "cogs.botinfo",
        "cogs.image",
        "cogs.music",
        "cogs.dev"
    ]:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print("Bot is online.")

@bot.check
async def global_cmd_check(ctx):
    cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]})
    cmdsList = ["0"]
    for i in cmds:
        cmdOff = i["commands"]
        cmdsList.extend(cmdOff)
        if ctx.invoked_with in cmdsList:
            return False
    return True

    channelList = ["0"]
    channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": "channeloff"}]})

    for i in channels:
        channeloff = i["channels"]
        channelList.extend(channeloff)
        if ctx.message.channel.id in channelList:
            return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if error.retry_after < 1:
            await ctx.send(f"This command is on a `{round(error.retry_after, 2)} second` cooldown, try again later.")
            return

        fixedRetry = int(error.retry_after)
        await ctx.send(f"This command is on a `{display_time(fixedRetry)}` cooldown, try again later.")
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the permissions to run this command.")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing arguments in your command, check u.help [command] for the arguments.")
        return

    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("Queros does not have the proper permissions. Try: \nGiving Queros role or the other roles that Queros has the proper permissions\nMoving Queros up the role list\nMaking sure that the Muted roles are below Queros's role.")

    print(error)


bot.run(os.getenv("DISCORD_TOKEN"), bot=True, reconnect=True)
