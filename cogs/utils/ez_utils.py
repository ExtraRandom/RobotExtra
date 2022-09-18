import asyncio
import discord
from discord.ext import commands
from datetime import datetime
import os
from cogs.utils.logger import Logger
from typing import List, Union, Optional


def base_directory():
    """
    Base file directory of the bot (the folder main.py is in)

    :return: Base file directory
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


def english_characters_check(check_string: str):
    """
    Checks if the given string contains english characters
    :param check_string:
    :return: True if all characters are english, false if not
    """
    # https://stackoverflow.com/questions/27084617/detect-strings-with-non-english-characters-in-python

    try:
        check_string.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def capitalise_every_word(input_string: str, split_char=" "):
    """
    Capitalise every word in a string
    :param input_string: The string
    :param split_char: The character that defines a space between words. A space by default
    :return: String with capitalised words
    """
    as_list = input_string.split(split_char)
    output_string = ""
    for word in as_list:
        output_string += "{} ".format(word.capitalize())
    output_string = output_string.strip()  # remove trailing space
    return output_string
