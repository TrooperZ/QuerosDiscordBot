#!/usr/bin/python
# -*- coding: utf-8 -*-
# Fun command category
import asyncio
import sys
import os
import random
import json
import requests
import asyncpraw
from bs4 import BeautifulSoup
import urllib.request
import discord
from discord.ext import commands
import PIL.Image
import deeppyer
import re
import asyncdagpi
import datetime
 
reddit = asyncpraw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'), 
					 client_secret=os.getenv('REDDIT_API_KEY'),
					 password=os.getenv('REDDIT_PASSWORD'), 
					 user_agent='QuerosDiscordBot accessAPI:v0.0.1 (by /u/Troopr_Z)',
					 username=os.getenv('REDDIT_USERNAME'))

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
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'pickupline' in cmdsList:
			return

		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)
		if ctx.message.channel.id in channelList:
			return
		line = await self.bot.dagpi.pickup_line()
		await ctx.send(line.line)

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def joke(self, ctx):
		"""Generates a joke, may be NSFW"""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'joke' in cmdsList:
			return

		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)
		if ctx.message.channel.id in channelList:
			return
		await ctx.send(await self.bot.dagpi.joke())

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def roast(self, ctx):
		"""Generates a roast, may be NSFW"""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'roast' in cmdsList:
			return

		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)
		if ctx.message.channel.id in channelList:
			return
		await ctx.send(await self.bot.dagpi.roast())

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def yomama(self, ctx):
		"""Generates a roast, may be NSFW"""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'yomama' in cmdsList:
			return

		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)
		if ctx.message.channel.id in channelList:
			return
		await ctx.send(await self.bot.dagpi.yomama())

	@commands.command()
	async def snipe(self, ctx, *, channel: discord.TextChannel = None):
		channel = channel or ctx.channel
		try:
			msg = self.bot.snipes[channel.id]
		except KeyError:
			return await ctx.send('Nothing to snipe!')
		if msg.author.id == 390841378277425153 and ctx.author != msg.author:
			await ctx.send("I cannot snipe my master.")
		await ctx.send(embed=discord.Embed(description=msg.content, color=msg.author.color).set_author(name=str(msg.author), icon_url=str(msg.author.avatar_url)))

	@commands.command(aliases=['murder'])
	@commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
	async def kill(self, ctx, user: discord.Member):
		"""Eliminates a user of your choice."""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'kill' in cmdsList:
			return
		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		kill_choices = [f"{user.name} just got 360 noscoped by {ctx.message.author.name}, let's gooooooo!",
			f"{user.name} drank expired milk and died.",
			f"{user.name} tripped and fell in the industrial blender.",
			f"{user.name} got poisoned by {ctx.message.author.name}",
			f"{user.name} has been eliminated. Well done Agent 47, proceed to the extraction point.",
			f"*chk chik* **BOOM!** {user.name}'s guts just got splattered on the wall by {ctx.message.author.name}",
			f"{user.name} was skooter ankled."
			]

		await ctx.send(random.choice(kill_choices))

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def redditgrab(self, ctx, subreddit: str, spoiler='no'):
		"""Grabs a post from reddit subreddit, add spoiler to make the image a spoiler"""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'redditgrab' in cmdsList:
			return
		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		await ctx.channel.trigger_typing()
		try:
				subredditGrabbed = await reddit.subreddit(subreddit)
		except Exception as e:
				await ctx.send("Hmm, there was an issue getting that subreddit. Make sure to type the subreddit without the r/.")
				print(e)
		Listposts = []
		randomPost = random.randint(1, 120)
		async for post in subredditGrabbed.hot(limit=60):
			Listposts.append(post)
		post = Listposts[randomPost]

		if post.over_18:
				if ctx.channel.is_nsfw():		
							embed = discord.Embed(title=post.title, description="Posted by: " + str(post.author), url="https://www.reddit.com" + post.permalink, color=0xff4000)
							embed.set_author(name="Post from r/" + subreddit)
							if post.is_self:
								embed.add_field(name="** **", value=str(post.selftext))
							else:
								embed.set_image(url=post.url)
							embed.set_footer(text="Upvotes: " + str(post.score))
							await ctx.send(embed=embed)

				else:
						await ctx.send("Content is NSFW, this channel is not NSFW, content will not be loaded.")

		if post.over_18 == False:
					embed = discord.Embed(title=post.title, description="Posted by: " + str(post.author), url="https://www.reddit.com" + post.permalink, color=0xff4000)
					embed.set_author(name="Post from r/" + subreddit)
					if post.is_self:
						embed.add_field(name="** **", value=str(post.selftext))
					else:
						embed.set_image(url=post.url)
					embed.set_footer(text="Upvotes: " + str(post.score))
					await ctx.send(embed=embed)

	@commands.command(aliases=['8ball'])
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def eightB(self, ctx: commands.Context, *, query: str):
		"""Eight Ball shall tell your future"""
		cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if '8ball' in cmdsList:
			return
		elif 'eightB' in cmdsList: 
			return
		channelList = ['0']
		channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		if query.endswith("?") != True:
				await ctx.send("Ya gotta ask me a yes or no question that ends with a question mark bro")
				return

		valuE = 0

		for letter in query:
			valuE = valuE + (ord(letter)*ord(letter))
			if (valuE % 5) == 0:
						resultNeu = ["I cannot predict that",
					"Only time will tell",
					"Ask me later",
					"That question is beyond my knowledge"]
						await ctx.send(random.choice(resultNeu))
						return

			if (valuE % 2) > 0:
						resultPos = ["Most likely",
					"My sources point to yes",
					"High chance",
					"I think yes"]
						await ctx.send(random.choice(resultPos))
						return

			if (valuE % 2) == 0:
						resultNo = ["Not likely",
					"High chance of no",
					"I don't think it is a yes...",
					"Sources point to no"]
						await ctx.send(random.choice(resultNo))
						return

#setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
	bot.add_cog(Fun(bot))
