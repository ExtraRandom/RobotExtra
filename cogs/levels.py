from discord.ext import commands
from time import time
import os
from cogs.utils import perms, IO
from cogs.utils.logger import Logger


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def db_add_user(self, msg):
        query = """
INSERT INTO
    tracking (user_id, messages_total, messages_valid, message_last_time)
VALUES
    ({}, 1, 1, {})
        """.format(msg.author.id, time())

        eq = self.bot.execute_query(query)
        return eq

    def db_read_user(self, msg):
        query = """
SELECT
    *
FROM
    tracking
WHERE
    user_id = "{}"
        """.format(msg.author.id)
        erq = self.bot.execute_read_query(query)
        return erq

    def db_message_count_update(self, ctx, valid=False):
        print("")

    @commands.command(hidden=True)
    async def level(self, msg):
        user_id = msg.author.id
        print(user_id)

    async def do_leveling_stuff(self, msg):
        # check if user in db
        user_data = self.db_read_user(msg)
        print(user_data)

        if len(user_data) is 0:
            print("no user")
            self.db_add_user(msg)
        else:
            u_id, u_msg_total, u_msg_valid, u_msg_last = user_data[0]
            print(u_msg_total, u_msg_last, u_msg_valid)


def setup(bot):
    n = Levels(bot)
    bot.add_cog(n)
    # bot.add_listener(n.do_leveling_stuff, "on_message")


