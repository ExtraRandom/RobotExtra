from discord.ext import commands
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import discord
from cogs.utils import IO
from urllib import parse
import time
from cogs.utils.logger import Logger


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO fix and re-enable
    @commands.slash_command(guild_ids=[])
    async def hltb(self, ctx, game: discord.Option(str, "The game to search for", required=True)):
        """HowLongToBeat.com search"""
        # https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI/blob/master/howlongtobeatpy/howlongtobeatpy/HTMLRequests.py
        base_url = "https://howlongtobeat.com/"
        search_url = base_url + "search_results.php"
        ua = UserAgent()

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'accept': '*/*',
            'User-Agent': ua.random
        }
        payload = {
            'queryString': game,
            't': 'games',
            'sorthead': 'popular',
            'sortd': 'Normal Order',
            'plat': '',
            'length_type': 'main',
            'length_min': '',
            'length_max': '',
            'detail': ""
        }

        r = requests.post(search_url, data=payload, headers=headers)
        if r is not None and r.status_code == 200:
            base_data = BeautifulSoup(r.text, 'lxml')
            games = base_data.select('li div[class="search_list_details"]')
            res = discord.Embed(title="HowLongToBeat.com Search for '{}'".format(game),
                                colour=discord.Colour.blue())

            if len(games) == 0:
                res.add_field(name="No results for search", value="Try again with a different search")
                await ctx.respond(embed=res)
                # await ctx.send(embed=res)
                return

            for game_data in games:
                game_name = game_data.select('a')[0].get_text()
                game_times = game_data.select('div[class="search_list_details_block"]')[0]

                game_name = str(game_name).strip()

                full_info = []

                for time_info in game_times:
                    print("time info", time_info)
                    t = time_info.get_text()
                    t = str(t).strip()
                    full_info.append(t)

                full_info = "\n".join(full_info)

                # TODO fix with minecraft solo/co-op/vs

                print(repr(full_info))

                # game_times = str(game_times).strip()

                # TODO break down game times by line so we can format it better

                res.add_field(name=game_name, value=full_info)  # value=game_times)

                if len(res.fields) >= 5:
                    break

            # await ctx.send(embed=res)
            await ctx.respond(embed=res)

        else:
            await ctx.respond(content="Failed to fetch data")
            # await ctx.send("Failed to fetch data")

    # TODO fix/maybe even rewrite if necessary

    @commands.slash_command()
    async def itad(self, ctx, search_term: discord.Option(str, "The term to search for", required=True)):
        """IsThereAnyDeal.com Search"""

        key = IO.fetch_from_settings('keys', 'itad_api')
        if key is None:
            await ctx.respond("No ITAD API key in settings config.", delete_after=15)
            return

        search = parse.quote(search_term)

        limit = 4
        search_url = "https://api.isthereanydeal.com/v02/search/search/?key={}&q={}&limit={}&strict=0" \
                     "".format(key, search, limit)

        res = requests.get(search_url)
        res_code = res.status_code
        title_lookup = {}
        if res is not None and res_code == 200:
            plains_data = res.json()
            plains_list = []
            for result in plains_data['data']['results']:
                plains_list.append(result['plain'])
                title_lookup[result['plain']] = result['title']
        else:
            await ctx.respond("ITAD Search Failed, See logs for more info")
            Logger.write(f"--------------\nITAD Search Failed\nURL: {search_url}\nStatus Code: {res_code}"
                         f"\n--------------", print_log=True)
            return

        overview_url = "https://api.isthereanydeal.com/v01/game/overview/?key={}&region=uk&country=GB" \
                       "&plains={}".format(key, ",".join(plains_list))
        overview_res = requests.get(overview_url)
        overview_res_code = overview_res.status_code

        if overview_res is not None and overview_res_code == 200:
            overview_data = overview_res.json()

            embed = discord.Embed(title=f"IsThereAnyDeal.com Search for '{search_term}'", colour=discord.Colour.blue())

            for game in overview_data['data']:
                # print(overview_data['data'][game])

                title = title_lookup[str(game)]
                try:
                    price = overview_data['data'][game]['price']['price_formatted']
                    if price == "£0.00":
                        price = "Free"
                except TypeError:
                    price = "Free or Unavailable"

                try:
                    url = overview_data['data'][game]['price']['url']
                except TypeError:
                    url = overview_data['data'][game]['urls']['info']

                info_url = overview_data['data'][game]['urls']['info']

                try:
                    store = overview_data['data'][game]['price']['store']
                except TypeError:
                    store = "Not Available"

                embed.add_field(name=title,
                                value=f"Price: **{price}**\n"
                                      f"Store: [**{store}**]({url})\n"
                                      f"Info: [**All Prices**]({info_url})\n")

            await ctx.respond(embed=embed)

        else:
            await ctx.respond("ITAD Search Failed, See logs for more info")
            Logger.write(f"--------------\nITAD Search Failed\nURL: {overview_url}\nStatus Code: {res_code}"
                         f"\n--------------", print_log=True)
            return

    @commands.slash_command()
    async def dltime(
            self, ctx,
            size_in_gigabytes: discord.Option(float, "Download size in GigaBytes", required=True),
            download_speed_mbps: discord.Option(float, "Download speed in MegaBytes per second", required=False)):
        """Calculate time to download given file size"""

        def secs_to_days(seconds):
            return round(seconds / 86400)

        def secs_to_years(seconds):
            return round(seconds / 31536000)

        if size_in_gigabytes >= 1000000:
            await ctx.send("{} GigaBytes?! Now you're just being silly...".format(size_in_gigabytes))
            return

        if download_speed_mbps is None:
            speeds = {'3MB/s (24Mb/s)': 24,
                      '4MB/s (32Mb/s)': 32,
                      '5MB/s (40Mb/s)': 40,
                      '25MB/s (200Mb/s)': 200,
                      '37.5MB/s (300Mb/s)': 300,
                      '50MB/s (400Mb/s)': 400}
            order = ['3MB/s (24Mb/s)',
                     '4MB/s (32Mb/s)',
                     '5MB/s (40Mb/s)',
                     '25MB/s (200Mb/s)',
                     '37.5MB/s (300Mb/s)',
                     '50MB/s (400Mb/s)']

            embed = discord.Embed(title="Download Times for {} GigaBytes (GB)".format(size_in_gigabytes),
                                  colour=discord.Colour.dark_green(),
                                  description="Actual times taken may vary. Speeds are in MegaBytes per second")
            for i in order:
                if i in speeds:
                    value = (((1048576 * size_in_gigabytes) * 1024) * 8) / (speeds[i] * 1000000)

                    try:
                        if 60 > value:
                            fmt_value = "{} Seconds".format(round(value))
                        elif 3599 < value < 7199:
                            fmt_value = time.strftime('%H hour, %M minutes', time.gmtime(value))
                        elif 7199 < value < 86399:
                            fmt_value = time.strftime('%H hours, %M minutes', time.gmtime(value))
                        elif 86399 < value:
                            fmt_value = time.strftime('{} Day(s), %H hours, %M minutes'.format(secs_to_days(value)),
                                                      time.gmtime(value))
                            if embed.footer is discord.Embed.Empty:
                                embed.set_footer(text="Now that's a lot of data")
                        elif value >= 31536000:
                            fmt_value = time.strftime('{} Year(s), {} Day(s), %H hours, %M minutes'.format(
                                secs_to_years(value), secs_to_days(value)), time.gmtime(value))
                            embed.set_footer(text="Yeah it's gonna take a while")
                        else:
                            fmt_value = time.strftime('%M minutes', time.gmtime(value))

                        embed.add_field(name="{}".format(i),
                                        value="{}".format(fmt_value))

                    except Exception as e:
                        Logger.write(e)
                        await ctx.respond("An error occurred whilst calculating.")
                        return

            await ctx.respond(embed=embed)

        else:
            speed = download_speed_mbps * 8
            value = (((1048576 * size_in_gigabytes) * 1024) * 8) / (speed * 1000000)

            if 60 > value:
                fmt_value = "{} Seconds".format(round(value))
            elif 3599 < value < 7199:
                fmt_value = time.strftime('%H hour, %M minutes', time.gmtime(value))
            elif 7199 < value < 86399:
                fmt_value = time.strftime('%H hours, %M minutes', time.gmtime(value))
            elif 86399 < value:
                fmt_value = time.strftime('{} Day(s), %H hours, %M minutes'.format(secs_to_days(value)),
                                          time.gmtime(value))
            elif value >= 31536000:
                fmt_value = time.strftime('{} Year(s), {} Day(s), %H hours, %M minutes'.format(
                    secs_to_years(value), secs_to_days(value)), time.gmtime(value))
            else:
                fmt_value = time.strftime('%M minutes', time.gmtime(value))

            embed = discord.Embed(title="Download Time for {} GigaBytes (GB)".format(size_in_gigabytes),
                                  colour=discord.Colour.dark_green(),
                                  description="Actual times taken may vary. Speed is MegaBytes per second")

            embed.add_field(name="{} MB/s".format(download_speed_mbps),
                            value="{}".format(fmt_value))

            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Games(bot))
