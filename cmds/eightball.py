from discord.ext import commands
import random



@commands.group(
    help="Putting this command in will make the bot use the eightball command",
    description="Command: !eightball",
    brief="Command to get an eightball reading"
)    
async def eightball(ctx, *, arg):
    question = arg
    responses = ["Concentrate and ask again", "Yes!", "No!", "Cannot predict at the moment", "My sources say...no", "Very doubtful", "Without a doubt", "Yes, definitely!", "Don't count on it", "Better not tell you now" ]
    await ctx.send(f"**Question: ** {question}\n**Answer: ** {random.choice(responses)}")  
    
    
async def setup(client):
    client.add_command(eightball)