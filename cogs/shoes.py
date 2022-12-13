from discord.ext import commands
from cogs.utils import IO
from cogs.utils.autocomplete import autocomplete
import discord


class Shoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_ids = []

    debug = IO.fetch_from_settings("testing", "debug")
    if debug is True:
        shoes = discord.commands.SlashCommandGroup("shoes", "Shoe Related Commands",
                                                   guild_ids=[223132558609612810])   # 956806641892859904,
    else:
        shoes = discord.commands.SlashCommandGroup("shoes", "Shoe Related Commands",
                                                   guild_ids=[956806641892859904, 223132558609612810])

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
        return await autocomplete(ctx, ['Nike Men', 'Nike Women', 'Nike GS', 'Nike PS', 'Nike TD'])

    @shoes.command(name="size")
    async def shoe_size_conversion(self,
                                   ctx: discord.ApplicationContext,
                                   brand: discord.Option(
                                       str,
                                       "Shoe Brand to get sizes for",
                                       autocomplete=brands_autocomplete,
                                       required=True
                                   ),
                                   ):
        """Shoe sizes"""
        if brand == "Nike Men":
            size_us = [6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13,
                       13.5, 14, 15]
            size_eu = [38.5, 39, 40, 40.5, 41, 42, 42.5, 43, 44, 44.5, 45, 45.5, 46, 47,
                       47.5, 48, 48.5, 49.5]
            size_uk = [5.5, 6, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12,
                       12.5, 13, 13.5]
        elif brand == "Nike Women":
            size_us = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12]
            size_eu = [35.5, 36, 36.5, 37.5, 38, 38.5, 39, 40, 40.5, 41, 42, 42.5, 43,
                       44, 44.5]
            size_uk = [2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5]
        elif brand == "Nike GS":
            size_us = [3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]
            size_eu = [35, 36, 36.5, 37.5, 38, 38.5, 39, 40]
            size_uk = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5]
        elif brand == "Nike PS":
            size_us = ["10.5C", "11C", "11.5C", "12C", "12.5C", "13C", "13.5C", "1Y",
                       "1.5Y", "2Y", "2.5Y", "3Y"]
            size_eu = [27.5, 28, 28.5, 29.5, 30, 31, 31.5, 32, 33, 33.5, 34, 35]
            size_uk = [10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 1, 1.5, 2, 2.5]
        elif brand == "Nike TD":
            size_us = ["2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C"]
            size_eu = [17, 18.5, 19.5, 21, 22, 23.5, 25, 26, 27]
            size_uk = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
        else:
            await ctx.respond("Invalid Brand Given")  # todo more helpful error
            return

        msg = f"```{str('UK'):10s}{str('US'):10s}{str('EU'):10s}\n"
        for size in range(len(size_us)):
            msg += f"{str(size_uk[size]):10s}{str(size_us[size]):10s}{str(size_eu[size]):10s}"

            if size is not len(size_us) - 1:
                msg += "\n"
        msg += "```"

        embed = discord.Embed(title=f"{brand} Sizes")
        embed.add_field(name="\u200b", value=msg)
        embed.set_footer(text="Work in Progress Command")

        await ctx.respond(embed=embed)

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
