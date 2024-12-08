from discord.ext import commands
import datetime
from cogs.utils import IO, errors, ez_utils
from cogs.utils.logger import Logger
import discord
import traceback
import os
import time

"""
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("default")
"""


def testing_check():
    data = IO.read_settings_as_json()
    
    if data is None:
        print("No settings file, Debug Guilds Off")
        return []
    else:
        try:
            if data["testing"]["debug"] is True:
                print("Debug Guilds On")
                return data["testing"]["ids"]
            else:
                print("Debug Guilds Off")
                return []
        except KeyError:
            print("Key Error, Debug Guilds Off")
            return []


class RobotExtra(commands.Bot):
    def __init__(self):
        self.start_time = None
        self.reconnect_time = None

        d_intents = discord.Intents.all()

        super().__init__(debug_guilds=testing_check(),
                         description="Bot Developed by @Extra_Random#2564\n"
                                     "Source code: https://github.com/ExtraRandom/RobotExtra",
                         intents=d_intents,
                         command_prefix=commands.when_mentioned)

    async def on_ready(self):
        self.reconnect_time = datetime.datetime.now(datetime.UTC)
        login_msg = "Bot Connected at {} UTC".format(str(self.reconnect_time))
        Logger.log_write("----------------------------------------------------------\n"
                         "{}\n"
                         "".format(login_msg))
        print(login_msg)

    async def on_message(self, message):
        bot_msg = message.author.bot
        if bot_msg is True:
            return

        await self.process_commands(message)

    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, exception: discord.DiscordException
    ) -> None:
        cmd = ctx.command

        if isinstance(exception, commands.errors.CheckFailure):
            await ctx.respond(content="You do not have permission to use this command.", ephemeral=True)
            return

        else:
            err = traceback.format_exception(type(exception), exception, exception.__traceback__)
            Logger.write(err, True)
            try:
                await ctx.respond("**Error in '{}' Command!**\n"
                                  "{}\n"
                                  "See the log for more details".format(cmd.name, exception))
            except discord.NotFound:
                pass
            return

    async def on_command_error(
            self, ctx: discord.ext.commands.Context, error: discord.DiscordException
    ) -> None:
        channel = ctx.message.channel
        cmd = ctx.command

        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await self.show_cmd_help(ctx)
            return
        elif isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("The command '{}' is currently disabled.".format(cmd.name))
            return
        elif isinstance(error, commands.CheckFailure):
            if type(error) == errors.WrongGuild:
                await ctx.send("This command can not be used in this server.")
            elif type(error) == discord.ext.commands.NoPrivateMessage:
                await ctx.send("This command can only be used in servers.")
            elif type(error) == discord.ext.commands.PrivateMessageOnly:
                await ctx.send("This command can only be used in DMs.")
            else:
                await channel.send("You do not have permission to use that command!")
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await channel.send("This command is currently on cooldown. {}" 
                               "".format(str(error).split(". ")[1]))
            return
        else:
            err = traceback.format_exception(type(error), error, error.__traceback__)
            Logger.write(err)
            await channel.send("**Error in '{}' Command!**\n"
                               "{}\n"
                               "See the log for more details".format(cmd.name, error))
            return

    @staticmethod
    async def show_cmd_help(ctx, full_doc=False):
        """Show command help for given command"""
        cmd = ctx.command
        cmd_name = cmd.name
        cmd_help = cmd.help
        cmd_sig = cmd.signature
        cmd_dir = dir(ctx.command)
        cmd_aliases = cmd.aliases
        cmd_parent = cmd.full_parent_name

        if cmd_parent:
            msg = "```e?{} {} {}\n\n".format(cmd_parent, cmd_name, cmd_sig)
        else:
            msg = "```e?{} {}\n\n".format(cmd_name, cmd_sig)

        if "commands" in cmd_dir and cmd_help is None:
            cmd_help = "Use with one of the sub commands listed below"
        elif cmd_help is None:
            cmd_help = "No Description Provided"

        msg += "{}\n\n".format(cmd_help)

        if "commands" in cmd_dir:
            if full_doc is False:
                msg += "Subcommands:\n"
            for sub_cmd in cmd.commands:
                if sub_cmd.enabled:
                    if full_doc is False:
                        msg += " {:<12} {:<55}\n".format(sub_cmd.name[:12], sub_cmd.short_doc[:55])
                    else:
                        msg += " e?{} {} {}\n{}\n\n" \
                               "".format(cmd_name, sub_cmd.name[:12], sub_cmd.signature, sub_cmd.help)

        if len(cmd_aliases) > 0:
            msg += "\n\n" \
                   "Aliases: {}".format(",".join(cmd_aliases))

        msg += "```"

        await ctx.send(msg)

    @staticmethod
    def get_cogs_in_folder():
        """Get list of cogs in the cogs folder"""
        c_dir = os.path.dirname(os.path.realpath(__file__))
        c_list = []
        for file in os.listdir(os.path.join(c_dir, "cogs")):
            if file.endswith(".py"):
                c_list.append(file.replace(".py", ""))
        return c_list

    @staticmethod
    def get_cogs_in_settings():
        """Get list of cogs in the settings json cogs section"""
        c_list = []
        data = IO.read_settings_as_json()
        if data is None:
            return None
        for cog in data['cogs']:
            c_list.append(cog)
        return c_list

    @staticmethod
    def ensure_all_fields(settings_data: dict):
        """Ensure settings.json has all the necessary settings"""
        fields = \
            {
                "testing": {
                    "debug": False,
                    "ids": [223132558609612810]
                },
                "keys": {
                    "token": None,
                    "itad_api": None,
                    "youtube_api": None,
                    "rtt_name": None,
                    "rtt_key": None
                },
                "cogs":
                    {
                }
            }
        sd_len = len(settings_data)
        if sd_len == 0:
            settings_data = fields
            return settings_data
        else:
            for top_field in fields:
                if top_field in settings_data:
                    for inner_field in fields[top_field]:
                        if inner_field not in settings_data[top_field]:
                            settings_data[top_field][inner_field] = fields[top_field][inner_field]
                            Logger.write("Settings.json - Added inner field '{}' to category '{}'".format(inner_field,
                                                                                                          top_field))
                else:
                    settings_data[top_field] = {}

                    Logger.write("Settings.json - Added category '{}'".format(top_field))

                    for inner_field in fields[top_field]:
                        if inner_field not in settings_data[top_field]:
                            settings_data[top_field][inner_field] = fields[top_field][inner_field]
                            Logger.write("Settings.json - Added inner field '{}' to category '{}'".format(inner_field,
                                                                                                          top_field))
            return settings_data

    def run(self):
        first_time = False
        s_data = {}

        """First time run check"""
        if os.path.isfile(IO.settings_file_path) is False:
            Logger.write("First Time Run", print_log=True)
            configs_f = os.path.join(ez_utils.base_directory(), "configs")
            if not os.path.exists(configs_f):
                os.mkdir(configs_f)
            first_time = True
        else:
            s_data = IO.read_settings_as_json()
            if s_data is None:
                raise Exception(IO.settings_fail_read)

        s_data = self.ensure_all_fields(s_data)

        """Load cogs"""
        folder_cogs = self.get_cogs_in_folder()
        for folder_cog in folder_cogs:
            cog_path = "cogs.{}".format(folder_cog)
            if first_time is True:
                # noinspection PyTypeChecker
                s_data['cogs'][folder_cog] = True
            else:
                try:
                    should_load = s_data['cogs'][folder_cog]
                except KeyError:
                    Logger.write("New Cog '{}'".format(folder_cog), print_log=True)
                    # noinspection PyTypeChecker
                    s_data['cogs'][folder_cog] = True
                    should_load = True

                if should_load is True:
                    try:
                        self.load_extension(cog_path)
                    except Exception as exc:
                        print("Failed to load cog '{}', Reason: {}".format(folder_cog, type(exc).__name__))
                        Logger.write(exc)
                        # noinspection PyTypeChecker
                        # s_data['cogs'][folder_cog] = False

        """Check for environment variables (docker)"""
        env_token = os.getenv("DISCORD_BOT_TOKEN", default=None)
        if env_token is None:
            if first_time is True:
                if IO.write_settings(s_data) is False:
                    raise Exception(IO.settings_fail_write)
                token = None
            else:
                token = s_data['keys']['token']
        else:
            token = env_token


        """ Read in discord token
        if first_time is True:
            if IO.write_settings(s_data) is False:
                raise Exception(IO.settings_fail_write)
            token = None
        else:
            token = s_data['keys']['token']
        """

        """Clean up removed cogs from settings"""
        r_cogs = self.get_cogs_in_folder()
        f_cogs = self.get_cogs_in_settings()
        for f_cog in f_cogs:
            if f_cog not in r_cogs:
                Logger.write("Cog '{}' no longer exists, removing settings entry".format(f_cog), print_log=True)
                del s_data['cogs'][f_cog]

        """Write settings to file"""
        if IO.write_settings(s_data) is False:
            raise Exception(IO.settings_fail_write)

        if token:
            self.start_time = datetime.datetime.now(datetime.UTC)
            super().run(token)
        else:
            Logger.write("Token is not set! Go to {} and change the token parameter!"
                         "".format(IO.settings_file_path), print_log=True)
            print("Waiting 30 seconds before trying again")
            time.sleep(30)


if __name__ == '__main__':
    the_bot = RobotExtra()
    the_bot.run()
