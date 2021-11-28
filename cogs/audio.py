from discord.ext import commands
import discord
from cogs.utils import time_formatting as time_fmt, ez_utils, perms, IO
from discord_components import (
    Button,
    ButtonStyle,
    ActionRow,
    # Select,
    # SelectOption
    # Interaction
)
import asyncio
from cogs.utils.logger import Logger
from yt_dlp import YoutubeDL, utils as yt_utils
# from youtube_dl import YoutubeDL, utils as yt_utils
from functools import partial
from async_timeout import timeout
import itertools
import random
import re
from typing import List, Union, Optional
# import urllib.request
import requests
# import http.cookiejar as cookiejar

# https://discordpy.readthedocs.io/en/latest/api.html?highlight=is_playing#voiceclient
# https://stackoverflow.com/questions/65231130/pausing-queuing-and-looping-songs-with-discord-py

# https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
# https://stackoverflow.com/questions/63036753/discord-py-bot-how-to-play-audio-from-local-files
# https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
# https://stackoverflow.com/questions/56031159/discord-py-rewrite-what-is-the-source-for-youtubedl-to-play-music


class Player:
    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = SongQueue()  # asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        # self.volume = .5
        self.volume = 1
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            np_embed = discord.Embed(title=source.title, url=source.web_url, colour=discord.Colour.green())
            np_embed.add_field(name="Requested By", value=source.requester.mention)
            np_embed.add_field(name="Duration", value=time_fmt.seconds_to_time(source.duration))
            np_embed.set_image(url=source.thumbnail)
            np_embed.set_footer(text="This feature is a WIP, there may be issues.")

            self.np = await self._channel.send(embed=np_embed)
            await self.next.wait()

            source.cleanup()
            self.current = None

            try:
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


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

    def index(self, item):
        return self._queue.index(item)

    def find_from_index(self, index: int):
        return self._queue[index]


# todo add
class Song:
    def __init__(self, url: str, requester: discord.Member, title: str, duration: str, thumbnail: str):
        self.url = url
        self.requester = requester
        self.title = title
        self.duration = duration
        self.thumbnail = thumbnail


yt_utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = YoutubeDL(ytdl_format_options)


class LinkCheck:
    is_yt_link = 0  # string is a youtube link
    is_not_yt_link = 1  # string is a link, but not a youtube link
    is_not_link = 2  # string is not a link

    debug = ["is_yt_link", "is_not_yt_link", "is_not_link"]


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source_original(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        await ctx.message.delete()
        await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source, **ffmpeg_options), data=data, requester=ctx.author)

    @staticmethod
    def __check_for_link(search: str) -> int:
        # https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if re.match(regex, search):  # is a link
            if "youtube.com" in search or "youtu.be" in search:  # is a yt link
                return LinkCheck.is_yt_link
            else:
                return LinkCheck.is_not_yt_link  # is not a youtube link
        return LinkCheck.is_not_link  # is not a link at all

    # TODO quicker playlist fetching
    @classmethod
    async def __playlist_fetch(cls, ctx, url: str, api_key: str):
        print(url)

        regex = re.compile(r"[&?]list=([^&]+)", re.IGNORECASE)
        playlist_id = re.findall(regex, url)[0]

        print(playlist_id)

        api_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=25&" \
                  f"playlistId={playlist_id}&key={api_key}"

        res = requests.get(url=api_url, timeout=5)

        print(res.status_code)
        # print(res.text)

        links = []

        if res and res.status_code == 200:
            data = res.json()['items']

            for item in data:
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                links.append(video_url)

        else:
            return None

        return links

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, api_key: Optional[str] = None) -> Union[List[Song], None]:
        search_type = cls.__check_for_link(search)
        # print("search type: " + LinkCheck.debug[search_type])

        links = None
        player = ctx.command.cog.players[ctx.guild.id]

        if search_type == LinkCheck.is_not_yt_link:
            await ctx.send(f"`{search}` is not a valid youtube link.", delete_after=15)
            return None

        elif search_type == LinkCheck.is_yt_link:
            if "playlist" in search:

                if api_key:
                    print("yes key")
                    links = await cls.__playlist_fetch(ctx, search, api_key)
                else:
                    # log then move on
                    print("no key")

                msg = await ctx.send("Fetching songs, may take a moment...")
            else:
                msg = await ctx.send("Fetching song...")

        elif search_type == LinkCheck.is_not_link:
            msg = await ctx.send(f"Fetching first result for '{search}'...")

        else:  # makes the IDE stop telling me 'msg' might not exist
            await ctx.send("This shouldn't occur, but if it has check the logs to see why.")
            Logger.write(f"Error: search_type is {search_type}, search is {search}", print_log=True)
            return

        loop = loop or asyncio.get_event_loop()

        if links is None:
            to_run = partial(ytdl.extract_info, url=search, download=False)

            data = await loop.run_in_executor(None, to_run)

            if 'entries' in data:
                playlist_length = len(data['entries'])
                final_data = []
                for entry in data['entries']:
                    await player.queue.put(Song(
                        url=entry['webpage_url'],
                        requester=ctx.author,
                        title=entry['title'],
                        duration=entry['duration'],
                        thumbnail=entry['thumbnail']
                    ))
                    continue
                    final_data.append(Song(
                        url=entry['webpage_url'],
                        requester=ctx.author,
                        title=entry['title'],
                        duration=entry['duration'],
                        thumbnail=entry['thumbnail']
                    ))
                if playlist_length > 1:
                    await ctx.send(f'```ini\n[Added {playlist_length} videos from playlist to the Queue.]\n```',
                                   delete_after=15)
                else:
                    await ctx.send(f'```ini\n[Added {data["entries"][0]["title"]} to the Queue.]\n```', delete_after=15)
            else:
                final_data = Song(
                    url=data['webpage_url'],
                    requester=ctx.author,
                    title=data['title'],
                    duration=data['duration'],
                    thumbnail=data['thumbnail']
                )
                await player.queue.put(Song(
                    url=data['webpage_url'],
                    requester=ctx.author,
                    title=data['title'],
                    duration=data['duration'],
                    thumbnail=data['thumbnail']
                ))

                await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

        else:
            final_data = []

            for link in links:
                to_run = partial(ytdl.extract_info, url=link, download=False)
                data = await loop.run_in_executor(None, to_run)

                final_data.append(
                    Song(
                        url=data['webpage_url'],
                        requester=ctx.author,
                        title=data['title'],
                        duration=data['duration'],
                        thumbnail=data['thumbnail']
                    )
                )
                final_data = []

                await player.queue.put(Song(
                        url=data['webpage_url'],
                        requester=ctx.author,
                        title=data['title'],
                        duration=data['duration'],
                        thumbnail=data['thumbnail']
                    ))

        await msg.delete()

        # print("final data")
        # print(final_data)
        return None
        # return final_data

    @classmethod
    async def regather_stream(cls, data: Song, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data.requester

        to_run = partial(ytdl.extract_info, url=data.url, download=False)
        s_data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(s_data['url'], **ffmpeg_options), data=s_data, requester=requester)


class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        self.delete_after_time = 15
        self.longer_delete_after_time = 60
        self.msg_not_playing = "The bot isn't currently playing anything."
        self.msg_same_channel = "The bot must be in a channel and you must be in the same channel to use this command."

        self.yt_api_key = IO.fetch_from_settings("keys", "youtube_api")

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx, create=True):
        """Retrieve the guild player, or generate one and return it. (unless create = false, then return none)"""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            if create:
                player = Player(ctx)
                self.players[ctx.guild.id] = player
            else:
                return None

        return player

    @staticmethod
    def is_bot_connected(guild):
        """is the bot connected to voice"""
        vc = guild.voice_client
        return vc and vc.is_connected()

    @staticmethod
    def is_member_connected(member: discord.Member):
        """is the user connected to voice"""
        if member.voice:
            return True
        return False

    @staticmethod
    def is_member_in_same_channel_as_bot(member: discord.Member):
        """is the user in the same channel as the bot"""
        guild: discord.Guild = member.guild
        guild_vc: discord.VoiceClient = guild.voice_client
        mem_vs: discord.VoiceState = member.voice
        if guild_vc and guild_vc.is_connected():
            if mem_vs:
                if guild_vc.channel == mem_vs.channel:
                    return True
        return False

    async def player_check(self, ctx):
        """Check is user is in same channel as the bot, then fetch the player object,
        give user error messages if user is not in the same channel"""
        if self.is_member_in_same_channel_as_bot(ctx.author):
            player = self.get_player(ctx, False)  # we don't want to create a player, just find if one exists

            if player:
                return player

            else:
                await ctx.send(self.msg_not_playing, delete_after=self.delete_after_time)
                return None
        else:
            await ctx.send(self.msg_same_channel, delete_after=self.delete_after_time)
            return None

    @commands.command()
    @perms.is_dev()
    async def buttons(self, ctx):
        playing_options = ActionRow(
            [
                Button(style=ButtonStyle.green, label="Pause playback", custom_id="music_menu_toggle", emoji="⏸️"),
                Button(style=ButtonStyle.green, label="Skip song", custom_id="music_menu_skip", emoji="⏭️"),
                Button(style=ButtonStyle.red, label="Stop", custom_id="music_menu_stop", emoji="⏹️")
            ],

        )
        """
                    [
                        Button(style=ButtonStyle.red, label="Stop and disconnect", custom_id="music_menu_stop"),
                        Button(style=ButtonStyle.red, label="Clear queue", custom_id="music_menu_clear"),
                        Button(style=ButtonStyle.red, label="Remove a song from queue", custom_id="music_menu_remove"),
                    ]"""
        paused_options = ActionRow([
            Button(style=ButtonStyle.blue, label="Resume playback", custom_id="music_menu_play"),
            Button(style=ButtonStyle.blue, label="Skip song", custom_id="music_menu_skip"),
            Button(style=ButtonStyle.blue, label="Clear queue", custom_id="music_menu_stop"),
        ])

        msg = await ctx.send("_ _", components=playing_options)

        # msg = await ctx.send("PLAYBACK OPTIONS", components=playing_options)
        # msg2 = await ctx.send("QUEUE OPTIONS", components=queue_options)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def dc(self, ctx):
        player = await self.player_check(ctx)
        if player:
            player.queue.clear()

            guild = ctx.guild
            vc = guild.voice_client
            vc.stop()

            await self.cleanup(guild)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def resume(self, ctx):
        player = await self.player_check(ctx)
        if player:
            guild = ctx.guild
            vc = guild.voice_client
            vc.resume()
            await ctx.send("Playback resumed", delete_after=self.delete_after_time)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def pause(self, ctx):
        print(ez_utils.base_directory())

        player = await self.player_check(ctx)
        if player:
            guild = ctx.guild
            vc = guild.voice_client
            vc.pause()
            await ctx.send("Playback paused", delete_after=self.delete_after_time)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def skip(self, ctx):
        player = await self.player_check(ctx)
        if player:
            if player.current:
                guild = ctx.guild
                vc = guild.voice_client
                vc.stop()
                await ctx.send("Song `{}` skipped".format(player.current['title']), delete_after=self.delete_after_time)
            else:
                await ctx.send(self.msg_not_playing, delete_after=self.delete_after_time)

    # TODO fix or replace with similar command which actually works
    """
    @commands.command()
    @commands.guild_only()
    async def skip_to(self, ctx, skip_to_index: int):
        skip_index = skip_to_index - 1
        player = await self.player_check(ctx)
        if player:
            if player.current and len(player.queue) > 1:
                try:
                    print("uh")
                    print(player.queue.find_from_index(skip_index))
                except IndexError:
                    print("nah")
                    return

                t = player.queue.find_from_index(skip_index)
                for song_index in range(0, skip_index - 1):
                    print()
                    player.queue.remove(song_index)

                guild = ctx.guild
                vc = guild.voice_client
                vc.stop()

                await ctx.send("Skipped songs", delete_after=self.delete_after_time)

            else:
                await ctx.send(self.msg_not_playing, delete_after=self.delete_after_time)
    """

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def remove(self, ctx, *, index: int):
        player = await self.player_check(ctx)
        if player:
            if len(player.queue) > 0:

                player.queue.remove(index - 1)
            else:
                await ctx.send("No songs queued", delete_after=self.delete_after_time)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def queue(self, ctx):
        player = await self.player_check(ctx)
        if player:
            if len(player.queue) > 0:
                msg = "```\n"

                # todo pagination

                for i in range(len(player.queue)):
                    item: Song = player.queue[i]
                    print(item)

                    msg += f"{'#' + str(i + 1):<3} " \
                           f"{str(item.title)[:50]} " \
                           f"[{time_fmt.seconds_to_time(item.duration)}]\n"

                msg += "```"

                await ctx.send(msg, delete_after=self.longer_delete_after_time)

            else:
                await ctx.send("No songs queued.", delete_after=self.delete_after_time)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def play(self, ctx, *, link_or_search: str):
        vc = ctx.voice_client
        if not vc:
            try:
                await ctx.author.voice.channel.connect()
                # log

            except asyncio.TimeoutError:
                print("VC join timeout")
                await ctx.send("Timed out whilst trying to connect.")
                return
            except AttributeError:
                await ctx.send("Join a voice channel first!")
                return

        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, link_or_search, loop=self.bot.loop, api_key=self.yt_api_key)
        if source:
            await player.queue.put(source)
            
            return
            print(source)
            print(len(source))
            for src in source:
                # log song
                await player.queue.put(src)

    @commands.command()
    @commands.guild_only()
    @perms.is_dev()
    async def clear(self, ctx):
        player = self.get_player(ctx)
        player.queue.clear()

        guild = ctx.guild
        vc = guild.voice_client
        vc.stop()


def setup(bot):
    bot.add_cog(Audio(bot))

