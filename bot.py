#!/usr/bin/python
# -*- coding: utf-8 -*-
# bot.py
# Note: this code is designed for a Visual Studio virtual environment. Exclude the load_dotenv() for non venv.

import os
import discord
from discord.ext import commands
from discord.ext import tasks
import time
import re
import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
import requests	
import asyncio
import functools
import itertools
import math
import datetime
import random
from pretty_help import PrettyHelp
import json
import pymongo
import wavelink
from dotenv import load_dotenv
from better_profanity import profanity

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
configcol = mydb["configs"]
modcol = mydb["moderation"]
premServercol = mydb["vipServers"]


initial_extensions = ['cogs.utillity', 'cogs.fun', 'cogs.configuration', 'cogs.moderation', 'cogs.economy', 'cogs.music']

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

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='u.', intents=intents, help_command=PrettyHelp())
bot.help_command = PrettyHelp(color=0x6bd5ff, active=60, verify_checks=False)
bot.wavelink = wavelink.Client(bot=bot)
#profanity.load_censor_words(whitelist_words=

@bot.command(hidden=True)
async def addpremiumserver(ctx, serverid: int):
    owner = await bot.fetch_user(390841378277425153)
    if ctx.author != owner:
        return
    premServercol.insert_one({"server":ctx.guild.id})
    await ctx.send("done")
    return

@bot.command(hidden=True)
async def delpremiumserver(ctx, serverid: int):
    owner = await bot.fetch_user(390841378277425153)
    if ctx.author != owner:
        return
    premServercol.delete_one({"server":ctx.guild.id})
    await ctx.send("done")
    return

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    #profVal = configcol.find({"$and": [{"guild": message.guild.id}, {"cfg_type": 'profanity'}]})
    #for x in profVal:
    #    levelProf = str(x['level'])

    #try:
    #    if levelProf == 'on':                                                   #profanity config is disabled temporarly
    #        if profanity.contains_profanity(message.content.lower()):
    #            await message.delete()
    #            warnmsg = await message.channel.send(f"{message.author.mention}, watch your language.")
    #            await asyncio.sleep(10)
    #            await warnmsg.delete()

    #except UnboundLocalError:
    #    return

    if "pog" in message.content.lower():
        if message.author.bot:
            return
        serversOn = configcol.find({"$and": [{"guild": message.guild.id}, {"cfg_type": 'pogToggle'}]})
        for x in serversOn:
            toggle = str(x['yN'])
        try:
            if toggle == 'on':
                coinflip123 = random.randint(1,2)
                if coinflip123 == 1:
                    await message.channel.send(file=discord.File('pog1.gif'))
                if coinflip123 == 2:
                   await message.channel.send(file=discord.File('pog2.gif'))
                return

            elif toggle == 'off':
                return

        except UnboundLocalError:
                coinflip123 = random.randint(1,2)
                if coinflip123 == 1:
                    await message.channel.send(file=discord.File('pogGifs/pog1.gif'))
                if coinflip123 == 2:
                   await message.channel.send(file=discord.File('pogGifs/pog2.gif'))
                return

@bot.event 
async def on_ready():
    print("Bot is online.")
    #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="u.help and other Queros commands in " + str(len(bot.guilds)) + " servers"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if error.retry_after < 1:
            await ctx.send('This command is on a `' + str(round(error.retry_after, 2)) + ' second` cooldown, try again later.')
            return
        fixedRetry = int(error.retry_after)
        await ctx.send('This command is on a `' + display_time(fixedRetry) + '` cooldown, try again later.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the permissions to run this command.")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing arguments in your command, check u.help [command] for the arguments.")
    print(error)

bot.run(TOKEN, bot=True, reconnect=True)
