import json
import discord
from discord.ext.commands import command, Cog, group
from cogs.utils import ez_utils, perms
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    InteractionType
)
from asyncio import TimeoutError
from typing import List


class ServerSetup(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_message = "No selection made within 60 seconds"

    async def dynamic_menu(self, ctx, menu_select_options_list: List[SelectOption],
                           placeholder_text: str,
                           message_text: str,
                           max_values: int = None):
        """setup menu and return results"""
        if max_values is None:
            max_values = len(menu_select_options_list)
        message = await ctx.send(message_text,
                                 components=[Select(placeholder=placeholder_text,
                                                    max_values=max_values,
                                                    options=menu_select_options_list)])

        def check(res):
            return ctx.author == res.user and res.channel == ctx.channel

        try:
            resp = await self.bot.wait_for("select_option", check=check, timeout=60)
            await resp.respond(type=InteractionType.DeferredUpdateMessage)
            await message.delete()

            new_ids = []
            for comp in resp.component:
                new_ids.append(int(comp.value))
            return new_ids

        except TimeoutError:
            await message.delete()
            await ctx.send(self.timeout_message)
            return None

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

    async def boolean_updater(self, ctx, settings_category: str, setting: str, ask_text: str):
        options = [[Button(style=ButtonStyle.green, label="Yes", custom_id="yes"),
                    Button(style=ButtonStyle.red, label="No", custom_id="no")]]

        msg = await ctx.send(content=ask_text,
                             components=options)

        def check(res):
            return ctx.author == res.user and res.channel == ctx.channel

        try:
            resp = await self.bot.wait_for("button_click", check=check, timeout=60)
            await resp.respond(type=InteractionType.DeferredUpdateMessage)
            enable = resp.component.custom_id
            await msg.delete()

            if enable == "yes":
                self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = True
                set_v = True
            else:
                self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = False
                set_v = False
            self.bot.update_server_json()
            await ctx.send("Set {} {} to {}".format(settings_category, setting, set_v))
        except TimeoutError:
            await ctx.send(self.timeout_message)
            return

    async def continue_checker(self, ctx, ask_continue_text: str):
        options = [[Button(style=ButtonStyle.green, label="Yes", custom_id="yes"),
                    Button(style=ButtonStyle.red, label="No", custom_id="no")]]

        msg = await ctx.send(content=ask_continue_text,
                             components=options)

        def check(res):
            return ctx.author == res.user and res.channel == ctx.channel

        try:
            resp = await self.bot.wait_for("button_click", check=check, timeout=60)
            await resp.respond(type=InteractionType.DeferredUpdateMessage)
            enable = resp.component.custom_id
            await msg.delete()

            if enable == "yes":
                return True
            else:
                return False
        except TimeoutError:
            await ctx.send(self.timeout_message)
            return False

    async def category_updater(self, ctx, settings_category: str, setting: str, setting_text: str,
                               max_values: int = None):
        config = self.bot.servers_config[str(ctx.guild.id)][settings_category]
        categories = ctx.guild.categories
        categories_selects = []
        for category in categories:
            if category.id in config[setting]:
                enabled = True
            else:
                enabled = False
            first_channel = category.channels[0]
            categories_selects.append(SelectOption(label=category.name[:25],
                                                   value=category.id,
                                                   default=enabled,
                                                   description="First channel name: {}".format(first_channel)))

        res = await self.dynamic_menu(ctx, categories_selects,
                                      "Select Categories",
                                      setting_text,
                                      max_values=max_values)
        if res is not None:
            self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = res
            self.bot.update_server_json()
            await ctx.send("Updated {} {}".format(settings_category, setting))

    async def role_updater(self, ctx, settings_category: str, setting: str, setting_text: str):
        config = self.bot.servers_config[str(ctx.guild.id)][settings_category]
        roles = ctx.guild.roles
        role_selects = []
        for role in roles:
            if role.is_integration() or role.is_bot_managed():
                continue
            if role.name == "@everyone":
                continue
            if role.permissions != role.permissions.none():
                if role.id in config[setting]:
                    enabled = True
                else:
                    enabled = False

                role_selects.append(SelectOption(label=role.name,
                                                 value=role.id,
                                                 default=enabled,
                                                 description="{} members have this role".format(len(role.members))))

        res = await self.dynamic_menu(ctx, role_selects,
                                      "Select Roles",
                                      setting_text)
        if res is not None:
            self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = res
            self.bot.update_server_json()
            await ctx.send("Updated {} {}".format(settings_category, setting))

    async def single_channel_updater(self, ctx, settings_category: str, setting: str,
                                     setting_text: str):
        categories = ctx.guild.categories
        categories_selects = []
        for category in categories:
            list_channels = []
            for channel in category.channels:
                list_channels.append(channel.name)
            channels = ", ".join(list_channels)
            channels = channels[:50]
            categories_selects.append(SelectOption(label=category.name[:25],
                                                   value=category.id,
                                                   description=channels))

        res = await self.dynamic_menu(ctx, categories_selects,
                                      "Select category",
                                      "Select the category the desired channel is in (60s timeout)",
                                      max_values=1)

        if res is None:
            return

        category_id = res[0]
        category_channels = []

        for category in categories:
            if category_id == category.id:
                category_channels = category.text_channels

        channel_selects = []
        for channel in category_channels:
            if channel.topic is None:
                topic = "No topic set"
            else:
                topic = channel.topic[:50]
            channel_selects.append(SelectOption(label=channel.name[:25],
                                                value=channel.id,
                                                description=topic))

        res2 = await self.dynamic_menu(ctx, channel_selects,
                                       "Select channel",
                                       setting_text,
                                       max_values=1)
        if res2 is None:
            return
        channel_id = res2[0]
        channel_final = None
        for channel in category_channels:
            if channel_id == channel.id:
                channel_final = channel

        self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = channel_final.id
        self.bot.update_server_json()
        await ctx.send("{} has been set as the {} {} channel".format(channel_final.mention, settings_category, setting))

    async def channels_updater(self, ctx, settings_category: str, setting: str,
                               setting_text: str):
        selected_channels = []
        continue_loop = True
        while continue_loop:
            categories = ctx.guild.categories
            categories_selects = []
            for category in categories:
                list_channels = []
                for channel in category.channels:
                    list_channels.append(channel.name)
                channels = ", ".join(list_channels)
                channels = channels[:50]
                categories_selects.append(SelectOption(label=category.name[:25],
                                                       value=category.id,
                                                       description=channels))

            res = await self.dynamic_menu(ctx, categories_selects,
                                          "Select category",
                                          "Select the category the desired channel is in (60s timeout)",
                                          max_values=1)

            if res is None:
                return

            category_id = res[0]
            category_channels = []

            for category in categories:
                if category_id == category.id:
                    category_channels = category.text_channels

            channel_selects = []
            for channel in category_channels:
                if channel.topic is None:
                    topic = "No topic set"
                else:
                    topic = channel.topic[:50]
                channel_selects.append(SelectOption(label=channel.name[:25],
                                                    value=channel.id,
                                                    description=topic))

            res2 = await self.dynamic_menu(ctx, channel_selects,
                                           "Select channel",
                                           setting_text,
                                           max_values=None)
            if res2 is None:
                return
            channel_ids = res2
            for channel in category_channels:
                if channel.id in channel_ids:
                    if channel in selected_channels:
                        selected_channels.remove(channel)
                    else:
                        selected_channels.append(channel)

            selected_msg = ""
            if len(selected_channels) == 0:
                selected_msg = "No channels"
            else:
                for channel in selected_channels:
                    selected_msg += "{} ".format(channel.mention)

            continue_loop = await self.continue_checker(ctx,
                                                        "Channels: {}- are currently selected, continue adding? "
                                                        "(60s timeout)".format(selected_msg))

        selected_ids = []
        channel_final_msg = ""
        for channel in selected_channels:
            selected_ids.append(channel.id)
            channel_final_msg += "{} ".format(channel.mention)
        self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = selected_ids
        self.bot.update_server_json()
        await ctx.send("{}have been set as the {} {} channels".format(channel_final_msg, settings_category, setting))

    @group(name="set", invoke_without_command=True)
    async def set(self, ctx):
        """Set server config values"""
        await self.bot.show_cmd_help(ctx)

    @set.command()
    async def menu(self, ctx):
        menu_loop = True
        while menu_loop:
            settings_buttons = []
            settings = list(ctx.command.cog.get_commands()[0].commands)
            settings.sort(key=lambda x: x.name)
            for setting in settings:
                if setting.name in ["show", "jsonset", "menu"]:
                    continue
                else:
                    settings_buttons.append(Button(style=ButtonStyle.green,
                                                   custom_id=setting.name,
                                                   label=str(setting.name).capitalize()))

            def check(res):
                return ctx.author == res.user and res.channel == ctx.channel

            main_menu = await ctx.send("Select a settings type to change (60s timeout)",
                                       components=[settings_buttons])
            try:
                resp = await self.bot.wait_for("button_click", check=check, timeout=60)
                await resp.respond(type=InteractionType.DeferredUpdateMessage)
                sub_menu_type = resp.component.custom_id
            except TimeoutError:
                await ctx.send(self.timeout_message)
                return

            sub_settings = None
            for setting in settings:
                if setting.name == sub_menu_type:
                    sub_settings = list(setting.commands)
                    sub_settings.sort(key=lambda x: x.name)

            sub_settings_buttons = []
            for sub_setting in sub_settings:
                sub_settings_buttons.append(Button(style=ButtonStyle.green,
                                                   custom_id=sub_setting.name,
                                                   label=str(sub_setting.name).capitalize()))

            await main_menu.edit("Select {} Sub Setting (60s timeout)".format(sub_menu_type),
                                 components=[sub_settings_buttons])

            try:
                resp = await self.bot.wait_for("button_click", check=check, timeout=60)
                await resp.respond(type=InteractionType.DeferredUpdateMessage)
                cmd = resp.component.custom_id
                await main_menu.delete()
            except TimeoutError:
                await ctx.send(self.timeout_message)
                return

            for sub_setting in sub_settings:
                if sub_setting.name == cmd:
                    await sub_setting.__call__(ctx)

            menu_loop = await self.continue_checker(ctx, "Continue editing server configuration? (60s timeout)")

    # TODO update to be an embed, normalise the ids to mentions and just sorta make it look nice
    @set.command()
    @perms.is_dev()
    async def show(self, ctx):
        await ctx.send("```json\n{}\n```".format(json.dumps(self.bot.servers_config[str(ctx.guild.id)], indent=4)))

    @set.command(enabled=False, hidden=True)
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
    async def channel(self, ctx):
        await self.single_channel_updater(ctx, "invites", "log", "Select the channel to log invites to (60s timeout)")
        return

    @invites.command(name="categories")
    async def invites_categories(self, ctx):
        await self.role_updater(ctx, "invites", "ignore_categories",
                                "Set Categories to ignore invite links in (60s timeout)")

    @invites.command(name="roles")
    async def roles_set(self, ctx):
        await self.role_updater(ctx, "invites", "ignore_roles",
                                "Set roles to ignore invite links from (60s timeout)")

    @set.group(invoke_without_command=True)
    async def tracking(self, ctx):
        """Tracking related settings"""
        await self.bot.show_cmd_help(ctx)

    @tracking.command()
    async def track(self, ctx):
        await self.boolean_updater(ctx, "track", "last_message",
                                   "Enable tracking? (60s timeout)")

    @tracking.command(name="categories")
    async def tracking_categories(self, ctx):
        await self.category_updater(ctx, "tracking", "ignore_categories",
                                    "Select categories to be ignored by tracking (60s timeout)")

    @set.group(invoke_without_command=True, name="anti-raid")
    async def anti_raid(self, ctx):
        """Anti-raid related settings"""
        await self.bot.show_cmd_help(ctx)

    @anti_raid.command(name="categories")
    async def lockdown_categories(self, ctx):
        await self.category_updater(ctx, "anti-raid", "lockdown_categories",
                                    "Select categories enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="roles")
    async def lockdown_roles(self, ctx):
        await self.role_updater(ctx, "anti-raid", "lockdown_roles",
                                "Select roles to enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="channels")
    async def lockdown_channels(self, ctx):
        await self.channels_updater(ctx, "anti-raid", "lockdown_channels", "Select channels (60s timeout)")

    @anti_raid.command(name="caution")
    async def lockdown_caution(self, ctx):
        await self.boolean_updater(ctx, "anti-raid", "caution",
                                   "Cautious booting? (Yes = Kick, No = Ban) (60s timeout)")

    @set.group(invoke_without_command=True)
    async def logging(self, ctx):
        """Logging related settings"""
        await self.bot.show_cmd_help(ctx)

    @logging.command(name="join-leave")
    async def join_leave_log(self, ctx):
        await self.single_channel_updater(ctx, "logging", "join_leave_log",
                                          "Select the channel to log joins and leaves to (60s timeout)")

    @logging.command(name="kick-ban")
    async def kick_ban_log(self, ctx):
        await self.single_channel_updater(ctx, "logging", "kick_ban_log",
                                          "Select the channel to log kicks, bans and unbans to (60s timeout)")


def setup(bot):
    bot.add_cog(ServerSetup(bot))
