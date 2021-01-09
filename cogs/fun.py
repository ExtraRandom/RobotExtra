from discord.ext import commands
import discord
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        response = "\n**My Response is:** {}".format(random.choice(answers))
        await ctx.reply(response)


def setup(bot):
    bot.add_cog(Fun(bot))

