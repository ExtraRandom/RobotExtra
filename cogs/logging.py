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


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        bot_msg = message.author.bot
        if bot_msg is True:
            return

        query = """
        INSERT OR REPLACE INTO
            tracking(user_id, message_last_time, message_last_url)
        VALUES
            ({}, {}, "{}")    
                """.format(message.author.id, message.created_at.timestamp(), message.jump_url)

        eq = self.bot.execute_query(query)

    async def on_message_edit(self, old, new):
        if new.author.bot is True:
            return
        print("old: ", old.content, "\nnew: ", new.content)

    async def on_member_remove(self, member):
        if member.guild.id == 750689226382901288:
            async for entry in member.guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                    channel = discord.utils.get(member.guild.text_channels, id=761212419388604477)
                    user = entry.target
                    msg = discord.Embed(title="{} kicked".format(user),
                                        colour=discord.Colour.dark_gold(),
                                        description="**Offender:** {}\n"
                                                    "**Reason:** {}\n"
                                                    "**Responsible admin:** {}"
                                                    "".format(entry.target, entry.reason, entry.user))
                    msg.set_footer()
                    await channel.send(embed=msg)
                    return
                elif entry.action == discord.AuditLogAction.ban and entry.target.name == member.name:
                    channel = discord.utils.get(member.guild.text_channels, id=761212419388604477)
                    user = entry.target
                    msg = discord.Embed(title="{} banned".format(user),
                                        colour=discord.Colour.red(),
                                        description="**Offender:** {}\n"
                                                    "**Reason:** {}\n"
                                                    "**Responsible admin:** {}"
                                                    "".format(entry.target, entry.reason, entry.user))
                    await channel.send(embed=msg)
                    return

    async def on_member_update(self, before, after):
        return
        print(before.name)
        print(before.status)
        print(after.status)


def setup(bot):
    b = Logging(bot)
    bot.add_cog(b)
    bot.add_listener(b.on_message, "on_message")
    # bot.add_listener(b.on_message_edit, "on_message_edit")
    bot.add_listener(b.on_member_remove, "on_member_remove")
    # bot.add_listener(b.on_member_update, "on_member_update")

