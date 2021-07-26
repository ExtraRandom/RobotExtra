import asyncio
import copy
import json
import discord
from discord.ext.commands import command, Cog, group
from cogs.utils import ez_utils, perms
from cogs.utils.logger import Logger
from discord_components import (
    DiscordComponents,
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    InteractionType,
    Interaction
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
                           max_values: int = None,
                           accept_button: bool = False,
                           accept_button_disabled: bool = False):
        """setup menu and return results"""
        if max_values is None:
            max_values = len(menu_select_options_list)

        if accept_button:
            buttons = [Button(style=ButtonStyle.red, label="Cancel", custom_id="cancel"),
                       Button(style=ButtonStyle.green, label="Accept", custom_id="accept",
                              disabled=accept_button_disabled)]
        else:
            buttons = [Button(style=ButtonStyle.red, label="Cancel", custom_id="cancel")]

        message = await ctx.send(message_text,
                                 components=[Select(placeholder=placeholder_text,
                                                    min_values=0,
                                                    max_values=max_values,
                                                    options=menu_select_options_list),
                                             buttons])

        def check(res):
            return ctx.author == res.user and res.channel == ctx.channel

        tasks = [self.bot.wait_for("select_option", check=check, timeout=60),
                 self.bot.wait_for("button_click", check=check, timeout=60)]

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for future in pending:
                future.cancel()

            for completed in done:
                interaction = completed.result()
                if interaction:
                    if isinstance(interaction, Interaction):
                        await interaction.respond(type=InteractionType.DeferredUpdateMessage)
                        await message.delete()

                        comp = interaction.component
                        if isinstance(comp, list):
                            # select options
                            new_ids = []
                            for option in comp:
                                new_ids.append(int(option.value))
                            return new_ids
                        elif isinstance(comp, Button):
                            # button
                            button_id = comp.custom_id
                            if button_id == "cancel":
                                return None
                            elif button_id == "accept":
                                return "menu_accept"

            """
            
            resp = await self.bot.wait_for("select_option", check=check, timeout=60)
            await resp.respond(type=InteractionType.DeferredUpdateMessage)
            await message.delete()

            new_ids = []
            if resp.component:
                for comp in resp.component:
                    new_ids.append(int(comp.value))
            return new_ids
            """
        except TimeoutError:
            await message.delete()
            await ctx.send(self.timeout_message)
            return None

    def updated_embed(self, ctx, setting: str, setting_category: str, config_before: dict, config_after: dict):
        try:
            setting_type = setting_category.split("_")[1:][0]
        except IndexError:
            setting_type = setting_category

        normal_setting = self.capitalise_every_word(setting)
        normal_category = self.capitalise_every_word(setting_category, "_")

        output = discord.Embed(title="Setting Updated",
                               description="{} {}".format(normal_setting, normal_category),
                               colour=discord.Colour.purple())

        removed_id = []
        added_id = []
        changed_id = ()
        new_bool_value = None

        for top_setting in config_after:
            inner_value = config_after[top_setting]
            if isinstance(inner_value, list):
                for value in inner_value:
                    if value not in config_before[top_setting]:
                        added_id.append(value)

                for value in config_before[top_setting]:
                    if value not in inner_value:
                        removed_id.append(value)

            elif isinstance(inner_value, bool):
                if inner_value != config_before[top_setting]:
                    new_bool_value = inner_value

            elif isinstance(inner_value, int):
                if inner_value != config_before[top_setting]:
                    changed_id = (inner_value, config_before[top_setting])

        def get_name_or_mention(check_id: int):
            if setting_type == "categories":
                return ctx.guild.get_channel(check_id).name
            elif setting_type == "channels":
                return ctx.guild.get_channel(check_id).mention
            elif setting_type == "roles":
                return ctx.guild.get_role(check_id).name
            return None

        def add_field(field_type: str, ids: List[int]):
            normal_list = []
            for r_id in ids:
                normal_list.append(get_name_or_mention(r_id))
            output.add_field(name="{} {}".format(field_type, setting_type),
                             value="\n".join(normal_list))

        if len(removed_id) > 0:
            add_field("Removed", removed_id)
        if len(added_id) > 0:
            add_field("Added", added_id)
        if len(changed_id) > 0:
            old, new = changed_id
            setting_type = "channels"
            new_mention = get_name_or_mention(new)
            if old is not None:
                old_mention = get_name_or_mention(old)
            else:
                old_mention = "N/A"
            output.add_field(name="Changed {}".format(setting_type),
                             value="Old: {}\nNew: {}".format(new_mention, old_mention))
        if new_bool_value is not None:
            output.add_field(name="Changed {}".format(setting_category), value="Set to {}".format(new_bool_value))

        if len(removed_id) == 0 and len(added_id) == 0 and len(changed_id) == 0 and new_bool_value is None:
            return discord.Embed(title="Setting was set to same value as before",
                                 description="No change to setting",
                                 colour=discord.Colour.dark_purple())
        return output

    async def boolean_updater(self, ctx, settings_category: str, setting: str, ask_text: str):
        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
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
            else:
                self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = False
            self.bot.update_server_json()
            await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                    self.bot.servers_config[str(ctx.guild.id)][settings_category]))
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

        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
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
            await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                    self.bot.servers_config[str(ctx.guild.id)][settings_category]))

    async def role_updater(self, ctx, settings_category: str, setting: str, setting_text: str):
        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
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

                role_selects.append(SelectOption(label=role.name[:25],
                                                 value=role.id,
                                                 default=enabled,
                                                 description="{} members have this role".format(len(role.members))))

        res = await self.dynamic_menu(ctx, role_selects,
                                      "Select Roles",
                                      setting_text)
        if res is not None:
            self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = res
            self.bot.update_server_json()
            await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                    self.bot.servers_config[str(ctx.guild.id)][settings_category]))

    async def single_channel_updater(self, ctx, settings_category: str, setting: str,
                                     setting_text: str):
        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
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
        await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                self.bot.servers_config[str(ctx.guild.id)][settings_category]))

    async def channels_updater(self, ctx, settings_category: str, setting: str,
                               setting_text: str):
        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
        selected_channels = []
        continue_loop = True
        while continue_loop:
            if len(selected_channels) > 0:
                accept_button_disabled = False
            else:
                accept_button_disabled = True
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
                                          max_values=1,
                                          accept_button=True,
                                          accept_button_disabled=accept_button_disabled)

            if res is None:
                return
            if res == "menu_accept":
                break

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
                                           max_values=None,
                                           accept_button=True,
                                           accept_button_disabled=accept_button_disabled)
            if res2 is None:
                return
            if res == "menu_accept":
                break

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
        await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                self.bot.servers_config[str(ctx.guild.id)][settings_category]))

    @staticmethod
    def capitalise_every_word(input_string: str, split_char=" "):
        as_list = input_string.split(split_char)
        output_string = ""
        for word in as_list:
            output_string += "{} ".format(word.capitalize())
        output_string = output_string.strip()  # remove trailing space
        return output_string

    @group(name="set", invoke_without_command=True)
    @perms.is_admin()
    async def set(self, ctx):
        """Set server config values"""
        await self.bot.show_cmd_help(ctx)

    @command()
    @perms.is_admin()
    async def rdebug(self, ctx):
        """list all roles with perms, excluding everyone and bot roles"""
        roles = ctx.guild.roles
        role_list = []
        for role in roles:
            if role.is_integration() or role.is_bot_managed():
                continue
            if role.name == "@everyone":
                continue
            if role.permissions != role.permissions.none():
                role_list.append(role.mention)

        await ctx.send(", ".join(role_list))

    @set.command()
    @perms.is_admin()
    async def menu(self, ctx):
        menu_loop = True
        exit_button = Button(style=ButtonStyle.red, label="Exit", custom_id="menu_exit")
        back_button = Button(style=ButtonStyle.red, label="Back", custom_id="menu_back")
        back_button_disabled = Button(style=ButtonStyle.red, label="Back", disabled=True)
        while menu_loop:
            settings_buttons = []
            settings = list(ctx.command.cog.get_commands()[0].commands)
            settings.sort(key=lambda x: x.name)
            for setting in settings:
                if setting.name in ["show", "jsonset", "menu", "jsonshow"]:
                    continue
                else:
                    settings_buttons.append(Button(style=ButtonStyle.green,
                                                   custom_id=setting.name,
                                                   label=str(setting.name).capitalize()))

            def check(res):
                return ctx.author == res.user and res.channel == ctx.channel

            main_menu = await ctx.send("Select a settings type to change (60s timeout)",
                                       components=[settings_buttons, [back_button_disabled, exit_button]])
            try:
                resp = await self.bot.wait_for("button_click", check=check, timeout=60)
                await resp.respond(type=InteractionType.DeferredUpdateMessage)
                sub_menu_type = resp.component.custom_id
                if sub_menu_type == exit_button.custom_id:
                    await main_menu.delete()
                    return
            except TimeoutError:
                await main_menu.delete()
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
                                 components=[sub_settings_buttons, [back_button, exit_button]])

            try:
                resp = await self.bot.wait_for("button_click", check=check, timeout=60)
                await resp.respond(type=InteractionType.DeferredUpdateMessage)
                cmd = resp.component.custom_id
                await main_menu.delete()
                if cmd == exit_button.custom_id:
                    return
                if cmd == back_button.custom_id:
                    continue
            except TimeoutError:
                await main_menu.delete()
                await ctx.send(self.timeout_message)
                return

            for sub_setting in sub_settings:
                if sub_setting.name == cmd:
                    await sub_setting.__call__(ctx)

            menu_loop = await self.continue_checker(ctx, "Continue editing server configuration? (60s timeout)")

    @set.command()
    @perms.is_admin()
    async def show(self, ctx):
        """Show the current server settings"""
        settings_embed = discord.Embed(title="{} Server Settings".format(ctx.guild.name),
                                       colour=discord.Colour.gold())
        config = self.bot.servers_config[str(ctx.guild.id)]
        for top_setting in config:
            field_name = self.capitalise_every_word(top_setting)
            field_text = ""
            for inner_setting in config[top_setting]:
                field_text += "{}:\n".format(self.capitalise_every_word(inner_setting, "_"))
                inner_value = config[top_setting][inner_setting]
                if isinstance(inner_value, bool):
                    normal_inner_value = str(inner_value)
                elif isinstance(inner_value, type(None)):
                    normal_inner_value = "Not set"
                elif isinstance(inner_value, int):
                    normal_inner_value = "{} ".format(ctx.guild.get_channel(inner_value).mention)
                elif isinstance(inner_value, list):
                    list_of = str(inner_setting).split("_")[1:][0]
                    if len(inner_value) == 0:
                        normal_inner_value = "None set"
                    elif list_of == "categories":
                        names_list = []
                        for value in inner_value:
                            try:
                                names_list.append(ctx.guild.get_channel(value).name)
                            except AttributeError as e:
                                Logger.write_and_print("Couldn't find category with id '{}'".format(value))
                                Logger.write_and_print(e)
                                continue
                        normal_inner_value = ", ".join(names_list)
                    elif list_of == "channels":
                        mention_list = []
                        for value in inner_value:
                            try:
                                mention_list.append(ctx.guild.get_channel(value).mention)
                            except AttributeError as e:
                                Logger.write_and_print("Couldn't find channel with id '{}'".format(value))
                                Logger.write_and_print(e)
                                continue
                        normal_inner_value = ", ".join(mention_list)
                    elif list_of == "roles":
                        mention_list = []
                        for value in inner_value:
                            try:
                                mention_list.append(ctx.guild.get_role(value).mention)
                            except AttributeError as e:
                                Logger.write_and_print("Couldn't find role with id '{}'".format(value))
                                Logger.write_and_print(e)
                                continue
                        normal_inner_value = ", ".join(mention_list)
                    else:
                        normal_inner_value = "Unhandled list of {}".format(list_of)
                else:
                    normal_inner_value = "Unhandled inner type of {}".format(type(inner_value))

                field_text += "{}\n\n".format(normal_inner_value)

            settings_embed.add_field(name=field_name, value=field_text)

        await ctx.send(embed=settings_embed)

    @set.command(enabled=False, hidden=True)
    @perms.is_dev()
    async def jsonshow(self, ctx):
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
    @perms.is_admin()
    async def invites(self, ctx):
        """Invite filter related settings"""
        await self.bot.show_cmd_help(ctx)

    @invites.command(name="channel")
    @perms.is_admin()
    async def invites_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "invites", "log", "Select the channel to log invites to (60s timeout)")
        return

    @invites.command(name="categories")
    @perms.is_admin()
    async def invites_categories(self, ctx):
        await self.category_updater(ctx, "invites", "ignore_categories",
                                    "Set Categories to ignore invite links in (60s timeout)")

    @invites.command(name="roles")
    @perms.is_admin()
    async def invites_roles(self, ctx):
        await self.role_updater(ctx, "invites", "ignore_roles",
                                "Set roles to ignore invite links from (60s timeout)")

    @set.group(invoke_without_command=True)
    @perms.is_admin()
    async def tracking(self, ctx):
        """Tracking related settings"""
        await self.bot.show_cmd_help(ctx)

    @tracking.command()
    @perms.is_admin()
    async def track(self, ctx):
        await self.boolean_updater(ctx, "tracking", "last_message",
                                   "Enable tracking? (60s timeout)")

    @tracking.command(name="categories")
    @perms.is_admin()
    async def tracking_categories(self, ctx):
        await self.category_updater(ctx, "tracking", "ignore_categories",
                                    "Select categories to be ignored by tracking (60s timeout)")

    @set.group(invoke_without_command=True, name="anti-raid")
    @perms.is_admin()
    async def anti_raid(self, ctx):
        """Anti-raid related settings"""
        await self.bot.show_cmd_help(ctx)

    @anti_raid.command(name="categories")
    @perms.is_admin()
    async def lockdown_categories(self, ctx):
        await self.category_updater(ctx, "anti-raid", "lockdown_categories",
                                    "Select categories enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="roles")
    @perms.is_admin()
    async def lockdown_roles(self, ctx):
        await self.role_updater(ctx, "anti-raid", "lockdown_roles",
                                "Select roles to enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="channels")
    @perms.is_admin()
    async def lockdown_channels(self, ctx):
        await self.channels_updater(ctx, "anti-raid", "lockdown_channels", "Select channels (60s timeout)")

    @anti_raid.command(name="caution")
    @perms.is_admin()
    async def lockdown_caution(self, ctx):
        await self.boolean_updater(ctx, "anti-raid", "caution",
                                   "Cautious booting? (Yes = Kick, No = Ban) (60s timeout)")

    @set.group(invoke_without_command=True)
    @perms.is_admin()
    async def logging(self, ctx):
        """Logging related settings"""
        await self.bot.show_cmd_help(ctx)

    @logging.command(name="join-leave")
    @perms.is_admin()
    async def join_leave_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "logging", "join_leave_log",
                                          "Select the channel to log joins and leaves to (60s timeout)")

    @logging.command(name="kick-ban")
    @perms.is_admin()
    async def kick_ban_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "logging", "kick_ban_log",
                                          "Select the channel to log kicks, bans and unbans to (60s timeout)")


def setup(bot):
    bot.add_cog(ServerSetup(bot))
