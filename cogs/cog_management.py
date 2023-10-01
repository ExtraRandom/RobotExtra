from discord.ext import commands
import discord
import os
from cogs.utils import perms, IO, ez_utils
from cogs.utils.logger import Logger
from typing import List


class CogManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    cogs = discord.commands.SlashCommandGroup("cog", "Cog Management Commands")

    async def loadable_cogs(self, ctx):
        all_cogs: List = self.bot.get_cogs_in_folder()
        return all_cogs

    # https://github.com/Pycord-Development/pycord/issues/1630

    #@commands.slash_command(name="cog_load")
    @cogs.command(name="load")
    @perms.is_dev()
    async def load(self, ctx, cog: discord.Option(str,
                                                  "Cog to Load",
                                                  autocomplete=loadable_cogs,
                                                  required=True)):
        """Load a cog"""
        await ctx.defer()

        cog_list = []
        for c_file in os.listdir(os.path.join(ez_utils.base_directory(), "cogs")):
            if c_file.endswith(".py"):
                cog_list.append("cogs.{}".format(c_file.replace(".py", "")))

        l_cog_name = "cogs.{}".format(cog)  # print(cog, cog_name, cog_list)

        if l_cog_name in cog_list:
            try:
                self.bot.load_extension(l_cog_name)
                await ctx.respond("Successfully loaded cog '{}'.".format(cog))
            except Exception as e:
                Logger.write(e)
                await ctx.respond("Failed to load cog '{}'. Reason: {}. \n {}".format(cog, type(e).__name__, e.args))
                return
        else:
            await ctx.respond("No cog called '{}'.".format(cog))
            return

        data = IO.read_settings_as_json()
        if data is None:
            await ctx.send(IO.settings_fail_read)
            return

        data['cogs'][cog] = True

        if IO.write_settings(data) is False:
            await ctx.send(IO.settings_fail_write)
            return

    # @commands.slash_command(name="cog_unload")
    @cogs.command(name="unload")
    @perms.is_dev()
    async def unload(self, ctx, cog: discord.Option(str,
                                                    "Cog to Unload",
                                                    autocomplete=loadable_cogs,
                                                    required=True)):
        """Unload a cog"""
        await ctx.defer()
        ext_list = self.bot.extensions
        cog_list = []
        for cogs in ext_list:
            cog_list.append(cogs)

        l_cog_name = "cogs.{}".format(cog)  # print(cog, cog_name, cog_list)

        if l_cog_name in cog_list:
            try:
                self.bot.unload_extension(l_cog_name)
                await ctx.respond("Successfully unloaded cog '{}'.".format(cog))
            except Exception as e:
                await ctx.respond("Failed to unload cog '{}'. Reason: {}".format(cog, type(e).__name__))
                return
        else:
            await ctx.respond("No loaded cog called '{}'.".format(cog))
            return

        data = IO.read_settings_as_json()
        if data is None:
            await ctx.send(IO.settings_fail_read)
            return
        data['cogs'][cog] = False
        if IO.write_settings(data) is False:
            await ctx.send(IO.settings_fail_write)
            return

    # @commands.slash_command(name="cog_reload")
    @cogs.command(name="reload")
    @perms.is_dev()
    async def reload(self, ctx, cog: discord.Option(str,
                                                    "Cog to Reload",
                                                    autocomplete=loadable_cogs,
                                                    required=True)):

        """Reload a cog"""
        await ctx.defer()
        ext_list = self.bot.extensions
        cog_list = [cog for cog in ext_list]

        cog_n = "cogs.{}".format(cog)
        if cog_n in cog_list:
            try:
                self.bot.unload_extension(cog_n)
            except Exception as e:
                Logger.write(e)
                await ctx.respond("Failed to unload cog '{}'".format(cog))
                return
        else:
            await ctx.respond("No loaded cogs called '{}'".format(cog))
            return

        try:
            self.bot.load_extension(cog_n)
            await ctx.respond("Successfully reloaded cog '{}'".format(cog))
        except Exception as e:
            Logger.write(e)
            await ctx.respond("Failed to reload cog '{}'".format(cog))
            return

    # @commands.slash_command(name="cogs")
    @cogs.command(name="list")
    @perms.is_dev()
    async def the_cog_list(self, ctx):
        """List all loaded and unloaded cogs"""
        await ctx.defer()
        ext_list = self.bot.extensions
        loaded = []
        unloaded = []
        for cog in ext_list:
            loaded.append(str(cog).replace("cogs.", ""))

        cogs_in_folder = self.bot.get_cogs_in_folder()
        for cog_f in cogs_in_folder:
            if cog_f not in loaded:
                unloaded.append(cog_f.replace(".py", ""))

        await ctx.respond("```diff\n"
                          "+ Loaded Cogs:\n{}\n\n"
                          "- Unloaded Cogs:\n{}"
                          "```"
                          "".format(", ".join(sorted(loaded)),
                                    ", ".join(sorted(unloaded))))


def setup(bot):
    bot.add_cog(CogManagement(bot))
