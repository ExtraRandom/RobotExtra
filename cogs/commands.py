from discord.ext import commands
from cogs.utils import time_formatting as timefmt, IO
from datetime import datetime
from cogs.utils import perms
import discord
import requests
from platform import python_version as py_v
from cogs.utils import train_stations


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def uptime(self, ctx):
        """Shows the bots current uptime"""
        try:
            start = self.bot.start_time
            rc = self.bot.reconnect_time

            await ctx.respond("Bot Uptime: {}\n"
                              "Last Reconnect Time: {}"
                              "".format(timefmt.time_ago(start.timestamp()),
                                        timefmt.time_ago(rc.timestamp())))

        except Exception as e:
            await ctx.respond("Error getting bot uptime. Reason: {}".format(type(e).__name__))

    @commands.slash_command()
    @perms.is_dev()
    async def invite(self, ctx):
        """Get bot invite link"""
        await ctx.respond("https://discord.com/oauth2/authorize?client_id=571947888662413313&scope=bot",
                          ephemeral=True)

    @commands.slash_command(name="server")
    @commands.guild_only()
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

        icon = ctx.guild.icon
        if icon:
            res.set_thumbnail(url=icon)

        await ctx.respond(embed=res)

    @commands.slash_command(name="bot")
    async def bot(self, ctx):
        """Bot Info"""
        bot_info = await self.bot.application_info()
        bot_name = bot_info.name
        bot_owner = bot_info.owner.mention
        discord_version = discord.__version__
        python_version = py_v()
        github_link = "https://github.com/ExtraRandom/RobotExtra"
        uptime = timefmt.time_ago(self.bot.start_time.timestamp())
        avatar = self.bot.user.avatar.url

        res = discord.Embed(title="Bot Info", colour=discord.colour.Colour.dark_blue())
        res.add_field(name="Name", value="{}".format(bot_name))
        res.add_field(name="Owner", value="{}".format(bot_owner))
        res.add_field(name="Pycord Version", value="{}".format(discord_version))
        res.add_field(name="Python Version", value="{}".format(python_version))
        res.add_field(name="Source Code", value="{}".format(github_link))
        res.add_field(name="Uptime", value="{}".format(uptime))
        res.set_footer(text="Currently being a robot in {} servers".format(len(self.bot.guilds)))

        res.set_thumbnail(url=avatar)

        await ctx.respond(embed=res)

    @commands.user_command(name="Role Colour")
    async def colour(self, ctx, user: discord.Member):
        await ctx.respond(content=user.colour, ephemeral=True)

    @commands.user_command(name="Avatar")
    async def user_avatar(self, ctx, user: discord.Member):
        # TODO embed similar to carl bot avatar command
        await ctx.respond(content=user.avatar.url)
        return

    async def get_stations(self, ctx: discord.AutocompleteContext):
        res = []
        data = train_stations.station_names

        for name in data:
            if name is not None:
                if ctx.value.lower() in name.lower():
                    res.append(name)
            else:
                res.append(name)

        return res

    def time_colon(self, time):
        return str(time)[:2] + ":" + str(time)[2:]

    @commands.slash_command(name="trains")
    async def trains_command(
            self,
            ctx: discord.ApplicationContext,
            station: discord.Option(
                str,
                "The Station to check for train times at",
                autocomplete=get_stations
            )
    ):
        """Find when the next train to call at a station is"""
        station_crs = train_stations.crs_lookup[station]

        data = IO.read_settings_as_json()
        auth = (data['keys']['rtt_name'], data['keys']['rtt_key'])

        res = requests.get(f"https://api.rtt.io/api/v1/json/search/{station_crs}", auth=auth)  # print(res.text)

        res_json = res.json()

        loc = res_json['services'][0]['locationDetail']

        origin_station = loc['origin'][0]['description']
        origin_departure = self.time_colon(loc['origin'][0]['publicTime'])

        station_name = res_json['location']['name']
        try:
            station_arrival = loc['realtimeArrival']
        except KeyError:  # Service starts here
            station_arrival = loc['realtimeDeparture']

        station_arrival = self.time_colon(station_arrival)

        destination_station = loc['destination'][0]['description']
        destination_arrival = self.time_colon(loc['destination'][0]['publicTime'])

        train_operator = res_json['services'][0]['atocName']

        embed = discord.Embed(title=f"The Next Train Calling at {station_name}", description="Actual times may vary",
                              colour=discord.Colour.blue())
        embed.add_field(name=f"{train_operator}",
                        value=f"Calling at {station_name}: **{station_arrival}**")
        embed.add_field(name="Origin", value=f"Started at: {origin_station}\n"
                                             f"At: *{origin_departure}*")
        embed.add_field(name="Destination", value=f"Terminating at: {destination_station}\n"
                                                  f"At: *{destination_arrival}*")

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
