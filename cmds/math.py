from discord.ext import commands



@commands.group()
async def math (ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to math command")
        
@math.command()
async def add (ctx, one : int , two : int):
    await ctx.send(one + two)

@math.command()
async def multiply (ctx, one : int , two : int):
    await ctx.send(one * two)

@math.command()
async def divide (ctx, one : int , two : int):
    await ctx.send(one / two)
    
@math.command()
async def minus (ctx, one : int , two : int):
    await ctx.send(one - two)
    
@math.command()
async def squareroot (ctx, one : int):
    await ctx.send(one * one)
    
    
async def setup(client):
    client.add_command(math)
