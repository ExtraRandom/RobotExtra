from discord.ext import commands
from cogs.utils import time_formatting as timefmt, IO
from datetime import datetime
from cogs.utils import perms
import discord
import requests
import tinytuya


class Tuya(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(name="tuya")
    async def lights_tuya(self, ctx):
        print("")


def setup(bot):
    bot.add_cog(Tuya(bot))


"""
https://github.com/jasonacox/tinytuya/blob/master/examples/cloud.py
https://github.com/jasonacox/tinytuya/tree/master/examples
https://github.com/jasonacox/tinytuya/blob/master/tinytuya/BulbDevice.py
https://github.com/jasonacox/tinytuya
"""
