from discord.ext import commands
import os
from cogs.utils import perms, IO, ez_utils
from cogs.utils.logger import Logger


class CogManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @perms.is_dev()
    async def load(self, ctx, *, cog: str):
        """Load a cog"""
        cog_list = []
        for c_file in os.listdir(os.path.join(ez_utils.base_directory(), "cogs")):
            if c_file.endswith(".py"):
                cog_list.append("cogs.{}".format(c_file.replace(".py", "")))

        l_cog_name = "cogs.{}".format(cog)  # print(cog, cog_name, cog_list)

        if l_cog_name in cog_list:
            try:
                self.bot.load_extension(l_cog_name)
                await ctx.send("Successfully loaded cog '{}'.".format(cog))
            except Exception as e:
                Logger.write(e)
                await ctx.send("Failed to load cog '{}'. Reason: {}. \n {}".format(cog, type(e).__name__, e.args))
                return
        else:
            await ctx.send("No cog called '{}'.".format(cog))
            return

        data = IO.read_settings_as_json()
        if data is None:
            await ctx.send(IO.settings_fail_read)
            return

        data['cogs'][cog] = True

        if IO.write_settings(data) is False:
            await ctx.send(IO.settings_fail_write)
            return

    @commands.command()
    @perms.is_dev()
    async def unload(self, ctx, *, cog: str):
        """Unload a cog"""
        ext_list = self.bot.extensions
        cog_list = []
        for cogs in ext_list:
            cog_list.append(cogs)

        l_cog_name = "cogs.{}".format(cog)  # print(cog, cog_name, cog_list)

        if l_cog_name in cog_list:
            try:
                self.bot.unload_extension(l_cog_name)
                await ctx.send("Successfully unloaded cog '{}'.".format(cog))
            except Exception as e:
                await ctx.say("Failed to unload cog '{}'. Reason: {}".format(cog, type(e).__name__))
                return
        else:
            await ctx.send("No loaded cog called '{}'.".format(cog))
            return

        data = IO.read_settings_as_json()
        if data is None:
            await ctx.send(IO.settings_fail_read)
            return
        data['cogs'][cog] = False
        if IO.write_settings(data) is False:
            await ctx.send(IO.settings_fail_write)
            return

    @commands.command()
    @perms.is_dev()
    async def reload(self, ctx, *, cog: str):
        """Reload a cog"""
        ext_list = self.bot.extensions
        cog_list = [cog for cog in ext_list]

        cog_n = "cogs.{}".format(cog)
        if cog_n in cog_list:
            try:
                self.bot.unload_extension(cog_n)
            except Exception as e:
                Logger.write(e)
                await ctx.send("Failed to unload cog '{}'".format(cog))
                return
        else:
            await ctx.send("No loaded cogs called '{}'".format(cog))
            return

        try:
            self.bot.load_extension(cog_n)
            await ctx.send("Successfully reloaded cog '{}'".format(cog))
        except Exception as e:
            Logger.write(e)
            await ctx.send("Failed to reload cog '{}'".format(cog))
            return

    @commands.command(aliases=["ra"])
    @perms.is_dev()
    async def reload_all(self, ctx):
        """Reload all cogs"""
        msg = await ctx.send("Reloading all non critical cogs (excludes cog_management and logging)")
        reloaded = 0
        cog_list = [cog for cog in self.bot.extensions]
        cog_count = len(cog_list)

        for cog in cog_list:
            if cog in ["cogs.cog_management", "cogs.logging"]:
                cog_count -= 1
                continue

            try:
                self.bot.unload_extension(cog)
            except Exception as e:
                Logger.write(e)
                cog_list.remove(cog)
                continue

            try:
                self.bot.load_extension(cog)
                reloaded += 1
            except Exception as e:
                Logger.write(e)
                continue

        await msg.edit(content="{} cogs out of {} successfully reload "
                               "(cog_management and logging must be reload manually)\n"
                               "Any errors can be found in the logs.".format(reloaded, cog_count))

    @commands.command(name="cogs")
    @perms.is_dev()
    async def the_cog_list(self, ctx):
        """List all loaded and unloaded cogs"""
        ext_list = self.bot.extensions
        loaded = []
        unloaded = []
        for cog in ext_list:
            loaded.append(str(cog).replace("cogs.", ""))

        cogs_in_folder = self.bot.get_cogs_in_folder()
        for cog_f in cogs_in_folder:
            if cog_f not in loaded:
                unloaded.append(cog_f.replace(".py", ""))

        await ctx.send("```diff\n"
                       "+ Loaded Cogs:\n{}\n\n"
                       "- Unloaded Cogs:\n{}"
                       "```"
                       "".format(", ".join(sorted(loaded)),
                                 ", ".join(sorted(unloaded))))


def setup(bot):
    bot.add_cog(CogManagement(bot))
