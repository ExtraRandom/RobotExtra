from discord.ext import commands
from cogs.utils import perms
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import discord


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
            res = discord.Embed(title="HowLongToBeat.com Search for '{}'".format(game))

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


def setup(bot):
    bot.add_cog(Games(bot))


