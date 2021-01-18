#!/usr/bin/python
# -*- coding: utf-8 -*-
# Fun command category
import asyncio
import sys
import os
import random
import json
import requests
import praw
from bs4 import BeautifulSoup
import urllib.request
import discord
from discord.ext import commands
import pymongo
import PIL.Image
import deeppyer
from wand.image import Image 
from dotenv import load_dotenv

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
configcol = mydb["configs"]

#reddit ID stuff
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_API_KEY = os.getenv('REDDIT_API_KEY')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, 
					 client_secret=REDDIT_API_KEY,
					 password=REDDIT_PASSWORD, 
					 user_agent='QuerosDiscordBot accessAPI:v0.0.1 (by /u/Troopr_Z)',
					 username=REDDIT_USERNAME)

class Fun(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(rate=1, per=3.0, type=commands.BucketType.user)
	async def meme(self, ctx): 
		"""Sends a meme fresh from reddit"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'meme' in cmdsList:
			return

		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return

		coinflip = random.randint(1, 2) #randomizes between 2 subs
		#grabs the meme
		if coinflip == 1:
			response = requests.get("https://www.reddit.com/r/dankmemes.json", headers={"User-Agent": "linux:queros:v1.0.0"})

		if coinflip == 2:
			response = requests.get("https://www.reddit.com/r/memes.json", headers={"User-Agent": "linux:queros:v1.0.0"})
		#loads the meme
		page = response.json()
		meme = random.choice(page["data"]["children"])["data"]["url"]

		await ctx.send(meme)

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def deepfry(self, ctx): 
		"""Deepfries an image, must put command with uploaded image"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'deepfryuser' in cmdsList:
			return

		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		for attachment in ctx.message.attachments:
			await attachment.save("targetImgdp.png")
			providedimage = PIL.Image.open("targetImgdp.png")
			image = await deeppyer.deepfry(providedimage, flares=False)
			image.save("fryer.png")
			pic = discord.File('fryer.png')
			await ctx.send(file=pic)

	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def waveify(self, ctx, height = 32, width = 4): 
		"""Adds wave effect to an image, must put command with uploaded image"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'deepfryuser' in cmdsList:
			return

		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		for attachment in ctx.message.attachments:
			await attachment.save("wavetargetimg.png")
			with Image(filename ="wavetargetimg.png") as img:
						img.wave(amplitude = img.height / height, wave_length = img.width / width) 
						img.save(filename ="wavedimg.png") 
			pic = discord.File('wavedimg.png')
			await ctx.send(file=pic)
		
	@commands.command()
	@commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
	async def deepfryuser(self, ctx, user: discord.Member): 
		"""Deepfries a user's profile pic"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'deepfryuser' in cmdsList:
			return

		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return

		img = user.avatar_url_as()
		await img.save("targetuserImgdp.png")
		providedimage = PIL.Image.open("targetuserImgdp.png")
		image = await deeppyer.deepfry(providedimage, flares=False)
		image.save("fryer.png")
		pic = discord.File('fryer.png')
		await ctx.send(file=pic)

	@commands.command()
	@commands.cooldown(rate=1, per=3.0, type=commands.BucketType.user)
	async def pingy(self, ctx):
		"""Pings a random online user"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'pingy' in cmdsList:
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		user = random.choice(ctx.guild.members) #gets a random user
			
		while user.status == discord.Status.offline or user.bot == True:
			user = random.choice(ctx.guild.members)
		await ctx.send(f'{user.mention} come join the fun!')

	@commands.command()
	@commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
	async def say(self, ctx, *, message: str):
		"""Says whatever crap you want"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'say' in cmdsList:
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		await ctx.message.delete()
		await ctx.send(message)

	@commands.command(aliases=['murder'])
	@commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
	async def kill(self, ctx, user: discord.Member):
		"""Eliminates a user of your choice."""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'kill' in cmdsList:
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		kill_choices = [f"{user.mention} just got 360 noscoped by {ctx.message.author.mention}, let's gooooooo!",
			f"{user.mention} drank expired milk and died.",
			f"{user.mention} tripped and fell in the industrial blender.",
			f"{user.mention} got poisoned by {ctx.message.author.mention}",
			f"{user.mention} has been eliminated. Well done Agent 47, proceed to the extraction point.",
			f"*chk chik* **BOOM!** {user.mention}'s guts just got splattered on the wall by {ctx.message.author.mention}"]

		await ctx.send(random.choice(kill_choices))

	@commands.command()
	@commands.cooldown(rate=1, per=3.0, type=commands.BucketType.user)
	async def redditgrab(self, ctx, subreddit: str, spoiler='no'):
		"""Grabs a post from reddit subreddit, add spoiler to make the image a spoiler"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if 'redditgrab' in cmdsList:
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

		for i in channels:
			channeloff = i['channels']
			channelList.extend(channeloff)

		if ctx.message.channel.id in channelList:
			return
		await ctx.channel.trigger_typing()
		try:
				subredditGrabbed = reddit.subreddit(subreddit)
		except Exception as e:
				await ctx.send("Hmm, there was an issue getting that subreddit. Make sure to type the subreddit without the r/.")
				print(e)

		randomPost = random.randint(1, 120)
		Listposts = [post for post in subredditGrabbed.hot(limit=120)]
		post = Listposts[randomPost]

		if post.over_18:
				if ctx.channel.is_nsfw():		
						if spoiler == 'spoiler':
								urllib.request.urlretrieve(post.url, "SPOILER_image_nsfw.jpg")

								with open('SPOILER_image_nsfw.jpg', 'rb') as f:
										picture = discord.File(f)
										await ctx.send(file=picture)

						if spoiler == 'no':
								embed = discord.Embed(title=post.title, description="Posted by: " + str(post.author), url="https://www.reddit.com" + post.permalink, color=0xff4000)
								embed.set_author(name="Post from r/" + subreddit)
								embed.set_image(url=post.url)
								embed.set_footer(text="Upvotes: " + str(post.score))
								await ctx.send(embed=embed)

				else:
						await ctx.send("This channel is not NSFW, go somewhere else!")

		if post.over_18 == False:
				if spoiler == 'spoiler':
								urllib.request.urlretrieve(post.url, "SPOILER_image_sfw.jpg")

								with open('SPOILER_image_sfw.jpg', 'rb') as f:
									picture = discord.File(f)
									await ctx.send(file=picture)

				if spoiler == 'no':
						embed = discord.Embed(title=post.title, description="Posted by: " + str(post.author), url="https://www.reddit.com" + post.permalink, color=0xff4000)
						embed.set_author(name="Post from r/" + subreddit)
						embed.set_image(url=post.url)
						embed.set_footer(text="Upvotes: " + str(post.score))
						await ctx.send(embed=embed)

	@commands.command(aliases=['8ball'])
	@commands.cooldown(rate=1, per=1.0, type=commands.BucketType.user)
	async def eightB(self, ctx: commands.Context, *, query: str):
		"""Eight Ball shall tell your future"""
		cmds = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
		cmdsList = ['0']
		for i in cmds:
			cmdOff = i['commands']
			cmdsList.extend(cmdOff)
		if '8ball' in cmdsList:
			return
		elif 'eightB' in cmdsList: 
			return
		channelList = ['0']
		channels = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

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
