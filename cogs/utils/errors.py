from discord.ext import commands
# import discord


class WrongGuild(commands.CheckFailure):
    pass


class DevOnly(commands.CheckFailure):
    pass


class ProtectedCog(Exception):
    pass


class GuildsOnly(commands.CheckFailure):
    pass


class DMOnly(commands.CheckFailure):
    pass
