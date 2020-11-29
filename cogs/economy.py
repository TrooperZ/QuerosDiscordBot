import discord
import os
import pymongo
import random
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()



MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
balcol = mydb['balances']
configcol = mydb['configuration']


class Economy(commands.Cog):
	def __init__(self, bot):
		#Initalizes bot.
		self.bot = bot

	@commands.command(aliases=['bopen'])
	@commands.cooldown(rate=1, per=20.0, type=commands.BucketType.user)
	async def bankopen(self, ctx):
		"""Opens a bank for your cash"""
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

		if balcol.count({'user':ctx.message.author.id}) > 0:
			await ctx.send("You already have a bank, get lost!")
			return

		balcol.insert_one({'user':ctx.message.author.id, 'wallet':0, 'safe':0})
		await ctx.send(ctx.author.mention + ", you have opened a bank! Do u.bal to check your balance.")

	@commands.command(aliases=['bal'])
	@commands.cooldown(rate=1, per=3.0, type=commands.BucketType.user)
	async def balance(self, ctx, user: discord.Member):
		"""Gets balance"""
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
		if user == None: 
			user = ctx.message.author
		balance = balcol.find({'user':user.id})
		userStr = user.name

		for x in balance:
			wallet = int(x['wallet'])
			bank = int(x['safe'])

		embed = discord.Embed(title="**Balance for: **" + userStr, color=0xffee00)
		embed.set_author(name="Economy")

		try:
			embed.add_field(name="Wallet", value=str(wallet) + " QuCoin", inline=False)
			embed.add_field(name="Bank", value=str(bank) + " QuCoin", inline=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send(embed=embed)

	@commands.command()
	@commands.cooldown(rate=1, per=120.0, type=commands.BucketType.user)
	async def forage(self, ctx):
		"""Looks for coins"""
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
		randomCoins = random.randint(1,100)
		balance = balcol.find({'user':ctx.message.author.id})

		for x in balance:
			wallet = int(x['wallet'])

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + randomCoins}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send("You found **" + str(randomCoins) + "** QuCoins somewhere. I don't think it's a good idea to pick them up tho...")

	@commands.command(aliases=['dep'])
	@commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
	async def deposit(self, ctx, amt='all'):
		"""Deposits wallet"""
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
		balance = balcol.find({'user':ctx.message.author.id})

		for x in balance:
			wallet = int(x['wallet'])
			bank = int(x['safe'])

		if amt == 'all':
			depAmt = wallet

		elif amt != 'all':
			depAmt = int(amt)

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'safe':bank + depAmt}}, upsert=False)
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet - depAmt}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send("**" + str(depAmt) + "** QuCoins deposited. They're safe now.")

	@commands.command(aliases=['with'])
	@commands.cooldown(rate=1, per=15.0, type=commands.BucketType.user)
	async def withdraw(self, ctx, amt='all'):
		"""Withdraws to wallet"""
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
		balance = balcol.find({'user':ctx.message.author.id})

		for x in balance:
			wallet = int(x['wallet'])
			bank = int(x['safe'])

		if amt == 'all':
			withAmt = wallet

		elif amt != 'all':
			withAmt = int(amt)

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'safe':bank - withAmt}}, upsert=False)
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + withAmt}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send("**" + str(withAmt) + "** QuCoins withdrawn. They're in your pocket now.")

	@commands.command()
	@commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)
	async def daily(self, ctx, amt='all'):
		"""Grabs daily rations"""
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
		balance = balcol.find({'user':ctx.message.author.id})
		for x in balance:
			wallet = int(x['wallet'])

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + 2000}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send("Daily claimed, **2000** QuCoins added to your wallet.")

	@commands.command(aliases=['gamble'])
	@commands.cooldown(rate=1, per=0, type=commands.BucketType.user)
	async def bet(self, ctx, amt=45):
		"""Bets money. Need at least 100 coins"""
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
		if amt < 100:
			await ctx.send("Please bet more than **100** QuCoins.")
			return

		balance = balcol.find({'user':ctx.message.author.id})

		for x in balance:
			wallet = int(x['wallet'])

		try:
			if wallet < 100:
				await ctx.send("Get some more cash you peasent.")
				return

			seed = random.randint(1, 10)


			if seed >= 5:
				lostAmt = random.randint(1, 2 * amt) + amt

				if wallet < lostAmt:
					lostAmt = wallet

				embed = discord.Embed(title="Betting **" + str(amt) + "** QuCoins", color=0xFF0000)
				embed.set_author(name="Economy\n")

				balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet - lostAmt}}, upsert=False)
				embed.add_field(name="You Lost", value="`" + str(lostAmt) + "` QuCoins", inline=True)

				await ctx.send(embed=embed)
				return

			if seed >= 2 and seed <= 4:
				WonAmt = random.randint(1, 2 * amt)

				embed = discord.Embed(title="Betting **" + str(amt) + "** QuCoins", color=0x008000)
				embed.set_author(name="Economy\n")

				embed.add_field(name="You Won", value="`" + str(WonAmt) + "` QuCoins", inline=True)
				balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + WonAmt}}, upsert=False)

				await ctx.send(embed=embed)
				return

			if seed == 1:
				embed = discord.Embed(title="Betting **" + str(amt) + "** QuCoins", color=0xffee00)
				embed.set_author(name="Economy\n")

				embed.add_field(name="Nothing lost.", value="`" + str(amt) + "` QuCoins", inline=True)

				await ctx.send(embed=embed)
				return

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

	@commands.command()
	@commands.cooldown(rate=1, per=31449600, type=commands.BucketType.user)
	async def yearly(self, ctx):
		"""Yearly payout. BIG amount of cash ;)"""
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
		balance = balcol.find({'user':ctx.message.author.id})
		for x in balance:
			wallet = int(x['wallet'])

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + 2}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send("Yearly claimed, **2** QuCoins added to your wallet. What did you expect?")

	@commands.command(aliases=['pay'])
	@commands.cooldown(rate=1, per=8, type=commands.BucketType.user)
	async def give(self, ctx, user: discord.Member, amt: int):
		"""Gives coins to someone"""
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
		balance = balcol.find({'user':ctx.message.author.id})
		giver = balcol.find({'user':user.id})

		for x in balance:
			wallet = int(x['wallet'])

		for x in giver:
			gwallet = int(x['wallet'])

		if amt <= 0:
			await ctx.send("Please choose a valid amount.")
			return

		elif amt > 0:
			giveamt = amt

		try:
			balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet - giveamt}}, upsert=False)
			balcol.update_one({'user':user.id}, {"$set": {'wallet':wallet + giveamt}}, upsert=False)

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return

		await ctx.send(f"**{giveamt}** QuCoins given to {user.mention}. Enjoy your coins!")

	@commands.command(aliases=['rob'])
	@commands.cooldown(rate=1, per=90, type=commands.BucketType.user)
	async def steal(self, ctx, user: discord.Member):
		"""Robs a person"""
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
		if user == ctx.message.author:
			await ctx.send("You rob yourself and find out that you're poor. :|")
			return

		balance = balcol.find({'user':ctx.message.author.id})
		robbee = balcol.find({'user':user.id})

		for x in balance:
			wallet = int(x['wallet'])

		if wallet < 420:
			await ctx.send("You're too poor to rob, get **420** QuCoins to rob people, peasent.")
			return

		for x in robbee:
			rwallet = int(x['wallet'])
		
		if rwallet < 420:
			await ctx.send("Stealing from the poor? What a scumbag. The victim needs to have at least **420** QuCoins.")
			return

		coinflip = random.randint(1, 3)
		
		try:
			if coinflip == 1:
				robamt = random.randint(1, rwallet*0.85)
				balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet + robamt}}, upsert=False)
				balcol.update_one({'user':user.id}, {"$set": {'wallet':wallet - robamt}}, upsert=False)
				await ctx.send(f"You stole **{robamt}** from {user.name}! Shh, keep it hush hush...")
				return

			else:
				fine = random.randint(150, 420)
				balcol.update_one({'user':ctx.message.author.id}, {"$set": {'wallet':wallet - fine}}, upsert=False)
				balcol.update_one({'user':user.id}, {"$set": {'wallet':wallet + fine}}, upsert=False)
				await ctx.send(f"You paid **{fine}** to {user.name} for getting caught, so much for being sneaky.")
				return

		except UnboundLocalError:
			await ctx.send("Hmm, no bank found. Open a bank by using u.bankopen!")
			return


def setup(bot):
	bot.add_cog(Economy(bot))

