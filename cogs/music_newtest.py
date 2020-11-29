import discord
from discord.ext import commands
import wavelink
import asyncio
import asyncio
import sys
import re
import datetime

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
        
    def clear(self):
        self.queue = []
        self.requestlist = []
    
    def add(self, item, requ):
        self.queue.append(item)
        self.requestlist.append(requ)
        
    def skip(self, amount=1):
        for x in range(amount):
            self.queue.pop(0)
            self.requestlist.pop(0)
    def remove(self, position=1):
        self.queue.pop(position)
        self.requestlist.pop(position)
        
    def data(self):
        return self.queue
    
    def latest(self):
        return self.queue[0]

    def queueLen(self):
        return int(len(self.queue))
    
    def queueUser(self):
        return self.requestlist

    def latestQueueUser(self):
        return self.requestlist[0]

class songdata(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def songdata(self, query, guild_id, requester):
        url_rx = re.compile(r'https?://(?:www\.)?.+')
        if url_rx.match(query) and "playlist" in query:
            playlist = await self.bot.wavelink.get_tracks(query)
            embed = discord.Embed(title=f":musical_note:  Playlist added", description=f"Adding {len(playlist.tracks)} songs.", color=0x6bd5ff)
            embed.add_field(name="Requested By:", value=f"{requester.mention}")
            embed.set_author(name=requester.name, icon_url=requester.avatar_url)

            for track in playlist.tracks:
                queue = await self.bot.QueueSystem.get_queue(guild_id)
                queue.add(track, requester)

            return embed

        elif url_rx.match(query):
            track = await self.bot.wavelink.get_tracks(query)
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
            queue.add(track, requester)
            if pos == '0':
                return None
            embed.add_field(name="Position", value=f"{pos}", inline=True)
            return embed

        else:
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
            queue.add(track, requester)
            if pos == '0':
                return None
            embed.add_field(name="Position", value=f"{pos}", inline=True)
            return embed

class Music(commands.Cog):
    """Music related commands."""
    
    def __init__(self, bot):
        self.bot = bot
    

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.bot.QueueSystem = self.bot.get_cog('QueueSystem')
        for guild in self.bot.guilds:
            await self.bot.QueueSystem.newqueue(guild.id)
        await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                              port=2333,
                                              rest_uri='http://127.0.0.1:2333',
                                              password='youshallnotpass',
                                              identifier='TEST',
                                              region='us_central')
    
    @commands.command()
    async def join(self, ctx):
        """Join the users current voice channel."""
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Join a VC, **NOW!**")
        player = self.bot.wavelink.get_player(ctx.guild.id)
        _ = await self.bot.QueueSystem.newchannel(ctx.guild.id, channel)
        await ctx.send(f':signal_strength: Connecting to **{channel.name}**')
        await player.connect(channel.id)

    @commands.command(aliases=['nowplaying'])
    async def now(self, ctx):
        """Displays the current song that is playing"""
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Join a VC, **NOW!**")

        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        song = queue.latest()
        requester = queue.latestQueueUser()
        embed = discord.Embed(title=':musical_note: Now Playing', description=f"```{song.title}```", color=0x6bd5ff)
        if song.is_stream:
            durationTrack = "Live :red_circle:"
        elif song.is_stream == False:
            durationTrack = datetime.timedelta(milliseconds=song.length)
        embed.add_field(name='Duration', value=durationTrack)
        embed.add_field(name='Requested By', value=requester.mention)
        embed.add_field(name='Uploader', value=f"{song.author}")
        embed.add_field(name='URL', value=f"[Click]({song.uri})")
        embed.set_thumbnail(url=song.thumb)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def summon(self, ctx, *, channel: discord.VoiceChannel=None):
        """Moves the bot to another VC"""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send('Invalid Voice Channel.')
        player = self.bot.wavelink.get_player(ctx.guild.id)
        _ = await self.bot.QueueSystem.newchannel(ctx.guild.id, channel)
        await ctx.send(f':signal_strength: Connecting to **{channel.name}**')
        await player.connect(channel.id)
        
    @commands.command(aliases=["quit"])
    async def leave(self, ctx):
        """Leave the bots current voice channel."""
        try:
            queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
            queue.clear()
            player = self.bot.wavelink.get_player(ctx.guild.id)
            await player.destroy()
            queue.clear()
            await ctx.send(":door: Leaving the voice channel...")
        except Exception as e:
            print(e)

    @commands.command(aliases=["emptyqueue"])
    @commands.has_permissions(manage_channels=True)
    async def clear(self, ctx):
        """Clears the queue for the bot."""
        try:
            queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
            queue.clear()
            await ctx.send(":wastebasket: Emptied the queue.")
        except Exception as e:
            print(e)
            
    @commands.command()
    async def loop(self, ctx):
        """Loops the queue one time once it ends."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        data = queue.data()[:]
        try:
            for x in data:
                queue.add(x)
        except Exception as e:
            print(e)
            await ctx.send("Hmm, I got an error, try again.")
            return
        await ctx.send("Your queue will now loop.")
    
    @commands.command(aliases=['vol'])
    async def volume(self, ctx, *, volume: int):
        """Set the volume. Volume above 100 causes earrape."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if volume > 100:
            await ctx.send(":warning: ***WARNING: VOLUME ABOVE 100 CAUSES AUDIO QUALITY DROP!!!*** :warning:")
            await asyncio.sleep(1)
            await ctx.send(f":sound: Volume set to **{volume}%**.")
            await player.set_volume(volume)
            return
        elif volume <= 100 or volume >= 0:
            await ctx.send(f":sound: Volume set to **{volume}%**.")
            await player.set_volume(volume)
        elif volume < 0:
            await ctx.send("Invalid volume defined.")

        
    @commands.command()
    async def play(self, ctx, *, query):
        """Play a song of your choice. Searching, playlists, and URLs are supported."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            try:
                await ctx.invoke(self.bot.get_command('join'))
            except Exception as e:
                print(e)
                await ctx.send("Join a VC, **NOW!**")
                return
        if ctx.author.voice == None:
            await ctx.send("Join a VC, **NOW!**")
            return
        try:
            await ctx.send(embed=await self.bot.get_cog('songdata').songdata(query, ctx.guild.id, ctx.author))
        except:
            pass
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        channel = await self.bot.QueueSystem.get_channel(ctx.guild.id)
        while True:
            song = queue.latest()
            if song == None:
                return
            if player.is_playing:
                pass
            else:
                await player.play(song)
                cmd = self.bot.get_command("now")
                await cmd(ctx)
            elapsed = 0
            while queue.latest() == song:
                await asyncio.sleep(1)
                elapsed += 975
                if elapsed > song.length:
                    queue.skip()
    
    @commands.command()
    async def skip(self, ctx):
        """Skip the currently playing song."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        song = queue.data()[1]
        player = self.bot.wavelink.get_player(ctx.guild.id)
        queue.skip()
        await ctx.send(":track_next: Skipping song...")
        await player.stop()

    @commands.command()
    async def remove(self, ctx, pos: int):
        """Removes a song from the specified position."""

        
        
    @commands.command(aliases=["resume", "unpause"])
    async def pause(self, ctx):
        """Pause or resume the music player."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        song = queue.latest()
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_paused:
            await player.set_pause(False)
            await ctx.send(f":arrow_forward: Resuming current song.")
        else:
            await player.set_pause(True)
            await ctx.send(f":pause_button: Pausing current song.")
            
    @commands.command()
    async def queue(self, ctx):
        """Gets the queue of the songs."""
        queue = await self.bot.QueueSystem.get_queue(ctx.guild.id)
        embed = discord.Embed(title=f":musical_note: {ctx.guild.name}'s queue", description="** **", color=0x6bd5ff)
        y = 0
        for x, user in zip(queue.data(), queue.queueUser()):
            y += 1
            print(x.title.encode(sys.stdout.encoding, errors='replace'))
            print(x)
            if x.is_stream:
                durationTrack = "Live :red_circle:"
            elif x.is_stream == False:
                durationTrack = datetime.timedelta(milliseconds=int(x.length))
            if y == 1:
                position = "Now Playing"
            elif y > 1:
                position = y - 1
            embed.add_field(name=f"*{str(position)}* | {x.title}", value=f"Length: {durationTrack}\nRequested By: {user.mention}", inline=False)
            if y == 10:
                y = 0
                await ctx.send(embed=embed)
                embed = discord.Embed(title=f"{ctx.guild.name}'s queue", description="** **", color=0x6bd5ff)
                embed.set_footer(text="Page 1")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
    bot.add_cog(QueueSystem(bot))
    bot.add_cog(songdata(bot))