from discord.ext import commands
import datetime
import discord



@commands.group()
async def moderation (ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to moderation command")
        
@moderation.command()
async def clear (ctx, amount, month=None, day=None, year=None):
    if amount == "-":
        amount == None
    else:
        amount = int(amount) + 1
    if month == None or day == None or year == None:
        date = None
    else:
        date = datetime.datetime(int(year), int(month), int(day))
    await ctx.channel.purge(limit=amount, after=date)
    
    
@moderation.command()
async def kick (ctx, member: discord.Member, *, reason):
    await member.kick(reason=reason)
    
@moderation.command()
async def ban (ctx, member: discord.Member, *, reason):
    await member.ban(reason=reason)
    
@moderation.command()
async def unban (ctx, *, member):
    banned_members = await ctx.guild.bans()
    for person in banned_members:
        user: person.user
        if member == str(user):
            await ctx.guild.unban(member)
    
    
    
async def setup(client):
    client.add_command(moderation)
    