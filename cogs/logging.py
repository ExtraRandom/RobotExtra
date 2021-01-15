from discord.ext import commands
import discord
from datetime import datetime
# from cogs.utils import perms, IO
# from cogs.utils.logger import Logger
from cogs.utils import time_formatting as timefmt


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.somewhere_nice = {
            "server": 750689226382901288,
            "join_leave_log": 796381270799024150,
            "kick_ban_log": 761212419388604477
        }

        self.dev = {
            "server": 223132558609612810,
            "join_leave_log": 796547566509621260,
            "kick_ban_log": 796547635485343784
        }

        self.ids = self.somewhere_nice

    async def on_message(self, message):
        bot_msg = message.author.bot
        if bot_msg is True:
            return

        if message.guild.id == self.ids["server"]:
            query = """
INSERT OR REPLACE INTO
    tracking(user_id, message_last_time, message_last_url)
VALUES
    ({}, {}, "{}")
""".format(message.author.id, message.created_at.timestamp(), message.jump_url)
            eq = self.bot.execute_query(query)

    async def on_member_join(self, member):
        if member.guild.id == self.ids["server"]:
            channel = discord.utils.get(member.guild.text_channels, id=self.ids["join_leave_log"])

            account_age = timefmt.datetime_to_time_ago(member.created_at)
            age_stamp = datetime.utcnow().timestamp() - member.created_at.timestamp()
            if age_stamp < (60 * 60 * 24):
                account_age_msg = ":warning: {} :warning:".format(account_age)
            else:
                account_age_msg = account_age

            result = discord.Embed(title="User Joined",
                                   colour=discord.Colour.green(),
                                   description="**User:** {}\n"
                                               "**Member Count:** {}\n"
                                               "**Created:** {}"
                                               "".format(member.mention, member.guild.member_count,
                                                         account_age_msg))

            result.set_author(name="{}".format(member), icon_url=member.avatar_url)
            result.timestamp = datetime.utcnow()
            result.set_footer(text="ID: {}".format(member.id))

            await channel.send(embed=result)

    async def on_member_remove(self, member):
        if member.guild.id == self.ids["server"]:
            # Log kick/ban if applicable
            async for entry in member.guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                    channel = discord.utils.get(member.guild.text_channels, id=self.ids["kick_ban_log"])
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

            # Log leave
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
            result.set_author(name="{}".format(member), icon_url=member.avatar_url)
            result.timestamp = datetime.utcnow()
            result.set_footer(text="ID: {}".format(member.id))

            channel = discord.utils.get(member.guild.text_channels, id=self.ids["join_leave_log"])

            await channel.send(embed=result)

    async def on_member_ban(self, guild, user):
        if guild.id == self.ids["server"]:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.ban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=self.ids["kick_ban_log"])
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
        if guild.id == self.ids["server"]:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.unban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=self.ids["kick_ban_log"])
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
        # print(before.name)
        # print(before.status)
        # print(after.status)

    async def on_message_edit(self, old, new):
        if new.author.bot is True:
            return
        print("old: ", old.content, "\nnew: ", new.content)

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
