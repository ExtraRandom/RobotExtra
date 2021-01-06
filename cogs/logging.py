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

        # self.sn_server_id = 750689226382901288
        # self.sn_joinleave_log =

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

    async def on_member_join(self, member):
        if member.guild.id == 750689226382901288:
            channel = discord.utils.get(member.guild.text_channels, id=796381270799024150)

            result = discord.Embed(title="User Joined",
                                   colour=discord.Colour.green(),
                                   description="**User:** {}\n"
                                               "**Member Count:** {}\n"
                                               "**Created:** {}"
                                               "".format(member.mention, member.guild.member_count,
                                                         timefmt.datetime_to_time_ago(member.created_at)))

            result.set_author(name="{}".format(member.name), icon_url=member.avatar_url)
            result.timestamp = datetime.utcnow()
            result.set_footer(text="ID: {}".format(member.id))

            await channel.send(embed=result)
            # await channel.send("User {} joined at {} UTC".format(member.name, datetime.utcnow()))

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
                    msg.set_footer(text="User ID: {}".format(user.id))
                    msg.timestamp = datetime.utcnow()
                    await channel.send(embed=msg)
                    # return
                """
                elif entry.action == discord.AuditLogAction.ban and entry.target.name == member.name:
                    channel = discord.utils.get(member.guild.text_channels, id=761212419388604477)
                    user = entry.target
                    msg = discord.Embed(title="{} banned".format(user),
                                        colour=discord.Colour.red(),
                                        description="**Offender:** {}\n"
                                                    "**Reason:** {}\n"
                                                    "**Responsible admin:** {}"
                                                    "".format(entry.target, entry.reason, entry.user))
                    msg.set_footer(text="User ID: {}".format(user.id))
                    msg.timestamp = datetime.utcnow()
                    await channel.send(embed=msg)
                    return
                """

            role_list = member.roles
            roles = []
            for role in role_list:
                if role.name == "@everyone":
                    continue
                roles.append(role.mention)
            roles.reverse()

            result = discord.Embed(title="User Left",
                                   colour=discord.Colour.red(),
                                   description="**User:** {}\n"
                                               "**Member for:** {}\n"
                                               "**Roles:** {}"
                                               "".format(member.mention, timefmt.datetime_to_time_ago(member.joined_at),
                                                         " ".join(roles)))
            result.set_author(name="{}".format(member.name), icon_url=member.avatar_url)
            result.timestamp = datetime.utcnow()

            channel = discord.utils.get(member.guild.text_channels, id=796381270799024150)

            # await channel.send("User {} left at {} UTC".format(member.name, datetime.utcnow()))
            await channel.send(embed=result)

    async def on_member_ban(self, guild, user):
        # print("guild", guild.name, " just banned", user.name)
        if guild.id == 750689226382901288:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.ban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=761212419388604477)
                    user = entry.target
                    msg = discord.Embed(title="{} banned".format(user),
                                        colour=discord.Colour.dark_red(),
                                        description="**Offender:** {}\n"
                                                    "**Reason:** {}\n"
                                                    "**Responsible admin:** {}"
                                                    "".format(entry.target, entry.reason, entry.user))
                    msg.set_footer(text="User ID: {}".format(user.id))
                    msg.timestamp = datetime.utcnow()
                    await channel.send(embed=msg)
                    return

    async def on_member_unban(self, guild, user):
        if guild.id == 750689226382901288:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.unban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=761212419388604477)
                    user = entry.target
                    msg = discord.Embed(title="{} unbanned".format(user),
                                        colour=discord.Colour.green(),
                                        description="**Offender:** {}\n"
                                                    "**Responsible admin:** {}"
                                                    "".format(entry.target, entry.user))
                    msg.set_footer(text="User ID: {}".format(user.id))
                    msg.timestamp = datetime.utcnow()
                    await channel.send(embed=msg)
                    return

    async def on_member_update(self, before, after):
        return
        print(before.name)
        print(before.status)
        print(after.status)

    async def on_message_delete(self, message):
        print("DELETED", message.content)

    async def on_bulk_message_delete(self, messages):
        for msg in messages:
            print("DELETED BULK", msg.content)


def setup(bot):
    b = Logging(bot)
    bot.add_cog(b)
    bot.add_listener(b.on_message, "on_message")
    bot.add_listener(b.on_member_join, "on_member_join")
    bot.add_listener(b.on_member_remove, "on_member_remove")
    bot.add_listener(b.on_member_ban, "on_member_ban")
    bot.add_listener(b.on_member_unban, "on_member_unban")

    # bot.add_listener(b.on_message_edit, "on_message_edit")
    # bot.add_listener(b.on_member_update, "on_member_update")
    # bot.add_listener(b.on_message_delete, "on_message_delete")
    # bot.add_listener(b.on_bulk_message_delete, "on_bulk_message_delete")


