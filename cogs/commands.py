from discord.ext import commands
import re
from cogs.utils import time_formatting as timefmt, IO
import datetime
from cogs.utils import perms
import discord
import requests
from platform import python_version as py_v
from cogs.utils import train_stations
from cogs.utils.logger import Logger


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
        # discord.OptionChoice(station_name, station_crs)

        if len(ctx.value) == 2 or len(ctx.value) == 3:
            index = 0
            for crs in data.values():
                if ctx.value.upper() in crs:
                    name = list(data.keys())[index]
                    if name not in res:
                        res.append(discord.OptionChoice(name, data[name]))
                        if len(res) >= 5:
                            break

                index += 1

        for name in data.keys():
            if name is not None:
                if ctx.value.lower() in name.lower():
                    if name not in res:
                        res.append(discord.OptionChoice(name, data[name]))

            if len(res) >= 5:
                break
        return res

    def time_colon(self, inp_time):
        """Add a colon to time, or return given value if not a time"""
        if len(inp_time) == 4:
            return str(inp_time)[:2] + ":" + str(inp_time)[2:]
        else:
            return inp_time

    # todo perhaps an advanced version of the below command that allows for filtering a TO station, and date/time
    #  see the api page for more https://www.realtimetrains.co.uk/about/developer/pull/docs/locationlist/

    @commands.slash_command(name="trains")
    async def trains_command(
            self,
            ctx: discord.ApplicationContext,
            station_crs: discord.Option(
                str,
                name="station",
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
            ),
    ):
        """Find when the next trains to call at a UK rail station are"""
        await ctx.defer()

        rtt_name = IO.fetch_from_settings("keys", "rtt_name", "DISCORD_RTT_NAME")
        rtt_key = IO.fetch_from_settings("keys", "rtt_key", "DISCORD_RTT_KEY")
        auth = (rtt_name, rtt_key)

        try:
            res = requests.get(f"https://api.rtt.io/api/v1/json/search/{station_crs}", auth=auth)
            # print(res.text)
            res_json = res.json()

        except Exception as e:
            Logger.write(e, True)
            await ctx.respond("An error occurred whilst making a request to the RealTime Trains API.\n"
                              "This could be because the the RealTime Trains API keys are not configured (extra pls fix),"
                              "or that API is down. This error has been logged.")
            return

        if res_json['services'] is None:
            await ctx.respond("There are no trains running to or from this station right now.")
            return

        services = res_json['services']
        services_added_count = 0
        station = res_json['location']['name']

        embed = discord.Embed(title=f"The next trains calling at {station} [{station_crs}]",
                              description="Actual times may vary - All data from Realtime Trains",
                              colour=discord.Colour.blue())

        for service in services:
            services_added_count = services_added_count + 1
            if services_added_count == services_count + 1:
                break

            # realtimeDeparture

            loc_detail = service['locationDetail']
            time_this_station = loc_detail.get("realtimeDeparture", None)   # was gbttBookedDeparture
            if time_this_station is None:
                time_this_station = loc_detail.get("realtimeArrival", "Not Found")  # was gbttBookedArrival

            # delay = loc_detail.get("realtimeGbttDepartureLateness", None)
            # if delay is None:
            #    delay = loc_detail.get("realtimeGbttArrivalLateness", None)

            time_booked = loc_detail.get("gbttBookedDeparture", None)
            time_realtime = loc_detail.get("realtimeDeparture", None)

            if time_booked is None:
                time_booked = loc_detail.get("gbttBookedArrival", 0)
            if time_realtime is None:
                time_realtime = loc_detail.get("realtimeArrival", 0)

            delay = int(time_realtime) - int(time_booked)

            show_delay = False

            # print("delay is ", delay)
            if delay is not None:
                if delay > 6:
                    show_delay = True

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

            destination_time = self.time_colon(destination_time)  # print(service)
            headcode = service['trainIdentity']
            toc = service['atocName']

            platform = loc_detail.get("platform", -1)
            platform_msg = ""
            if platform != -1:
                platform_msg = f"Platform {platform}\n"

            service_type = service['serviceType']
            if service_type != "train":
                headcode += f" ({str(service_type).capitalize()})"

            if show_delay is False:
                msg = f"**Expected:** \n{time_this_station}\n{platform_msg}"  # final new line is in platform msg
            else: # show delay
                msg = f"**Expected:** \n{time_this_station} - {delay} minutes late\n{platform_msg}"

            if detailed:
                msg += f"**Origin:** \n{origin_location} \nAt {origin_time}\n"
            msg += f"**Destination:** \n{destination_location}"
            if detailed:
                msg += f"\nAt {destination_time}"
            msg += f"\n**Operator:** \n{toc}"

            if detailed:
                msg += f"\n**Service ID:**\n{service['serviceUid']}"

            embed.add_field(name=f"{headcode}",
                            value=msg)

        await ctx.respond(embed=embed)

    @commands.slash_command(name="train_service_info")
    async def specific_train_command(
            self,
            ctx: discord.ApplicationContext,
            service_id: discord.Option(
                str,
                description="The service ID of the train",
                required=True
            ),
            start_date: discord.Option(
                str,
                description="The date the service started on - FORMAT YYYY/MM/DD",
                required=False,
                default=None
            )
            # todo better date input
    ):
        """Information about a specific train service"""
        await ctx.defer()

        valid_id = re.search("[A-Z][0-9]{5}", service_id)

        if valid_id is None:
            await ctx.respond("The given service ID is not a valid service ID. ")
            return


        rtt_name = IO.fetch_from_settings("keys", "rtt_name", "DISCORD_RTT_NAME")
        rtt_key = IO.fetch_from_settings("keys", "rtt_key", "DISCORD_RTT_KEY")
        auth = (rtt_name, rtt_key)

        if len(rtt_name) < 3:
            await ctx.respond("RTT Name and Key are not set, or incorrectly set. Extra pls fix")
            return

        if start_date is None:
            run_date = datetime.datetime.now().strftime("%Y/%m/%d")
        else:
            valid_date_basic = re.search("[0-9]{4}/[0-9]{2}/[0-9]{2}", start_date)
            if valid_date_basic:
                run_date = start_date
            else:
                await ctx.respond("Invalid date")
                return

        res = requests.get(f"https://api.rtt.io/api/v1/json/service/{service_id}/{run_date}", auth=auth)
        # print(res.text)
        try:
            data = res.json()
        except requests.JSONDecodeError:
            await ctx.respond("Error whilst fetching service. Please make sure to use a valid service ID, "
                              "especially if setting a custom date.")
            return


        # ABOVE IS CODE FOR CALLING THE API
        # ALL LOGIC FOR PROCESSING THE DATA IS BELOW THIS

        # set up some variables
        displayed_as_cancelled = "CANCELLED_CALL"
        # displayed_as_starts_short = "STARTS"
        # part_cancelled = False
        # cancelled_origin = None
        # cancelled_reason = None
        origin = data['origin'][0]['description']



        loc_data = ""
        loc_index = 0

        # todo make this less of a complete abomination
        #  the presentation on the discord side is okay but the way we get to that here is really just a mess
        #  so if we can make it more readable that would be great

        for location in data['locations']:
            station_name = location['description']
            # print(station_name)

            approaching = False  # is the train approaching a station
            standing = False  # is the train standing at a platform
            platform = location.get("platform", -1)
            # platform_text = ""

            current_station = ""
            if 'serviceLocation' in location:
                service_location_type = location['serviceLocation']
                service_current_station_text = "***<-- The Train is here***"

                # print(station_name)
                # print(service_location_type)

                if service_location_type == "APPR_STAT": # show arriving at  + approaching msg
                    approaching = True
                elif service_location_type == "APPR_PLAT": # show arriving at + approaching msg
                    approaching = True
                elif service_location_type == "AT_PLAT": # show departing at (or arrived at)
                    standing = True
                elif service_location_type == "DEP_PREP": # show departing at
                    standing = True
                elif service_location_type == "DEP_READY": # show departing at
                    standing = True

                current_station = service_current_station_text

            if platform != -1:
                station_name += f" [P{platform}]"

            if "realtimeDeparture" in location:
                has_departed = location['realtimeDepartureActual']  # has this train departed
                has_arrived = location.get('realtimeArrivalActual', False)  # has this train arrived
                display_as = location['displayAs']
                # print(f"{station_name} {display_as}")

                if approaching or standing:
                    has_departed = False

                if display_as == displayed_as_cancelled:
                    if loc_index == 0:
                        # part_cancelled = True
                        cancelled_origin = station_name
                        cancelled_reason = f"{str(location['cancelReasonLongText']).capitalize()} \n"

                        loc_data += (f"\n***Cancelled between {cancelled_origin} "
                                     f"and {origin} due to {cancelled_reason}***\n")
                    else:
                        pass
                else:
                    if has_departed: # has left the station
                        departure_time = location['realtimeDeparture']
                        loc_data += f"- **{station_name}:** Departed at {departure_time}\n"

                    elif has_departed is False and loc_index > 0: # hasn't left this station and isn't the first in list
                        # add logic to say "due to depart" if this is the current station

                        if approaching is True:
                            current_station = "***<-- Train Approaching***"
                            arrival_time = location['realtimeArrival']
                            loc_data += f"- **{station_name}:** Expected to arrive at {arrival_time} {current_station}\n"
                        elif standing is True:
                            current_station = "***<-- The Train is here***"

                            departure_time = location['realtimeDeparture']   # change to .get
                            loc_data += f"- **{station_name}:** Expected to depart at {departure_time} {current_station}\n"

                        else:
                            arrival_time = location['realtimeArrival']
                            loc_data += f"- **{station_name}:** Expected to arrive at {arrival_time}\n"


                    elif has_departed is False and loc_index == 0: # the first location service hasn't started or hasn't left origin yet
                        departure_time = location['realtimeDeparture']
                        loc_data += f"- **{station_name}:** Expected to depart at {departure_time} {current_station}\n"

                    else:
                        if has_arrived:
                            arrival_time = location['realtimeArrival']
                            loc_data += f"- **{station_name}:** Arrived at {arrival_time} {current_station}\n"

            else:  # "realtimeDeparture" doesn't exist in location data
                if approaching is True:
                    current_station = "***<-- Train Approaching***"
                elif standing is True:
                    current_station = "***<-- The Train is here***"
                else:
                    current_station = ""

                arrived = location['realtimeArrivalActual']  # has the service arrived to this location?
                if arrived: # yes
                    arrival_time = location['realtimeArrival'] # when
                    loc_data += f"- **{station_name}:** Arrived at {arrival_time} {current_station}\n"
                else: # no
                    arrival_time = location['realtimeArrival'] # when is it due
                    loc_data += f"- **{station_name}:** Expected to arrive at {arrival_time} {current_station}\n"


            loc_index += 1

        await ctx.respond(
            f"**__{data['atocName']} Service ({data['trainIdentity']}) Calling at:__**\n"
            f"{loc_data}"
        )


def setup(bot):
    bot.add_cog(Commands(bot))
