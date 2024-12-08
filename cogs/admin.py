from discord.ext import commands
from datetime import datetime
from cogs.utils import perms
from cogs.utils import time_formatting as timefmt, ez_utils
from cogs.utils.logger import Logger
import discord
import re
import os


def user_info_embed(target: discord.Member):
    name = str(target)
    if target.nick:
        name += " (aka '{}')".format(target.nick)

    result = discord.Embed(title="",
                           description="[Avatar]({}) - {} - {}".format(target.avatar.url, target.mention,
                                                                       target.colour),
                           colour=target.colour)
    result.set_author(name="{}".format(name), icon_url=target.avatar.url)

    role_list = target.roles
    roles = []
    for role in role_list:
        if role.name == "@everyone":
            continue
        roles.append(role.mention)

    roles.reverse()

    if len(roles) != 0:
        result.add_field(name="Roles",
                         value="{}".format(" ".join(roles)))
    else:
        result.add_field(name="Roles",
                         value="No Roles")

    result.add_field(name="Created Account at:",
                     value="{}\n({} ago)".format(str(target.created_at).split(".")[0],
                                                 timefmt.time_ago(target.created_at, brief=True)))

    result.add_field(name="Joined Server at:",
                     value="{}\n({} ago)".format(str(target.joined_at).split(".")[0],
                                                 timefmt.time_ago(target.joined_at, brief=True)))

    result.set_footer(text="ID: {}".format(target.id))
    result.timestamp = datetime.utcnow()

    return result


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(
        name="Steal Emoji",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def emoji_please(self, ctx, message):
        """Steal emoji from a message"""
        await ctx.defer()
        custom_emojis = re.findall(r'<\w*:\w*:\d*>', message.content)
        custom_emojis = list(dict.fromkeys(custom_emojis))

        if len(custom_emojis) >= 25:
            await ctx.respond("Message contains too many emojis. (26 or more)")
            return

        result = discord.Embed(title="Emojis found in message")

        if len(custom_emojis) > 0:
            for emote in custom_emojis:
                file_type = "png"
                is_animated = str(emote.split(":")[0]).replace("<", "")
                if len(is_animated) != 0:
                    file_type = "gif"
                emoji_id = str(emote.split(":")[-1]).replace(">", "")
                link = "<https://cdn.discordapp.com/emojis/{}.{}?v=1>".format(emoji_id, file_type)
                result.add_field(name="{}".format(str(emote.split(":")[-2])),
                                 value="[Link]({})".format(link))

            await ctx.respond(embed=result)
        else:
            await ctx.respond(content="Selected message contains no custom emoji.", ephemeral=True)

    @commands.slash_command(name="info")
    async def info_slash_command(self, ctx,
                                 user: discord.Option(discord.Member, "Member to get info of", required=True)):
        """Show a user's info"""
        await ctx.defer()
        result = user_info_embed(user)

        await ctx.respond(embed=result)

    @commands.user_command(name="User Info")
    async def info_user_command(self, ctx, user: discord.Member):
        await ctx.defer()
        target = user

        if target is None:
            await ctx.send("Couldn't find that user")
            return

        result = user_info_embed(target)

        await ctx.respond(embed=result)

    @commands.slash_command()
    @commands.has_permissions(administrator=True)
    async def log(self, ctx):
        """Get the latest log file"""
        await ctx.defer()
        log_file = os.path.join(ez_utils.base_directory(), "logs", Logger.get_filename())
        await ctx.author.send(file=discord.File(log_file))
        await ctx.respond("Check your DMs :D")


def setup(bot):
    bot.add_cog(Admin(bot))
