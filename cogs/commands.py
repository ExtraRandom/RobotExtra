from discord.ext import commands  # , tasks
from cogs.utils import time_formatting as timefmt, IO
import datetime
from cogs.utils import perms
import discord
import requests
from platform import python_version as py_v
from cogs.utils import train_stations
# import re
# from time import time


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def uptime(self, ctx):
        """Shows the bots current uptime"""
        await ctx.defer()
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
        await ctx.defer()
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
        res.timestamp = datetime.datetime.now(datetime.UTC)

        icon = ctx.guild.icon
        if icon:
            res.set_thumbnail(url=icon)

        await ctx.respond(embed=res)

    @commands.slash_command(name="bot")
    async def bot(self, ctx):
        """Bot Info"""
        await ctx.defer()
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

    @commands.user_command(name="Server Avatar")
    async def user_server_avatar(self, ctx, user: discord.Member):
        # TODO embed similar to carl bot avatar command
        if user.guild_avatar is None:
            link = user.avatar.url
        else:
            link = user.guild_avatar.url

        await ctx.respond(content=link)
        return

    async def get_stations(self, ctx: discord.AutocompleteContext):
        res = []
        data = train_stations.crs_lookup

        if len(ctx.value) == 2 or len(ctx.value) == 3:
            index = 0
            for crs in data.values():
                if ctx.value.upper() in crs:
                    name = list(data.keys())[index]
                    if name not in res:
                        res.append(name)
                        if len(res) >= 5:
                            break

                index += 1

        for name in data.keys():
            if name is not None:
                if ctx.value.lower() in name.lower():
                    if name not in res:
                        res.append(name)

            if len(res) >= 5:
                break
        return res

    def time_colon(self, inp_time):
        """Add a colon to time, or return given value if not a time"""
        if len(inp_time) == 4:
            return str(inp_time)[:2] + ":" + str(inp_time)[2:]
        else:
            return inp_time

    """
    @commands.slash_command(name="traininfo")
    async def train_info_command(
            self,
            ctx: discord.ApplicationContext,
            station: discord.Option(
                str,
                description="The Station to check for train at",
                autocomplete=get_stations
            ),
    ):
        print("test")
        """
        # todo info on a specific train from realtime trains
        # todo figure way of presenting info in a concise manner

    @commands.slash_command(name="trains")
    async def trains_command(
            self,
            ctx: discord.ApplicationContext,
            station: discord.Option(
                str,
                description="The Station to check for train times at",
                autocomplete=get_stations
            ),
            detailed: discord.Option(
                bool,
                description="Whether to include extra details or not ",
                required=False,
                default=False
            ),
            services_count: discord.Option(
                int,
                description="Max number of services to include - Limited to 25",
                required=False,
                default=4,
                max_value=25,
                min_value=1
            )
    ):
        """Find when the next trains to call at a UK rail station are"""
        await ctx.defer()

        station_crs = train_stations.crs_lookup[station]

        # data = IO.read_settings_as_json()
        # auth = (data['keys']['rtt_name'], data['keys']['rtt_key'])
        rtt_name = IO.fetch_from_settings("keys", "rtt_name", "DOCKER_RTT_NAME")
        rtt_key = IO.fetch_from_settings("keys", "rtt_key", "DOCKER_RTT_KEY")
        auth = (rtt_name, rtt_key)

        res = requests.get(f"https://api.rtt.io/api/v1/json/search/{station_crs}", auth=auth)  # print(res.text)
        res_json = res.json()

        if res_json['services'] is None:
            await ctx.respond("There are no trains running to or from this station right now.")
            return

        # else:
        #     print(res.text)
        # print(res_json['services'][0])
        # print(res.text)

        # service_id = res_json['services'][0]['serviceUid']
        # run_date = str(res_json['services'][0]['runDate']).replace("-", "/")
        # res2 = requests.get(f"https://api.rtt.io/api/v1/json/service/{service_id}/{run_date}", auth=auth)  # print(res.text)
        # print(res2.text)

        services = res_json['services']
        services_added_count = 0

        embed = discord.Embed(title=f"The next trains calling at {station} [{station_crs}]",
                              description="Actual times may vary",
                              colour=discord.Colour.blue())

        for service in services:
            services_added_count = services_added_count + 1
            if services_added_count == services_count + 1:
                break

            loc_detail = service['locationDetail']
            time_this_station = loc_detail.get("gbttBookedDeparture", None)
            if time_this_station is None:
                time_this_station = loc_detail.get("gbttBookedArrival", "Not Found")

            time_this_station = self.time_colon(time_this_station)

            origin_detail = loc_detail['origin']

            if len(origin_detail) == 1:
                origin_location = origin_detail[0]['description']
                origin_time = origin_detail[0]['publicTime']
            else:
                origin_location_list = []
                for loc in origin_detail:
                    origin_location_list.append(loc['description'])

                origin_location = " & ".join(origin_location_list)
                origin_time = origin_detail[0]['publicTime']

            origin_time = self.time_colon(origin_time)

            destination_detail = loc_detail['destination']

            if len(destination_detail) == 1:
                destination_location = destination_detail[0]['description']
                destination_time = destination_detail[0]['publicTime']
            else:
                destination_location_list = []
                for loc in destination_detail:
                    destination_location_list.append(loc['description'])
                destination_location = " & ".join(destination_location_list[::-1])
                destination_time = destination_detail[len(destination_detail) - 1]['publicTime']

            destination_time = self.time_colon(destination_time)

            # print(service)
            headcode = service['trainIdentity']
            toc = service['atocName']

            service_type = service['serviceType']
            if service_type != "train":
                headcode += f" ({str(service_type).capitalize()})"

            msg = f"**Due:** \n{time_this_station}\n"
            if detailed:
                msg += f"**Origin:** \n{origin_location} \nAt {origin_time}\n"
            msg += f"**Destination:** \n{destination_location}"
            if detailed:
                msg += f"\nAt {destination_time}"
            msg += f"\n**Operator:** \n{toc}"

            embed.add_field(name=f"{headcode}",
                            value=msg)


        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
