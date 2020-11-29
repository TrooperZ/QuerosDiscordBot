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
import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGO_PASS = os.getenv('MONGO_PASS')
myclient = pymongo.MongoClient("mongodb+srv://queroscode:" + MONGO_PASS + "@querosdatabase.rm7rk.mongodb.net/data?retryWrites=true&w=majority")
mydb = myclient["data"]
configcol = mydb["configs"]


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



     def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float=0.5):
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
     async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop=None):
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
                raise YTDLError('I searched everything on Youtube, including my sock drawer, and I could not find anything that matches `{}`'.format(search))

          if 'entries' not in data:
                process_info = data
          else:
                process_info = None
                for entry in data['entries']:
                     if entry:
                          process_info = entry
                          break

                if process_info is None:
                     raise YTDLError('I searched everything on Youtube, including my sock drawer, and I could not find anything that matches `{}`'.format(search))
          try:
            webpage_url = process_info['webpage_url']
          except KeyError:
            webpage_url = process_info['url']
            print(webpage_url)
          partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
          processed_info = await loop.run_in_executor(None, partial)

          if processed_info is None:
                raise YTDLError('I can\'t fetch `{}`'.format(webpage_url) + "  because I suck at caching *ba dum tiss*")

          if 'entries' not in processed_info:
                info = processed_info
          else:
                info = None
                while info is None:
                     try:
                          info = processed_info['entries'].pop(0)
                     except IndexError:
                          raise YTDLError('I couldn\'t grab the data `{}`'.format(webpage_url) + " because someone farted in the database")
          
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
          embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.blurple())
                     .add_field(name='Duration', value=self.source.duration)
                     .add_field(name='Requested by', value=self.requester.mention)
                     .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                     .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                     .set_thumbnail(url=self.source.thumbnail)
                     .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
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

                if self.loop == False:
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
                     self.voice.play(self.current.source, after=self.play_next_song)
                     await self.current.source.channel.send(embed=self.current.create_embed())
                
                #If the song is looped
                elif self.loop == True:
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
                raise commands.NoPrivateMessage('Bruh you can\'t use me to play music in DM.')

          return True

     async def cog_before_invoke(self, ctx: commands.Context):
          ctx.voice_state = self.get_voice_state(ctx)

     async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
          await ctx.send('Oopsy whoopsy, I slipped and fell: {}'.format(str(error)))

     @commands.command(name='join', invoke_without_subcommand=True)
     async def _join(self, ctx: commands.Context):
          """Joins a voice channel of your choice."""
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
          self.join_requester = ctx.message.author
          destination = ctx.author.voice.channel
          if ctx.voice_state.voice:
                await ctx.voice_state.voice.move_to(destination)
                return
          ctx.voice_state.voice = await destination.connect()
          ctx.voice_state.voice.play(discord.FFmpegPCMAudio('joinmsg.mp3'))

     @commands.command(name='summon')
     @commands.has_permissions(manage_guild=True)
     async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel=None):
          """Summons and moves the bot to a voice channel. If no channel was specified, it joins your channel."""
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
          self.join_requester = ctx.message.author
          if not channel and not ctx.author.voice:
                await ctx.send('You see, I cannot join you, not because I hate you (I kinda do), but you\'re not in one.')

          destination = channel or ctx.author.voice.channel
          if ctx.voice_state.voice:
                await ctx.voice_state.voice.move_to(destination)
                return

          ctx.voice_state.voice = await destination.connect()
          ctx.voice_state.voice.play(discord.FFmpegPCMAudio('joinmsg.mp3'))

     @commands.command(name='leave', aliases=['disconnect', 'quit'])
     async def _leave(self, ctx: commands.Context):
          """Clears the queue and leaves the voice channel. Requires vote"""
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
          channel = ctx.author.voice.channel
          members = channel.members
          memids = []
          for member in members:
                memids.append(member.id)
          memidLen = len(memids) 
          memLenF = (memidLen - 1) // 2
          if not ctx.voice_state.voice:
                return await ctx.send('Join a VC or I will spank you.')
          voter = ctx.message.author
          if voter == self.join_requester:
                     await ctx.voice_state.stop()
                     del self.voice_states[ctx.guild.id]


          elif voter.id not in ctx.voice_state.leave_votes:
                ctx.voice_state.leave_votes.add(voter.id)
                total_votes = len(ctx.voice_state.leave_votes)

                if total_votes >= memLenF:
                     await ctx.voice_state.stop()
                     del self.voice_states[ctx.guild.id]

                else:
                     await ctx.send('Leave vote added, currently at **' + str(total_votes) + "/" + str(memLenF) + "**")
          else:
                await ctx.send('You have already voted to kick me out, dumdum.')

     @commands.command(name='volume', aliases=['vol'])
     @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
     @commands.has_permissions(manage_guild=True)
     async def _volume(self, ctx: commands.Context, *, volume: int):
          """Sets the volume of the player. Need Manage Server perms."""
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

          if not ctx.voice_state.is_playing:
                return await ctx.send('Can\'t you hear? I\'m not playing anything.')

          ctx.voice_state.current.source.volume = volume / 100
          await ctx.send('Volume set to {}%'.format(volume) + ", because you asked for it")

     @commands.command(name='now', aliases=['current', 'playing'])
     @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
     async def _now(self, ctx: commands.Context):
          """Displays the currently playing song."""
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
          embed = ctx.voice_state.current.create_embed()
          await ctx.send(embed=embed)

     @commands.command(name='pause', aliases=['pa'])
     async def _pause(self, ctx: commands.Context):
          """Pauses the currently playing song."""
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
          ctx.voice_state.voice.pause()
          await ctx.send("Pausing your song... now.")

     @commands.command(name='resume', aliases=['re', 'res'])
     async def _resume(self, ctx: commands.Context):
          """Resumes a currently paused song."""
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
          await ctx.send("Oh thank god, I can finally stop the music.")
          ctx.voice_state.voice.resume()

     @commands.command(name='stop')
     async def _stop(self, ctx: commands.Context):
          """Stops playing song and clears the queue. Requires vote"""
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
          channel = ctx.author.voice.channel
          members = channel.members
          memids = []
          for member in members:
                memids.append(member.id)
          memidLen = len(memids) 
          memLenF = (memidLen - 1) // 2

          voter = ctx.message.author
          if voter == ctx.voice_state.current.requester:
                await ctx.send("Oh thank god, I can finally stop the music.")
                ctx.voice_state.songs.clear()
                ctx.voice_state.voice.stop()

          elif voter.id not in ctx.voice_state.stop_votes:
                ctx.voice_state.stop_votes.add(voter.id)
                total_votes = len(ctx.voice_state.stop_votes)

                if total_votes >= 3:
                     await ctx.send("Oh thank god, I can finally stop the music.")
                     ctx.voice_state.songs.clear()
                     ctx.voice_state.voice.stop()
                else:
                     await ctx.send('Stop vote added, currently at **' + str(total_votes) + "/" + str(memLenF) + "**")
          else:
                await ctx.send('You have already voted to stop the music, dumdum.')
                

     @commands.command(name='skip', aliases=['next'])
     async def _skip(self, ctx: commands.Context):
          """Vote to skip a song. The requester can automatically skip."""
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
          channel = ctx.author.voice.channel
          members = channel.members
          memids = []
          for member in members:
                memids.append(member.id)
          memidLen = len(memids) 
          memLenF = (memidLen - 1) // 2

          if not ctx.voice_state.is_playing:
                return await ctx.send('Not playing any music right now, can\'t you hear?')

          voter = ctx.message.author
          if voter == ctx.voice_state.current.requester:
                await ctx.send("Skipping the ear deafining thing you call music")
                ctx.voice_state.skip()

          elif voter.id not in ctx.voice_state.skip_votes:
                ctx.voice_state.skip_votes.add(voter.id)
                total_votes = len(ctx.voice_state.skip_votes)

                if total_votes >= memLenF:
                     await ctx.send("Skipping the ear deafining thing you call music")
                     ctx.voice_state.skip()
                else:
                     await ctx.send('Skip vote added, currently at **' + str(total_votes) + "/" + str(memLenF) + "**")

          else:
                await ctx.send('You have already voted to skip this song, dumdum.')

     @commands.command(name='queue')
     async def _queue(self, ctx: commands.Context, *, page: int=1):
          """Shows the player's queue. Choose the pages by adding a number. Each page shows 10 items."""
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
     @commands.has_permissions(manage_guild=True)
     async def _shuffle(self, ctx: commands.Context):
          """Shuffles the queue. Requires Manage Server perms."""
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
          ctx.voice_state.songs.shuffle()
          await ctx.send("Shuffling songs...")

     @commands.command(name='remove')
     async def _remove(self, ctx: commands.Context, index: int):
          """Removes a song from the queue at a given index."""
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
          ctx.voice_state.songs.remove(index - 1)
          await ctx.send("Removing the horrible thing you call music from the list.")

     @commands.command(name='loop')
     @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
     @commands.has_permissions(manage_guild=True)
     async def _loop(self, ctx: commands.Context):
          """Toggles looping of the current song. Requires Manage Server perms."""
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
          ctx.voice_state.loop = not ctx.voice_state.loop
          await ctx.send("Looping toggled, your music still sucks tho")

     @commands.command(name='skipOVRR')
     @commands.has_permissions(manage_guild=True)
     async def _skipOVRR(self, ctx: commands.Context):
          """Skip command that overrides standard command. Need Manage Server perms."""
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
          await ctx.send("Skipping with elevated permissions, because the rest of y'all are stupid.")
          ctx.voice_state.skip()     

     @commands.command(name='stopOVRR')
     @commands.has_permissions(manage_guild=True)
     async def _stopOVRR(self, ctx: commands.Context):
          """Stop command that overrides standard command. Need Manage Server perms."""
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
          await ctx.send("Stopping with elevated permissions, because the rest of y'all are stupid.")
          ctx.voice_state.songs.clear()
          ctx.voice_state.voice.stop()

     @commands.command(name='leaveOVRR')
     @commands.has_permissions(manage_guild=True)
     async def _leaveOVRR(self, ctx: commands.Context):
          """Leave command that overrides standard command. Need Manage Server perms."""
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
          await ctx.voice_state.stop()
          await ctx.send("Leaving with elevated permissions, because the rest of y'all are stupid.")
          del self.voice_states[ctx.guild.id]

     @commands.command(name='play')
     @commands.cooldown(rate=1, per=2.5, type=commands.BucketType.user)
     async def _play(self, ctx: commands.Context, *, search: str):
          """Plays a song by searching.
          If there are songs in the queue, this will be queued until the
          other songs finished playing.
          This command automatically searches from various sites if no URL is provided.
          A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
          """
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

          if not ctx.voice_state.voice:
                await ctx.invoke(self._join)
                asyncio.sleep(3)

          async with ctx.typing():
                try:
                     source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                except YTDLError as e:
                     await ctx.send('Oopsy whoopsy, I tripped and fell: {}'.format(str(e)))
                else:
                     song = Song(source)

                     await ctx.voice_state.songs.put(song)
                     await ctx.send('Enqueued {}'.format(str(source)))

                
     @_join.before_invoke
     @_play.before_invoke
     async def ensure_voice_state(self, ctx: commands.Context):
          if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send('Join a voice channel, **NOW!**')

          if ctx.voice_client:
                if ctx.voice_client.channel != ctx.author.voice.channel:
                     await ctx.send('Bot is already in a voice channel, look.')


#setups command.  command is needed, make sure to use cogs.[name of file]
def setup(bot):
    bot.add_cog(Music(bot))
