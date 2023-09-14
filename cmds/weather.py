import requests
import json
import os
from discord.ext import commands
import discord




#using API to grab weather information
    
with open('api_key.json', 'r') as f:
    api_key = json.load(f)
    
@commands.group(
    help="Displays weather in requested city",
    description="Command: !weather <city> <state> <country>",
    brief="Displays weather in requested city"
    
)

async def weather (ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to the weather command")


#current weather command with city, state and country inputs
@weather.command()
@commands.cooldown(2, 1, commands.BucketType.default)
async def currentweather (ctx, city: str, state: str = None, country: str = None):
    
    r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city},{state},{country}&units=metric&APPID={api_key['api_key']}")
    json_data = r.json()
    
    weather = json_data['weather'][0]['main']
    description = json_data['weather'][0]['description']
    temp = json_data['main']['temp']
    icon = "http://openweathermap.org/img/wn/" + json_data['weather'][0]['icon'] + "@2x.png"
    
    #print(weather, description, temp)
#creating embed to send weather info to discord server
    embed = discord.Embed(
        title="Current Weather",
        description=f"{(str.title(city))}, {(str.title(state))}, {(str.title(country))}",
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
        
#current weather command with only city input

@weather.command()
@commands.cooldown(2, 1, commands.BucketType.default)
async def city (ctx, city: str):
    
    r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={api_key['api_key']}")
    json_data = r.json()
    
    weather = json_data['weather'][0]['main']
    description = json_data['weather'][0]['description']
    temp = json_data['main']['temp']
    icon = "http://openweathermap.org/img/wn/" + json_data['weather'][0]['icon'] + "@2x.png"
    
    #print(weather, description, temp)
#creating embed to send weather info to discord server
    embed = discord.Embed(
        title="Current Weather",
        description=f"{(str.title(city))}",
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
        await ctx.send("This is not a valid city, please try again.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing city, please input proper city")
        
async def setup(client):
    client.add_command(weather)