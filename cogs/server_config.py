import asyncio
import copy
import json
import discord
from datetime import datetime
from discord.ext.commands import command, Cog, group
from cogs.utils import ez_utils, perms
from cogs.utils.logger import Logger
from discord import (
    User,
    Embed,
    Member,
    TextChannel,
    Message,
    DMChannel
)
from discord_components import (
    # DiscordComponents,
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)
from typing import List, Union


class Menu:
    def __init__(self,
                 bot: discord.Client,
                 channel: Union[TextChannel, DMChannel],
                 user: Union[User, Member],
                 initial_text: Union[str, Embed],
                 initial_options: Union[list, type(None)],  # Union[List[Union[Button, Select]], type(None)],
                 message: Message,
                 message_listener: bool = True
                 ):
        self.bot = bot
        self.channel = channel
        self.user = user
        self.message = message
        self.text = initial_text
        self.options = initial_options

        self.message_count = 0
        self.repost_at_next_chance = False

        self.last_change_timestamp = datetime.utcnow().timestamp()

        if message_listener:
            self.message_listener = self.bot.add_listener(self.__message_counter, "on_message")
        else:
            self.message_listener = None

    async def start(self) -> bool:
        try:
            if isinstance(self.text, str):
                await self.message.edit(content=self.text, embed=None, components=self.options)
            elif isinstance(self.text, Embed):
                await self.message.edit(content=None, embed=self.text, components=self.options)
            self.last_change_timestamp = datetime.utcnow().timestamp()
            return True
        except TypeError:  # only really occurs during testing just after bot (re)start
            return False

    async def update(self, menu_text: Union[str, Embed], menu_options: list):  # List[Union[Button, Select]]):
        self.text = menu_text
        self.options = menu_options
        await self.repost_if_necessary()
        await self.start()

    async def wait_for_response(self) -> Union[str, list, None]:
        def check(res: Interaction):
            return res.channel.id == self.channel.id \
                   and res.user.id == self.user.id \
                   and res.message.id == self.message.id

        timeout_time = 60

        tasks = [self.bot.wait_for("select_option", check=check),  # , timeout=timeout_time),
                 self.bot.wait_for("button_click", check=check)]  # , timeout=timeout_time)]

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=timeout_time)

            for future in pending:
                future.cancel()

            for completed in done:
                interaction = completed.result()
                if interaction:
                    if isinstance(interaction, Interaction):
                        await interaction.respond(type=6)

                        comp = interaction.component
                        print(comp)

                        if isinstance(comp, Select):
                            # select options
                            new_ids = []
                            for option in interaction.values:
                                try:
                                    new_ids.append(int(option))
                                except ValueError:
                                    print("Non int in list")
                                    pass
                            return new_ids
                        elif isinstance(comp, Button):
                            # button
                            return comp.custom_id
            return None  # if we haven't returned by this point then we probably timed out
        except asyncio.TimeoutError:
            # timed out
            return None

    async def __message_counter(self, message):
        if message.channel.id == self.channel.id:
            self.message_count += 1
            if self.message_count >= 2:
                self.repost_at_next_chance = True

    async def repost_if_necessary(self, force_repost: bool = False):
        if self.repost_at_next_chance or (force_repost and self.message_count >= 1):
            await self.message.delete()
            self.message = await self.channel.send("_ _")
            await self.start()

            self.message_count = 0
            self.repost_at_next_chance = False

    async def end(self, silent: bool = False):
        if silent is False:
            if self.message_count >= 1:
                await self.message.delete()
                await self.channel.send("Menu Closed (either due to timeout or being exited)")
            else:
                await self.message.edit(content="Menu Closed (either due to timeout or being exited)",
                                        components=[],
                                        embed=None)
        else:
            await self.message.delete()
        if self.message_listener:
            self.bot.remove_listener(self.__message_counter, "on_message")


def get_menu(menu_list: List[Menu], channel: Union[int, discord.TextChannel]) -> Union[Menu, type(None)]:
    """search menu list for a menu in channel, return menu or none if it exists or not"""
    if isinstance(channel, int):
        # find from channel id
        for menu in menu_list:
            if menu.channel.id == channel:
                return menu
    elif isinstance(channel, discord.TextChannel):
        # find from channel
        for menu in menu_list:
            if menu.channel.id == channel.id:
                return menu
    return None


class ServerSetup(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_message = "No selection made within 60 seconds"
        self.menus: List[Menu] = []

    def clear_setting(self, server_id: str, settings_category: str, setting: str):
        old_setting = self.bot.servers_config[server_id][settings_category][setting]
        if old_setting is None or old_setting == []:
            # already clear
            return
        else:
            if isinstance(old_setting, list):
                null = []
            elif isinstance(old_setting, int):
                null = None
            else:
                return

            self.bot.servers_config[server_id][settings_category][setting] = null
            # self.bot.update_server_json()
            return

    async def dynamic_menu(self, ctx, menu_select_options_list: List[SelectOption],
                           placeholder_text: str,
                           message_text: str,
                           max_values: int = None,
                           accept_button: bool = False,
                           accept_button_disabled: bool = False,
                           clear_button: bool = False,
                           clear_button_disabled: bool = False):
        """setup menu and return results"""
        if max_values is None:
            max_values = len(menu_select_options_list)

        button_cancel = Button(style=ButtonStyle.red, label="Cancel", custom_id="menu_cancel")
        button_accept = Button(style=ButtonStyle.green, label="Accept", custom_id="menu_accept",
                               disabled=accept_button_disabled)
        button_clear = Button(style=ButtonStyle.red, label="Clear Setting", custom_id="menu_clear",
                              disabled=clear_button_disabled)

        buttons = [button_cancel]

        if accept_button:
            buttons.append(button_accept)
        if clear_button:
            buttons.append(button_clear)

        options = [Select(placeholder=placeholder_text,
                          min_values=0, max_values=max_values,
                          options=menu_select_options_list),
                   buttons]

        menu = get_menu(self.menus, ctx.channel)
        if menu is None:
            msg = await ctx.channel.send("_ _")
            menu = Menu(bot=self.bot, channel=ctx.channel, user=ctx.message.author, initial_text=message_text,
                        initial_options=options, message=msg)
            await menu.start()
            self.menus.append(menu)
        else:
            await menu.update(menu_text=message_text, menu_options=options)

        res = await menu.wait_for_response()
        if isinstance(res, str):
            if res == button_cancel.custom_id:
                return None
            else:
                return res
        elif isinstance(res, list):
            return res
        elif isinstance(res, type(None)):
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
        setting_cleared = False

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

            elif isinstance(inner_value, type(None)):
                if config_before[top_setting] is not None:
                    setting_cleared = True

        def get_name_or_mention(check_id: int):
            if setting_type == "categories":
                try:
                    return ctx.guild.get_channel(check_id).name
                except AttributeError:
                    return None  # "<#{}>".format(check_id)
            elif setting_type == "channels":
                try:
                    return ctx.guild.get_channel(check_id).mention
                except AttributeError:
                    return None  # "<#{}>".format(check_id)
            elif setting_type == "roles":
                try:
                    return ctx.guild.get_role(check_id).name
                except AttributeError:
                    return None  # "<@&{}>".format(check_id)
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
            output.add_field(name="Changed {}".format(setting_category),
                             value="Set to {}".format(new_bool_value))

        if setting_cleared is True:
            output.add_field(name="Setting Cleared",
                             value="{} {} was cleared.".format(normal_setting, normal_category))

        if len(output.fields) == 0:
            # if len(removed_id) == 0 and len(added_id) == 0 and len(changed_id) == 0 and new_bool_value is None:
            return discord.Embed(title="Setting unchanged",
                                 description="{} {}\nNo change were made".format(normal_setting, normal_category),
                                 colour=discord.Colour.dark_purple())
        return output

    async def boolean_updater(self, ctx, settings_category: str, setting: str, ask_text: str):
        config = copy.deepcopy(self.bot.servers_config[str(ctx.guild.id)][settings_category])
        options = [[Button(style=ButtonStyle.green, label="Yes", custom_id="yes"),
                    Button(style=ButtonStyle.red, label="No", custom_id="no")]]

        menu = get_menu(self.menus, ctx.channel)
        if menu is None:
            msg = await ctx.channel.send("_ _")
            menu = Menu(bot=self.bot, channel=ctx.channel, user=ctx.message.author, initial_text=ask_text,
                        initial_options=options, message=msg)
            await menu.start()
            self.menus.append(menu)
        else:
            await menu.update(menu_text=ask_text, menu_options=options)

        res = await menu.wait_for_response()
        if res is None:
            return None
        elif res == "yes":
            self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = True
        elif res == "no":
            self.bot.servers_config[str(ctx.guild.id)][settings_category][setting] = False

        self.bot.update_server_json()
        await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                self.bot.servers_config[str(ctx.guild.id)][settings_category]))
        return

    async def continue_checker(self, ctx, ask_continue_text: str):
        options = [[Button(style=ButtonStyle.green, label="Yes", custom_id="yes"),
                    Button(style=ButtonStyle.red, label="No", custom_id="no")]]

        menu = get_menu(self.menus, ctx.channel)
        if menu is None:
            msg = await ctx.channel.send("_ _")
            menu = Menu(bot=self.bot, channel=ctx.channel, user=ctx.message.author, initial_text=ask_continue_text,
                        initial_options=options, message=msg)
            await menu.start()
            self.menus.append(menu)
        else:
            await menu.update(menu_text=ask_continue_text, menu_options=options)

        res = await menu.wait_for_response()
        if res is None:
            return False
        elif res == "yes":
            return True
        elif res == "no":
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

        clear_button_disabled = False
        if config[setting] is None:
            clear_button_disabled = True

        res = await self.dynamic_menu(ctx, categories_selects,
                                      "Select category",
                                      "Select the category the desired channel is in (60s timeout)",
                                      max_values=1,
                                      clear_button=True,
                                      clear_button_disabled=clear_button_disabled)

        if res is None:
            return
        if res == "menu_clear":
            self.clear_setting(str(ctx.guild.id), settings_category, setting)
            self.bot.update_server_json()
            await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                    self.bot.servers_config[str(ctx.guild.id)][settings_category]))
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
                                       max_values=1,
                                       clear_button=True,
                                       clear_button_disabled=clear_button_disabled)
        if res2 is None:
            return
        if res2 == "menu_clear":
            self.clear_setting(str(ctx.guild.id), settings_category, setting)
            self.bot.update_server_json()
            await ctx.send(embed=self.updated_embed(ctx, settings_category, setting, config,
                                                    self.bot.servers_config[str(ctx.guild.id)][settings_category]))
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
            if res2 == "menu_accept":
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

    @command(hidden=True)
    @perms.is_dev()
    async def menus(self, ctx):
        """debugging menus"""
        await ctx.send(len(self.menus))
        for menu in self.menus:
            await ctx.send("menu in channel {} by user {}".format(menu.channel, menu.user))

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
        menu = get_menu(self.menus, ctx.channel)
        if menu is None:
            msg = await ctx.send("_ _")
            menu = Menu(bot=self.bot, channel=ctx.channel, user=ctx.message.author,
                        initial_text="Starting up menu...", initial_options=None, message=msg)
            if await menu.start():
                self.menus.append(menu)
            else:
                await menu.end()
                return
        else:
            await ez_utils.reply_then_delete(
                "{}, a menu is already running.".format(ctx.message.author.mention),
                menu.message, time=20)
            return

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

            await menu.update(menu_text="Select a settings type to change (60s timeout)",
                              menu_options=[settings_buttons, [back_button_disabled, exit_button]])

            menu_resp = await menu.wait_for_response()
            if menu_resp is None or menu_resp == exit_button.custom_id:
                await menu.end()
                self.menus.remove(menu)
                break
            sub_menu_type = menu_resp

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

            await menu.update(menu_text="Select {} Sub Setting (60s timeout)".format(sub_menu_type),
                              menu_options=[sub_settings_buttons, [back_button, exit_button]])
            sub_resp = await menu.wait_for_response()
            if sub_resp is None or sub_resp == exit_button.custom_id:
                await menu.end()
                self.menus.remove(menu)
                break
            elif sub_resp == back_button:
                continue

            for sub_setting in sub_settings:
                if sub_setting.name == sub_resp:
                    await sub_setting.__call__(ctx)

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
                                Logger.write(f"Couldn't find category with id '{value}'\nError: {e}", print_log=True)
                                continue
                        normal_inner_value = ", ".join(names_list)
                    elif list_of == "channels":
                        mention_list = []
                        for value in inner_value:
                            try:
                                mention_list.append(ctx.guild.get_channel(value).mention)
                            except AttributeError as e:
                                Logger.write(f"Couldn't find channel with id '{value}'\nError: {e}", print_log=True)
                                continue
                        normal_inner_value = ", ".join(mention_list)
                    elif list_of == "roles":
                        mention_list = []
                        for value in inner_value:
                            try:
                                mention_list.append(ctx.guild.get_role(value).mention)
                            except AttributeError as e:
                                Logger.write(f"Couldn't find role with id '{value}'\nError: {e}", print_log=True)
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

    @set.group(invoke_without_command=True, enabled=False)
    @perms.is_admin()
    async def invites(self, ctx):
        """Invite filter related settings"""
        await self.bot.show_cmd_help(ctx)

    @invites.command(name="channel", enabled=False)
    @perms.is_admin()
    async def invites_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "invites", "log", "Select the channel to log invites to (60s timeout)")
        return

    @invites.command(name="categories", enabled=False)
    @perms.is_admin()
    async def invites_categories(self, ctx):
        await self.category_updater(ctx, "invites", "ignore_categories",
                                    "Set Categories to ignore invite links in (60s timeout)")

    @invites.command(name="roles", enabled=False)
    @perms.is_admin()
    async def invites_roles(self, ctx):
        await self.role_updater(ctx, "invites", "ignore_roles",
                                "Set roles to ignore invite links from (60s timeout)")

    @set.group(invoke_without_command=True, enabled=False)
    @perms.is_admin()
    async def tracking(self, ctx):
        """Tracking related settings"""
        await self.bot.show_cmd_help(ctx)

    @tracking.command(enabled=False)
    @perms.is_admin()
    async def track(self, ctx):
        await self.boolean_updater(ctx, "tracking", "last_message",
                                   "Enable tracking? (60s timeout)")

    @tracking.command(name="categories", enabled=False)
    @perms.is_admin()
    async def tracking_categories(self, ctx):
        await self.category_updater(ctx, "tracking", "ignore_categories",
                                    "Select categories to be ignored by tracking (60s timeout)")

    @set.group(invoke_without_command=True, name="anti-raid", enabled=False)
    @perms.is_admin()
    async def anti_raid(self, ctx):
        """Anti-raid related settings"""
        await self.bot.show_cmd_help(ctx)

    @anti_raid.command(name="categories", enabled=False)
    @perms.is_admin()
    async def lockdown_categories(self, ctx):
        await self.category_updater(ctx, "anti-raid", "lockdown_categories",
                                    "Select categories enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="roles", enabled=False)
    @perms.is_admin()
    async def lockdown_roles(self, ctx):
        await self.role_updater(ctx, "anti-raid", "lockdown_roles",
                                "Select roles to enforce lockdown on during lockdowns (60s timeout)")

    @anti_raid.command(name="channels", enabled=False)
    @perms.is_admin()
    async def lockdown_channels(self, ctx):
        await self.channels_updater(ctx, "anti-raid", "lockdown_channels", "Select channels (60s timeout)")

    @anti_raid.command(name="caution", enabled=False)
    @perms.is_admin()
    async def lockdown_caution(self, ctx):
        await self.boolean_updater(ctx, "anti-raid", "caution",
                                   "Cautious booting? (Yes = Kick, No = Ban) (60s timeout)")

    @set.group(invoke_without_command=True, enabled=False)
    @perms.is_admin()
    async def logging(self, ctx):
        """Logging related settings"""
        await self.bot.show_cmd_help(ctx)

    @logging.command(name="join-leave", enabled=False)
    @perms.is_admin()
    async def join_leave_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "logging", "join_leave_log",
                                          "Select the channel to log joins and leaves to (60s timeout)")

    @logging.command(name="kick-ban", enabled=False)
    @perms.is_admin()
    async def kick_ban_log_channel(self, ctx):
        await self.single_channel_updater(ctx, "logging", "kick_ban_log",
                                          "Select the channel to log kicks, bans and unbans to (60s timeout)")


def setup(bot):
    bot.add_cog(ServerSetup(bot))
