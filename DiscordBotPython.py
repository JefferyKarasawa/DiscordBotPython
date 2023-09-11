import discord
import json
import os
import settings
from discord.ext import commands

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

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    logger.info(f"User: {client.user} (ID: {client.user.id})")
    
    for cmd_file in settings.CMDS_DIR.glob("*.py"):
        if cmd_file.name != "__init__.py":
            await client.load_extension(f"cmds.{cmd_file.name[:-3]}")

    
#@client.event
#async def on_message(message):
#    if message.author == client.user:
#        return
#    if str(message.author) == "Kentaru#1633":
#        if str(message.content).lower() == "checking":
#            await message.channel.send("Python Bot checking in!")

        
#@client.event
#async def on_message_edit(before, after):
#    await before.channel.send(str(before.author) + " edited a message.\nBefore: " + before.content + "\nAfter: " + after.content)


client.run(token, root_logger=True)





