from discord.ext import commands
# from cogs.utils import perms
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import discord
from cogs.utils import IO
from urllib import parse
from discord_components import (
    # Button,
    # ButtonStyle,
    Select,
    SelectOption,
    InteractionType
    # Interaction
)
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hltb(self, ctx, *, game: str):
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
                await ctx.send(embed=res)
                return

            for game_data in games:
                game_name = game_data.select('a')[0].get_text()
                game_times = game_data.select('div div div')[0].get_text()

                game_name = str(game_name).strip()
                game_times = str(game_times).strip()

                # TODO break down game times by line so we can format it better

                res.add_field(name=game_name, value=game_times)

                if len(res.fields) >= 5:
                    break

            await ctx.send(embed=res)

        else:
            await ctx.send("Failed to fetch data")

    @commands.command()
    async def itad(self, ctx, *, search_term: str):
        key_data = IO.read_settings_as_json()
        if key_data is None:
            return
        else:
            key = key_data['keys']['itad_api']

        search = parse.quote(search_term)

        limit = 4
        search_url = "https://api.isthereanydeal.com/v02/search/search/?key={}&q={}&limit={}&strict=0" \
                     "".format(key, search, limit)

        res = requests.get(search_url)
        res_code = res.status_code
        if res is not None and res_code == 200:
            plains_data = res.json()

            if len(plains_data['data']['results']) == 0:
                await ctx.send("No results found for '{}'".format(search_term))
                return

            plains_title_lookup = {}

            options = []
            for result in plains_data['data']['results']:
                options.append(SelectOption(label=result['title'], value=result['plain'], emoji="🎮"))
                p_key = result['plain']
                p_value = result['title']
                plains_title_lookup[p_key] = p_value

            options.append(SelectOption(label="Cancel", value="itad_menu_cancel", emoji="❌"))

            m = await ctx.send("Pick game (30s)", components=[Select(options=options)])
            try:
                def check(i_res):
                    return ctx.author == i_res.user and i_res.channel == ctx.channel

                interaction = await self.bot.wait_for("select_option", check=check, timeout=30)
                await interaction.respond(type=InteractionType.DeferredUpdateMessage)
                game_plain = interaction.component[0].value

                if game_plain == "itad_menu_cancel":
                    await m.edit(content="ITAD Search Canceled",
                                 components=[])
                    return
                else:
                    await m.delete()

            except asyncio.TimeoutError:
                await m.edit(content="Prompt timed out.",
                             components=[Select(options=options, disabled=True)])
                return

            deals_url = "https://api.isthereanydeal.com/v01/game/prices/" \
                        "?key={}&plains={}&region=uk&country=gb&shops=&exclude=&added=0" \
                        "".format(key, game_plain)

            deals_res = requests.get(deals_url)
            deals_res_code = deals_res.status_code
            if deals_res is not None and deals_res_code == 200:
                deals_data = deals_res.json()
                deals = deals_data['data'][game_plain]
                embed = discord.Embed(title="Prices for {}".format(plains_title_lookup[game_plain]),
                                      colour=discord.Colour.dark_blue())
                embed.url = deals['urls']['game']

                stores_msg = ""
                had_to_shorten = False
                break_store = None

                for deal in deals['list']:
                    add = "[{}]({})\n".format(deal['shop']['name'], deal['url'])
                    if len(add) + len(stores_msg) >= 1024:
                        had_to_shorten = True
                        break_store = deal['shop']['name']
                        break
                    stores_msg += add

                prices_msg = ""
                for deal in deals['list']:
                    if had_to_shorten is True and deal['shop']['name'] == break_store:
                        break

                    percent = ""
                    if deal['price_cut'] != 0:
                        percent = "({}% off)".format(deal['price_cut'])

                    percent = ""

                    prices_msg += "£{:.2f} {}\n".format(deal['price_new'], percent)

                drm_msg = ""
                for deal in deals['list']:
                    if had_to_shorten is True and deal['shop']['name'] == break_store:
                        break

                    drm = deal['drm']
                    drm_neat = []
                    for name in drm:
                        drm_neat.append(str(name).capitalize())

                    if len(drm) == 0:
                        f_drm = "-"
                    else:
                        f_drm = ", ".join(drm_neat)

                    drm_msg += "{}\n".format(f_drm)

                embed.add_field(name="Seller", value=stores_msg)
                embed.add_field(name="Price", value=prices_msg)
                embed.add_field(name="DRM", value=drm_msg)

                await ctx.send(embed=embed)

            else:
                await ctx.send("Failed to fetch deals data. (Code: {})".format(deals_res_code))
                return
        else:
            await ctx.send("Search failed. (Code: {})".format(res_code))


def setup(bot):
    bot.add_cog(Games(bot))
