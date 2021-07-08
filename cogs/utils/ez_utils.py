import asyncio
import discord
from datetime import datetime


def quick_embed(title: str, description: str, colour=discord.colour.Colour.red(), fields=None, timestamp=False):
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
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


async def send_then_delete(message, channel, time=60):
    msg = await channel.send(message)
    await asyncio.sleep(time)
    await msg.delete()
