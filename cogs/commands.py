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

    @commands.command(hidden=True)
    @perms.is_dev()
    async def asdfasdfasdfasdf(self, ctx):
        print("")
        return


def setup(bot):
    bot.add_cog(Commands(bot))


