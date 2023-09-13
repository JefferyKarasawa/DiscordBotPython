from discord.ext import commands




@commands.group(
    help="Putting this command in will make the bot respond with with pong",
    description="Command: Ping",
    brief="Command to respond with pong"
)
@commands.has_any_role("moderator", "owner")

async def checking(ctx):
    await ctx.send("Python Bot checking in!")
            
async def setup(client):
    client.add_command(checking)