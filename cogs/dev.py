import discord.ext.commands
from discord.ext import commands
from cogs.utils import perms, errors, ez_utils


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="command", invoke_without_command=True, aliases=['cmd'])
    @perms.is_dev()
    async def command_group(self, ctx):
        """Command management"""
        await self.bot.show_cmd_help(ctx)
        # await ctx.send("cmd")

    @command_group.command()
    @perms.is_dev()
    async def disable(self, ctx, *, command_name: str):
        """Disable a command"""
        res = self.command_enabled(False, command_name)
        if res == True:
            await ctx.send("Command '{}' disabled".format(command_name))
        else:
            await ctx.send(res)

    @command_group.command()
    @perms.is_dev()
    async def enable(self, ctx, command_name: str):
        """Enable a command"""
        res = self.command_enabled(True, command_name)
        if res == True:
            await ctx.send("Command '{}' enabled".format(command_name))
        else:
            await ctx.send(res)

    """
    @command_group.command()
    @perms.is_dev()
    async def hide(self, ctx, command_name: str):
        " ""hides a command in the help menu" ""
        await ctx.send("wip\n{}".format(command_name))

    @command_group.command(aliases=['unhide'])
    @perms.is_dev()
    async def show(self, ctx, command_name: str):
        " ""shows a command in the help menu" ""
        await ctx.send("wip\n{}".format(command_name))

    @command_group.command()
    @perms.is_dev()
    async def permission(self, ctx, permission_name: str):
        " ""adds check (permission) to a command" ""
        await ctx.send("wip\n{}".format(permission_name))
    """

    def command_enabled(self, enabled: bool, command_name: str):
        if enabled is True:
            word = "enabled"
        else:
            word = "disabled"

        try:
            cmd = self.get_command(command_name)
        except errors.ProtectedCog:
            return "Can't disable commands from protected cogs"

        if cmd is None:
            return "Command '{}' not found, include the parent command if its a subcommand.".format(command_name)

        if cmd.enabled == enabled:
            return "Command '{}' is already {}".format(command_name, word)

        # cmd.update(enabled=enabled)  # breaks the command

        self.bot.remove_command(cmd.name)
        cmd.enabled = enabled
        self.bot.add_command(cmd)

        return True

    def get_command(self, command_name: str):
        cmd = self.bot.get_command(command_name)

        if cmd is None:
            return None
        else:
            if cmd.cog_name == "Dev" or cmd.cog_name == "CogManagement":
                raise errors.ProtectedCog()
            return cmd


def setup(bot):
    bot.add_cog(Dev(bot))


