from discord.ext import commands
from cogs.utils import time_formatting as timefmt
from PIL import Image
from datetime import datetime
from cogs.utils import perms, IO
import os
import io
import discord
import requests


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx):
        """Shows the bots current uptime"""
        try:
            data = IO.read_settings_as_json()
            if data is None:
                await ctx.send(IO.settings_fail_read)
                return

            now = datetime.now().timestamp()
            tfmt = '%Y-%m-%d %H:%M:%S.%f'
            start = datetime.strptime(data['info']['start-time'], tfmt)
            rc = datetime.strptime(data['info']['reconnect-time'], tfmt)

            await ctx.send("Bot Uptime: {}\n"
                           "Last Reconnect Time: {}"
                           "".format(timefmt.timestamp_to_time_ago(now - start.timestamp()),
                                     timefmt.timestamp_to_time_ago(now - rc.timestamp())))

        except Exception as e:
            await ctx.send("Error getting bot uptime. Reason: {}".format(type(e).__name__))

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def why(self, ctx, emote: discord.Emoji):
        """Why does this emote exist?

        Input emote must be a discord custom emoji.
        Doesn't work with animated emoji or default emoji."""

        BASE = Image.open(os.path.join(self.bot.base_directory, "cogs", "data", "memes", "emote_why.png"))
        res = requests.get(emote.url)
        EMOTE = Image.open(io.BytesIO(res.content)).convert("RGBA")
        EMOTE = EMOTE.resize((400, 400))
        BASE.paste(EMOTE, (69, 420), EMOTE)
        file = io.BytesIO()
        BASE.save(file, format="PNG")
        file.seek(0)
        await ctx.send(file=discord.File(file, "why.png"))


def setup(bot):
    bot.add_cog(Commands(bot))


