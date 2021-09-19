from asyncio import TimeoutError as Timeout
from discord.ext import commands
from time import time
from datetime import datetime, timedelta
from cogs.utils import perms  # , IO
from cogs.utils import time_formatting as timefmt, ez_utils
from cogs.utils.logger import Logger
import discord
import re
import os


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.purge_immune_role_id = 857532290527657984

    @staticmethod
    async def get_role_from_id(ctx, role_id: int):
        role = ctx.guild.get_role(role_id)
        return role

    @commands.group(name="check", invoke_without_command=True, aliases=['chk'])
    @perms.is_admin()
    async def _check(self, ctx, *, user: str):
        """Check member activity

        Use with a user id or mention to check when a member last spoke.
        Use with one of the below subcommands to list multiple users.
        """
        target = await ez_utils.find_member_from_id_or_mention(ctx, user)  # self,

        if target is None:
            await ctx.send("Couldn't find that user")
            return

        try:
            result = discord.Embed(title="{}#{}".format(target.name, target.discriminator),
                                   description="{}".format(target.mention),
                                   colour=discord.Color.green())
        except AttributeError:
            await ctx.send("The user with the ID '{}' is not part of this server.".format(user))
            return

        if target.bot:
            result.add_field(name="Bot",
                             value="The user ID provided is for a bot.")
            result.colour = discord.Color.blue()
            await ctx.send(embed=result)
            return

        erq = self.bot.db_quick_read(target.id, ctx.message.guild.id)

        if erq is None:
            result.add_field(name="Last Message Time:",
                             value="Never")
            result.colour = discord.Color.red()
            await ctx.send(embed=result)
            return

        _, user, server, m_time, m_url = erq
        n_time = str(datetime.fromtimestamp(m_time)).split(".")[0]

        result.add_field(name="Last Message Time:",
                         value="{} UTC".format(n_time))
        result.add_field(name="Time Ago:",
                         value="{} ago".format(timefmt.time_ago(m_time)))
        result.add_field(name="URL:",
                         value="{}".format(m_url))

        await ctx.send(embed=result)

    @_check.command(name="member", aliases=["members", "mems", "mem"])
    @perms.is_admin()
    async def check_member(self, ctx):
        """List users who didn't read the rules

        Lists all users in server who don't have the member role (i.e. didn't read the rules)"""
        is_not_member = []

        all_members = ctx.message.guild.members
        for member in all_members:
            if member.bot:
                continue
            roles = member.roles
            role_count = len(roles)
            if role_count == 0:
                is_not_member.append(member)
            else:
                add = True
                for role in roles:
                    if role.name == "Member":
                        add = False
                        continue
                if add is True:
                    is_not_member.append(member)

        users = []
        for user in is_not_member:
            new = "{} - Joined: {}".format(user.mention, timefmt.time_ago(user.joined_at))
            users.append(new)

        if len(is_not_member) == 0:
            await ctx.send("No users missing member role.")
            return

        await ctx.send("Server members who do not have the member role (didn't read rules): ")
        await ctx.send("\n".join(users))

    @_check.command(name="all")
    @perms.is_admin()
    async def check_all(self, ctx):
        """List all server members who have never spoken"""
        users = []
        for member in ctx.guild.members:
            user_id = member.id
            query = """
    SELECT
        *
    FROM
        activity
    WHERE
        user_id = "{}"
                """.format(user_id)
            erq = self.bot.execute_read_query(query)
            if member.bot:
                continue

            if len(erq) == 0:
                new = "{} - Joined: {}".format(member.mention, timefmt.time_ago(member.joined_at))
                users.append(new)
                continue

        if len(users) >= 1:
            await ctx.send("Members who have never spoken: ")
            await ctx.send("\n".join(users))
        else:
            await ctx.send("Every member has spoken at least once")

    @_check.command(name="active")
    @perms.is_admin()
    async def check_active(self, ctx):
        """List inactive members

        Lists server members who haven't spoken for 4 weeks or more"""

        await ctx.send("Members who haven't spoken for 4 weeks or more:")

        for member in ctx.guild.members:
            user_id = member.id
            query = """
            SELECT
                *
            FROM
                activity
            WHERE
                user_id = "{}" AND server_id = {}
            """.format(user_id, ctx.guild.id)
            erq = self.bot.execute_read_query(query)
            if member.bot:
                continue

            if len(erq) == 0:
                continue
            else:
                _, server_id, last_id, last_time, last_url = erq[0]
                total_time = datetime.utcnow().timestamp() - last_time
                if total_time >= 2419200:
                    result = discord.Embed(title="{}#{}".format(member.name, member.discriminator),
                                           description="{}".format(member.mention),
                                           colour=discord.Color.green())

                    n_time = str(datetime.fromtimestamp(last_time)).split(".")[0]

                    result.add_field(name="Last Message Time:",
                                     value="{} UTC".format(n_time))
                    result.add_field(name="Time Ago:",
                                     value="{} ago".format(timefmt.time_ago(last_time)))
                    result.add_field(name="URL:",
                                     value="{}".format(last_url))
                    await ctx.send(embed=result)

    # TODO fix these 4 commands and give them names that make sense

    @_check.command(name="new", enabled=False)  # TODO FIX
    @perms.is_admin()
    @perms.is_in_somewhere_nice()
    async def check_new(self, ctx):
        """List newest server members"""
        users = []
        for member in ctx.guild.members:
            users.append((member.joined_at, member))

        newest = sorted(users, key=lambda tup: tup[0])[-5:]
        msg = ""
        for join_time, member in newest:
            msg += "{} - Joined server {} ago\n".format(member.mention, timefmt.time_ago(join_time))

        if len(newest) >= 1:
            await ctx.send("The five newest server members: ")
            await ctx.send(msg)
        else:
            await ctx.send("No members detected (something broke)")

    @_check.command(name="old", enabled=False)  # TODO FIX
    @perms.is_admin()
    @perms.is_in_somewhere_nice()
    async def check_oldest(self, ctx):
        """List oldest server members"""
        users = []
        for member in ctx.guild.members:
            users.append((member.joined_at, member))

        oldest = sorted(users, key=lambda tup: tup[0])[:5]
        msg = ""
        for join_time, member in oldest:
            msg += "{} - Joined server {} ago\n".format(member.mention, timefmt.time_ago(join_time))

        if len(oldest) >= 1:
            await ctx.send("The five oldest server members: ")
            await ctx.send(msg)
        else:
            await ctx.send("No members detected (something broke)")

    @_check.command(name="young", enabled=False)  # TODO FIX
    @perms.is_admin()
    @perms.is_in_somewhere_nice()
    async def check_young(self, ctx):
        """List youngest server members"""
        users = []
        for member in ctx.guild.members:
            users.append((member.created_at, member))

        newest = sorted(users, key=lambda tup: tup[0])[-5:]
        msg = ""
        for join_time, member in newest:
            msg += "{} - Joined Discord {} ago\n".format(member.mention, timefmt.time_ago(join_time))

        if len(newest) >= 1:
            await ctx.send("The five youngest server members: ")
            await ctx.send(msg)
        else:
            await ctx.send("No members detected (something broke)")

    @_check.command(name="earliest", enabled=False)  # TODO FIX
    @perms.is_admin()
    @perms.is_in_somewhere_nice()
    async def check_early(self, ctx):
        """List earliest remaining members"""
        users = []
        for member in ctx.guild.members:
            if member.bot is False:
                users.append((member.joined_at, member))

        newest = sorted(users, key=lambda tup: tup[0])[:5]
        msg = ""
        for join_time, member in newest:
            msg += "{} - Joined server {} ago\n".format(member.mention, timefmt.time_ago(join_time))

        if len(newest) >= 1:
            await ctx.send("The five earliest remaining server members: ")
            await ctx.send(msg)
        else:
            await ctx.send("No members detected (something broke)")

    @commands.command(name="checkpurge", hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def check_purge(self, ctx):
        """Check how many members a purge may kick"""
        count = 0
        immune_role = await self.get_role_from_id(ctx, self.purge_immune_role_id)
        immune_count = 0
        for member in ctx.guild.members:
            if member.bot:
                continue

            if immune_role in member.roles:
                immune_count += 1
                continue

            user_id = member.id
            query = """
        SELECT
            *
        FROM
            activity
        WHERE
            user_id = "{}"
                    """.format(user_id)
            erq = self.bot.execute_read_query(query)

            if len(erq) == 0:
                count += 1
                continue
            else:
                _, server_id, last_id, last_time, last_url = erq[0]
                total_time = datetime.utcnow().timestamp() - last_time
                if total_time >= 2419200:
                    count += 1
                    continue
                else:
                    continue

        await ctx.send("{} members have been inactive or have never spoken.".format(count))

    @commands.command(hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def purgetxt(self, ctx):
        """purge.txt"""
        purge_file = os.path.join(ez_utils.base_directory(), "cogs", "data", "purge.txt")
        immune_role = await self.get_role_from_id(ctx, self.purge_immune_role_id)
        with open(purge_file, "w", encoding="utf-8") as fw:
            for member in ctx.guild.members:
                if member.bot:
                    continue
                if immune_role in member.roles:
                    continue

                user_id = member.id
                query = """
            SELECT
                *
            FROM
                activity
            WHERE
                user_id = "{}"
                        """.format(user_id)
                erq = self.bot.execute_read_query(query)

                if len(erq) == 0:
                    join_time = member.joined_at.timestamp()
                    kick_reason = "Never Spoke"

                    fw.write("User: {0} (ID: {0.id})\n"
                             "Purge Reason: {1}\n"
                             "Join Time: {2}\n"
                             "\n".format(member, kick_reason, datetime.fromtimestamp(float(join_time))))

                else:
                    _, server_id, last_id, last_time, last_url = erq[0]
                    total_time = datetime.utcnow().timestamp() - last_time
                    if total_time >= 2419200:
                        kick_reason = "Inactive"
                        fw.write("User: {0} (ID: {0.id})\n"
                                 "Purge Reason: {1}\n"
                                 "Last message time: {2}\n"
                                 "\n".format(member, kick_reason, datetime.fromtimestamp(float(last_time))))
                    else:
                        continue

        await ctx.send(file=discord.File(purge_file))

    @commands.command(hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def purge(self, ctx):
        """Purge inactive members"""
        yes = "✅"
        no = "❌"
        stop = "🛑"
        timeout_length = 60

        total_count = 0
        kicked_count = 0

        immune_role = await self.get_role_from_id(ctx, self.purge_immune_role_id)

        for member in ctx.guild.members:
            if member.bot:
                continue
            if immune_role in member.roles:
                continue

            user_id = member.id
            query = """
        SELECT
            *
        FROM
            activity
        WHERE
            user_id = "{}"
                    """.format(user_id)
            erq = self.bot.execute_read_query(query)

            result = discord.Embed(title="Kick User?",
                                   description="{}".format(member.mention),
                                   colour=discord.Color.gold())
            if len(erq) == 0:
                total_count += 1
                join_time = member.joined_at
                kick_reason = "never spoke"
                result.add_field(name="Kick Reason:",
                                 value="Never spoke")
                result.add_field(name="Time ago:",
                                 value=timefmt.time_ago(join_time))
                result.add_field(name="Joined Server:",
                                 value="{} UTC".format(join_time))
            else:
                _, server_id, last_id, last_time, last_url = erq[0]
                total_time = datetime.utcnow().timestamp() - last_time
                if total_time >= 2419200:
                    kick_reason = "inactive"
                    total_count += 1
                    result.add_field(name="Kick Reason:",
                                     value="Inactivity")
                    result.add_field(name="Time ago:",
                                     value=timefmt.time_ago(last_time))
                    result.add_field(name="Last Message Time:",
                                     value="{} UTC".format(datetime.fromtimestamp(last_time)))
                    result.add_field(name="Last Message Link:",
                                     value=last_url)
                else:
                    continue

            result.set_author(name="{}".format(member), icon_url=member.avatar_url)
            result.set_footer(text="Waiting {} seconds before cancelling".format(timeout_length))

            role_list = member.roles
            roles = []
            for role in role_list:
                if role.name == "@everyone":
                    continue
                roles.append(role.mention)

            roles.reverse()
            if len(roles) != 0:
                result.add_field(name="Roles",
                                 value="{}".format(" ".join(roles)))
            else:
                result.add_field(name="Roles",
                                 value="No Roles")

            msg = await ctx.send(embed=result)

            await msg.add_reaction(yes)
            await msg.add_reaction(no)
            await msg.add_reaction(stop)

            def check(m_reaction, m_user):
                return m_user == ctx.author and m_reaction.message == msg \
                       and m_reaction.emoji in [yes, no, stop]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=timeout_length, check=check)
            except Timeout:
                await msg.reply("No response within {} seconds, stopping purge :octagonal_sign:")
                return

            else:
                if reaction.emoji == yes:
                    await member.kick(reason="{} - kicked in purge".format(kick_reason))
                    await ctx.send(":wave: Kicked {}".format(member))
                    kicked_count += 1
                elif reaction.emoji == no:
                    continue
                elif reaction.emoji == stop:
                    await ctx.send(":octagonal_sign: Stopped purge :octagonal_sign:")
                    break
        await ctx.send("Finished Purge:\nOut of {} users, {} were kicked".format(total_count, kicked_count))

    @commands.command(aliases=["steal", "emoteplease"])
    @perms.is_admin()
    async def emotepls(self, ctx, *, message_id: str):
        """Steal emotes from a message

        Input must be a message id"""
        msg_channel = ctx.channel

        try:
            int(message_id)
        except ValueError:
            await ctx.send("`{}` is an invalid message id!".format(message_id))
            return

        channels = ctx.guild.text_channels
        message = None

        try:
            message = await msg_channel.fetch_message(message_id)
        except discord.NotFound:
            pass

        if message is None:
            for channel in channels:
                if channel.category_id in self.bot.servers_config[str(ctx.guild.id)]['tracking']['ignore_categories']:
                    continue
                if channel == msg_channel:
                    continue
                try:
                    message = await channel.fetch_message(message_id)
                    break
                except discord.NotFound:
                    continue

        if message is None:
            await ctx.send("Couldn't find message with the id `{}`!".format(message_id))
            return

        custom_emojis = re.findall(r'<\w*:\w*:\d*>', message.content)
        custom_emojis = list(dict.fromkeys(custom_emojis))

        if len(custom_emojis) >= 25:
            await ctx.send("Message contains too many emojis. (26 or more)")
            return

        result = discord.Embed(title="Emojis found in message with id '{}'".format(message_id))

        if len(custom_emojis) > 0:
            for emote in custom_emojis:
                file_type = "png"
                is_animated = str(emote.split(":")[0]).replace("<", "")
                if len(is_animated) != 0:
                    file_type = "gif"
                emoji_id = str(emote.split(":")[-1]).replace(">", "")
                link = "<https://cdn.discordapp.com/emojis/{}.{}?v=1>".format(emoji_id, file_type)
                result.add_field(name="{}".format(str(emote.split(":")[-2])),
                                 value="[Link]({})".format(link))

            await ctx.send(embed=result)

        reactions = message.reactions

        if len(reactions) != 0:
            reacts = discord.Embed(title="Reactions to message with id '{}'".format(message_id))
            for reaction in reactions:
                try:
                    link = "<https://cdn.discordapp.com/emojis/{}.png?v=1>".format(reaction.emoji.id)
                    reacts.add_field(name="{}".format(reaction.emoji.name),
                                     value="[Link]({})".format(link))
                except Exception as e:
                    Logger.write(e)
                    continue

            if len(reacts.fields) >= 1:
                await ctx.send(embed=reacts)

    @commands.command(enabled=True, hidden=False)
    async def info(self, ctx, *, user=None):
        """Show info of a member

        Optional Argument: Mention or User ID
        No Argument will return your own info"""
        # https://discordpy.readthedocs.io/en/latest/api.html#member
        # target = None
        target = await ez_utils.find_member_from_id_or_mention(ctx, user)

        if target is None:
            await ctx.send("Couldn't find that user")
            return

        name = str(target)
        if target.nick:
            name += " (aka '{}')".format(target.nick)

        result = discord.Embed(title="",
                               description="[Avatar]({}) - {}".format(target.avatar_url, target.mention),
                               colour=target.colour)
        result.set_author(name="{}".format(name), icon_url=target.avatar_url)

        role_list = target.roles
        roles = []
        for role in role_list:
            if role.name == "@everyone":
                continue
            roles.append(role.mention)

        roles.reverse()

        if len(roles) != 0:
            result.add_field(name="Roles",
                             value="{}".format(" ".join(roles)))
        else:
            result.add_field(name="Roles",
                             value="No Roles")

        result.add_field(name="Created Account at:",
                         value="{}\n({} ago)".format(str(target.created_at).split(".")[0],
                                                     timefmt.time_ago(target.created_at, brief=True)))

        result.add_field(name="Joined Server at:",
                         value="{}\n({} ago)".format(str(target.joined_at).split(".")[0],
                                                     timefmt.time_ago(target.joined_at, brief=True)))
        result.set_footer(text="ID: {}".format(target.id))
        result.timestamp = datetime.utcnow()

        await ctx.send(embed=result)

    @commands.command(hidden=True, name="updatedb", enabled=False)
    @perms.is_dev()
    async def update_db(self, ctx, days_ago: int = 2):
        """Used to update the message time db.
        Kinda janky"""
        start_time = time()
        await ctx.send("Updating DB with messages from the last {} days. Started at {}"
                       "".format(days_ago, start_time))

        for channel in ctx.guild.text_channels:
            if channel.category_id in self.bot.servers_config[str(ctx.guild.id)]['tracking']['ignore_categories']:
                continue

            async for msg in channel.history(limit=50000,
                                             after=datetime.utcnow() - timedelta(days=days_ago)):
                if msg.author.bot is True:
                    continue

                check = self.bot.db_quick_read(msg.author.id, msg.guild.id)

                if check is None:
                    query = """
                    INSERT INTO
                        activity(user_id, server_id, message_last_time, message_last_url)
                    VALUES
                        ({}, {}, {}, "{}")
                    """.format(msg.author.id, msg.guild.id, msg.created_at.timestamp(), msg.jump_url)
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
                    """.format(msg.created_at.timestamp(), msg.jump_url, db_id)

                self.bot.execute_query(query)

        end_time = time()
        await ctx.reply(content="DB updated with messages from the last {} days. Time taken {}"
                                "".format(days_ago, end_time - start_time))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def time(self, ctx, *, time_inp: int):
        """Time testing"""
        then_ts = datetime.utcnow().timestamp()-time_inp
        await ctx.send("time since {}:\n"
                       "{}".format(datetime.fromtimestamp(then_ts),
                                   timefmt.time_ago(then_ts)))

        # await ctx.send(timefmt.time_ago(datetime.utcnow().timestamp()-time_inp))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def timeb(self, ctx, *, time_inp: int):
        """Time brief testing"""
        then_ts = datetime.utcnow().timestamp() - time_inp
        await ctx.send("time since {}:\n"
                       "{}".format(datetime.fromtimestamp(then_ts),
                                   timefmt.time_ago(then_ts, brief=True)))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def log(self, ctx):
        """DM latest log file"""
        log_file = os.path.join(ez_utils.base_directory(), "logs", Logger.get_filename())
        await ctx.author.send(file=discord.File(log_file))
        await ctx.send("DM'd latest log file <:somewhere_nice:766664959979159553>")

    @commands.command(hidden=True)
    @perms.is_dev()
    async def eid(self, ctx, *, emoji: discord.Emoji):
        """Get ID of an Emoji"""
        await ctx.send(emoji.id)


def setup(bot):
    bot.add_cog(Admin(bot))
