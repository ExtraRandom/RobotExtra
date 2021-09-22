import asyncio
import discord
from datetime import datetime
import os
from cogs.utils.logger import Logger


def quick_embed(title: str, description: str, colour=discord.colour.Colour.red(), fields=None, timestamp: bool = False):
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
    """Reply to a message and then delete after time (default 60s)"""
    msg = await reply_message.reply(message)
    await asyncio.sleep(time)
    await msg.delete()


def base_directory():
    """Base file directory of the bot (the folder main.py is in)"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


async def find_member_from_id_or_mention(ctx, user):
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
            except ValueError:
                return None
            except Exception as e:
                Logger.write(e)
                return None
    return target
