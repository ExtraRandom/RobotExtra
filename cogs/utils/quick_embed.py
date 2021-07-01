import discord


def create(title, description, colour=discord.colour.Colour.red(), fields=None):
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    for field in fields:
        name, value = field
        embed.add_field(name=name, value=value)

    return embed

