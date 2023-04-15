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
        data = train_stations.crs_lookup

        if len(ctx.value) == 2 or len(ctx.value) == 3:
            index = 0
            for crs in data.values():
                if ctx.value.upper() in crs:
                    name = list(data.keys())[index]
                    if name not in res:
                        res.append(name)

                index += 1

        for name in data.keys():
            #if len(res) > 5:
            #    break

            if name is not None:
                if ctx.value.lower() in name.lower():
                    if name not in res:
                        res.append(name)
            else:
                if len(res) < 25:
                    res.append(name)
                else:
                    break

        """
        data = train_stations.station_names

        for name in data:
            if name is not None:
                if ctx.value.lower() in name.lower():
                    res.append(name)
            else:
                res.append(name)
        """
        return res

    def time_colon(self, time):
        """Add a colon to time, or return given value if not a time"""
        if len(time) == 4:
            return str(time)[:2] + ":" + str(time)[2:]
        else:
            return time

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

        embed = discord.Embed(title=f"The next trains calling at {station}",
                              description="Actual times may vary",
                              colour=discord.Colour.blue())

        for service in services:
            services_added_count = services_added_count + 1
            if services_added_count == 5:
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


            headcode = service['runningIdentity']
            toc = service['atocName']

            embed.add_field(name=f"{headcode}",
                            value=f"**Time at {station}:** \n{time_this_station}\n"
                                  f"**Origin:** \n{origin_location} \nAt {origin_time}\n"
                                  f"**Destination:** \n{destination_location} \nAt {destination_time}\n"
                                  f"**Operator:** \n{toc}")

            # await ctx.send(f"{station} : {time_this_station}\n{origin_location} : {origin_time}\n{headcode}, {toc}")



        """


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

        embed = discord.Embed(title=f"The Next Train Calling at {station_name}",
                              description="Actual times may vary",
                              colour=discord.Colour.blue())
        embed.add_field(name=f"{train_operator}",
                        value=f"Calling at {station_name}: **{station_arrival}**")
        embed.add_field(name="Origin", value=f"Started at: {origin_station}\n"
                                             f"At: *{origin_departure}*")
        embed.add_field(name="Destination", value=f"Terminating at: {destination_station}\n"
                                                  f"At: *{destination_arrival}*")
        """
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
