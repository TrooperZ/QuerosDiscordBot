#!/usr/bin/python
# -*- coding: utf-8 -*-
# Utillity cog for main bot.
import random
from bs4 import BeautifulSoup
import time
import sys
import os
import urllib.request
import discord
import googletrans
from googletrans import Translator
from discord.ext import commands
from googlesearch import search
import datetime
import traceback
import asyncio
import yfinance as yf
import matplotlib.pyplot as plt 
from yahoo_fin import stock_info as si
import pymongo
import logging
from dotenv import load_dotenv

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
configcol = mydb["configs"]

bot_launch_time = datetime.datetime.now() #bot launch time for uptime command

for handler in logging.root.handlers[:]:
	logging.root.removeHandler(handler)

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Utillity(commands.Cog):
	"""General commands that can help you with things."""

	def __init__(self, bot):
		#Initalizes bot.
		self.bot = bot

	@commands.command()
	@commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
	async def stonks(self, ctx, stock: str, time='1d'):
		"""Grabs stock info for a ticker of your choice. 
		Choose from 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, and max"""
		try:
			cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			cmdsList = ['0']

			for i in cmds:
				cmdOff = i['commands']
				cmdsList.extend(cmdOff)

			channelList = ['0']
			channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})
			for i in channels:
				channeloff = i['channels']
				channelList.extend(channeloff)
			if 'stonks' in cmdsList:
				return

			channelList = ['0']
			channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})
	
			for i in channels:
				channeloff = i['channels']
				channelList.extend(channeloff)

			if ctx.message.channel.id in channelList:
				return
		
			await ctx.channel.trigger_typing()

			if time not in ('1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max'):
				await ctx.send("Please choose a valid time period, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, and max")
				return

			stSTONKprice = round(si.get_live_price(stock.lower()), 2)
			if time not in ('3mo','6mo','1y','2y','5y','10y','ytd','max'):
				data = yf.download(stock.upper(), period=time, interval = "15m")
			else:
				data = yf.download(stock.upper(), period=time)
			yfTick = yf.Ticker(stock)
			
			plot = data.Close.plot() 
			plt.ylabel('USD')
			plt.savefig('stocksgraph.png')
			plt.clf()
			

			linkchannel = self.bot.get_channel(776505285216043039)
			myfile = discord.File('stocksgraph.png')
			await linkchannel.send(file=myfile)
			message = await linkchannel.fetch_message(linkchannel.last_message_id)

			link = message.attachments
			for i in link:
				imagelink = i.proxy_url

			embed = discord.Embed(title=f"Stock info", description=f"{yfTick.info['shortName']}", color=0x7300ff)
			embed.set_author(name=f"{stock}", icon_url=yfTick.info['logo_url'])
			embed.set_image(url=imagelink)
			embed.add_field(name="Current price", value="$" + str(stSTONKprice) + " USD", inline=False)
			embed.add_field(name="Graph", value="** **", inline=False)

			embed.set_footer(text="Powered by Yahoo Finance")
			await ctx.send(embed=embed)
			os.remove('stocksgraph.png')
			return

		except Exception as e:
			await ctx.send("Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server.")
			await ctx.send("Error: " + str(e))
			logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command()
	@commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
	async def uptime(self, ctx): #Uptime provides how long the bot is running.  Periodic restarts are reccomended.
		"""Bot uptime."""
		try:
			cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			cmdsList = ['0']
			for i in cmds:
				cmdOff = i['commands']
				cmdsList.extend(cmdOff)
			if 'uptime' in cmdsList:
				return
			channelList = ['0']
			channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

			for i in channels:
				channeloff = i['channels']
				channelList.extend(channeloff)

			if ctx.message.channel.id in channelList:
				return

			delta_uptime = datetime.datetime.now() - bot_launch_time 
			hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
			minutes, seconds = divmod(remainder, 60)
			days, hours = divmod(hours, 24)

			await ctx.send(f"{days}d, {hours}h, {minutes}m, {seconds}s")
			return

		except Exception as e:
			await ctx.send("Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server.")
			await ctx.send("Error: " + str(e))
			logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command()
	@commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
	async def raninteger(self, ctx, num1:int, num2:int):  #Generates a random number within 2 integers.
		"""Gives a random integer within two predefined integers.
		Example: u.raninteger 2 9""" 
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'raninteger' in cmdsList:
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		try:
			if (num1 < num2): #checks if 1st num is less than 2nd
				resultNum = random.randint(num1, num2) #generates number
				await ctx.send(str(resultNum)) 

			if num1 > num2: #errors if 1st num is greater.
				await ctx.send("The 1st number should be less than the 2nd.")

		except Exception as e:
			await ctx.send("Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server.")
			await ctx.send("Error: " + str(e))
			logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command()
	@commands.cooldown(rate=1, per=6.0, type=commands.BucketType.user)
	async def gsearch(self, ctx, *, searchQ: str):   #searches google for query
		"""Searches something on google.
		Example: u.search How to make pizza"""
		#embed stuff
		try:
			cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			cmdsList = ['0']
			for i in cmds:
				cmdOff = i['commands']
				cmdsList.extend(cmdOff)
			if 'gsearch' in cmdsList:
				return
			channelList = ['0']
			channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

			for i in channels:
				channeloff = i['channels']
				channelList.extend(channeloff)

			if ctx.message.channel.id in channelList:
				return

			await ctx.channel.trigger_typing()
			embed = discord.Embed(title="Results for: *" + searchQ + "*", color=0x5ec1ff)
			embed.set_author(name="Google Search")

			for j in search(str(searchQ), num=3, stop=3, pause=1):
					req = urllib.request.Request(j)
					req.add_header('User-Agent', 'Mozilla/5.0')
					soup = BeautifulSoup(urllib.request.urlopen(req))
					embed.add_field(name=soup.title.string, value=j, inline=False)
	
			await ctx.send(embed=embed)
			return

		except Exception as e:
				await ctx.send("Hmm, thats odd. The command errored out. Please try again with different arguments and report it on the support server if it continues.")
				await ctx.send("Error: " + str(e))
				logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command()
	@commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
	async def translate(self, ctx, text, toLang='_', fromLang='0'): #translates text via google translate
		"""Translates text via Google Translate. Put your text in quotes fromLang is the origin language and toLang is the target language. Make sure to spell the languages right.
		Examples: 
		u.translate "kako si?" (fromLang and toLang is not here so it auto detects and translates to English)
		u.translate "je suis faim" spanish (toLang is specified and translates to Spanish)
		u.translate "no habla espanol" spanish french (fromLang and toLang are specified and it does the translation)
		"""
		try: 
			cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			cmdsList = ['0']
			for i in cmds:
				cmdOff = i['commands']
				cmdsList.extend(cmdOff)
			if 'translate' in cmdsList:
				return

			channelList = ['0']
			channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

			for i in channels:
				channeloff = i['channels']
				channelList.extend(channeloff)

			if ctx.message.channel.id in channelList:
				return
			await ctx.channel.trigger_typing() 
			translator = Translator() #generates translator item

			conversionKey = googletrans.LANGUAGES #grabs lang codes to physical languages
			reversed_dictionary = {value : key for (key, value) in conversionKey.items()} #reverses it for frontend

			try:
				if toLang == '_' and fromLang == '0': #if no languages are specified
					result = translator.translate(text) 
					resultSRCconv = result.src.lower() #converts lang code to lowercase
					convertedSrc = conversionKey[resultSRCconv] #converts code to word

					 #embed stuff
					embed = discord.Embed(title="**Queros Translate**", description="Here's the translated text!", color=0x2b00ff) 
					embed.add_field(name=convertedSrc.capitalize(), value=text, inline=True)
					embed.add_field(name="English", value=result.text, inline=True)
					embed.set_footer(text="Powered by Google Translate's Python library")

					await ctx.send(embed=embed)
					return

				elif fromLang == '0': #if dest lang is specified
					toLanglow = toLang.lower() #grabs lowercase dest lang
					toLangDictC = reversed_dictionary[toLanglow] #converts language name to code

					result = translator.translate(text, dest=toLangDictC) 
					resultSRCconv = result.src.lower() #lowers the origin lang src
					convertedSrc = conversionKey[resultSRCconv] #converts src to language

					 #embed stuff
					embed = discord.Embed(title="**Queros Translate**", description="Here's the translated text!", color=0x2b00ff)
					embed.add_field(name=convertedSrc.capitalize(), value=text, inline=True)
					embed.add_field(name=toLang.capitalize(), value=result.text, inline=True)
					embed.set_footer(text="Powered by Google Translate's Python library")

					await ctx.send(embed=embed)
					return

				elif fromLang != '0' and toLang != '_': #if languages are specified
					fromLanglow = fromLang.lower() #lowers languages
					toLanglow = toLang.lower()

					fromLangDictC = reversed_dictionary[fromLanglow] #converts to codes
					toLangDictC = reversed_dictionary[toLanglow]

					result = translator.translate(text, src=fromLangDictC, dest=toLangDictC)

					 #embed stuff
					embed = discord.Embed(title="**Queros Translate**", description="Here's the translated text!", color=0x2b00ff)
					embed.add_field(name=fromLang.capitalize(), value=text, inline=True)
					embed.add_field(name=toLang.capitalize(), value=result.text, inline=True)
					embed.set_footer(text="Powered by Google Translate's Python library")

					await ctx.send(embed=embed)
					return

			except Exception as e: #catches exception
					await ctx.send("Your arguments seem to be invalid, try again.")

		except Exception as e:
			await ctx.send("Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server.")
			await ctx.send("Error: " + str(e))
			logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command(aliases=['calculate', 'calculator'])
	@commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
	async def calc(self, ctx, equation): #simple calculator
		"""Calculates math problems. Only use symbols and numbers for now."""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'calc' in cmdsList:
			return
		elif 'calculate'in cmdsList:
			return
		elif 'calculator' in cmdsList:
			return

		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		try:  

			try:
				equation = equation.replace("^", "**")
				ans = eval(equation)

				await ctx.send(ans)

			#error stuff
			except ZeroDivisionError:
				await ctx.send("**SHUT IT DOWN!** Whew, you almost caused a black hole! Don't divide by zero")

			except SyntaxError or NameError:
				await ctx.send("Formulate your math problem correctly you illiterate moron.")

		except Exception as e:
			await ctx.send("Hmm, thats odd. The command errored out. Please try again, or with different arguments and report it on the support server.")
			await ctx.send("Error: " + str(e))
			logging.exception(f"Excecutor: {ctx.message.author.name}", exc_info=True)

	@commands.command()
	@commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
	async def botlink(self, ctx): 
		"""My link!"""
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return

		await ctx.send("Add Queros to your server today!\nhttps://discord.com/oauth2/authorize?client_id=760856635425554492&permissions=2146954871&scope=bot")

	@commands.command()
	@commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
	async def support(self, ctx):
		"""Help for the bot"""
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return

		await ctx.send("Join this server for bot support: https://discord.gg/7qvsUCBZ8W")

	@commands.command()
	@commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
	async def website(self, ctx):
		"""Bot's website"""
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return

		await ctx.send("We do not have a website yet.")

	@commands.command()
	@commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
	async def botinfo(self, ctx):
		"""General bot info"""
		delta_uptime = datetime.datetime.now() - bot_launch_time 
		hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
		minutes, seconds = divmod(remainder, 60)
		days, hours = divmod(hours, 24)
		
		author = await self.bot.fetch_user(390841378277425153)

		uptime = f"{days}d, {hours}h, {minutes}m, {seconds}s"
		embed=discord.Embed(title="Queros Information", description="Info about creator and bot status")
		embed.set_author(name=str(author), icon_url=author.avatar_url)
		embed.add_field(name="Uptime:", value=uptime, inline=True)
		embed.add_field(name="Total Users", value=str(len(self.bot.users)), inline=True)
		embed.add_field(name="Total Servers", value=str(len(self.bot.guilds)), inline=True)
		embed.add_field(name="Language Used", value="Python, using discord.py", inline=True)
		embed.add_field(name="Version", value="v0.0.1", inline=True)
		await ctx.send(embed=embed)

#setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
	bot.add_cog(Utillity(bot))
