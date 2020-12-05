import pymongo
import discord
from discord.ext import commands
import time
import datetime
import asyncio
from discord.ext.tasks import loop
import os
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
modcol = mydb["moderation"]

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, reason="No reason"):
         """Gives a person the boot"""

         kicklisting = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':reason, 'infraction':'Kick', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'duration':'N/A', 'punisher':ctx.author.name}
         kick = discord.Embed(title=f":boot: Kicked {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}")

         await user.kick(reason=reason)

         await ctx.channel.send(embed=kick)
         await user.send(embed=kick)     

         x = modcol.insert_one(kicklisting)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, reason="No reason", duration=99999999999999999999999999999999999999999999999, unit='perm'):
        """Let the ban hammer swing. Do not specify a duration and unit if you want permaban"""

        if unit == 'perm':
            durationlog = duration

        elif unit == 'sec':
            durationlog = duration

        elif unit == 'min':
            durationlog = duration * 60

        elif unit == 'hr':
            durationlog = duration * 60 * 60

        elif unit == 'day':
            durationlog = duration * 60 * 60 * 24

        elif unit == 'wk':
            durationlog = duration * 60 * 60 * 24 * 7

        elif unit == 'mth':
            durationlog = duration * 60 * 60 * 24 * 30

        elif unit == 'yr':
            durationlog = duration * 60 * 60 * 24 * 365

        if unit == 'perm':
            strDur = 'perm'

        else:
            strDur = str(duration) + unit

        banlisting = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':reason, 'infraction':'Ban', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'removetime':durationlog + time.time(), 'duration':strDur, 'punisher':ctx.author.name}
        ban = discord.Embed(title=f":hammer: Banned {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}\nDuration: {strDur}")

        await user.ban(reason=reason)

        await ctx.channel.send(embed=ban)
        await user.send(embed=ban)

        x = modcol.insert_one(banlisting)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
         """Reverse bans a user"""

         await ctx.guild.unban(user)

         unban = discord.Embed(title=f":angel: Unbanned {user.name}!\nGuild: {ctx.guild.name}", description=f"Enjoy and don't screw it up again!\nBy: {ctx.author.mention}")

         await ctx.channel.send(embed=unban)
         await user.send(embed=unban)

    @commands.command(aliases=['purge', 'del', 'delete'])
    @commands.has_permissions(manage_messages=True)
    async def msgdel(self, ctx, amt: int):
         """Deletes messages (Max 500)"""
         if amt > 500:
             await ctx.send("Due to performace and API limits, I cannot delete more than 500 messages at a time.")
         await ctx.channel.purge(limit=amt)

         message = await ctx.send("Whatcha lookin at, I deleted **" + str(amt) + "** messsages")

         await asyncio.sleep(10)
         await message.delete()

    @commands.command(aliases=['vcmute'])
    @commands.has_guild_permissions(mute_members=True)
    async def vmute(self, ctx, user: discord.Member, duration=99999999999999999999999999999999999999999999999, unit='perm', reason="no reason"):
         """Mutes a user in vc (do not use timed mute, broken rn)"""

         if ctx.author.voice and ctx.author.voice.channel:
            if unit == 'perm':
                durationlog = duration

            elif unit == 'sec':
                durationlog = duration

            elif unit == 'min':
                durationlog = duration * 60

            elif unit == 'hr':
                durationlog = duration * 60 * 60

            elif unit == 'day':
                durationlog = duration * 60 * 60 * 24

            elif unit == 'wk':
                durationlog = duration * 60 * 60 * 24 * 7

            elif unit == 'mth':
                durationlog = duration * 60 * 60 * 24 * 30

            elif unit == 'yr':
                durationlog = duration * 60 * 60 * 24 * 365


            if unit == 'perm':
                strDur = 'perm'

            else:
                strDur = str(duration) + unit

            vcmutelisting = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':reason, 'infraction':'VC Mute', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'duration':strDur, 'removetime':durationlog, 'punisher':ctx.author.name}
            
            await user.edit(mute=True)

            vcmute = discord.Embed(title=f":mute: Voice Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}\nDuration: {strDur}")

            await ctx.channel.send(embed=vcmute)
            await user.send(embed=vcmute)

            x = modcol.insert_one(vcmutelisting)
            return

         else:
               await ctx.send("You are not connected to a voice channel!")

    @commands.command(aliases=['unvcmute'])
    @commands.has_guild_permissions(mute_members=True)
    async def unvmute(self, ctx, user: discord.Member):
         """Unmutes a user in vc"""

         if ctx.author.voice and ctx.author.voice.channel:
            await user.edit(mute=False)

            vcmute = discord.Embed(title=f":microphone2: Voice Unmuted {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't screw it up!\nBy: {ctx.author.mention}")

            await ctx.channel.send(embed=vcmute)
            await user.send(embed=vcmute)
            return

         else:
               await ctx.send("You are not connected to a voice channel!")

    @commands.command()
    @commands.has_guild_permissions(deafen_members=True)
    async def deafen(self, ctx, user: discord.Member, duration=99999999999999999999999999999999999999999999999, unit='perm', reason="it's private"):
         """Deafens a user in vc (do not use timed deafen, its broken)"""

         if ctx.author.voice and ctx.author.voice.channel:
            if unit == 'perm':
                durationlog = duration

            elif unit == 'sec':
                durationlog = duration

            elif unit == 'min':
                durationlog = duration * 60

            elif unit == 'hr':
                durationlog = duration * 60 * 60

            elif unit == 'day':
                durationlog = duration * 60 * 60 * 24

            elif unit == 'wk':
                durationlog = duration * 60 * 60 * 24 * 7

            elif unit == 'mth':
                durationlog = duration * 60 * 60 * 24 * 30

            elif unit == 'yr':
                durationlog = duration * 60 * 60 * 24 * 365


            if unit == 'perm':
                strDur = 'perm'

            else:
                strDur = str(duration) + unit

            deaflisting = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':reason, 'infraction':'VC Deafen', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'duration':strDur, 'removetime':durationlog, 'punisher':ctx.author.name}
            
            await user.edit(deafen=True)
            deafen = discord.Embed(title=f"Deafened {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}\nDuration: {strDur}")
            await ctx.send(embed=deafen)
            await user.send(embed=deafen)
            x = modcol.insert_one(deaflisting)

         else:
               await ctx.send("You are not connected to a voice channel!")

    @commands.command()
    @commands.has_guild_permissions(deafen_members=True)
    async def undeafen(self, ctx, user: discord.Member):
         """Undeafens a user in vc"""

         if ctx.author.voice and ctx.author.voice.channel:
            mute = discord.Embed(title=f"Undeafened {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't mess it up!\nBy: {ctx.author.mention}")
            await ctx.send(embed=mute)
            await user.send(embed=mute)

         else:
               await ctx.send("You are not connected to a voice channel!")

    @commands.command()
    @commands.has_guild_permissions(move_members=True)
    async def vckick(self, ctx, user: discord.Member):
         """Kicks a user in vc"""

         if ctx.author.voice and ctx.author.voice.channel:
                await user.edit(voice_channel=None)

         else:
               await ctx.send("You are not connected to a voice channel!")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def txtmute(self, ctx, user: discord.Member, duration=99999999999999999999999999999999999999999999999, unit='perm', reason="No reason"):
        """Mutes a user in text channels (do not use timed mute, its broken)"""

        if discord.utils.get(ctx.guild.roles, name='Queros Muted'):
            role = discord.utils.get(ctx.guild.roles, name='Queros Muted')

            await user.add_roles(role)
            mute = discord.Embed(title=f"Text Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}\nDuration: {strDur}")
            await ctx.send(embed=mute)
            await user.send(embed=mute)
            return

        else:
            guild = ctx.guild
            perms = discord.Permissions(send_messages=False, read_messages=True)
            Rcolor = discord.Colour(0xff0000)
            await guild.create_role(name='Queros Muted', permissions=perms, color=Rcolor)
            role = discord.utils.get(ctx.guild.roles, name='Queros Muted')
            await role.edit(position=5)
            await user.add_roles(role)
            mute = discord.Embed(title=f"Text Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {ctx.author.mention}\nDuration: {strDur}")
            await ctx.send(embed=mute)
            await user.send(embed=mute)
            return

        if unit == 'perm':
            durationlog = duration

        elif unit == 'sec':
            durationlog = duration

        elif unit == 'min':
            durationlog = duration * 60

        elif unit == 'hr':
            durationlog = duration * 60 * 60

        elif unit == 'day':
            durationlog = duration * 60 * 60 * 24

        elif unit == 'wk':
            durationlog = duration * 60 * 60 * 24 * 7

        elif unit == 'mth':
            durationlog = duration * 60 * 60 * 24 * 30

        elif unit == 'yr':
            durationlog = duration * 60 * 60 * 24 * 365


        if unit == 'perm':
            strDur = 'perm'

        else:
            strDur = str(duration) + unit

        txtmutelisting = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':reason, 'infraction':'Text Channel Mute', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'duration':strDur, 'removetime':durationlog, 'punisher':ctx.author.name}
        x = modcol.insert_one(txtmutelisting)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def untxtmute(self, ctx, user: discord.Member):
        """Unmutes a user in text channels"""

        role = discord.utils.get(ctx.guild.roles, name='Queros Muted')

        await user.remove_roles(role)
        unmute = discord.Embed(title=f"Removed Text Mute from {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't mess it up!\nBy: {ctx.author.mention}")
        await ctx.send(embed=unmute)
        await user.send(embed=unmute)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, user: discord.Member, *, warning="N/A"):
        """Warns a user."""

        await ctx.send(str(user.mention) + ", You have been warned for: **" + warning + "**")
        await user.send("You have been warned for: **" + warning + "** in the server: " + str(ctx.guild.name))
        strDur = 'N/A'

        warnlist = {'userid':user.id, 'guildid':ctx.message.guild.id, 'reason':warning, 'infraction':'Warn', 'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 'sectime':time.time(), 'duration':strDur, 'removetime':durationlog, 'punisher':ctx.author.name}
        x = modcol.insert_one(warnlist)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def usrhistory(self, ctx, user: discord.Member):
        """Gets a user's history"""

        history = modcol.find({"$and": [{"userid": user.id}, 
                          {"guildid": ctx.message.guild.id}]})
        embed = discord.Embed(title="History of: " + str(user.name) + " in: " + str(ctx.author.guild.name), color=0xe1ff00)

        for x in history:
             embed.add_field(name="**" + str(x['infraction']) + "** `" + str(x['_id']) + "`" , value="Reason: **" + str(x['reason']) + "**\nTime: **" + str(x['time']) + "**\nPunisher: **" + str(x['punisher']) + "**\nDuration: **" + str(x['duration']) + "**", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def delitem(self, ctx, user: discord.Member, delid: str):
        """Deletes an item from user history"""
        delete = modcol.delete_one({'_id': ObjectId(delid)})
        await ctx.send(f"Deleted item `{delid}` from {user.mention}'s history.")

def setup(bot):
    bot.add_cog(Moderation(bot))
