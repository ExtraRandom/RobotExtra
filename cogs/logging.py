from discord.ext import commands
from datetime import datetime
from cogs.utils import perms, IO
# from cogs.utils.logger import Logger
from cogs.utils import time_formatting as timefmt
import discord


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message: discord.Message):  # log user_id, server_id, message time and jump url to db
        if message.author.bot is True:
            return

        if type(message.channel) is discord.DMChannel:
            return

        gid = str(message.guild.id)
        config = self.bot.servers_config[gid]

        if config['tracking']['last_message']:
            if message.channel.category_id in config['tracking']['ignore_categories']:
                # don't log if in these categories
                return

            u_id = message.author.id
            new_time = message.created_at.timestamp()

            check = self.bot.db_quick_read(u_id, message.guild.id)
            if check is None:
                query = """
                INSERT INTO
                    activity(user_id, server_id, message_last_time, message_last_url)
                VALUES
                    ({}, {}, {}, "{}")
                """.format(u_id, message.guild.id, new_time, message.jump_url)
            else:
                db_id, __user_id, __server_id, __message_last_time, __message_last_url = check
                query = """
                UPDATE
                    activity
                SET
                    message_last_time = {},
                    message_last_url = "{}"
                WHERE
                    db_id = {}
                """.format(new_time, message.jump_url, db_id)

            self.bot.execute_query(query)  # eq =

    async def on_member_join(self, member):
        gid = str(member.guild.id)
        config = self.bot.servers_config[gid]

        if config['logging']['join_leave_log'] is not None:
            channel = discord.utils.get(member.guild.text_channels, id=config['logging']["join_leave_log"])

            account_age = timefmt.time_ago(member.created_at)
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
        gid = str(member.guild.id)
        config = self.bot.servers_config[gid]

        if config['logging']['join_leave_log'] is not None:
            # Log kick/ban if applicable and set in config
            if config['logging']['kick_ban_log'] is not None:
                async for entry in member.guild.audit_logs(limit=5):
                    if entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                        channel = discord.utils.get(member.guild.text_channels, id=config['logging']["kick_ban_log"])
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
                                               "".format(member.mention, timefmt.time_ago(member.joined_at),
                                                         " ".join(roles)))
            result.set_author(name="{}".format(member), icon_url=member.avatar_url)
            result.timestamp = datetime.utcnow()
            result.set_footer(text="ID: {}".format(member.id))

            channel = discord.utils.get(member.guild.text_channels, id=config['logging']["join_leave_log"])

            await channel.send(embed=result)

    async def on_member_ban(self, guild, user):
        gid = str(guild.id)
        config = self.bot.servers_config[gid]

        if config['logging']['kick_ban_log'] is not None:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.ban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=config['logging']["kick_ban_log"])
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
        gid = str(guild.id)
        config = self.bot.servers_config[gid]

        if config['logging']['kick_ban_log'] is not None:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.unban and entry.target.name == user.name:
                    channel = discord.utils.get(guild.text_channels, id=config['logging']["kick_ban_log"])
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


def setup(bot):
    b = Logging(bot)
    bot.add_cog(b)
    bot.add_listener(b.on_message, "on_message")
    bot.add_listener(b.on_member_join, "on_member_join")
    bot.add_listener(b.on_member_remove, "on_member_remove")
    bot.add_listener(b.on_member_ban, "on_member_ban")
    bot.add_listener(b.on_member_unban, "on_member_unban")
