from discord.ext import commands




@commands.group(
    help="You can use this command to check the bot in",
    description="Command: !Checking",
    brief="Command to check the bot in"
)
@commands.has_any_role("moderator", "owner")

async def checking(ctx):
    await ctx.send("Python Bot checking in!")
            
async def setup(client):
    client.add_command(checking)