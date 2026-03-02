from discord.ext import commands



@commands.group(
    help="Putting this command in will make the bot respond with with pong",
    description="Command: Ping",
    brief="Command to respond with pong"
)   
#Bot created in version 3.11.5 
async def whoami(ctx):
    await ctx.send("I am a bot created by Kentaru Mupuru, for suggestion please contact him. Please reference !help for more commands")  
    
    
async def setup(client):
    client.add_command(whoami)