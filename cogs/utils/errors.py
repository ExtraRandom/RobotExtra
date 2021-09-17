from discord.ext import commands
# import discord


class WrongGuild(commands.CheckFailure):
    pass


class DevOnly(commands.CheckFailure):
    pass


class ProtectedCog(Exception):
    pass

