#!/usr/bin/python
# -*- coding: utf-8 -*-
# music.py 

import discord 
from discord.ext import commands 
from discord.ext import tasks 
import wavelink 
import asyncio 
import datetime 
import time 
import os 
import random 
import re 
import math 
from dotenv import load_dotenv 

class QueueSystem(commands.Cog):
    def __init__(self, bot):
        self.guildtracker = {}
        self.channeltracker = {}
        self.bot = bot
    
    async def newqueue(self, guild_id):
        queue = Queue() 
        self.guildtracker[guild_id] = queue 
        return
    
    async def get_queue(self, guild_id):
        return self.guildtracker[guild_id] 
    
    async def newchannel(self, guild_id, channel):
        self.channeltracker[guild_id] = channel 
        return 
    
    async def get_channel(self, guild_id):
        return self.channeltracker[guild_id] 
     
class Queue():
    def __init__(self):
        self.queue = [] 
        self.requestlist = [] 
        self.skipsong = None 
        self.skipvoters = []

    def clear(self):
        self.nowsong = self.queue[0]
        self.nowreq = self.requestlist[0]
        self.queue = [self.nowsong]
        self.requestlist = [self.nowreq]
        self.skipsong = None 
        self.skipvoters = []
    
    def add(self, item, requ):
        self.queue.append(item)
        self.requestlist.append(requ)
        
    def addtop(self, item, requ):
        self.queue.insert(1, item)
        self.requestlist.insert(1, requ)

    def voteskip(self, user):
        self.skipvoters.append(user)

    def voteskiplen(self):
        return len(self.skipvoters)

    def skiplist(self):
        return self.skipvoters

    def skip(self, amount=1):
        for x in range(amount):
            self.queue.pop(0)
            self.requestlist.pop(0)
        self.skipsong = None 
        self.skipvoters = []

    def remove(self, position=1):
        self.queue.pop(position)
        self.requestlist.pop(position)

    def queueLen(self):
        return int(len(self.queue))
        
    def data(self):
        return self.queue
    
    def latest(self):
        return self.queue[0]
    
    def queueUser(self):
        return self.requestlist

    def latestQueueUser(self):
        return self.requestlist[0]

    def getSongData(self, position=0):
        return self.queue[position]

    def getSongReq(self, position=0):
        return self.requestlist[position]

    def shuffle(self):
        firstQueue = self.queue[0] 
        firstRequest = self.requestlist[0]

        queuetail = self.queue[1:] 
        requesttail = self.requestlist[1:]

        zipList = list(zip(queuetail, requesttail)) 
        random.shuffle(zipList)

        self.queue, self.requestlist = map(list,zip(*zipList)) 
        self.queue.insert(0, firstQueue) 
        self.requestlist.insert(0, firstRequest)

class songdata(commands.Cog): #song data retrevial part
    def __init__(self, bot):
        self.bot = bot
        
    async def songdata(self, query, guild_id, requester, type): #gets the song and returns an embed + adds it to queue
        url_rx = re.compile(r'https?://(?:www\.)?.+') #just a filtering thing

        if url_rx.match(query) and "playlist" in query: #checks for playlist
            playlist = await self.bot.wavelink.get_tracks(query) #gets the playlist

            #embed for playlist
            embed = discord.Embed(title=f":musical_note:  Playlist added", description=f"Adding {len(playlist.tracks)} songs.", color=0x6bd5ff)
            embed.add_field(name="Requested By:", value=f"{requester.mention}")
            embed.set_author(name=requester.name, icon_url=requester.avatar_url)

            for track in playlist.tracks: #adds each track to list
                queue = await self.bot.QueueSystem.get_queue(guild_id)
                if type == "top":
                    queue.addtop(track, requester)
                    asyncio.sleep(0.5)
                    return embed
                if type == "play":
                    queue.add(track, requester)
                    asyncio.sleep(0.5)
                    return embed
              

        elif url_rx.match(query): #search via link
            track = await self.bot.wavelink.get_tracks(query) #searches the query
            track = track[0]

            if track.is_stream: #checks for stream
                durationTrack = "Live :red_circle:"

            elif track.is_stream == False: #formats the time
                durationTrack = datetime.timedelta(milliseconds=track.length)

            #embed generate
            embed = discord.Embed(title=":musical_note: Added Song to Queue", url=track.uri, description=f"`{track.title}`", color=0x6bd5ff)
            embed.add_field(name="Requested By:", value=f"{requester.mention}", inline=True)
            embed.add_field(name="Duration", value=f"{durationTrack}", inline=True)

            queue = await self.bot.QueueSystem.get_queue(guild_id)
            pos = str(len(queue.data())) #gets song position in queue

            if pos == '0': #prevents added to queue embed by returning None as position, which errors out
                return None

            embed.add_field(name="Position", value=f"{pos}", inline=True)

            if type == "top":
                queue.addtop(track, requester)
                return embed
            if type == "play":
                queue.add(track, requester)
                return embed

        else: #if it is not a link or playlist, search query, essentially the same as above
            track = await self.bot.wavelink.get_tracks(f"ytsearch:{query}")
            track = track[0]

            if track.is_stream:
                durationTrack = "Live :red_circle:"

            elif track.is_stream == False:
                durationTrack = datetime.timedelta(milliseconds=track.length)

            embed = discord.Embed(title=":musical_note: Added Song to Queue", url=track.uri, description=f"`{track.title}`", color=0x6bd5ff)
            embed.add_field(name="Requested By:", value=f"{requester.mention}", inline=True)
            embed.add_field(name="Duration", value=f"{durationTrack}", inline=True)

            queue = await self.bot.QueueSystem.get_queue(guild_id)
            pos = str(len(queue.data()))

            if pos == '0':
                return None

            embed.add_field(name="Position", value=f"{pos}", inline=True)

            if type == "top":
                queue.addtop(track, requester)
                return embed
            if type == "play":
                queue.add(track, requester)
                return embed
   
class dj_perm_error(commands.CheckFailure): 
     pass
     
class premiumServer_error(commands.CheckFailure): 
     pass

class disabledCommand_error(commands.CheckFailure): 
    pass


class Music(commands.Cog):
    """Music related commands. Join a VC to use these."""
    
    def __init__(self, bot):
        self.bot = bot 
        self.configcol = self.bot.mongodatabase["configs"]
        self.premServercol = self.bot.mongodatabase["vipServers"] 


    async def cog_check(self, ctx):
            player = self.bot.wavelink.get_player(ctx.guild.id)
            channel = self.bot.get_channel(player.channel_id)

            if ctx.author.voice == None:
                await ctx.send("Join a VC, **NOW!**")
            return

            try:
                members = channel.members - 1
            except:
                return True

            AdminCmd = ['summon', 'equalizer', 'clearqueue', 'volume',
                        'playskip', 'playtop', 'skipover', 'shuffle', 'stop']

            if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
                return True
            elif members == 1:
                return True
            else:
                if ctx.invoked_with in AdminCmd:
                    raise dj_perm_error()
                else:
                    return 

    def disabledCmd_check():
        # Checks for disabled channel/command
        def predicate(ctx):
            cmds = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'cmdsoff'}]})
            cmdsList = ['0']

            for i in cmds:
                cmdOff = i['commands']
                cmdsList.extend(cmdOff)
            
            for i in cmdsList:
                if ctx.invoked_with not in cmdsList:
                    pass
              
                else:
                    raise disabledCommand_error()

            channelList = ['0']
            channels = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'channeloff'}]})

            for i in channels:
                channeloff = i['channels']
                channelList.extend(channeloff)

            if ctx.message.channel.id not in channelList:
                    pass
            else:
                    raise disabledCommand_error()

            categories = self.configcol.find({"$and": [{"guild": ctx.guild.id}, {"cfg_type": 'categoryoff'}]})
            catList = ['0']

            for i in categories:
                catoff = i['categories']
                catList.extend(catoff)

            if "music" not in catList:
                    return True
            else:
                raise disabledCommand_error()

        return commands.check(predicate)

    def premiumUser():
        # Checks for premium server
        def predicate(ctx):
            server = self.premServercol.find({'server':ctx.guild.id})
            status = 'off'

            for x in server:
                status = x["status"]

            if status == 'on':
                return True

            else:
                raise premiumServer_error()

        return commands.check(predicate)


    @tasks.loop(seconds=90) #if bot is inactive for 1.5 minutes, it leaves
    async def timeOutMusic(self):
        for i in self.bot.guilds:
            player = self.bot.wavelink.get_player(i.id)
            queue = await self.bot.QueueSystem.get_queue(i.id)
            channel = self.bot.get_channel(player.channel_id)
            try:
                if len(channel.members) == 1:
                        queue.clear()
                        await player.destroy()
                        queue.clear()
            except:
                pass
            if player.is_playing == False:
                try:
                    queue.clear()
                    await player.destroy()
                    queue.clear()
                except:
                    pass
            elif player.is_connected == False:
                try:
                    queue.clear()
                    await player.destroy()
                    queue.clear()
                except:
                    pass
            
    @timeOutMusic.before_loop #basic loop handeling
    async def before_timeOutMusic(self):
        await self.bot.wait_until_ready()


    @commands.Cog.listener() 
    async def on_ready(self): #stuff to do when bot is ready
        await self.bot.wait_until_ready() #waits until ready

        self.bot.QueueSystem = self.bot.get_cog('QueueSystem') #sets up queue

        for guild in self.bot.guilds:
            await self.bot.QueueSystem.newqueue(guild.id)

        await self.bot.wavelink.initiate_node(host='127.0.0.1', 
                                              port=2333,
                                              rest_uri='http://127.0.0.1:2333',
                                              password='youshallnotpass',
                                              identifier='TEST',
                                              region='us_central') #connects to wavelink 
        await self.timeOutMusic.start() #starts timeout loop

    @commands.Cog.listener() 
    async def on_command_error(self, ctx, error): #error checking
        if isinstance(error, premiumServer_error): #premium server error
            embed = embed=discord.Embed(title="Command is for Qu+ Server Only", 
                                        description="This command is only for Qu+ Servers. Use u.premium to get a premium server/account.\nPlease subscribe and help the developer here. By subscribing to Qu+ services, you help the developer continue making the bot and pay for server fees. (I'm a high school freshman so this really helps)", 
                                        color=0x6bd5ff)
            await ctx.send(embed=embed)

        if isinstance(error, dj_perm_error): #permission error
            await ctx.send(":x: You need either the Manage Channels permissions or a role named `DJ` to perform this action.")

        if isinstance(error, disabledCommand_error): #ignore disabled 
            return


    @commands.command(aliases=['connect'])
    @disabledCmd_check()
    async def join(self, ctx):
        """Join the users current voice channel. If the bot is in use, it will not join."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        try: 
            channel = self.bot.get_channel(player.channel_id)
            members = len(channel.members) - 1

        except AttributeError:
            members = 0

        if ctx.author.voice.channel.id != player.channel_id and members >= 1:
            await ctx.send(":x: The bot is currently being used in another channel, wait until it leaves or it is alone.\nYou can get it to join it via u.summon if you have perms.")
            return

        else:
            player = self.bot.wavelink.get_player(ctx.guild.id)
            await self.bot.QueueSystem.newchannel(ctx.guild.id, ctx.author.voice.channel)
            await ctx.send(f':signal_strength: Connecting to **{ctx.author.voice.channel}**...')
            await player.connect(ctx.author.voice.channel.id)

    @commands.command(aliases=['nowplaying'])
    @disabledCmd_check()
    async def now(self, ctx):
        """Displays the current song that is playing"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)

        if player.is_playing == False:
            await ctx.send("<:tumbleweed:794967194470973520> Nothing is playing...")

        song = queue.latest()
        requester = queue.latestQueueUser()

        embed = discord.Embed(title=':musical_note: Now Playing', description=f"```{song.title}```", color=0x6bd5ff)
        embed.add_field(name='Requested By', value=requester.mention)
        embed.add_field(name='Uploader', value=f"{song.author}")
        embed.add_field(name='URL', value=f"[Open]({song.uri})")

        if song.is_stream:
            durationTrack = "Live :red_circle:"
            embed.add_field(name='Duration', value=durationTrack)

        elif song.is_stream == False:
            durationTrack = datetime.timedelta(milliseconds=song.length)
            curPos = datetime.timedelta(milliseconds=player.position)
            curPos = str(curPos).split(".")[0]
            embed.add_field(name='Duration', value=f"{curPos} / {durationTrack}")

        embed.set_thumbnail(url=song.thumb)

        await ctx.send(embed=embed)

    @commands.command()
    @disabledCmd_check()
    async def summon(self, ctx, *, channel: discord.VoiceChannel=None):
        """Moves the bot to another VC (need Manage Channels perms)"""
        if not channel:
            try:
                channel = ctx.author.voice.channel

            except AttributeError:
                await ctx.send(':x: Invalid Voice Channel.')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await self.bot.QueueSystem.newchannel(ctx.guild.id, channel)

        await ctx.send(f':signal_strength: Connecting to **{channel.name}**...')

        await player.connect(channel.id)
        
    @commands.command(aliases=["quit", "disconnect"])
    @disabledCmd_check()
    async def leave(self, ctx):
        """Leave the bots current voice channel."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        
        if player.is_playing:
            if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
                queue.clear()
                await player.destroy()
                queue.clear()
                await ctx.send(":door: Leaving the voice channel...")
                return

            await ctx.send(":x: The bot is in use right now. Please have a DJ or someone with permissions kick the bot.")
            return
        queue.clear()
        await player.destroy()
        queue.clear()
        await ctx.send(":door: Leaving the voice channel...")

    @commands.command(aliases=['eq', 'equalizer'], name="equalizer (<:silverstar11:794770265657442347> Qu+ Server)")
    @disabledCmd_check()
    @premiumUser()
    async def equalizer(self, ctx, type:str):
        """Sets the equalizer for the player.
        flat = Resets your EQ to Flat (resets it)
        metal = Experimental Metal/Rock Equalizer. Expect clipping on Bassy songs.
        piano = Piano Equalizer. Suitable for Piano tracks, or tacks with an emphasis on Female Vocals. Could also be used as a Bass Cutoff.
        boost = This equalizer emphasizes Punchy Bass and Crisp Mid-High tones. Not suitable for tracks with Deep/Low Bass."""


        player = self.bot.wavelink.get_player(ctx.guild.id)

        if type == 'flat':
            await player.set_eq(wavelink.eqs.Equalizer.flat())

        if type == 'metal':
            await player.set_eq(wavelink.eqs.Equalizer.metal())

        if type == 'piano':
            await player.set_eq(wavelink.eqs.Equalizer.piano())

        if type == 'boost':
            await player.set_eq(wavelink.eqs.Equalizer.boost())  

        await ctx.send(f":control_knobs: Setting EQ to **{type}**...")

    @commands.command()
    @disabledCmd_check()
    async def seek(self, ctx, *, seek):
        """Seek the current song to hh:mm:ss."""

        player = self.bot.wavelink.get_player(ctx.guild.id)
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)

        if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
                pass

        elif ctx.author == queue.latestQueueUser():
            pass

        else:
            await ctx.send(":x: You need either the Manage Channels permissions or a role named `DJ` to perform this action.")
            return

        if not player.current:
            return await ctx.send(':mute: No music is playing.')

        splited = seek.split(':')

        if len(splited) == 3:
            res = int(splited[0]) * 3600 + int(splited[1]) * 60 + int(splited[2])

        elif len(splited) == 2:
            res = int(splited[0]) * 60 + int(splited[1])

        elif len(splited) == 1:
            res = int(splited[0])

        else:
            return await ctx.send(":x: Invalid format. Use `hh:mm:ss`")

        if res > player.current.duration / 1000:
            return await ctx.send(":x: Seek cannot be longer than song duration.")

        await player.seek(int(res) * 1000)
        await ctx.send("Seeked to `{}` out of `{}`".format(time.strftime('%H:%M:%S', time.gmtime(res)), time.strftime('%H:%M:%S', time.gmtime(player.current.duration / 1000))))

    @commands.command(aliases=["emptyqueue", "clearq", "emptyq"]) 
    @disabledCmd_check()
    async def clearqueue(self, ctx):
        """Clears the queue for the bot."""
        try:
            queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
            queue.clear()

            await ctx.send(":wastebasket: Emptied the queue.")

        except Exception as e:
            print(e)
            
    #@commands.command()
    #async def loop(self, ctx):
    #    """Loops the queue one time once it ends."""
    #    if ctx.author.voice == None:
    #        await ctx.send("Join a VC, **NOW!**")
    #        return
    #    queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
    #    data = queue.data()[:]
    #    try:                                                                               #this is broken rn, i will fix this after release
    #        for x in data:
    #            queue.add(x)
    #    except Exception as e:
    #        print(e)
    #        await ctx.send("Hmm, I got an error, try again.")
    #        return
    #    await ctx.send("Your queue will now loop 1 time.")
    
    @commands.command(aliases=['vol', 'volume'], name="volume (<:silverstar1:794770265657442347> Qu+ Server)")
    @disabledCmd_check()
    @premiumUser()
    async def volume(self, ctx, *, volume: int):
        """Set the volume. Volume above 100 causes earrape."""

        player = self.bot.wavelink.get_player(ctx.guild.id)

        if volume > 100:
            await ctx.send(":warning: ***WARNING: VOLUME ABOVE 100% CAUSES AUDIO QUALITY DROP!!!*** :warning:")
            await asyncio.sleep(1)
            await ctx.send(f":loud_sound: Volume set to **{volume}%**.")
            await player.set_volume(volume)
            return

        elif volume <= 100 or volume >= 0:
            if volume > 80:
                await ctx.send(f":loud_sound: Volume set to **{volume}%**.")
                await player.set_volume(volume)
                return

            else: 
                await ctx.send(f":sound: Volume set to **{volume}%**.")
                await player.set_volume(volume)
                return

        elif volume < 0:
            await ctx.send(":x: Invalid volume defined.")
            return

    @commands.command()
    @disabledCmd_check()
    async def play(self, ctx, *, query):
        """Play a song of your choice. Searching, playlists, and URLs are supported."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_connected:
            await ctx.invoke(self.bot.get_command('join'))

        try:
            await ctx.send(embed=await self.bot.get_cog('songdata').songdata(query, ctx.guild.id, ctx.author, "play"))

        except:
            pass

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        channel = await self.bot.QueueSystem.get_channel(ctx.guild.id)

        while True:
            try:
                song = queue.latest()
            except:
                song = None

            if song == None:
                return

            if player.is_playing:
                pass

            else:
                await player.play(song)
                cmd = self.bot.get_command("now")
                await cmd(ctx)

            elapsed = 0
            try:
                while queue.latest() == song:
                    await asyncio.sleep(1)
                    elapsed += 975

                    if elapsed > song.length:
                        queue.skip()
            except:
                pass

    @commands.command()
    @disabledCmd_check()
    async def playskip(self, ctx, *, query):
        """Skips and plays a song of your choice. Searching, playlists, and URLs are supported."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_connected:
            try:
                await ctx.invoke(self.bot.get_command('join'))

            except Exception as e:
                print(e)
                await ctx.send("Join a VC, **NOW!**")
                return

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        if queue.latest() == None:                                                                                                              
            await ctx.send("Please play some music first.")
            return

        await ctx.send(f":track_next: Skipping and playing requested song...")

        await self.bot.get_cog('songdata').songdata_addtop(query, ctx.guild.id, ctx.author)
        queue.skip(1)
        await player.stop()

    @commands.command()
    @disabledCmd_check()
    async def playtop(self, ctx, *, query):
        """Puts a song at the top of the queue. Searching, playlists, and URLs are supported."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_connected:
            try:
                await ctx.invoke(self.bot.get_command('join'))

            except Exception as e:
                print(e)
                await ctx.send("Join a VC, **NOW!**")
                return

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)

        if queue.latest() == None:                                                                                                              
            await ctx.send("Please play some music first.")
            return

        await ctx.send(embed=await self.bot.get_cog('songdata').songdata(query, ctx.guild.id, ctx.author, "top"))

    @commands.command()
    @disabledCmd_check()
    async def skip(self, ctx):
        """Skip the currently playing song."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)
        channel = self.bot.get_channel(player.channel_id)

        members = channel.members

        if ctx.author == queue.latestQueueUser():
            queue.skip(1)
            await ctx.send(f":track_next: Skipping song...")
            await player.stop()

        elif ctx.author != queue.latestQueueUser():
            if (len(channel.members) - 1) // 1.5 == 1:
                queue.skip(1)
                await ctx.send(f":track_next: Skipping song...")
                await player.stop()

            if ctx.author in queue.skiplist():
                await ctx.send("You already voted to skip this song.")
                return

            await ctx.send(f"You have voted, **{queue.voteskiplen() + 1}/{int((len(channel.members) - 1) // 1.5)}** remaining")
            queue.voteskip(ctx.author)

            if queue.voteskiplen() >= (len(channel.members) - 1) // 1.5:
                queue.skip(1)
                await ctx.send(f":track_next: Skipping song...")
                await player.stop() #check this later with multiple people

    @commands.command()
    @disabledCmd_check()
    async def skipover(self, ctx, amt=1):
        """Skip but overrides voting, use u.skipover amt to skip a number of songs."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)

        song = queue.data()[1]
        queue.skip(amt)

        await ctx.send(f":track_next: Skipping **{amt}** song(s)...")

        await player.stop()

    @commands.command()
    @disabledCmd_check()
    async def shuffle(self, ctx):
        """Mixes up the songs in the queue"""

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)

        queue.shuffle()

        await ctx.send(":twisted_rightwards_arrows: Shuffling queue...")

    @commands.command()
    @disabledCmd_check()
    async def remove(self, ctx, pos: int):
        """Removes a song from the specified position."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        positionReq = queue.getSongReq(pos)

        if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
            pass

        elif positionReq == ctx.author:
            pass

        else:
            await ctx.send(":x: You need either the Manage Channels permissions or a role named `DJ` to perform this action.")
            return

        try: 
           song = queue.getSongData(pos)
           queue.remove(pos)

           await ctx.send(f":wastebasket: Removed: `{song.title}` from the queue.")

        except IndexError:
            await ctx.send(":x: Please specify a vaild position in the queue.")
            return      
        
    @commands.command()
    @disabledCmd_check()
    async def pause(self, ctx):
        """Pause or resume the music player."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)

        if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
                pass

        elif ctx.author == queue.latestQueueUser():
            pass

        else:
            await ctx.send(":x: You need either the Manage Channels permissions or a role named `DJ` to perform this action.")
            return

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if player.is_paused:
            await player.set_pause(False)
            await ctx.send(f":arrow_forward: Resuming current song.")

        else:
            await player.set_pause(True)
            await ctx.send(f":pause_button: Pausing current song.")
            
    @commands.command()
    @disabledCmd_check()
    async def queue(self, ctx, page=1):
        """Gets the queue of the songs."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        embed = discord.Embed(title=f":musical_note: {ctx.guild.name}'s queue", description="** **", color=0x6bd5ff)

        if len(queue.data()) == 0:
            return await ctx.send('<:tumbleweed:794967194470973520> Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(queue.data()) / items_per_page)

        if page > pages:
            await ctx.send(f"There are only {pages}. Please select a value within those pages. ")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page

        embed = discord.Embed(title=f"{ctx.guild.name}'s queue", description="** **", color=0x6bd5ff)


        for songList in enumerate(queue.data()[start:end], start=start):
            song = songList[1]
            reqU = queue.getSongReq(songList[0])
            positionNum = songList[0]

            if song.is_stream:
                durationTrack = "Live :red_circle:"

            elif song.is_stream == False:
                durationTrack = datetime.timedelta(milliseconds=int(song.length))

            if positionNum == 0:
                position = "Now Playing"

            if positionNum > 0:
                position = songList[0]

            embed.add_field(name=f"*{str(position)}* | {song.title}", value=f"Length: {durationTrack}\nRequested By: {reqU.mention}", inline=False)

        embed.set_footer(text=f"Page {page}/{pages}")
        await ctx.send(embed=embed)

    @commands.command()
    @disabledCmd_check()
    async def stop(self, ctx):
        """Stops and clears the queue."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)

        queue.clear()
        await player.stop()

        await ctx.send(":octagonal_sign: Stopped the music.")

def setup(bot):
    bot.add_cog(Music(bot))
    bot.add_cog(QueueSystem(bot))
    bot.add_cog(songdata(bot))