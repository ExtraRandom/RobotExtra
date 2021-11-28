from discord.ext import commands


class WrongGuild(commands.CheckFailure):
    pass


class ProtectedCog(Exception):
    pass

