import discord
import json
import os


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
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Bot is ready.")
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if str(message.content).lower() == "ping":
        await message.channel.send("pong")


client.run(token)



