from discord.ext import commands
from cogs.utils import time_formatting as timefmt, IO
from datetime import datetime
from cogs.utils import perms
from cogs.utils.autocomplete import autocomplete
import discord
import requests
import numpy


class Shoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_ids = []

    shoes = discord.commands.SlashCommandGroup("shoes", "Shoe Related Commands",
                                               guild_ids=[223132558609612810])   # 956806641892859904,

    class ShoeModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            # [Text](Link)
            self.add_item(discord.ui.InputText(label="Shoe SKU"))
            self.add_item(discord.ui.InputText(label="Tracking URL"))
            self.add_item(discord.ui.InputText(label="Price Paid / Likely Sell Price"))
            self.add_item(discord.ui.InputText(label="Notes", style=discord.InputTextStyle.long))
            self.add_item(discord.ui.InputText(label="Image URL"))

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(title="Shoe info")
            embed.add_field(name="Shoe SKU", value=self.children[0].value)
            embed.add_field(name="Tracking URL", value=self.children[1].value)
            embed.add_field(name="Price Paid / Likely Sell Price", value=self.children[2].value)
            embed.add_field(name="Notes", value=self.children[3].value)
            embed.set_thumbnail(url=self.children[4].value)
            await interaction.response.send_message(embeds=[embed])

    @shoes.command(name="embed")
    async def shoe_modal_embed(self, ctx, shoe_sku: discord.Option(str, "Shoe SKU Number")):
        """WIP - Shoe Embed creator via Modal"""
        modal = self.ShoeModal(title="Shoe embed creator")
        await ctx.send_modal(modal)
        await ctx.respond("👍", ephemeral=True)

    """
    https://github.com/druv5319/Sneaks-API/blob/master/scrapers/stockx-scraper.js
    https://stockx.com/api/products/air-jordan-1-mid-ice-blue-ps?includes=market
    
    https://github.com/druv5319/Sneaks-API/blob/master/models/Sneaker.js
    
    https://github.com/matthew1232/stockx-api/blob/master/src/api/scrapers/fetchproductdetails.js
    https://github.com/matthew1232/stockx-api/blob/master/src/api/scrapers/searchproducts.js
    """

    async def brands_autocomplete(self, ctx: discord.AutocompleteContext):
        return await autocomplete(ctx, ['Nike'])

    async def size_region_autocomplete(self, ctx: discord.AutocompleteContext):
        return await autocomplete(ctx, ['UK', 'US M', 'US W', 'EU'])

    async def regional_size_autocomplete(self, ctx: discord.AutocompleteContext):
        region = ctx.options["region"]
        sizes = []

        if region == "UK":
            sizes = numpy.arange(3, 21, 0.5).tolist()

        elif region == "US M":
            sizes = numpy.arange(3.5, 22, 0.5).tolist()

        elif region == "US W":
            sizes = numpy.arange(5, 23.5, 0.5).tolist()

        elif region == "EU":
            sizes = numpy.arange(35.5, 56.5, 0.5).tolist()

        return await autocomplete(ctx, sizes)

    @shoes.command(name="size")
    async def shoe_size_conversion(self,
                                   ctx: discord.ApplicationContext,
                                   # brand: discord.Option(
                                   #    str,
                                   #    "Shoe Brand to get sizes for",
                                   #    autocomplete=brands_autocomplete
                                   # ),
                                   region: discord.Option(
                                       str,
                                       "Region of size to convert from",
                                       autocomplete=size_region_autocomplete
                                   ),
                                   shoe_size: discord.Option(
                                       float,
                                       "Shoe Size",
                                       autocomplete=regional_size_autocomplete
                                   )):
        """WIP - Shoe size converter"""

        """
        Nike
        - Mens https://www.nike.com/gb/size-fit/mens-footwear
        - Womens https://www.nike.com/gb/size-fit/womens-footwear
        - Unisex https://www.nike.com/gb/size-fit/unisex-footwear-mens-based
        - https://www.nike.com/gb/size-fit/kids-footwear
        """
        brand = "Nike"
        size_table = {
            "Nike":
                [
                    {"US M": 3.5, "US W": 5, "UK": 3, "EU": 35.5},
                    {"US M": 4, "US W": 5.5, "UK": 3.5, "EU": 36},
                    {"US M": 4.5, "US W": 6, "UK": 4, "EU": 36.5},
                    {"US M": 5, "US W": 6.5, "UK": 4.5, "EU": 37.5},
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

        shoe_size = round(shoe_size * 2) / 2  # rounded to nearest half int
        if region == "UK":
            if 3 > shoe_size: shoe_size = 3
            elif shoe_size > 21: shoe_size = 21
        elif region == "US M":
            if 3.5 > shoe_size: shoe_size = 3.5
            elif shoe_size > 22: shoe_size = 22
        elif region == "US W":
            if 5 > shoe_size: shoe_size = 5
            elif shoe_size > 23.5: shoe_size = 23.5
        elif region == "EU":
            if 35.5 > shoe_size: shoe_size = 35.5
            elif shoe_size > 56.5: shoe_size = 56.5

        msg = f"Shoe size **{region}** **{shoe_size}** Matches:\n\n"

        for sizes in size_table[brand]:
            if (region, shoe_size) in sizes.items():
                del sizes[region]

                for s_region in sizes:
                    msg += f"{s_region}: {sizes[s_region]}\n"

                msg += "\n"

        msg += "\nWork in Progress Command"
        await ctx.respond(msg)

    @shoes.command(name="stockx_payout")
    async def stockx_payout(self,
                            ctx: discord.ApplicationContext,
                            price: discord.Option(
                                float,
                                "Sell Price"
                            )):
        """Payout Estimate"""
        payment_processing = price * 0.03
        if price < 70:
            transaction_fee = 7
        else:
            transaction_fee = price * 0.1
        shipping = 4

        fees = payment_processing + transaction_fee + shipping
        payout = price - fees

        embed = discord.Embed(title="Stockx Payout Estimate")
        embed.colour = discord.Colour.dark_green()
        embed.add_field(name=f"Payout: £{round(payout, 2)}",
                        value=f"*Handling Fees: £{round(transaction_fee, 2)}\n"
                              f"Payment Processing: £{round(payment_processing, 2)}\n"
                              f"Shipping: £{round(shipping, 2)}\n"
                              f"Fees Total: £{round(fees, 2)}*")
        embed.set_footer(text="This is an estimate, the actual payout may vary")
        await ctx.respond(embed=embed)

    @shoes.command(name="laced_payout")
    async def laced_payout(self,
                           ctx: discord.ApplicationContext,
                           price: discord.Option(
                               float,
                               "Sell Price"
                           )):
        """Payout Estimate"""
        payment_processing = price * 0.03
        handling_fee = price * 0.12
        shipping = 6.99

        fees = payment_processing + handling_fee + shipping
        payout = price - fees

        embed = discord.Embed(title="Laced Payout Estimate")
        embed.colour = discord.Colour.light_gray()
        embed.add_field(name=f"Payout: £{round(payout, 2)}",
                        value=f"*Handling Fees: £{round(handling_fee, 2)}\n"
                              f"Payment Processing: £{round(payment_processing, 2)}\n"
                              f"Shipping: £{round(shipping, 2)}\n"
                              f"Fees Total: £{round(fees, 2)}*")
        embed.set_footer(text="This is an estimate, the actual payout may vary")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Shoes(bot))
