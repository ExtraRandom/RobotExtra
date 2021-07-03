from discord.ext import commands
from datetime import datetime
from cogs.utils import IO, errors
from cogs.utils.logger import Logger
import discord
import traceback
import os
import time

import sqlite3
from sqlite3 import Error


def get_prefix(d_bot, message):
    prefixes = ["e?", "E?"]
    return commands.when_mentioned_or(*prefixes)(d_bot, message)


class SNBot(commands.Bot):
    def __init__(self):
        self.base_directory = os.path.dirname(os.path.realpath(__file__))

        self.start_time = None
        self.reconnect_time = None

        db_path = os.path.join(self.base_directory, "db", "testing.sqlite")
        try:
            s_connection = sqlite3.connect(db_path)  # print("Connected to the DB")
        except Error as e:
            print(f"Error connecting to DB: {e}")
            raise Exception("shits fucked oh dear god please fix")

        self.connection = s_connection

        cursor = self.connection.cursor()
        sql_file = os.path.join(self.base_directory, "db", "schema.sql")
        sql_as_string = open(sql_file).read()

        # print("Running SQL Scheme Script")
        cursor.executescript(sql_as_string)
        # print("Database setup done")

        self.d_intents = discord.Intents.all()

        super().__init__(command_prefix=get_prefix,
                         description="Bot Developed by @Extra_Random#2564\n"
                                     "Source code: https://github.com/ExtraRandom/SNBot",
                         pm_help=False,
                         intents=self.d_intents)

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()  # print("Query executed successfully")
            return True

        except Error as e:
            print(f"Error executing query: {e}")
            return False

    def execute_read_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error executing read query: {e}")
            return None

    def db_quick_read(self, user_id):
        query = """
        SELECT
            *
        FROM
            tracking
        WHERE
            user_id = "{}"
        """.format(user_id)
        res = self.execute_read_query(query)
        return res[0]

    async def on_ready(self):
        self.reconnect_time = datetime.utcnow()
        login_msg = "Bot Connected at {} UTC".format(str(datetime.utcnow()))
        Logger.log_write("----------------------------------------------------------\n"
                         "{}\n"
                         "".format(login_msg))
        print(login_msg)

    async def on_message(self, message):
        bot_msg = message.author.bot
        if bot_msg is True:
            return

        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
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
    async def show_cmd_help(ctx):
        cmd = ctx.command
        cmd_name = cmd.name
        cmd_help = cmd.help
        cmd_sig = cmd.signature
        cmd_dir = dir(ctx.command)
        cmd_aliases = cmd.aliases

        msg = "```e?{} {}\n\n".format(cmd_name, cmd_sig)

        if "commands" in cmd_dir and cmd_help is None:
            cmd_help = "Use with one of the sub commands listed below"
        elif cmd_help is None:
            cmd_help = "No Description Provided"

        msg += "{}\n\n".format(cmd_help)

        if "commands" in cmd_dir:
            msg += "Subcommands:\n"
            for sub_cmd in cmd.commands:
                if sub_cmd.enabled:
                    msg += " {:<12} {:<55}\n".format(sub_cmd.name[:12], sub_cmd.short_doc[:55])

        if len(cmd_aliases) > 0:
            msg += "\n\n" \
                   "Aliases: {}".format(",".join(cmd_aliases))

        msg += "```"

        await ctx.send(msg)

    @staticmethod
    def get_cogs_in_folder():
        c_dir = os.path.dirname(os.path.realpath(__file__))
        c_list = []
        for file in os.listdir(os.path.join(c_dir, "cogs")):
            if file.endswith(".py"):
                c_list.append(file.replace(".py", ""))
        return c_list

    @staticmethod
    def get_cogs_in_settings():
        c_list = []
        data = IO.read_settings_as_json()
        if data is None:
            return None
        for cog in data['cogs']:
            c_list.append(cog)
        return c_list

    @staticmethod
    async def find_member_from_id_or_mention(ctx, user):  # self,
        """Takes message context to check for mentions and user input to check if its an id and returns
        the member object should it find one, or none if it does not"""
        target = None

        if user is None:
            target = ctx.author
        else:
            # Check for mention
            try:
                mentions = ctx.message.mentions
                if len(mentions) == 1:
                    target = mentions[0]
                elif len(mentions) > 1:
                    return None
            except AttributeError:
                pass

            # Check for id
            if target is None:
                try:
                    user_id = int(user)
                    user_find = ctx.message.guild.get_member(user_id)
                    if user_find is not None:
                        target = user_find
                except Exception as e:
                    Logger.write(e)
                    pass

        return target

    @staticmethod
    def ensure_all_fields(settings_data: dict):
        fields = \
            {
                "keys": {
                    "token": None
                },
                "cogs":
                    {

                },
                "reddit":
                    {
                        "username": None,
                        "password": None,
                        "client_id": None,
                        "client_secret": None,
                        "user_agent": None,
                        "post_title": None,
                        "post_url": None
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
                            settings_data[top_field][inner_field] = None
                            Logger.write("Settings.json - Added inner field '{}' to category '{}'".format(inner_field,
                                                                                                          top_field))
                else:
                    settings_data[top_field] = {}

                    Logger.write("Settings.json - Added category '{}'".format(top_field))

                    for inner_field in fields[top_field]:
                        if inner_field not in settings_data[top_field]:
                            settings_data[top_field][inner_field] = None
                            Logger.write("Settings.json - Added inner field '{}' to category '{}'".format(inner_field,
                                                                                                          top_field))

            return settings_data

    def run(self):
        first_time = False
        s_data = {}

        """First time run check"""
        if os.path.isfile(IO.settings_file_path) is False:
            Logger.write_and_print("First Time Run")
            configs_f = os.path.join(self.base_directory, "configs")
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
                    Logger.write_and_print("New Cog '{}'".format(folder_cog))
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
                        s_data['cogs'][folder_cog] = False

        """Read in discord token"""
        if first_time is True:
            if IO.write_settings(s_data) is False:
                raise Exception(IO.settings_fail_write)
            token = None
        else:
            token = s_data['keys']['token']

        """Clean up removed cogs from settings"""
        r_cogs = self.get_cogs_in_folder()
        f_cogs = self.get_cogs_in_settings()
        for f_cog in f_cogs:
            if f_cog not in r_cogs:
                Logger.write_and_print("Cog '{}' no longer exists, removing settings entry".format(f_cog))
                del s_data['cogs'][f_cog]

        """Write settings to file"""
        if IO.write_settings(s_data) is False:
            raise Exception(IO.settings_fail_write)

        if token:
            self.start_time = datetime.utcnow()
            super().run(token)
        else:
            Logger.write_and_print("Token is not set! Go to {} and change the token parameter!"
                                   "".format(IO.settings_file_path))
            print("Waiting 30 seconds before trying again")
            time.sleep(30)


if __name__ == '__main__':
    the_bot = SNBot()
    the_bot.run()
