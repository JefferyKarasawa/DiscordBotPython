import discord
from discord.ext import commands
import requests




XIVAPI_BASE_URL = 'https://xivapi.com/'

XIVAPIKEY = ''

@commands.group()
async def lodestone(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to lodestone command group")
        
@lodestone.command()
async def char (ctx, server: str, *, character_name: str):
    params = {
        'name': character_name,
        'server': server,
        'key': XIVAPIKEY
    }
    
    response = requests.get(f'{XIVAPI_BASE_URL}character/search', params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get('Results', [])

        if results:
            char_data = results[0]
            await ctx.send(f"Found: {char_data['Name']} on {char_data['Server']}. Lodestone ID: {char_data['ID']}")
        else:
            await ctx.send("Character not found.")
    else:
        await ctx.send("Error retrieving data from the FFXIV API.")
        
async def setup(client):
    client.add_command(lodestone)