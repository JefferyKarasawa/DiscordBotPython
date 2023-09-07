from discord.ext import commands



@commands.group(
    help="This is help",
    description="This is description",
    brief="This is brief"
)    
async def ping(ctx):
    await ctx.send("pong")  
    
    
async def setup(client):
    client.add_command(ping)
    