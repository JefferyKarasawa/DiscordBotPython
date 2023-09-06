from discord.ext import commands



@commands.group()
async def ping(ctx):
    await ctx.send("pong")  
    
    
async def setup(client):
    client.add_command(ping)
    