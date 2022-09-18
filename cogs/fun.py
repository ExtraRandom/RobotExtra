from discord.ext import commands
import discord
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="8ball")
    async def eight_ball(self, ctx, question: discord.Option(str, "Question for the Eight Ball", required=False)):
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
        await ctx.respond(response)

    @commands.slash_command(name="pick")
    async def pick_random(self, ctx,
                          first_option: discord.Option(str, "The first option to pick from", required=True),
                          second_option: discord.Option(str, "The second option to pick from", required=True),
                          third_option: discord.Option(str, "The third option to pick from", required=False),
                          fourth_option: discord.Option(str, "The fourth option to pick from", required=False),
                          fifth_option: discord.Option(str, "The fifth option to pick from", required=False),
                          sixth_option: discord.Option(str, "The sixth option to pick from", required=False),
                          seventh_option: discord.Option(str, "The seventh option to pick from", required=False),
                          eighth_option: discord.Option(str, "The eighth option to pick from", required=False),
                          ninth_option: discord.Option(str, "The ninth option to pick from", required=False),
                          tenth_option: discord.Option(str, "The tenth option to pick from", required=False),
                          ):
        """Pick something from given options"""

        choice_list = [first_option, second_option]
        if third_option is not None:
            choice_list.append(third_option)

        if fourth_option is not None:
            choice_list.append(fourth_option)

        if fifth_option is not None:
            choice_list.append(fifth_option)

        if sixth_option is not None:
            choice_list.append(sixth_option)

        if seventh_option is not None:
            choice_list.append(seventh_option)

        if eighth_option is not None:
            choice_list.append(eighth_option)

        if ninth_option is not None:
            choice_list.append(ninth_option)

        if tenth_option is not None:
            choice_list.append(tenth_option)

        random.seed()
        await ctx.respond("{}".format(random.choice(choice_list)))


def setup(bot):
    bot.add_cog(Fun(bot))
