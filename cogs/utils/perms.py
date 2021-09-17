from discord.ext import commands
import discord
from cogs.utils import errors


def is_server_owner():
    def predicate(ctx):
        return ctx.message.author.id == ctx.message.channel.guild.owner
    return commands.check(predicate)


def is_dev():
    def predicate(ctx):
        return ctx.message.author.id == 92562410493202432
    return commands.check(predicate)


def is_server_owner_or_dev():
    def predicate(ctx):
        if ctx.message.author.id == ctx.message.channel.guild.owner or ctx.message.author.id == 92562410493202432:
            return True
        else:
            return False
    return commands.check(predicate)


def is_in_somewhere_nice():
    def predicate(ctx):
        if ctx.message.guild.id == 750689226382901288:
            return True
        else:
            raise errors.WrongGuild("Command cannot be used in this server")
    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        return ctx.message.author.guild_permissions.administrator
    return commands.check(predicate)


def is_in_a_server():
    def predicate(ctx):
        if isinstance(ctx.message.channel, discord.DMChannel):
            raise discord.ext.commands.NoPrivateMessage
        else:
            return True
    return commands.check(predicate)


def is_in_dms():
    def predicate(ctx):
        if isinstance(ctx.message.channel, discord.DMChannel):
            return True
        else:
            raise discord.ext.commands.PrivateMessageOnly

    return commands.check(predicate)
