import pymongo
import discord
from discord.ext import commands
from discord.ext import tasks
import time
import datetime
import asyncio
from discord.ext.tasks import loop
import os
from bson.objectid import ObjectId
from dotenv import load_dotenv
import re

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
modcol = mydb["moderation"]

time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhdw])")
time_dict = {"h":3600, "s":1, "m":60, "d":86400, "w":604800}

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        matches = time_regex.findall(argument.lower())
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k]*float(v)
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d/w are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        try: 
             time = int(time)

        except:
            time = float(time)

        return time

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1))

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

class Moderation(commands.Cog):
    """Moderation Commands"""
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=30.0)
    async def remove_inf(self):
            cursor = modcol.find({})
            for document in cursor:
                    if document['status'] == 'finished':
                        continue
                    if float(document['removetime']) < time.time():
                        if document['infraction'] == 'Softban':
                            serverGuild = self.bot.get_guild(int(document['guildid']))
                            user = self.bot.get_user(int(document['userid']))
                            await serverGuild.unban(user)
                            modcol.update_one({'_id': document['_id']}, {"$set": {'status': 'finished'}}, upsert=False)

                        elif document['infraction'] == 'Temp VC Mute':
                            serverGuild = self.bot.get_guild(int(document['guildid']))
                            userId = int(document['userid'])
                            user = await serverGuild.fetch_member(userId)
                            await user.edit(mute=False)
                            modcol.update_one({'_id': document['_id']}, {"$set": {'status': 'finished'}}, upsert=False)

                        elif document['infraction'] == 'Temp Deafen':
                            serverGuild = self.bot.get_guild(int(document['guildid']))
                            userId = int(document['userid'])
                            user = await serverGuild.fetch_member(userId)
                            await user.edit(deafen=False)
                            modcol.update_one({'_id': document['_id']}, {"$set": {'status': 'finished'}}, upsert=False)

                        elif document['infraction'] == 'Temp Chat Mute':
                            serverGuild = self.bot.get_guild(int(document['guildid']))
                            userId = int(document['userid'])
                            user = await serverGuild.fetch_member(userId)
                            role = discord.utils.get(serverGuild.roles, name='Muted')
                            await user.remove_roles(role)
                            modcol.update_one({'_id': document['_id']}, {"$set": {'status': 'finished'}}, upsert=False)
            await asyncio.sleep(0.5)


    @remove_inf.before_loop
    async def before_some_task(self):
      await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.remove_inf.start()

    @commands.Cog.listener() 
    async def on_command_error(self, ctx, error): #error checking
        if isinstance(error, commands.MemberNotFound): #missing member
            await ctx.send("That member does not exist.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason="No reason"):
         """Gives a person the boot (Needs Kick Members permissions)"""

         kicklisting = {'userid':user.id, 
                        'guildid':ctx.message.guild.id, 
                        'reason':reason, 'infraction':'Kick', 
                        'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                        'punisher':ctx.author.id}

         kick = discord.Embed(title=f":boot: Kicked {user.name}!\nGuild: {ctx.guild.name}", description=f"Reason: {reason}\nBy: {str(ctx.author)}", color=0xB53737)

         await ctx.channel.send(embed=kick)
         await user.send(embed=kick)   

         await user.kick(reason=reason)  

         x = modcol.insert_one(kicklisting)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, user: discord.Member, duration: TimeConverter, *, reason="No reason"):
        """Temporarly bans the user. (Needs Ban Members permissions) 
        Example: u.ban @JoeMama#6969 2 hr Reason (Bans user for 2 hours)
        
        Fun Fact: Perm ban is not permanent. It is equal to 1 quadrillion years. But technically permanent.
        """
        if duration < 30:
            await ctx.send("Duration must be longer than 30 seconds.")
            return
        banlisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Softban', 
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'removetime':float(duration) + time.time(), 
                      'duration':display_time(duration),
                      'status': 'open',
                      'punisher':ctx.author.id}

        ban = discord.Embed(title=f":hammer: Temporarily Banned {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}\n**Duration:** {display_time(duration)}", color=0xB53737)

        await ctx.channel.send(embed=ban)
        await user.send(embed=ban)

        await user.ban(reason=reason)

        x = modcol.insert_one(banlisting)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def hardban(self, ctx, user: discord.Member, *, reason="No reason"):
        """Bans the user. (Needs Ban Members permissions) 
        Example: u.ban @JoeMama#6969 Reason"""
        
        banlisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Hardban', 
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'status': 'finished',
                      'punisher':ctx.author.id}

        ban = discord.Embed(title=f":hammer: PERMANENTLY Banned {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}", color=0xB53737)

        await ctx.channel.send(embed=ban)
        await user.send(embed=ban)

        await user.ban(reason=reason)

        x = modcol.insert_one(banlisting)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
         """Unbans a user (Needs Ban Members permissions)"""

         await ctx.guild.unban(user)

         unban = discord.Embed(title=f":angel: Unbanned {user.name}!\nGuild: {ctx.guild.name}", description=f"Enjoy and don't screw it up again!\n**By:** {str(ctx.author)}", color=0xD6DAEB)

         await ctx.channel.send(embed=unban)
         try:
             await user.send(embed=unban)
         except:
             return

    @commands.command(aliases=['purge', 'del', 'delete'])
    @commands.has_permissions(manage_messages=True)
    async def msgdel(self, ctx, amt: int):
         """Deletes messages (Max 200, needs Manage Messages permissions)"""
         if amt > 200:
             await ctx.send(":x: Due to performance limits, I cannot delete more than 200 messages at a time. You are more than welcome to use this command repeatedly.")
             return

         await ctx.channel.purge(limit=amt)
         await ctx.send("Whatcha lookin at, I deleted **" + str(amt) + "** messsages!", delete_after=10)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def tempvcmute(self, ctx, user: discord.Member, duration: TimeConverter, *, reason="No reason"):
        """Temp mutes a user in vc (Needs Mute Members permissions)"""
        if duration < 30:
            await ctx.send("Duration must be longer than 30 seconds.")
            return

        vcmutelisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Temp VC Mute',
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'removetime':float(duration) + time.time(),
                      'duration':display_time(duration), 
                      'status': 'open',
                      'punisher':ctx.author.id}
        try:
            await user.edit(mute=True)
            vcmute = discord.Embed(title=f":mute: Temporarily Voice Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}\n**Duration:** {display_time(duration)}", color=0xB53737)
            
            await ctx.channel.send(embed=vcmute)
            await user.send(embed=vcmute)

            x = modcol.insert_one(vcmutelisting)

        except:
            await ctx.send("User is not connected to voice.")
            return

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def permvcmute(self, ctx, user: discord.Member, *, reason="No reason"):
        """Permanently mutes a user in voice channel (Needs Mute Members permissions)"""

        vcmutelisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Hard VC Mute', 
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'status': 'finished',
                      'punisher':ctx.author.id}

        await user.edit(mute=True)

        vcmute = discord.Embed(title=f":mute: PERMANENTLY Voice Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:* {reason}\n**By:** {str(ctx.author)}", color=0xB53737)

        await ctx.channel.send(embed=vcmute)
        await user.send(embed=vcmute)

        x = modcol.insert_one(vcmutelisting)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def unvcmute(self, ctx, user: discord.Member):
        """Unmutes a user in voice channel (Needs Mute Members permissions)"""

        await user.edit(mute=False)

        vcmute = discord.Embed(title=f":microphone2: Voice Unmuted {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't screw it up!\n**By:** {str(ctx.author)}", color=0xD6DAEB)

        await ctx.channel.send(embed=vcmute)
        await user.send(embed=vcmute)
        return

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def tempdeafen(self, ctx, user: discord.Member, duration: TimeConverter, *, reason="No reason"):
        """Temp deafens a user in voice channel, does not mute. (Needs Mute Members permissions)"""
        if duration < 30:
            await ctx.send("Duration must be longer than 30 seconds.")
            return

        deafenlisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Temp Deafen', 
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'removetime':float(duration) + time.time(),
                      'duration':display_time(duration), 
                      'status': 'open',
                      'punisher':ctx.author.id}

        deafen = discord.Embed(title=f":mute: Temporarily Deafened {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}\n**Duration:** {display_time(duration)}", color=0xB53737)

        await user.edit(deafen=True)

        await ctx.send(embed=deafen)
        await user.send(embed=deafen)

        x = modcol.insert_one(deafenlisting)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def permdeafen(self, ctx, user: discord.Member, *, reason="No reason"):
        """Perm deafens a user in voice channel, does not mute. (Needs Mute Members permissions)"""

        deafenlisting = {'userid':user.id, 
                      'guildid':ctx.message.guild.id, 
                      'reason':reason, 
                      'infraction':'Perm Deafen', 
                      'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                      'status': 'finished',
                      'punisher':ctx.author.id}

        deafen = discord.Embed(title=f":mute: PERMANENTLY Deafened {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}", color=0xB53737)

        await user.edit(deafen=True)

        await ctx.send(embed=deafen)
        await user.send(embed=deafen)

        x = modcol.insert_one(deaflisting)

    @commands.command()
    @commands.has_guild_permissions(deafen_members=True)
    async def undeafen(self, ctx, user: discord.Member):
        """Undeafens a user in voice channel. (Needs Deafen Members permissions)"""

        await user.edit(deafen=False)

        mute = discord.Embed(title=f"Undeafened {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't mess it up!\n**By:** {str(ctx.author)}", color=0xD6DAEB)

        await ctx.send(embed=mute)
        await user.send(embed=mute)

    @commands.command()
    @commands.has_guild_permissions(move_members=True)
    async def vckick(self, ctx, user: discord.Member):
        """Kicks a user in voice channel. (Needs Move Members permissions)"""
        await user.edit(voice_channel=None)

    @commands.command(aliases=['temptxtmute', 'softtxtmute', 'softtextmute'])
    @commands.has_permissions(manage_roles=True)
    async def temptextmute(self, ctx, user: discord.Member, duration: TimeConverter, *, reason="No reason"):
        """Temp mutes a user in text channels. (Needs Manage Roles permissions)"""

        if discord.utils.get(ctx.guild.roles, name='Muted'):
            role = discord.utils.get(ctx.guild.roles, name='Muted')

            await user.add_roles(role)

            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)

        else:
            perms = discord.Permissions(send_messages=False, read_messages=True)
            await ctx.guild.create_role(name='Muted', permissions=perms, color=Rcolor)

            role = discord.utils.get(ctx.guild.roles, name='Muted')
            await role.edit(position=0)
            await user.add_roles(role)

            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)

        txtmutelisting = {'userid':user.id, 
                          'guildid':ctx.message.guild.id, 
                          'reason':reason, 
                          'infraction':'Temp Chat Mute', 
                          'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                          'removetime':float(duration) + time.time(),
                          'duration':display_time(duration), 
                          'status': 'open',
                          'punisher':ctx.author.name}

        mute = discord.Embed(title=f"Temporarily Chat Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}\n**Duration:** {display_time(duration)}", color=0xB53737)
        await ctx.send(embed=mute)
        await user.send(embed=mute)
        x = modcol.insert_one(txtmutelisting)

    @commands.command(aliases=['permtxtmute', 'hardtxtmute', 'hardtextmute'])
    @commands.has_permissions(manage_roles=True)
    async def permtextmute(self, ctx, user: discord.Member,*, reason="No reason"):
        """Temp mutes a user in text channels. (Needs Manage Roles permissions)"""

        if discord.utils.get(ctx.guild.roles, name='Muted'):
            role = discord.utils.get(ctx.guild.roles, name='Muted')

            await user.add_roles(role)

            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)

        else:
            perms = discord.Permissions(send_messages=False, read_messages=True)
            await ctx.guild.create_role(name='Queros Muted', permissions=perms, color=Rcolor)

            role = discord.utils.get(ctx.guild.roles, name='Muted')
            await role.edit(position=0)
            await user.add_roles(role)

            overwrites = {
                Muted: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False,
                )
            }

            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False)

        txtmutelisting = {'userid':user.id, 
                          'guildid':ctx.message.guild.id, 
                          'reason':reason, 
                          'infraction':'Perm Chat Mute', 
                          'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                          'status': 'finished',
                          'punisher':ctx.author.name}

        mute = discord.Embed(title=f"PERMANENTLY Chat Muted {user.name}!\nGuild: {ctx.guild.name}", description=f"**Reason:** {reason}\n**By:** {str(ctx.author)}", color=0xB53737)
        await ctx.send(embed=mute)
        await user.send(embed=mute)
        x = modcol.insert_one(txtmutelisting)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def untxtmute(self, ctx, user: discord.Member):
        """Unmutes a user in text channels (Needs Manage Roles permissions)"""

        role = discord.utils.get(ctx.guild.roles, name='Muted')

        await user.remove_roles(role)
        unmute = discord.Embed(title=f"Removed Text Mute from {user.name}!\nGuild: {ctx.guild.name}", description=f"Don't mess it up!\n**By:** {str(ctx.author)}", color=0xD6DAEB)
        await ctx.send(embed=unmute)
        await user.send(embed=unmute)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, user: discord.User, *, warning="No reason"):
        """Warns a user. (Needs Manage Messages permissions)"""

        await ctx.send(str(user.mention) + ", You have been warned for: **" + warning + "**, from **" + str(ctx.author) + "**")
        await user.send("You have been warned for: **" + warning + "** in the server: " + str(ctx.guild.name))
        strDur = 'N/A'

        warnlist = {'userid':user.id, 
                    'guildid':ctx.message.guild.id, 
                    'reason':warning, 
                    'infraction':'Warn', 
                    'time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%Z", time.gmtime()), 
                    'status': 'finished',
                    'punisher':ctx.author.name}

        x = modcol.insert_one(warnlist)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def usrhistory(self, ctx, user: discord.User, items=5):
        """Gets a user's history. (Does not sync with non-Queros moderation)"""

        history = modcol.find({"$and": [{"userid": user.id}, 
                          {"guildid": ctx.message.guild.id}]})
        embed = discord.Embed(title="History of " + str(user.name) + " in: " + str(ctx.author.guild.name), color=0xe1ff00)
        
        itemsCount = 0

        for x in history:
            itemsCount += 1
            punisherUser = self.bot.get_user(x['punisher'])
            try:
                embed.add_field(name="**" + str(x['infraction']) + "** `" + str(x['_id']) + "`" , value="Reason: **" + str(x['reason']) + "**\nTime: **" + str(x['time']) + "**\nPunisher: **" + str(punisherUser) + "**\nDuration: **" + str(x['duration']) + "**", inline=False)
            
            except:
                embed.add_field(name="**" + str(x['infraction']) + "** `" + str(x['_id']) + "`" , value="Reason: **" + str(x['reason']) + "**\nTime: **" + str(x['time']) + "**\nPunisher: **" + str(punisherUser), inline=False)
            
            if itemsCount >= items:
                break

        embed.set_footer(text=f"Showing {itemsCount} items.")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def delitem(self, ctx, user: discord.User, delid: str):
        """Deletes an item from user history (Needs Manage Guild permissions)"""
        delete = modcol.delete_one({'_id': ObjectId(delid)})
        await ctx.send(f"Deleted item `{delid}` from {user.mention}'s history.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def clearhistory(self, ctx, user: discord.User):
        """Clears user's history (Needs Manage Guild permissions)"""
        history = modcol.find({"$and": [{"userid": user.id}, 
                          {"guildid": ctx.message.guild.id}]})
        for i in history:
            delete = modcol.delete_one({'_id': i['_id']})
        await ctx.send(f"Cleared {user.mention}'s infraction history.")

def setup(bot):
    bot.add_cog(Moderation(bot))
