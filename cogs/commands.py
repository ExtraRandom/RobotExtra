from discord.ext import commands
import discord
from time import time
from datetime import datetime
import os
from cogs.utils import perms, IO
from cogs.utils.logger import Logger
import random
import re
from cogs.utils import time_formatting as timefmt


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


def setup(bot):
    bot.add_cog(Commands(bot))


