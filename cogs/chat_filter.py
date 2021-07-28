from discord.ext import commands
from cogs.utils import ez_utils
from datetime import datetime
from typing import List, Union
import discord
import re


class ChatWarning:
    def __init__(self, *, user: Union[discord.User, discord.Member]):
        self.user = user
        self.warn_time = datetime.utcnow().timestamp()


class ChatFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.regex = r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)" \
                     "\/([a-zA-Z0-9]+)"

        self.warns: List[ChatWarning] = []

        self.warning_delete_time = 20

    async def on_message(self, message):
        if message.author.bot is True:
            return

        if type(message.channel) == discord.DMChannel:
            return

        gid = str(message.guild.id)
        config = self.bot.servers_config[gid]

        log_channel = config['invites']['log']
        ignore_channels = config['invites']['ignore_channels']
        ignore_roles = config['invites']['ignore_roles']
        ignore_categories = config['invites']['ignore_categories']

        if log_channel is not None:
            invites = re.findall(self.regex, message.content)

            if len(invites) == 0:
                return
            else:
                ignore_roles_as_roles = []
                log = message.guild.get_channel(log_channel)
                for role in ignore_roles:
                    ignore_roles_as_roles.append(message.guild.get_role(role))

                if message.channel.category_id in ignore_categories \
                    or message.channel.id in ignore_channels \
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
                        # another bot deleted the message as part of its spam filter, but lets warn the user anyways
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

                    warn = ChatWarning(user=message.author)

                    async def send_warn():
                        await message.author.send(
                            "Your message in {} was deleted because it contains a discord invite.\n"
                            "This is against the rules and has been logged."
                            "".format(message.guild.name))
                        await ez_utils.send_then_delete("{} your message was deleted as it contained a "
                                                        "discord invite.\n"
                                                        "This is against the server rules.\n"
                                                        "This message will self delete in {} seconds."
                                                        "".format(message.author.mention,
                                                                  self.warning_delete_time),
                                                        message.channel,
                                                        time=self.warning_delete_time)

                    for old_warning in self.warns:
                        if warn.warn_time > old_warning.warn_time + self.warning_delete_time:
                            self.warns.remove(old_warning)

                    def get_warn(check_warn: ChatWarning):
                        for warning in self.warns:
                            if warning.user == check_warn.user:
                                return warning
                        return None

                    if len(self.warns) > 0:
                        old_warning = get_warn(warn)
                        if old_warning is None:
                            self.warns.append(warn)
                            await send_warn()
                            return

                    else:
                        self.warns.append(warn)
                        await send_warn()
                        return


def setup(bot):
    b = ChatFilter(bot)
    bot.add_cog(b)
    bot.add_listener(b.on_message, "on_message")
