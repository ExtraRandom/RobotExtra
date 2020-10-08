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


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignore_channels = ["join-leave-log", "message-log", "changes-log", "discord-updates", "rules",
                                "roles", "announcements", "joins-and-leaves", "suggestions"]

    @commands.command(hidden=True, aliases=["random"])
    @perms.is_dev()
    # @perms.is_in_somewhere_nice()
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

        print(non_bot_members[t].name)
        print(non_bot_members[t].display_name)

        await ctx.send(non_bot_members[t].name)

    @commands.command(hidden=True, aliases=["members"])
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def memchk(self, ctx):
        """this is not a helpful help message"""
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
                if add == True:
                    is_not_member.append(member)

        msg = ""
        test = ""
        for user in is_not_member:
            msg += "{}#{}   ".format(user.name, user.discriminator)
            test += "{}   ".format(user.mention)

        # print(is_not_member)
        # print(msg)

        if len(is_not_member) is 0:
            await ctx.send("no users missing member role")
            return

        await ctx.send(msg)
        await ctx.send(test)

    @commands.command(hidden=True, aliases=["memsch"])
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
                # await ctx.send(member.name)

        res = ", ".join(peoples)
        if len(res) is 0:
            await ctx.send("no results")
        else:
            await ctx.send(res)

    @commands.command(aliases=["steal", "emoteplease"])
    @perms.is_admin()
    async def emotepls(self, ctx, *, message_id: str):
        """Returns a list of all emotes in/reacted to on a given message

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
                if channel.name in self.ignore_channels:
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
    @perms.is_dev()
    async def idk(self, ctx):
        added = []
        start_time = time()
        await ctx.send("started at {}".format(start_time))

        for channel in ctx.guild.text_channels:
            if channel.name in self.ignore_channels:
                continue
            print(channel)

            after = datetime(2020, 10, 7)

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
        query = """
SELECT
    *
FROM
    tracking
WHERE
    user_id = "{}"
        """.format(user_id)
        erq = self.bot.execute_read_query(query)

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
                # await ctx.send("user {} has never spoken".format(user_data.name))
                continue

            # user, m_time = erq[0]
            # n_time = datetime.fromtimestamp(m_time)
            # await ctx.send("{}, {} last msg time {}".format(user, user_data.name, n_time))

            # print(msg)

        await ctx.send("\n".join(users))

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def embed(self, ctx):
        await ctx.send(embed=discord.Embed(title="Test", description="Test", color=discord.Color.dark_red(),
                                           timestamp=datetime.utcnow()))

    @commands.command()
    async def now(self, ctx):
        await ctx.send(datetime.utcnow())

    @commands.command()
    @perms.is_dev()
    async def asdf(self, ctx):
        t = self.bot.get_emoji(685573187903422464)
        print(t)


def setup(bot):
    bot.add_cog(Admin(bot))


