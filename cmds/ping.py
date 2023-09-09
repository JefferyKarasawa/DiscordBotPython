from discord.ext import commands



@commands.group(
    help="Putting this command in will make the bot respond with with pong",
    description="Command: Ping",
    brief="Command to respond with pong"
)    
async def ping(ctx):
    await ctx.send("pong")  
    
    
async def setup(client):
    client.add_command(ping)
    