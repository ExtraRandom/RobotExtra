from discord.ext import commands
from time import time
from datetime import datetime
from cogs.utils import perms, IO
from cogs.utils import time_formatting as timefmt
from cogs.utils.logger import Logger
import discord
import random
import re
import os


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignore_categories = [758500155207974983,  # ADMIN LOGS
                                  750690307191865445,  # SERVER
                                  761526935200595988]  # ARCHIVED CHANNELS

        # self.ignore_channels = ["join-leave-log", "message-log", "changes-log", "discord-updates", "rules",
        #                        "roles", "announcements", "joins-and-leaves", "suggestions"]

    async def find_member_from_id_or_mention(self, ctx, user):
        target = None

        if user is None:
            target = ctx.author
        else:
            # Check for mention
            try:
                mentions = ctx.message.mentions
                if len(mentions) == 1:
                    target = mentions[0]
                elif len(mentions) > 1:
                    # await ctx.send("Please only mention **one** user")
                    return None
            except AttributeError:
                pass

            # Check for id
            if target is None:
                try:
                    user_id = int(user)
                    user_find = ctx.message.guild.get_member(user_id)
                    # user_find = discord.utils.find(lambda m: m.id == user_id, ctx.guild.members)
                    if user_find is not None:
                        target = user_find
                except Exception as e:
                    pass

        return target

    @commands.command(hidden=True, aliases=["random"], enabled=False)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def rndmem(self, ctx):
        """pick a member at random (ignores bots)"""
        all_members = ctx.message.guild.members
        non_bot_members = []
        for member in all_members:
            if member.bot:
                continue
            non_bot_members.append(member)

        random.seed()
        t = random.randint(0, len(non_bot_members) - 1)

        await ctx.send(non_bot_members[t].name)

    @commands.command(hidden=True, aliases=["members", "memchk", "checkmem"])
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def checkmember(self, ctx):
        """List all users in server who don't have the member role"""
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
            ago = datetime.utcnow().timestamp() - user.joined_at.timestamp()
            new = "{} - Joined: {}".format(user.mention,
                                           timefmt.timestamp_to_time_ago(ago)
                                           )
            users.append(new)

        if len(is_not_member) is 0:
            await ctx.send("no users missing member role")
            return

        await ctx.send("Server members who do not have the member role (didn't read rules): ")
        await ctx.send("\n".join(users))

    @commands.command(hidden=True, aliases=["memsch"], enabled=False)
    @perms.is_admin()
    async def search(self, ctx, *, search: str):
        """not really sure what the point of this one is"""
        peoples = []

        all_members = ctx.message.guild.members
        for member in all_members:
            if member.bot:
                continue
            if search.lower() in str(member.name).lower():
                peoples.append(member.name)

        res = ", ".join(peoples)
        if len(res) is 0:
            await ctx.send("no results")
        else:
            await ctx.send(res)

    @commands.command(aliases=["steal", "emoteplease"])
    @perms.is_admin()
    async def emotepls(self, ctx, *, message_id: str):
        """Steal emotes from a message

        Input must be a message id"""
        msg_channel = ctx.channel

        try:
            int(message_id)
        except Exception as e:
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
                if channel.category_id in self.ignore_categories:
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
                if len(is_animated) is not 0:
                    file_type = "gif"
                emoji_id = str(emote.split(":")[-1]).replace(">", "")
                link = "<https://cdn.discordapp.com/emojis/{}.{}?v=1>".format(emoji_id, file_type)
                result.add_field(name="{}".format(str(emote.split(":")[-2])),
                                 value="[Link]({})".format(link))

            await ctx.send(embed=result)

        reactions = message.reactions

        if len(reactions) is not 0:
            reacts = discord.Embed(title="Reactions to message with id '{}'".format(message_id))
            for reaction in reactions:
                try:
                    link = "<https://cdn.discordapp.com/emojis/{}.png?v=1>".format(reaction.emoji.id)
                    reacts.add_field(name="{}".format(reaction.emoji.name),
                                     value="[Link]({})".format(link))
                except Exception as e:
                    continue

            if len(reacts.fields) >= 1:
                await ctx.send(embed=reacts)

    @commands.command(hidden=True)
    @perms.is_admin()
    async def info(self, ctx, *, user=None):
        """Show info of a member

        Optional Argument: Mention or User ID
        No Argument will return your own info"""
        # https://discordpy.readthedocs.io/en/latest/api.html#member
        # target = None
        target = await Admin.find_member_from_id_or_mention(self, ctx, user)

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

        if len(roles) is not 0:
            result.add_field(name="Roles",
                             value="{}".format(" ".join(roles)))
        else:
            result.add_field(name="Roles",
                             value="No Roles")

        result.add_field(name="Created Account at:",
                         value="{}\n({} ago)".format(target.created_at,
                                                     timefmt.datetime_to_time_ago(target.created_at)))

        result.add_field(name="Joined Server at:",
                         value="{}\n({} ago)".format(target.joined_at,
                                                     timefmt.datetime_to_time_ago(target.joined_at)))
        result.set_footer(text="ID: {}".format(target.id))

        await ctx.send(embed=result)

    @commands.command(enabled=False, hidden=True)
    @perms.is_dev()
    async def song(self, ctx):
        """Fetch song the user is currently listening to on Spotify"""
        spotify_url = "https://open.spotify.com/track/"
        test = ctx.author.activities

        for t in test:  # print(t)
            if type(t) is discord.Spotify:
                await ctx.send("{}{}".format(spotify_url, t.track_id))
                return

        await ctx.send("{}, You are not listening to a song???".format(ctx.author.mention))
        # await ctx.send(test)

    @commands.command(hidden=True, enabled=False)
    @perms.is_dev()
    async def idk(self, ctx):
        added = []
        start_time = time()
        await ctx.send("started at {}".format(start_time))

        for channel in ctx.guild.text_channels:
            if channel.category_id in self.ignore_categories:
                continue
            # if channel.name in self.ignore_channels:
            #    continue
            # print(channel)

            # after = datetime(2020, 10, 7)

            async for msg in channel.history(limit=40000):
                if msg.author.bot is True:
                    continue
                if msg.author.id in added:
                    continue
                else:
                    added.append(msg.author.id)

                query = """
INSERT INTO 
    tracking (user_id, message_last_time, message_last_url)
VALUES
    ({}, {}, "{}")
                """.format(msg.author.id, msg.created_at.timestamp(), msg.jump_url)

                eq = self.bot.execute_query(query)

        end_time = time()
        await ctx.send("ended at {}".format(end_time))
        await ctx.send("took {}".format(end_time - start_time))

    @commands.command()
    @perms.is_admin()
    async def check(self, ctx, *, user_id: str):
        """Check when a given user last spoke

        Input must be a Users ID"""

        # TODO update to allow metions via the function

        try:
            user_id = int(user_id)
        except ValueError:
            await ctx.send("Invalid user ID: '{}'".format(user_id))
            return

        user_data = discord.utils.find(lambda m: m.id == user_id, ctx.guild.members)
        try:
            result = discord.Embed(title="{}#{}".format(user_data.name, user_data.discriminator),
                                   description="{}".format(user_data.mention),
                                   colour=discord.Color.green())
        except AttributeError:
            await ctx.send("The user with the ID '{}' is not part of this server.".format(user_id))
            return

        if user_data.bot:
            result.add_field(name="Bot",
                             value="The user ID provided is for a bot.")
            result.colour = discord.Color.blue()
            await ctx.send(embed=result)
            return

        query = """
SELECT
    *
FROM
    tracking
WHERE
    user_id = "{}"
        """.format(user_id)
        erq = self.bot.execute_read_query(query)

        if len(erq) == 0:
            result.add_field(name="Last Message Time:",
                             value="Never")
            result.colour = discord.Color.red()
            await ctx.send(embed=result)
            return

        user, m_time, m_url = erq[0]
        n_time = str(datetime.fromtimestamp(m_time)).split(".")[0]

        a_time = datetime.utcnow().timestamp() - m_time

        result.add_field(name="Last Message Time:",
                         value="{} UTC".format(n_time))
        result.add_field(name="Time Ago:",
                         value="{} ago".format(timefmt.timestamp_to_time_ago(a_time)))
        result.add_field(name="URL:",
                         value="{}".format(m_url))

        await ctx.send(embed=result)

    @commands.command(hidden=True)
    @perms.is_dev()
    async def checkall(self, ctx):
        """List all server members who have never spoken"""
        users = []
        for member in ctx.guild.members:
            user_id = member.id
            query = """
SELECT
    *
FROM
    tracking
WHERE
    user_id = "{}"
            """.format(user_id)
            erq = self.bot.execute_read_query(query)
            user_data = discord.utils.find(lambda m: m.id == user_id, ctx.guild.members)
            if user_data.bot:
                continue

            if len(erq) == 0:
                ago = datetime.utcnow().timestamp() - user_data.joined_at.timestamp()
                new = "{} - Joined: {}".format(user_data.mention,
                                               timefmt.timestamp_to_time_ago(ago)
                                               )
                users.append(new)
                continue

        await ctx.send("Members who have never spoken: ")
        await ctx.send("\n".join(users))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def checkactive(self, ctx):
        """List server members who haven't spoken for 4 weeks or more"""

        await ctx.send("Members who haven't spoken for 4 weeks or more:")

        for member in ctx.guild.members:
            user_id = member.id
            query = """
    SELECT
        *
    FROM
        tracking
    WHERE
        user_id = "{}"
                """.format(user_id)
            erq = self.bot.execute_read_query(query)
            user_data = discord.utils.find(lambda m: m.id == user_id, ctx.guild.members)
            if user_data.bot:
                continue

            if len(erq) == 0:
                continue
            else:
                last_id, last_time, last_url = erq[0]
                total_time = datetime.utcnow().timestamp() - last_time
                if total_time >= 2419200:

                    result = discord.Embed(title="{}#{}".format(user_data.name, user_data.discriminator),
                                           description="{}".format(user_data.mention),
                                           colour=discord.Color.green())

                    n_time = str(datetime.fromtimestamp(last_time)).split(".")[0]

                    a_time = datetime.utcnow().timestamp() - last_time

                    result.add_field(name="Last Message Time:",
                                     value="{} UTC".format(n_time))
                    result.add_field(name="Time Ago:",
                                     value="{} ago".format(timefmt.timestamp_to_time_ago(a_time)))
                    result.add_field(name="URL:",
                                     value="{}".format(last_url))
                    await ctx.send(embed=result)

    @commands.command(hidden=True, enabled=False)
    @perms.is_dev()
    async def lazy(self, ctx):
        message_id = 763670004162887721
        channel = 750974858820583474

        channel = discord.utils.get(ctx.guild.text_channels, id=channel)

        data = await channel.fetch_message(message_id)
        e = data.embeds[0]
        print(e.title)
        print(e.description)
        print(e.footer)
        print(e.timestamp)

    @commands.command(hidden=True)
    @perms.is_dev()
    async def time(self, ctx, *, time_inp: int):
        await ctx.send(timefmt.timestamp_to_time_ago(time_inp))

    @commands.command(hidden=True, enabled=False)
    @perms.is_dev()
    async def embed(self, ctx):
        await ctx.send(embed=discord.Embed(title="Test", description="Test", color=discord.Color.dark_red(),
                                           timestamp=datetime.utcnow()))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def now(self, ctx):
        await ctx.send(datetime.utcnow())


def setup(bot):
    bot.add_cog(Admin(bot))


