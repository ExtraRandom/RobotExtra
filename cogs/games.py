from discord.ext import commands
from bs4 import BeautifulSoup
import requests
import discord
from cogs.utils import IO, time_formatting
from urllib import parse
import time
from cogs.utils.logger import Logger


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def itad(self, ctx,
                   search_term: discord.Option(str, description="The term to search for", required=True)#,
                   # #allow_vouchers: discord.Option(bool,
                   #                               description="Allow Vouchers when considering cheapest price",
                   #                               required=False, default=True)
                   ):
        """IsThereAnyDeal.com Search"""

        await ctx.defer()

        allow_vouchers = True  # todo decide what to do with this

        key = IO.fetch_from_settings('keys', 'itad_api', "DOCKER_ITAD_TOKEN")
        if key is None:
            # TODO write to log (maybe?)
            await ctx.respond("No ITAD API key in settings config.", delete_after=15)
            return

        search = parse.quote(search_term)
        limit = 10
        result_limit = 4
        search_url = f"https://api.isthereanydeal.com/games/search/v1?key={key}&title={search}&results={limit}"

        res = requests.get(search_url)

        results = {}
        overview_payload = []

        if res is not None and res.status_code == 200:
            # print(res.text)
            search_json = res.json()

            for result in search_json:
                results[result['id']] = result['title']

                overview_payload.append(result['id'])
        else:
            await ctx.respond("An error occurred whilst searching for games")
            return

        # print(results)
        # print(overview_payload)

        country = "GB"  # Two-letter country code (ISO 3166-1 alpha-2)

        overview_url = (f"https://api.isthereanydeal.com/games/overview/v2"
                        f"?key={key}&country={country}&voucher={allow_vouchers}")
        overview_res = requests.post(overview_url, json=overview_payload)

        embed = discord.Embed(title=f"IsThereAnyDeal.com Search for '{search_term}'", colour=discord.Colour.blue())

        if overview_res is not None and overview_res.status_code == 200:
            overview_data = overview_res.json()['prices']
            # print(overview_res.text)

            for prices in overview_data:

                price_raw = prices['current']['price']['amount']
                if price_raw == 0:
                    price_clean = "Free"
                else:
                    price_clean = f"£{price_raw:.2f}"

                voucher = ""
                if prices['current']['voucher']:
                    voucher = f"with code **{prices['current']['voucher']}**"

                embed.add_field(name=f"{results[prices['id']]}",
                                value=f"Price: **{price_clean}** {voucher}\n"
                                      f"Store: **[{prices['current']['shop']['name']}]({prices['current']['url']})**\n"
                                      f"Info: **[All Prices]({prices['urls']['game']})**")

                if len(embed.fields) >= result_limit:
                    break
        else:
            await ctx.respond("An error occurred whilst fetching game prices")
            return

        embed.set_footer(text="This is a reworked version of the ITAD command using the new API, "
                              "it may still have some bugs!")
        await ctx.respond(embed=embed)

    @commands.slash_command()
    async def dltime(
            self, ctx,
            size_in_gigabytes: discord.Option(float, "Download size in GigaBytes", required=True),
            download_speed_mbps: discord.Option(float, "Download speed in MegaBytes per second", required=False)):
        """Calculate time to download given file size"""
        await ctx.defer()

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

    @commands.slash_command()
    async def proton_ge(self, ctx):
        """Check for the latest version of Proton Glorious Eggroll"""
        await ctx.defer()

        api_url = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
        res = requests.get(api_url, timeout=5)  # TODO add a timeout to every get request throughout the code
        if res:
            data = res.json()
            new_date = time_formatting.datetime_string_reformat(data['published_at'],
                                                                old_format='%Y-%m-%dT%H:%M:%SZ',
                                                                new_format='%d/%m/%Y')
            await ctx.respond(f"Latest Version: [{data['tag_name']}](<{data['html_url']}>) \nReleased: {new_date}")
            # example of time format: 2025-01-17T22:34:54Z
        else:
            await ctx.respond("Error fetching data, try again later")

def setup(bot):
    bot.add_cog(Games(bot))
