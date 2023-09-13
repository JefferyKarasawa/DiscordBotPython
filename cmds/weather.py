import requests
import json
import os
from discord.ext import commands
import discord




#using API to grab weather information
    
with open('api_key.json', 'r') as f:
    api_key = json.load(f)
    
@commands.group(
    help="Putting this command in will make the bot respond with with pong",
    description="Command: Ping",
    brief="Command to respond with pong"
    
)
@commands.cooldown(2, 1, commands.BucketType.default)
async def weather (ctx, city: str, state : str = None, country : str = None):
    
    r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&units=metric&APPID={api_key['api_key']}")
    json_data = r.json()
    
    weather = json_data['weather'][0]['main']
    description = json_data['weather'][0]['description']
    temp = json_data['main']['temp']
    icon = "http://openweathermap.org/img/wn/" + json_data['weather'][0]['icon'] + "@2x.png"
    
    #print(weather, description, temp)
#creating embed to send weather info to discord server
    embed = discord.Embed(
        title="Current Weather",
        description=f"{city.upper()}",
        color=discord.Color.blue()

    )    
    
    embed.set_thumbnail(url=icon)
    embed.add_field(name=weather, value=description, inline=False)
    embed.add_field(name="Temperature", value=f"{temp}\u2103", inline=False)
    
    await ctx.send (embed=embed)
#creating error handler for city and country
@weather.error
async def weather_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please wait a few seconds before inputting the command again")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("This is not a valid city or country, please try again.")
        
async def setup(client):
    client.add_command(weather)