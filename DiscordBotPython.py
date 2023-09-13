import discord
import json
import os
import settings
from discord.ext import commands
import requests

#making secure file config.json to add in prefix and token
logger = settings.logging.getLogger("client")


if os.path.exists(os.getcwd() + "/config.json"):
    with open("./config.json") as f:
        configData = json.load(f)
else: 
    configTemplate = {"Token": "", "Prefix" : "!"}
    with open(os.getcwd() + "/config.json", "w+") as f:
       json.dump(configTemplate, f) 
    
    
token = configData["Token"]
prefix = configData["Prefix"]

#intents and bot start command
intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

#logging info
@client.event
async def on_ready():
    logger.info(f"User: {client.user} (ID: {client.user.id})")
    
    for cmd_file in settings.CMDS_DIR.glob("*.py"):
        if cmd_file.name != "__init__.py":
            await client.load_extension(f"cmds.{cmd_file.name[:-3]}")

    


        
#@client.event
#async def on_message_edit(before, after):
#    await before.channel.send(str(before.author) + " edited a message.\nBefore: " + before.content + "\nAfter: " + after.content)

#using API to grab weather information
    
with open('api_key.json', 'r') as f:
    api_key = json.load(f)
    
@client.command()
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
#@weather.error
#async def weather_error(ctx, error):
#    if isinstance(error, commands.CommandInvokeError):
#        await ctx.send("This is not a valid city or country, please try again.")
        


    
    
    

#start the bot
client.run(token, root_logger=True)





