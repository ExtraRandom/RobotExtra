from discord import AutocompleteContext

async def autocomplete(ctx: AutocompleteContext, auto_complete_list: list):
    res = []
    for list_item in auto_complete_list:
        if ctx.value.lower() in str(list_item).lower():
            res.append(list_item)
    return res
