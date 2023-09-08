from discord.ext import commands
import datetime
import discord


#putting in role check for moderation commands


@commands.group()
async def moderation (ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to moderation command")
        
@moderation.command()
#@commands.is_owner()
@commands.has_role("moderator")
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

#creating error handler for when roles doesn't match    
@clear.error
async def clear_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the proper role for this command.")

    
    
@moderation.command()
@commands.has_role("moderator")
async def kick (ctx, member: discord.Member, *, reason):
    await member.kick(reason=reason)
    
#creating error handler for when roles doesn't match    
@clear.error
async def kick_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the proper role for this command.")
    
@moderation.command()
@commands.has_role("moderator")
async def ban (ctx, member: discord.Member, *, reason):
    await member.ban(reason=reason)
    
#creating error handler for when roles doesn't match    
@clear.error
async def ban_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the proper role for this command.")
    
@moderation.command()
@commands.has_role("moderator")
async def unban (ctx, *, member):
    banned_members = await ctx.guild.bans()
    for person in banned_members:
        user: person.user
        if member == str(user):
            await ctx.guild.unban(member)
            
            
#creating error handler for when roles doesn't match    
@unban.error
async def unban_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have the proper role for this command.")
    
    
    
async def setup(client):
    client.add_command(moderation)
    