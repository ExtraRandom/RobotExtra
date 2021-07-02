from discord.ext import commands
from datetime import datetime
# from cogs.utils import perms, IO
# from cogs.utils.logger import Logger
from cogs.utils import time_formatting as timefmt
import discord
import re
from cogs.utils import ez_utils
from time import time


class ChatFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.regex = r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)" \
                     "\/([a-zA-Z0-9]+)"

        self.log_channel = 860513900994232372

        self.ignore_channels = []
        self.ignore_categories = [750690307191865445, 750974763249172482]  # SERVER, STAFF
        # self.ignore_categories = [] # testing
        # self.ignore_roles = []  # testing
        self.ignore_roles = [765458196365967370]
        self.warning_delete_time = 20
        self.last_warning_time = 0

    async def on_message(self, message):
        if message.author.bot is True:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if message.guild.id == 750689226382901288:  # and message.channel.id == 766644856524636170: testing
            invites = re.findall(self.regex, message.content)

            if len(invites) is 0:
                return
            else:
                ignore_roles_as_roles = []
                log = message.guild.get_channel(self.log_channel)
                for role in self.ignore_roles:
                    ignore_roles_as_roles.append(message.guild.get_role(role))

                if message.channel.category_id in self.ignore_categories \
                    or message.channel.id in self.ignore_channels \
                        or any(role in message.author.roles for role in ignore_roles_as_roles):

                    await log.send(embed=ez_utils.quick_embed(
                        title="Invite Detected",
                        description="Message has not been deleted",
                        fields=[
                            ("Not deleted", "This invite was not deleted"),
                            ("Sender", "{} ({})".format(message.author, message.author.mention)),
                            ("Message Contents", message.content),
                            ("Channel", "{} ({})".format(message.channel.name, message.channel.mention))
                        ],
                        colour=discord.Colour.purple(),
                        timestamp=True
                    ))
                    return

                else:
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        # yag deleted the message as part of the spam filter, but lets warn the user anyways
                        pass

                    await log.send(embed=ez_utils.quick_embed(
                        title="Invite Detected",
                        description="Message has been deleted",
                        fields=[
                            ("Sender", "{} ({})".format(message.author, message.author.mention)),
                            ("Message Contents", message.content),
                            ("Channel", "{} ({})".format(message.channel.name, message.channel.mention))
                        ],
                        timestamp=True
                    ))

                    await message.author.send("Your message in {} was deleted because it contains a discord invite.\n"
                                              "This is against the rules and has been logged."
                                              "".format(message.guild.name))

                    if time() > self.last_warning_time + 20:
                        self.last_warning_time = time()
                        await ez_utils.send_then_delete("{} your message was deleted as it contained a "
                                                        "discord invite.\n"
                                                        "This is against the server rules.\n"
                                                        "This message will self delete in {} seconds."
                                                        "".format(message.author.mention, self.warning_delete_time),
                                                        message.channel,
                                                        time=self.warning_delete_time)


def setup(bot):
    b = ChatFilter(bot)
    bot.add_cog(b)
    bot.add_listener(b.on_message, "on_message")

