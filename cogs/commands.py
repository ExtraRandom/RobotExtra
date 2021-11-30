from discord.ext import commands
from cogs.utils import time_formatting as timefmt
from PIL import Image
from datetime import datetime
from cogs.utils import perms, ez_utils
import os
import io
import discord
import requests
import pytz
import random
import json
from platform import python_version as py_v


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx):
        """Shows the bots current uptime"""
        try:
            start = self.bot.start_time
            rc = self.bot.reconnect_time

            await ctx.send("Bot Uptime: {}\n"
                           "Last Reconnect Time: {}"
                           "".format(timefmt.time_ago(start.timestamp()),
                                     timefmt.time_ago(rc.timestamp())))

        except Exception as e:
            await ctx.send("Error getting bot uptime. Reason: {}".format(type(e).__name__))

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.guild)
    @perms.is_in_somewhere_nice()
    async def why(self, ctx, emote: discord.PartialEmoji):
        """Why does this emote exist?

        Input emote must be a discord custom emoji.
        Doesn't work with animated emoji or default emoji."""

        img_base = Image.open(os.path.join(ez_utils.base_directory(), "cogs", "data", "memes", "emote_why.png"))
        res = requests.get(emote.url)
        img_emote = Image.open(io.BytesIO(res.content)).convert("RGBA")
        img_emote = img_emote.resize((400, 400))
        img_base.paste(img_emote, (69, 420), img_emote)  # nice
        file = io.BytesIO()
        img_base.save(file, format="PNG")
        file.seek(0)
        await ctx.send(file=discord.File(file, "why.png"))

    @commands.command(hidden=True)
    @perms.is_dev()
    async def invite(self, ctx):
        """Get bot invite link"""
        await ctx.send("https://discord.com/oauth2/authorize?client_id=571947888662413313&scope=bot")

    @commands.command(hidden=True, enabled=False)
    @perms.is_dev()
    async def servers(self, ctx):
        """List servers the bot is in"""
        msg = "I am in these servers: \n"

        for guild in self.bot.guilds:
            msg += "{}\n".format(guild.name)

        await ctx.send(msg)

    @commands.command(enabled=True)
    @perms.is_in_a_server()
    async def server(self, ctx):
        """Server Info"""
        dt = ctx.guild.created_at
        year = dt.year
        # month = f'{dt.month:02}'
        day = f'{dt.day:01}'
        hour = f'{dt.hour:02}'
        minute = f'{dt.minute:02}'
        # second = f'{dt.second:02}'

        total_count = ctx.guild.member_count
        member_count = len([m for m in ctx.guild.members if not m.bot])
        bot_count = total_count - member_count

        res = discord.Embed(title="Server Info", description="Times in UTC", colour=ctx.guild.owner.colour)
        res.add_field(name="Creation Date", value="{}{} of {}, {} at {}:{}"
                      .format(day, timefmt.day_suffix(int(day)), dt.strftime("%B"), year, hour, minute))
        res.add_field(name="Server Age", value="{} old".format(timefmt.time_ago(dt, brief=True)))
        res.add_field(name="Server Owner", value="{}\n({})".format(ctx.guild.owner,
                                                                   ctx.guild.owner.mention))
        res.add_field(name="Member Count", value="{} Total Members\n"
                                                 "{} Users\n"
                                                 "{} Bots".format(total_count, member_count, bot_count))
        res.set_footer(text="ID: {}".format(ctx.guild.id))
        res.timestamp = datetime.utcnow()

        await ctx.send(embed=res)

    @commands.command()
    async def bot(self, ctx):
        """Bot Info"""
        bot_info = await self.bot.application_info()
        bot_name = bot_info.name
        bot_owner = bot_info.owner.mention
        discord_py_version = discord.__version__
        python_version = py_v()
        github_link = "https://github.com/ExtraRandom/RobotExtra"
        uptime = timefmt.time_ago(self.bot.start_time.timestamp())
        avatar = self.bot.user.avatar_url

        res = discord.Embed(title="Bot Info", colour=discord.colour.Colour.dark_blue())
        res.add_field(name="Name", value="{}".format(bot_name))
        res.add_field(name="Owner", value="{}".format(bot_owner))
        res.add_field(name="Discord Py Version", value="{}".format(discord_py_version))
        res.add_field(name="Python Version", value="{}".format(python_version))
        res.add_field(name="Source Code", value="{}".format(github_link))
        res.add_field(name="Uptime", value="{}".format(uptime))
        res.set_footer(text="Currently being a robot in {} servers".format(len(self.bot.guilds)))

        res.set_thumbnail(url=avatar)

        await ctx.send(embed=res)

    @commands.command()
    async def ag(self, ctx, *, letters: str):
        """Acronym Generator"""
        if len(letters) > 50:
            await ctx.send("This command is limited to 50 characters or less.")
            return

        word_file = os.path.join(ez_utils.base_directory(), "cogs", "data", "words_letters.json")
        with open(word_file, "r") as fr:
            data = fr.read()
            words = json.loads(data)

        clean_letters = letters.strip().lower()

        result = ""

        for letter in clean_letters:
            try:
                letter_words = words[letter]
            except IndexError:
                continue
            except KeyError:
                continue

            random.seed()
            res_word = random.choice(letter_words).capitalize()
            result += "{} ".format(res_word)

        await ctx.send(f"{letters} means {result}")

    @commands.command()
    @perms.is_dev()
    async def binary(self, ctx, way: str, *, to_convert: str):
        if len(to_convert) * 9 >= 1000:
            await ctx.send("Convert string is too long")
            return

        # converting_to_binary = False
        if way in ["to", "too", "2"]:
            converting_to_binary = True
        elif way in ["from", "form", "back"]:
            converting_to_binary = False
        else:
            await ctx.send("Way '{}' unknown, valid ways are 'to' and 'from'".format(way))
            return

        if converting_to_binary:
            if ez_utils.english_characters_check(to_convert) is True:
                con = ' '.join(format(ord(x), 'b') for x in to_convert)
                await ctx.send(con)

        else:
            chars = to_convert.split(" ")
            conversion = ""
            for char in chars:
                conversion += chr(int(char, 2))

            await ctx.send(conversion)


def setup(bot):
    bot.add_cog(Commands(bot))
