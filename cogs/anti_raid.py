import discord
from discord.ext.commands import command, Cog, group
from cogs.utils import perms
from datetime import datetime


class AntiRaid(Cog):
    def __init__(self, bot):
        self.bot = bot

    @group(invoke_without_command=True)
    @perms.is_admin()
    async def raid(self, ctx):
        """Info about the anti raid commands"""
        await self.bot.show_cmd_help(ctx, True)

    @raid.command(name="name")
    @perms.is_admin()
    async def anti_raid_name_kick(self, ctx, *, name_filter: str):
        """Kick new members from the last few hours with the given string in their name
        Must be more than 5 characters long"""
        if len(name_filter) <= 5:
            await ctx.send("Name filter too small (5 characters or less)")
            return
        limit = 2
        await ctx.send("Booting members with '{}' in their name who joined within the last {} hours"
                       "".format(name_filter, limit))

        now = datetime.utcnow().timestamp()
        all_members = ctx.message.guild.members

        for member in all_members:
            if member.bot:
                continue

            if member.joined_at.timestamp() >= now - (limit * 60 * 60):
                if name_filter in member.name:
                    await self.kick_or_ban(str(ctx.guild.id), member)
        await ctx.send("Finished. (Note that depending on how many people were booted, "
                       "the logs may take a while to catch up.")

    @raid.command(name="time")
    @perms.is_admin()
    async def anti_raid_time_kick(self, ctx, *, minutes=5):
        """Kick all new members who joined within the given time
        Defaults to 5 minutes if no time given
        Max time is 30 minutes"""
        limit = 30
        if minutes > limit:
            await ctx.send("Time input must be {} minutes or less.".format(limit))
            return

        now = datetime.utcnow().timestamp()

        for member in ctx.message.guild.members:
            if member.bot:
                continue
            if member.joined_at.timestamp() >= now - (minutes * 60):
                await self.kick_or_ban(str(ctx.guild.id), member)

        await ctx.send("Finished. (Note that depending on how many people were booted, "
                       "the logs may take a while to catch up.")

    async def kick_or_ban(self, server_id, member):
        caution = self.bot.servers_config[server_id]['anti-raid']['caution']
        if caution:
            await member.kick(reason="Kicked by ExtraBot Anti-Raid")
        else:
            await member.ban(reason="Banned by ExtraBot Anti-Raid")
        return

    @raid.command()
    @perms.is_admin()
    async def lockdown(self, ctx, *, enable: str):
        """Lockdowns the server as set in the config

          Inputs:
        y/yes/true/enable = Enable Lockdown
        n/no/false/disable = Disable Lockdown"""
        enable = enable.lower()
        if enable in ["yes", "y", "true", "enable"]:
            activate = False
        elif enable in ["no", "n", "false", "disable"]:
            activate = True
        else:
            await self.bot.show_cmd_help(ctx)
            return

        config = self.bot.servers_config[str(ctx.guild.id)]['anti-raid']
        if len(config['lockdown_categories']) == 0 and len(config['lockdown_roles']) == 0:
            await ctx.send("No lockdown categories or lockdown roles have been set.")
            return
        elif len(config['lockdown_categories']) == 0:
            await ctx.send("No lockdown categories have been set.")
            return
        elif len(config['lockdown_roles']) == 0:
            await ctx.send("No lockdown roles have been set.")
            return

        ids_categories = config['lockdown_categories']
        ids_roles = config['lockdown_roles']
        ids_channels = config['lockdown_channels']

        # Fetch list of roles to enforce lockdown on
        roles = []
        for role_id in ids_roles:
            role = ctx.guild.get_role(role_id)
            if role is not None:
                roles.append(role)
            else:
                await ctx.send("Failed to find role with id '{}'".format(role_id))

        if len(roles) == 0:
            await ctx.send("Failed to fetch any roles with the ids set in the configs, cancelling lockdown.")
            return

        # Lockdown Categories
        for category_id in ids_categories:
            category = ctx.guild.get_channel(category_id)

            for role in roles:
                overwrites = category.overwrites_for(role)
                overwrites.send_messages = activate
                await category.set_permissions(role, overwrite=overwrites)

        # Lockdown individual channels
        for channel_id in ids_channels:
            channel = ctx.guild.get_channel(channel_id)

            for role in roles:
                overwrites = channel.overwrites_for(role)
                overwrites.send_messages = activate
                await channel.set_permissions(role, overwrite=overwrites)


def setup(bot):
    bot.add_cog(AntiRaid(bot))
