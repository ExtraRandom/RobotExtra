import json

import discord
from discord.ext.commands import command, Cog, group
from cogs.utils import ez_utils, perms, time_formatting as timefmt
from datetime import datetime


class ServerSetup(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_channel_from_mention(self, ctx, channel_id):
        if channel_id is None:
            return ctx.message.channel
        else:
            try:
                mentions = ctx.message.channel_mentions
                if len(mentions) == 1:
                    return mentions[0]
                elif len(mentions) > 1:
                    return None
            except AttributeError:
                pass

            return None

    @group(name="set", invoke_without_command=True)
    async def set(self, ctx):
        """Set server config values"""
        await self.bot.show_cmd_help(ctx)

    @set.command()
    @perms.is_dev()
    async def show(self, ctx):
        await ctx.send("```json\n{}\n```".format(json.dumps(self.bot.servers_config[str(ctx.guild.id)], indent=4)))

    @set.command()
    @perms.is_dev()
    async def jsonset(self, ctx, *, config_str: str):
        try:
            config_dict = json.loads(config_str)
        except Exception as e:
            await ctx.send(e)
            return

        self.bot.servers_config[str(ctx.guild.id)] = config_dict
        self.bot.update_server_json()
        await ctx.send("updated :D")

    @set.group(invoke_without_command=True)
    async def invites(self, ctx):
        """Invite filter related settings"""
        await self.bot.show_cmd_help(ctx)

    @invites.command()
    async def channel(self, ctx, *, channel_m=None):
        channel = self.get_channel_from_mention(ctx, channel_m)
        if channel is None:
            await ctx.send("'{}' is an invalid channel".format(channel_m))
            return

        self.bot.servers_config[ctx.guild.id]['invites']['log'] = channel.id
        self.bot.update_server_json()

        await ctx.send("Set {} as the invite log channel".format(channel.mention))

    """
    @invites.command()
    async def rolessss(self, ctx, *, roles_m=None):
        roles = ctx.message.role_mentions

    @invites.command(name="roles")
    async def roles_set(self, ctx):
        roles = ctx.guild.roles
        list_roles = []
        for role in roles:
            if role.is_integration() or role.is_bot_managed():
                continue
            if role.permissions != role.permissions.none():
                list_roles.append(role)

        for role in list_roles:
            await ctx.send(role.name())
    """
def setup(bot):
    bot.add_cog(ServerSetup(bot))
