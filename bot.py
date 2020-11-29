#!/usr/bin/python
# -*- coding: utf-8 -*-
# bot.py
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


initial_extensions = ['cogs.utillity', 'cogs.fun', 'cogs.configuration', 'cogs.moderation', 'cogs.economy', 'cogs.music_newtest']

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
bot.help_command = PrettyHelp(color=0x6bd5ff, active=60)
bot.wavelink = wavelink.Client(bot=bot)
profanity.load_censor_words(whitelist_words=['ass', 'asses', 'gay', 'homosexual', 'lesbian', 'dick', 'homo',
                                       '4r5e', 'areole', 'cawk' 'cow girl', 'cow girls',
                                       'cowgirl', 'cowgirls', 'crap', 'butthole', 'crotch',
                                       'damn', 'dick', 'dong', 'doofus', 'dopey', 'doosh',
                                       'drunk','dummy','dumass', 'dumbass', 'dumbasses',
                                       'enlargement', 'f4nny', 'facial', 'fanny', 'fart', 
                                       'fat', 'flange', 'fondle', 'foobar', 'freex', 'frigg',
                                       'fubar', 'gae', 'gai', 'gaylord', 'gays', 'gey', 'ghay',
                                       'ghey', 'god', 'gtfo', 'guido', 'h0m0', 'h0mo', 'hardon', 
                                       'he11', 'hell', 'hebe', 'heeb', 'hemp', 'hentai', 'heroin', 
                                       'herp', 'herpes', 'herpy', 'heshe', 'hoar', 'hom0', 'homey',
                                       'homo', 'hookah', 'hooch', 'hootch', 'howtokill', 'howtomurdep',
                                       'hump', 'humped', 'humping', 'incest', 'jerk', 'junkie', 'junky',
                                       'kill', 'knob', 'kraut', 'LEN', 'leper', 'lesbians', 'lesbo', 
                                       'lesbos', 'lez', 'lezbian', 'lesbos', 'lezbos', 'lezbians', 'lezzie', 
                                       'lezzies', 'lezzy', 'lmao', 'lmfao', 'loin', 'loins', 'lube', 'maxi',
                                       'menses', 'menstruate', 'menstruation', 'molest', 'moron', 'muff', 'murder',
                                       'mutha', 'muther', 'nad', 'nads', 'naked', 'napalm', 'nappy', 'nazi', 'nipple',
                                       'nipples', 'nob', 'nobs', 'nude', 'nudes', 'nutbutter', 'omg', 'opium', 'opiate', 
                                       'oral', 'orally', 'organ', 'ovary', 'ovum', 'ovums', 'paddy', 'pantie', 'panties',
                                       'panty', 'pasty', 'pastie', 'pawn', 'pcp', 'pedo', 'pedophilia', 'pedophile', 
                                       'pee', 'peepee', 'penetrate', 'penetration', 'penis', 'peyote', 'piss', 'piss-off', 
                                       'pissed', 'pissing', 'pissin', 'pissoff', 'pms', 'pollock', 'poop', 'pornography',
                                       'pot', 'potty', 'prick', 'pricks', 'pron', 'punky', 'puss', 'quicky', 'queer', 
                                       'queers', 'rape', 'rapist', 'raped', 'rectal', 'rectum', 'reich', 'revue', 'ritard', 
                                       'rum', 'rump', 'pube', 'pubic', 'ruski', 's0b', 's-o-b', 's.o.b.', 'sandbar', 'scag', 
                                       'scantily', 'schizo', 'schlong', 'screwed', 'screw', 'screwing', 'scroat', 'scrot', 
                                       'scrotum', 'scrud', 'scum', 'seaman', 'seamen', 'seduce', 'sexual', 'shag', 'skag', 
                                       'skank', 'slave', 'slope', 'smut', 'smutty', 'snatch', 'sniper', 'snuff', 'sodom', 
                                       'souse', 'soused', 'spac', 'spunk', 'steamy', 'stfu', 'stiffy', 'stoned', 'strip', 
                                       'stroke', 'stupid', 'suck', 'sucked', 'sucking', 'tampon', 'tawdry', 'teabagging', 
                                       'testee', 'testicle', 'thrust', 'thug', 'tinkle', 'toke', 'transsexual', 
                                       'tramp', 'trashy', 'tw4t', 'twat', 'ugly', 'undies', 'unwed', 'urinal', 'urine', 
                                       'uterus', 'uzi', 'viagra', 'vagina', 'virgin', 'valium', 'vixen', 'vodka', 'vomit',
                                       'vulgar', 'wad', 'wedgie', 'weed', 'weewee', 'weenie', 'weiner', 'weirdo', 'willy', 
                                       'willies', 'womb', 'woody', 'wtf'])

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@tasks.loop(seconds=10.0)
async def remove_inf():
        cursor = modcol.find({})
        for document in cursor:
          if document['infraction'] == 'Ban':
              if document['removetime'] < time.time():
                  serverGuild = bot.get_guild(int(document['guildid']))
                  user = bot.get_user(int(document['userid']))
                  await serverGuild.unban(user)

@remove_inf.before_loop
async def before_some_task():
  await bot.wait_until_ready()


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    profVal = configcol.find({"$and": [{"guild": message.guild.id}, {"cfg_type": 'profanity'}]})
    for x in profVal:
        levelProf = str(x['level'])

    try:
        if levelProf == 'on':
            if profanity.contains_profanity(message.content.lower()):
                await message.delete()
                warnmsg = await message.channel.send(f"{message.author.mention}, watch your language.")
                await asyncio.sleep(10)
                await warnmsg.delete()

    except UnboundLocalError:
        return

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
                    await message.channel.send(file=discord.File('pog1.gif'))
                if coinflip123 == 2:
                   await message.channel.send(file=discord.File('pog2.gif'))
                return


@bot.event 
async def on_ready():
    print("Bot is online.")
    remove_inf.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="u.help and other Queros commands in " + str(len(bot.guilds)) + " servers"))

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
    raise error

bot.run(TOKEN, bot=True, reconnect=True)
