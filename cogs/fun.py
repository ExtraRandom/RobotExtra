from discord.ext import commands
import discord
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        answers = [
            "No",
            "Yes",
            "Maybe",
            "Perhaps",
            "Yeah!",
            "Nope!"
        ]

        random.seed()
        response = "\n**My Response is:** {}".format(random.choice(answers))
        await ctx.reply(response)


def setup(bot):
    bot.add_cog(Fun(bot))

