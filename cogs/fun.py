from discord.ext import commands
from cogs.utils import perms
import discord
import random
import json
import os
import re


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

    @commands.command()
    async def ship(self, ctx, first=None, *, second=None):
        pattern = "(?<=\<@!)(.*?)(?=\>)"
        ids = []

        if first is not None:
            is_first_a_mention = re.search(pattern, first)  # returns either id or none
            if is_first_a_mention is not None:
                first_mem = ctx.message.guild.get_member(int(is_first_a_mention[0]))
                first = first_mem.display_name
                ids.append(first_mem.id)

        if second is not None:
            is_second_a_mention = re.search(pattern, second)  # returns either id or none
            if is_second_a_mention is not None:
                second_mem = ctx.message.guild.get_member(int(is_second_a_mention[0]))
                second = second_mem.display_name
                ids.append(second_mem.id)

        if second is None and first is not None:
            second = first
            first = ctx.author.display_name
            ids.append(ctx.author.id)

        if first is None:  # then second is also none
            first = ctx.author.display_name
            ids.append(ctx.author.id)

            all_members = ctx.message.guild.members
            non_bot_members = []
            for member in all_members:
                if member.bot:
                    continue
                non_bot_members.append(member)

            random.seed()
            rndmem = random.randint(0, len(non_bot_members) - 1)
            second = non_bot_members[rndmem].display_name

        ship_name = str(first)[:len(first) // 2] + str(second)[len(second) // 2:]

        first_value = 0
        for f_char in first.lower():
            first_value += ord(f_char)

        second_value = 0
        for s_char in second.lower():
            second_value += ord(s_char)

        value = int(str(first_value + second_value)[-2:])

        if 92562410493202432 in ids and 287420218651967518 in ids:
            value = 100

        await ctx.send("{}\n"
                       ":small_red_triangle_down:{}\n"
                       ":small_red_triangle:{}\n"
                       "{}%".format(ship_name, first, second, value))
        # :heartpulse:


def setup(bot):
    bot.add_cog(Fun(bot))
