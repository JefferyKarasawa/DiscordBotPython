from discord.ext import commands



@commands.group(
    help="Putting this command in will make the bot respond with with pong",
    description="Command: Ping",
    brief="Command to respond with pong"
)    
async def whoami(ctx):
    await ctx.send("I am a bot created in Python version 3.11.5. Please reference !help for more commands")  
    
    
async def setup(client):
    client.add_command(whoami)