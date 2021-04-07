from discord.ext import commands
from cogs.utils import perms
import discord
import random
import json
import os


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fortune(self, ctx):
        """Fortune Cookie"""
        # https://github.com/larryprice/fortune-cookie-api/tree/master/data]
        folder = os.path.join(self.bot.base_directory, "cogs", "data", "fortune",)
        path = os.path.join(folder, "proverbs.json")

        with open(path, "r") as f:
            r_data = f.read()
            data = json.loads(r_data)
        random.seed()
        proverb = random.choice(list(data.keys()))

        numbers = []
        for i in range(6):
            numbers.append(random.randrange(1, 60))
        numbers = sorted(numbers)

        img = discord.File(os.path.join(folder, "cookie.png"), filename="image.png")
        resp = discord.Embed(title="{}".format(proverb),
                             description="Lucky Lotto Numbers: {}".format(" ".join(str(x) for x in numbers)))
        resp.set_author(name="Your Fortune...",
                        icon_url="attachment://image.png")
        await ctx.reply(embed=resp, file=img)

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        """It's a ~magic~ 8 ball"""
        answers = [
            # Affirmative answers (10)
            "Yes - definitely", "Yes", "Most likely", "Signs point to yes", "As I see it, yes",
            "It is certain", "It is decidedly so", "Without a doubt", "You may rely on it", "Outlook good" 
            
            # Non-committal answers (5) 
            "Reply hazy, try again", "Ask again later", "Better not tell you now", "Cannot predict now",
            "Concentrate and ask again",

            # Negative answers (5)
            "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"
        ]
        random.seed()
        response = "**My Response is:** {}".format(random.choice(answers))
        await ctx.reply(response)

    @commands.command(name="pick", aliases=["choose", "choice", "select"])
    async def pick_random(self, ctx, *, choices: str):
        """Pick a random choice

        Separate choices with commas"""

        choice_list = []

        if len(choices.split(",")) > 1:
            splitter = ","
        else:
            splitter = " "

        if len(choices.split(splitter)) <= 1:
            await ctx.reply("Requires 2 or more choices to pick from")
            return
        else:
            for choice in choices.split(splitter):
                choice_list.append(choice)

        random.seed()
        await ctx.reply("{}".format(random.choice(choice_list)))

    @commands.command(enabled=False)
    @perms.is_dev()
    async def ship(self, ctx, first=None, second=None):

        print(type(first), type(second))

        if second is None and first is not None:
            second = first
            first = ctx.author.display_name

        if first is None:  # then second is also none
            first = ctx.author.display_name
            second = "random user"

        ship_name = str(first)[:len(first) // 2] + str(second)[len(second) // 2:]
        # print(ship_name)

        # print(first, second)
        first_value = 0
        for f_char in first.lower():
            first_value += ord(f_char)
        # print(first_value)

        second_value = 0
        for s_char in second.lower():
            second_value += ord(s_char)
        # print(second_value)
        # print(first_value + second_value)

        value = int(str(first_value + second_value)[-2:])

        await ctx.send("{}\n"
                       ":small_red_triangle_down:{}\n"
                       ":small_red_triangle:{}\n"
                       "{}%".format(ship_name, first, second, value))
        # :heartpulse:


def setup(bot):
    bot.add_cog(Fun(bot))
