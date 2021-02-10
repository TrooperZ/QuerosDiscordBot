#!/usr/bin/python
# -*- coding: utf-8 -*-
# bot.py
# Note: this code is designed for a Visual Studio virtual environment. Exclude the load_dotenv() for non venv.

import os
import discord
from discord.ext import commands
from pretty_help import PrettyHelp
import pymongo
from dotenv import load_dotenv
import wavelink
from asyncdagpi import Client as dagpiClient
from discord.ext import tasks

load_dotenv()
mongoclient = pymongo.MongoClient("mongodb+srv://queroscode:" + os.getenv('MONGO_PASS') + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),)

def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='u.', intents=intents, help_command=PrettyHelp())
bot.help_command = PrettyHelp(color=0x6bd5ff, active=60, verify_checks=False)
bot.wavelink = wavelink.Client(bot=bot)
bot.mongodatabase = mongoclient["data"]
bot.dagpi = dagpiClient(os.getenv('DAGPI_TOKEN'))


configcol = bot.mongodatabase["configs"]
modcol = bot.mongodatabase["moderation"]
premServercol = bot.mongodatabase["vipServers"]

@bot.command(hidden=True)
async def addpremiumserver(ctx, serverid: int):
    if not await bot.is_owner(ctx.author):
        return
    premServercol.insert_one({"server":ctx.guild.id})
    await ctx.send("done")

@bot.command(hidden=True)
async def delpremiumserver(ctx, serverid: int):
    if not await bot.is_owner(ctx.author):
        return
    premServercol.delete_one({"server":ctx.guild.id})
    await ctx.send("done")

@bot.command(hidden=True)
async def getguilds(ctx):
    if not await bot.is_owner(ctx.author):
        return
    for i in bot.guilds:
        await ctx.send(i.name)

@bot.command(hidden=True)
async def say(ctx, msg):
    if not await bot.is_owner(ctx.author):
        return
    await ctx.send(msg)

@bot.command(hidden=True)
async def reload_cog(ctx, cog: str):
    if not await bot.is_owner(ctx.author):
        return
    bot.reload_extension(cog)
    await ctx.send("done")

if __name__ == '__main__':
    for extension in ['cogs.utillity', 'cogs.fun', 'cogs.configuration', 'cogs.moderation', 'cogs.economy', 'cogs.botinfo', 'cogs.image', 'cogs.music']:
        bot.load_extension(extension)

@bot.event 
async def on_ready():
    print("Bot is online.")

@tasks.loop(seconds=60)
async def statusLoop():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="u.help in" + str(len(bot.guilds)) + " servers"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if error.retry_after < 1:
            await ctx.send('This command is on a `' + str(round(error.retry_after, 2)) + ' second` cooldown, try again later.')
            return
        fixedRetry = int(error.retry_after)
        await ctx.send('This command is on a `' + display_time(fixedRetry) + '` cooldown, try again later.')
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the permissions to run this command.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing arguments in your command, check u.help [command] for the arguments.")
        return
    print(error)

bot.run(os.getenv('DISCORD_TOKEN'), bot=True, reconnect=True)
