import asyncio
import discord
from datetime import datetime
from typing import Union


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


async def send_then_delete(message: str, channel: Union[discord.TextChannel, discord.DMChannel], time=60):
    """Send message then delete after time (default 60s)"""
    msg = await channel.send(message, delete_after=time)
    # await asyncio.sleep(time)
    # await msg.delete()


async def reply_then_delete(message: str, reply_message: discord.Message, time=60):
    """Reply to a message and then delete after time (default 60s)"""
    msg = await reply_message.reply(message)
    await asyncio.sleep(time)
    await msg.delete()



