from discord.ext import commands
from cogs.utils import time_formatting as timefmt, IO
from datetime import datetime
from cogs.utils import perms
import discord
import requests


class Shoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    shoes = discord.commands.SlashCommandGroup("shoes", "Shoe Related Commands")

    class ShoeModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            self.add_item(discord.ui.InputText(label="Shoe SKU"))
            self.add_item(discord.ui.InputText(label="Tracking URL"))
            self.add_item(discord.ui.InputText(label="Price Paid"))
            self.add_item(discord.ui.InputText(label="Likely Sell Price"))
            self.add_item(discord.ui.InputText(label="Image URL"))

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(title="Shoe info")
            embed.add_field(name="Shoe SKU", value=self.children[0].value)
            embed.add_field(name="Tracking URL", value=self.children[1].value)
            embed.add_field(name="Price Paid", value=self.children[2].value)
            embed.add_field(name="Likely Sell Price", value=self.children[3].value)
            # embed.set_image(url=self.children[4].value)
            embed.set_thumbnail(url=self.children[4].value)
            await interaction.response.send_message(embeds=[embed])

    @shoes.command(name="embed")
    async def shoe_modal_embed(self, ctx):
        """WIP - Shoe Embed creator via Modal"""
        modal = self.ShoeModal(title="Shoe embed creator")
        await ctx.send_modal(modal)
        await ctx.respond("Done!")

    async def brands_autocomplete(self, ctx: discord.AutocompleteContext):
        return ['Nike']

    async def size_region_autocomplete(self, ctx: discord.AutocompleteContext):
        return ['UK', 'US M', 'US W', 'EU']  # , 'JP (CM)']

    @shoes.command(name="size")
    async def shoe_size_conversion(self,
                                   ctx: discord.ApplicationContext,
                                   brand: discord.Option(
                                       str,
                                       "Shoe Brand to get sizes for",
                                       autocomplete=brands_autocomplete
                                   ),
                                   region: discord.Option(
                                       str,
                                       "Region of size to convert from",
                                       autocomplete=size_region_autocomplete
                                   ),
                                   shoe_size: discord.Option(
                                       float,
                                       "Shoe Size"
                                   )):
        """WIP - Shoe size converter"""

        """
        Nike
        - Mens https://www.nike.com/gb/size-fit/mens-footwear
        - Womens https://www.nike.com/gb/size-fit/womens-footwear
        - Unisex https://www.nike.com/gb/size-fit/unisex-footwear-mens-based
        - https://www.nike.com/gb/size-fit/kids-footwear
        """

        size_table = {
            "Nike":
                [
                    # {"US M": , "US W": , "UK": , "EU": , "JP (CM)": },
                    # {"US M": , "US W": , "UK": , "EU": },
                    {"US M": 3.5, "US W": 5, "UK": 3, "EU": 35.5},  # "JP (CM)": 22.5},
                    {"US M": 4, "US W": 5.5, "UK": 3.5, "EU": 36},  # "JP (CM)": 23},
                    {"US M": 4.5, "US W": 6, "UK": 4, "EU": 36.5},  # "JP (CM)": 23.5},
                    {"US M": 5, "US W": 6.5, "UK": 4.5, "EU": 37.5},  # "JP (CM)": 23.5},
                    {"US M": 5.5, "US W": 7, "UK": 5, "EU": 38},
                    {"US M": 6, "US W": 7.5, "UK": 5.5, "EU": 38.5},
                    {"US M": 6.5, "US W": 8, "UK": 6, "EU": 39},
                    {"US M": 7, "US W": 8.5, "UK": 6, "EU": 40},
                    {"US M": 7.5, "US W": 9, "UK": 6.5, "EU": 40.5},
                    {"US M": 8, "US W": 9.5, "UK": 7, "EU": 41},
                    {"US M": 8.5, "US W": 10, "UK": 7.5, "EU": 42},
                    {"US M": 9, "US W": 10.5, "UK": 8, "EU": 42.5},
                    {"US M": 9.5, "US W": 11, "UK": 8.5, "EU": 43},
                    {"US M": 10, "US W": 11.5, "UK": 9, "EU": 44},
                    {"US M": 10.5, "US W": 12, "UK": 9.5, "EU": 44.5},
                    {"US M": 11, "US W": 12.5, "UK": 10, "EU": 45},
                    {"US M": 11.5, "US W": 13, "UK": 10.5, "EU": 45.5},
                    {"US M": 12, "US W": 13.5, "UK": 11, "EU": 46},
                    {"US M": 12.5, "US W": 14, "UK": 11.5, "EU": 47},
                    {"US M": 13, "US W": 14.5, "UK": 12, "EU": 47.5},
                    {"US M": 13.5, "US W": 15, "UK": 12.5, "EU": 48},
                    {"US M": 14, "US W": 15.5, "UK": 13, "EU": 48.5},
                    {"US M": 14.5, "US W": 16, "UK": 13.5, "EU": 49},
                    {"US M": 15, "US W": 16.5, "UK": 14, "EU": 49.5},
                    {"US M": 15.5, "US W": 17, "UK": 14.5, "EU": 50},
                    {"US M": 16, "US W": 17.5, "UK": 15, "EU": 50.5},
                    {"US M": 16.5, "US W": 18, "UK": 15.5, "EU": 51},
                    {"US M": 17, "US W": 18.5, "UK": 16, "EU": 51.5},
                    {"US M": 17.5, "US W": 19, "UK": 16.5, "EU": 52},
                    {"US M": 18, "US W": 19.5, "UK": 17, "EU": 52.5},
                    {"US M": 18.5, "US W": 20, "UK": 17.5, "EU": 53},
                    {"US M": 19, "US W": 20.5, "UK": 18, "EU": 53.5},
                    {"US M": 19.5, "US W": 21, "UK": 18.5, "EU": 54},
                    {"US M": 20, "US W": 21.5, "UK": 19, "EU": 54.5},
                    {"US M": 20.5, "US W": 22, "UK": 19.5, "EU": 55},
                    {"US M": 21, "US W": 22.5, "UK": 20, "EU": 55.5},
                    {"US M": 21.5, "US W": 23, "UK": 20.5, "EU": 56},
                    {"US M": 22, "US W": 23.5, "UK": 21, "EU": 56.5},
                ]
        }

        msg = f"Shoe size **{region}** **{shoe_size}** Matches:\n\n"

        for sizes in size_table[brand]:
            if (region, shoe_size) in sizes.items():
                del sizes[region]

                for s_region in sizes:
                    msg += f"{s_region}: {sizes[s_region]}\n"

                msg += "\n"

        msg += "\nWork in Progress Command"
        await ctx.respond(msg)


def setup(bot):
    bot.add_cog(Shoes(bot))

