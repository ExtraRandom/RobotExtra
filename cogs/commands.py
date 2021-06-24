from discord.ext import commands
from cogs.utils import time_formatting as timefmt
from PIL import Image
from datetime import datetime
from cogs.utils import perms, IO
import os
import io
import discord
import requests
import pytz
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
    async def why(self, ctx, emote: discord.Emoji):
        """Why does this emote exist?

        Input emote must be a discord custom emoji.
        Doesn't work with animated emoji or default emoji."""

        BASE = Image.open(os.path.join(self.bot.base_directory, "cogs", "data", "memes", "emote_why.png"))
        res = requests.get(emote.url)
        EMOTE = Image.open(io.BytesIO(res.content)).convert("RGBA")
        EMOTE = EMOTE.resize((400, 400))
        BASE.paste(EMOTE, (69, 420), EMOTE)
        file = io.BytesIO()
        BASE.save(file, format="PNG")
        file.seek(0)
        await ctx.send(file=discord.File(file, "why.png"))

    @commands.command()
    @perms.is_admin()
    async def times(self, ctx):
        """Get the current time for admins/mods"""
        extra_time = datetime.now(tz=pytz.timezone('Europe/London'))
        john_time = datetime.now(tz=pytz.timezone('Europe/Copenhagen'))
        nat_time = datetime.now(tz=pytz.timezone('Australia/Victoria'))
        jacob_time = datetime.now(tz=pytz.timezone('US/Central'))

        fmt = "%a %d %b\n%H:%M:%S\n%z %Z"

        results = discord.Embed(title="Admin/Mod Current Times")
        results.add_field(name="Jacob",
                          value="{}".format(jacob_time.strftime(fmt)))
        results.add_field(name="Extra",
                          value="{}".format(extra_time.strftime(fmt)))
        results.add_field(name="JohnDoe",
                          value="{}".format(john_time.strftime(fmt)))
        results.add_field(name="Natalie",
                          value="{}".format(nat_time.strftime(fmt)))

        await ctx.send(embed=results)

    @commands.command(hidden=True)
    @perms.is_dev()
    async def invite(self, ctx):
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
    async def server(self, ctx):
        """Server Info"""
        dt = ctx.guild.created_at
        year = dt.year
        month = f'{dt.month:02}'
        day = f'{dt.day:01}'
        hour = f'{dt.hour:02}'
        minute = f'{dt.minute:02}'
        second = f'{dt.second:02}'

        res = discord.Embed(title="Server Info", description="Times in UTC", colour=ctx.guild.owner.colour)
        res.add_field(name="Creation Date", value="{}{} of {}, {} at {}:{}"
                      .format(day, timefmt.day_suffix(day), dt.strftime("%B"), year, hour, minute))
        res.add_field(name="Server Age", value="{} old".format(timefmt.time_ago(dt, True)))
        res.add_field(name="Server Owner", value="{}\n({})".format(ctx.guild.owner,
                                                                   ctx.guild.owner.mention))

        await ctx.send(embed=res)

    @commands.command()
    async def bot(self, ctx):
        """Bot Info"""
        bot_info = await self.bot.application_info()
        bot_name = bot_info.name
        bot_owner = bot_info.owner.mention
        discord_py_version = discord.__version__
        python_version = py_v()
        github_link = "https://github.com/ExtraRandom/SNBot"
        uptime = timefmt.time_ago(self.bot.start_time.timestamp())

        res = discord.Embed(title="Bot Info", colour=discord.colour.Colour.dark_blue())
        res.add_field(name="Name", value="{}".format(bot_name))
        res.add_field(name="Owner", value="{}".format(bot_owner))
        res.add_field(name="Discord Py Version", value="{}".format(discord_py_version))
        res.add_field(name="Python Version", value="{}".format(python_version))
        res.add_field(name="Source Code", value="{}".format(github_link))
        res.add_field(name="Uptime", value="{}".format(uptime))

        await ctx.send(embed=res)


def setup(bot):
    bot.add_cog(Commands(bot))


