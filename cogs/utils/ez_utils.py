import asyncio
import discord
from discord.ext import commands
from datetime import datetime
import os
from cogs.utils.logger import Logger
from typing import List, Union, Optional


def quick_embed(title: str,
                description: str,
                colour=discord.colour.Colour.red(),
                fields=None,
                timestamp: bool = False):
    """

    :param title:
    :param description:
    :param colour:
    :param fields:
    :param timestamp:
    :return:
    """
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    if fields is not None:
        try:
            for field in fields:
                name, value = field
                embed.add_field(name=name, value=value)
        except ValueError:
            name, value = fields
            embed.add_field(name=name, value=value)

    if timestamp is True:
        embed.timestamp = datetime.utcnow()

    return embed


async def reply_then_delete(message: str, reply_message: discord.Message, time=60):
    """
    Reply to a message and then delete after time (default 60s)

    :param message: the message being sent
    :param reply_message: the message being replied to
    :param time: time before deletion
    :return: None
    """
    msg = await reply_message.reply(message)
    await asyncio.sleep(time)
    await msg.delete()
    return


def base_directory():
    """
    Base file directory of the bot (the folder main.py is in)

    :return: The bots file path
    """
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


async def find_member_from_id_or_mention(ctx: discord.ext.commands.Context,
                                         user: Optional[Union[int, str, discord.Member]]) -> Optional[discord.Member]:
    """
    Takes message context to check for mentions and user input to check if its an id and returns
    the member object should it find one, or none if it does not

    :param ctx: Context
    :param user: Desired user id as int or string, or none
    :return: The discord member if found, or none
    """
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
            except ValueError:
                return None
            except Exception as e:
                Logger.write(e)
                return None
    return target
