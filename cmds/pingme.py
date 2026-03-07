from discord.ext import commands
import datetime
import discord
import time


@commands.group(
    help="Putting this command in will show your latency",
    description="Command: pingme",
    brief="Command to show you your ping"
)    
async def pingme(ctx):
    before = time.monotonic()
    msg = await ctx.send("Pinging...")
    latency = (time.monotonic() - before) * 1000
    await msg.edit(content=f"Your ping is {int(latency)} ms.")
    
    
async def setup(client):
    client.add_command(pingme)