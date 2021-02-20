#!/usr/bin/python
# -*- coding: utf-8 -*-
# Utillity cog for main bot.
import asyncio
import datetime
import os
import random
import sys
import time
import traceback
import urllib.request
from math import *

import async_google_trans_new
import discord
import matplotlib.pyplot as plt
import psutil
import yahoo_finance_async as yf
from bs4 import BeautifulSoup
from discord.ext import commands
from googlesearch import search
from simpleeval import simple_eval
from yahoo_fin import stock_info as si

bot_launch_time = datetime.datetime.now()  # bot launch time for uptime command


class Utillity(commands.Cog):
    """General commands that can help you with things."""

    def __init__(self, bot):
        # Initalizes bot.
        self.bot = bot
        self.configcol = self.bot.mongodatabase["configs"]

    @commands.command()
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def stonks(self, ctx, stock: str, time="1d"):
        """Grabs stock info for a ticker of your choice.
        Choose from 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, and max"""
        try:
            cmds = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            cmdsList = ["0"]

            for i in cmds:
                cmdOff = i["commands"]
                cmdsList.extend(cmdOff)

            if "stonks" in cmdsList:
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

            await ctx.channel.trigger_typing()

            if time not in (
                "1d",
                "5d",
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "2y",
                "5y",
                "10y",
                "ytd",
                "max",
            ):
                await ctx.send(
                    "Please choose a valid time period, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, and max"
                )
                return

            stSTONKprice = round(si.get_live_price(stock.lower()), 2)
            if time not in ("3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"):
                data = yf.download(stock.upper(), period=time, interval="15m")
            else:
                data = yf.download(stock.upper(), period=time)
            yfTick = yf.Ticker(stock)

            plot = data.Close.plot()
            plt.ylabel("USD")
            plt.savefig("stocksgraph.png")
            plt.clf()

            linkchannel = self.bot.get_channel(776505285216043039)
            myfile = discord.File("stocksgraph.png")
            await linkchannel.send(file=myfile)
            message = await linkchannel.fetch_message(linkchannel.last_message_id)

            link = message.attachments
            for i in link:
                imagelink = i.proxy_url

            embed = discord.Embed(
                title=f"Stock info",
                description=f"{yfTick.info['shortName']}",
                color=0x7300FF,
            )
            embed.set_author(name=f"{stock}", icon_url=yfTick.info["logo_url"])
            embed.set_image(url=imagelink)
            embed.add_field(
                name="Current price",
                value="$" + str(stSTONKprice) + " USD",
                inline=False,
            )
            embed.add_field(name="Graph", value="** **", inline=False)

            embed.set_footer(text="Powered by Yahoo Finance")
            await ctx.send(embed=embed)
            os.remove("stocksgraph.png")
            return

        except Exception as e:
            await ctx.send(
                "Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server."
            )
            await ctx.send("Error: " + str(e))  # make asnyc

    @commands.command()
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def raninteger(
        self, ctx, num1: int, num2: int
    ):  # Generates a random number within 2 integers.
        """Gives a random integer within two predefined integers.
        Example: u.raninteger 2 9"""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "raninteger" in cmdsList:
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
        try:
            if num1 < num2:  # checks if 1st num is less than 2nd
                resultNum = random.randint(num1, num2)  # generates number
                await ctx.send(str(resultNum))

            if num1 > num2:  # errors if 1st num is greater.
                await ctx.send("The 1st number should be less than the 2nd.")

        except Exception as e:
            await ctx.send(
                "Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server."
            )
            await ctx.send("Error: " + str(e))

    @commands.command()
    @commands.cooldown(rate=1, per=6.0, type=commands.BucketType.user)  # make asnyc
    async def gsearch(self, ctx, *, searchQ: str):  # searches google for query
        """Searches something on google.
        Example: u.search How to make pizza"""
        # embed stuff
        try:
            cmds = self.configcol.find(
                {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
            )
            cmdsList = ["0"]
            for i in cmds:
                cmdOff = i["commands"]
                cmdsList.extend(cmdOff)
            if "gsearch" in cmdsList:
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

            await ctx.channel.trigger_typing()
            embed = discord.Embed(
                title="Results for: *" + searchQ + "*", color=0x5EC1FF
            )
            embed.set_author(name="Google Search")

            for j in search(str(searchQ), num=3, stop=3, pause=1):
                req = urllib.request.Request(j)
                req.add_header("User-Agent", "Mozilla/5.0")
                soup = BeautifulSoup(urllib.request.urlopen(req))
                embed.add_field(name=soup.title.string, value=j, inline=False)

            await ctx.send(embed=embed)
            return

        except Exception as e:
            await ctx.send(
                "Hmm, thats odd. The command errored out. Please try again with different arguments and report it on the support server if it continues."
            )
            await ctx.send("Error: " + str(e))

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def translate(
        self, ctx, text: str, toLang=None, fromLang=None
    ):  # translates text via google translate
        """Translates text via Google Translate. Put your text in quotes fromLang is the origin language and toLang is the target language. Make sure to spell the languages right.
        Examples:
        u.translate "kako si?" (fromLang and toLang is not here so it auto detects and translates to English)
        u.translate "je suis faim" spanish (toLang is specified and translates to Spanish)
        u.translate "no habla espanol" french spanish (fromLang and toLang are specified and it does the translation)
        """
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "translate" in cmdsList:
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
        await ctx.channel.trigger_typing()
        translator = async_google_trans_new.google_translator()

        conversionKey = async_google_trans_new.LANGUAGES
        reversed_dictionary = {value: key for (key, value) in conversionKey.items()}

        if toLang == None and fromLang == None:
            result = await translator.translate(text)
            source = await translator.detect(text)

            embed = discord.Embed(
                title="**Queros Translate**",
                description="Here's the translated text!",
                color=0x2B00FF,
            )
            embed.add_field(name=source[1].capitalize(), value=text, inline=True)
            embed.add_field(name="English", value=result, inline=True)

            await ctx.send(embed=embed)
            return

        elif fromLang == None:
            toLanglow = toLang.lower()
            toLangDictC = reversed_dictionary[toLanglow]

            result = await translator.translate(text, lang_tgt=toLangDictC)
            source = await translator.detect(text)

            embed = discord.Embed(
                title="**Queros Translate**",
                description="Here's the translated text!",
                color=0x2B00FF,
            )
            embed.add_field(name=source[1].capitalize(), value=text, inline=True)
            embed.add_field(name=toLang.capitalize(), value=result, inline=True)

            await ctx.send(embed=embed)
            return

        elif fromLang != None and toLang != None:  # if languages are specified
            fromLanglow = fromLang.lower()  # lowers languages
            toLanglow = toLang.lower()

            fromLangDictC = reversed_dictionary[fromLanglow]  # converts to codes
            toLangDictC = reversed_dictionary[toLanglow]

            result = await translator.translate(
                text, lang_tgt=toLangDictC, lang_src=fromLangDictC
            )

            embed = discord.Embed(
                title="**Queros Translate**",
                description="Here's the translated text!",
                color=0x2B00FF,
            )
            embed.add_field(name=fromLang.capitalize(), value=text, inline=True)
            embed.add_field(name=toLang.capitalize(), value=result, inline=True)

            await ctx.send(embed=embed)
            return

    @commands.command(aliases=["calculate", "calculator"])
    @commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
    async def calc(self, ctx, *, equation):  # simple calculator
        """Calculates math problems. Only use symbols and numbers for now."""
        cmds = self.configcol.find(
            {"$and": [{"guild": ctx.guild.id}, {"cfg_type": "cmdsoff"}]}
        )
        cmdsList = ["0"]
        for i in cmds:
            cmdOff = i["commands"]
            cmdsList.extend(cmdOff)
        if "calc" in cmdsList:
            return
        elif "calculate" in cmdsList:
            return
        elif "calculator" in cmdsList:
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
        try:

            try:
                no_no_words = [
                    "import",
                    "__",
                    "os",
                    "sys",
                    "await",
                    "bot",
                    "self",
                    "raise",
                    "ctx",
                    "eval",
                    "def",
                    "lambda",
                    "0x",
                    "dir",
                    "rm",
                    "rf",
                    "cd",
                    "exit",
                    "chr",
                    "sudo",
                    "getattr",
                    'f"',
                ]
                if any(x in no_no_words for x in equation):
                    await ctx.send(
                        ":neutral_face: Can't calculate that. Make sure you're using proper terms, and *mathematical* terms :wink:"
                    )
                    return

                equation = equation.replace("^", "**")

                await ctx.send(
                    simple_eval(
                        equation,
                        functions={
                            "acos": acos,
                            "asin": asin,
                            "atan": atan,
                            "atan2": atan2,
                            "ceil": ceil,
                            "cos": cos,
                            "cosh": cosh,
                            "degrees": degrees,
                            "exp": exp,
                            "fabs": fabs,
                            "floor": floor,
                            "fmod": fmod,
                            "frexp": frexp,
                            "hypot": hypot,
                            "ldexp": ldexp,
                            "log": log,
                            "log10": log10,
                            "modf": modf,
                            "pow": pow,
                            "radians": radians,
                            "sin": sin,
                            "sinh": sinh,
                            "sqrt": sqrt,
                            "tan": tan,
                            "tanh": tanh,
                            "rand": random.randint,
                        },
                    )
                )

            # error stuff
            except ZeroDivisionError:
                await ctx.send("You can't calculate by zero, duh.")

            except SyntaxError or NameError:
                await ctx.send(
                    "Formulate your math problem correctly you illiterate moron."
                )

        except Exception as e:
            await ctx.send(
                ":neutral_face: Can't calculate that. Make sure you're using proper terms, and *mathematical* terms :wink:"
            )
            print(e)


def setup(bot):
    bot.add_cog(Utillity(bot))
