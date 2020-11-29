import pymongo
import discord
from discord.ext import commands
import sys
import os
from dotenv import load_dotenv

load_dotenv()


MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
modcol = mydb["moderation"]
configcol = mydb["configs"]
balcol = mydb['balances']

class Configuration(commands.Cog):
	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def curse_filter(self, ctx, level: str):
		"""Profanity filter. Toggle on or off"""
		if level.lower() not in ('off', 'on'):
			await ctx.send("Please choose a valid level")
			return
		server = ctx.message.guild.id
		try:
			configcol.update_one({"$and": [{"guild": server}, {"cfg_type": 'profanity'}]}, {"$set":{'cfg_type':'profanity', 'guild':server, 'level':level.lower()}}, upsert=True)
		except Exception as e:
			print(e)
		await ctx.send("Profanity filter level set to: **" + level.lower() + "**")

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def toggle_pog(self, ctx, yN: str):
		"""Toggles the pog gifs if pog is in a message"""
		if yN not in ('on', 'off'):
			await ctx.send("Please choose a valid level, on or off.")
			return
		server = ctx.message.guild.id
		try:
			configcol.update_one({"$and": [{"guild": server}, {"cfg_type": 'pogToggle'}]}, {"$set":{'cfg_type':'pogToggle', 'guild':server, 'yN':yN}}, upsert=True)
		except Exception as e:
			print(e)
		await ctx.send("Toggled auto gif reply to 'pog': **" + yN + "**")
	
	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def togglecmd(self, ctx, cmd: str, yN: str):
		"""Toggles commands, currently moderation does not have this ability."""
		if yN not in ('on', 'off'):
			await ctx.send("Please choose a valid level, on or off.")
			return
		if yN == 'off':
			logging = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			listcmd = []
			for i in logging:
				listcmd.extend(i['commands'])
			listcmd.append(cmd)
			configcol.update_one({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]}, {"$set":{'cfg_type':'cmdsoff', 'guild':ctx.guild.id, 'commands':listcmd}}, upsert=True)
			await ctx.send(f"Added **{cmd}** to off list.")

		if yN == 'on':
			logging = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
			for i in logging:
				listcmd = []
				listcmd.extend(i['commands'])
			listcmd.remove(cmd)
			configcol.update_one({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]}, {"$set":{'cfg_type':'cmdsoff', 'guild':ctx.guild.id, 'commands':listcmd}}, upsert=True)
			await ctx.send(f"Removed **{cmd}** from off list.")

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def togglechannel(self, ctx, channel: discord.TextChannel, yN: str):
		"""Toggles which channel the bot to ignore, currently moderation does not have this ability."""
		if yN not in ('on', 'off'):
			await ctx.send("Please choose a valid level, on or off.")
			return
		if yN == 'off':
			logging = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})
			channels = []
			for i in logging:
				channels.extend(i['channels'])
			channels.append(channel.id)
			configcol.update_one({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]}, {"$set":{'cfg_type':'channeloff', 'guild':ctx.guild.id, 'channels':channels}}, upsert=True)
			await ctx.send(f"Added **{channel}** to off list.")

		if yN == 'on':
			logging = configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})
			for i in logging:
				channels = []
				channels.extend(i['channels'])
			channels.remove(channel.id)
			configcol.update_one({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]}, {"$set":{'cfg_type':'channeloff', 'guild':ctx.guild.id, 'channels':channels}}, upsert=True)
			await ctx.send(f"Removed **{channel}** from off list.")

	@commands.command()
	@commands.has_permissions(manage_guild=True)
	async def startticketing(self, ctx, channel: discord.TextChannel):
		"""Select a channel for the ticket function (broken rn)"""
		mainmsg = await channel.send("To create a ticket for help with moderators, react with :ticket:")
		await mainmsg.add_reaction("\U0001f3ab")


#setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
	bot.add_cog(Configuration(bot))
