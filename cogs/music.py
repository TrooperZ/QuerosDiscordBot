# This is the old music infrastructure I used. This will be there just in case the new one is broken.


import sys
import os
import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
import asyncio
import itertools
from async_timeout import timeout
import youtube_dl
import time
import functools
import datetime
import math

class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)
        print(data)
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries']
            lisst = list(data)
            print(lisst)
            data = lisst[0]

        if data is None:
            raise YTDLError(f'Could not find anything that matches `{search}`')

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(f'Could not find anything that matches `{search}`')
        try:
            webpage_url = process_info['webpage_url']
        except KeyError:
            webpage_url = process_info['url']
            print(webpage_url)
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Could not fetch `{webpage_url}`")

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(f"Could not fetch `{webpage_url}`")

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        if duration > 0:
            value = str(datetime.timedelta(seconds=duration))

        elif duration == 0:
            value = "LIVE"

        return value


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title=':musical_note: Now playing', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()
        self.stop_votes = set()
        self.resume_votes = set()
        self.pause_votes = set()
        self.leave_votes = set()
        self.shuffle_votes = set()
        self.loop_votes = set()
        self.remove_votes = set()
        self.join_requester = ''
        self.summon_requester = ''

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return

                self.current.source.volume = self._volume
                if self.voice is None:
                    return
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())

            # If the song is looped
            elif self.loop:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.stop_votes.clear()
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    """Music related commands. A DJ role is required for admin commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('Music is disabled in DMs.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f'Error: {error}')

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel of your choice."""
        self.join_requester = ctx.message.author
        if ctx.voice_state.is_playing:
            await ctx.send("Bot is being used, please have a DJ move it.")
            return
        if ctx.author.voice is None:
            return
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return
        ctx.voice_state.voice = await destination.connect()

        await ctx.send(f"Joining **{ctx.author.voice.channel}**")

    @commands.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons and moves the bot to a voice channel. If no channel was specified, it joins your channel. DJ Command"""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return

        self.join_requester = ctx.message.author
        if not channel and not ctx.author.voice:
            await ctx.send('Join a VC.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        try:
            ctx.voice_state.voice = await destination.connect()
        except BaseException:
            await ctx.send("Can't connect. Try checking that you're selecting the correct VC.")

    @commands.command(name='leave', aliases=['disconnect', 'quit'])
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""
        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        if ctx.voice_state.is_playing:
            if "dj" in [y.name.lower() for y in ctx.author.roles] or ctx.author.guild_permissions.manage_channels:
                await ctx.voice_state.stop()
                del self.voice_states[ctx.guild.id]
                return

            await ctx.send("Bot is being used. Please have someone with permissions force kick the bot.")
            return

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]
        await ctx.send(":door: Left the voice channel.")

    @commands.command(name='volume', aliases=['vol'])
    @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player. DJ Command."""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing anything.')

        ctx.voice_state.current.source.volume = volume / 100
        await ctx.send(f'Volume set to {volume}%')

    @commands.command(name='now', aliases=['current', 'playing'])
    @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        embed = ctx.voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @commands.command(name='pause', aliases=['pa'])
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        ctx.voice_state.voice.pause()
        await ctx.send(":pause_button:  Pausing your song.")

    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""
        await ctx.send(":arrow_forward:  Resuming.")
        ctx.voice_state.voice.resume()

    @commands.command(name='skip', aliases=['next'])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip."""
        channel = ctx.author.voice.channel
        members = channel.members
        memids = []
        for member in members:
            memids.append(member.id)
        memidLen = len(memids)
        memLenF = (memidLen - 1) // 2

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing right now.')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.send(":fast_forward: Skipping...")
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= memLenF:
                await ctx.send(":fast_forward: Skipping...")
                ctx.voice_state.skip()
            else:
                await ctx.send("Skip vote added, currently at **{total_votes} / {memLenF}**")

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue. Choose the pages by adding a number. Each page shows 10 items."""
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue. DJ Command."""
        ctx.voice_state.songs.shuffle()
        await ctx.send("Shuffling songs...")

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index. DJ Command."""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return

        ctx.voice_state.songs.remove(index - 1)
        await ctx.send("Removing song from list.")

    @commands.command(name='loop')
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def _loop(self, ctx: commands.Context):
        """Toggles looping of the current song. DJ Command."""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return

        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.send("Looping toggled.")

    @commands.command(name='skipover')
    async def _skipover(self, ctx: commands.Context):
        """Skip command that overrides standard command. DJ Command."""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return
        await ctx.send(":fast_forward: Skipping with elevated permissions.")
        ctx.voice_state.skip()

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        """Stops all music and clears queue. DJ Command."""
        if "dj" not in [y.name.lower() for y in ctx.author.roles]:
            await ctx.send(":no_entry: Missing permissions.")
            return

        await ctx.send("Stopping with elevated permissions.")
        ctx.voice_state.songs.clear()
        ctx.voice_state.voice.stop()

    @commands.command(name='play')
    @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song by searching.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
            await asyncio.sleep(3)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send(f'Error: {e}')
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send(f'Song added to queue: {source}')

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('Join a voice channel.')
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send('Bot is already in use.')
                return


def setup(bot):
    bot.add_cog(Music(bot))
