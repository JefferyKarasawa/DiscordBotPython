import discord
from discord.ext import commands



@commands.group(
    help="This is help",
    description="This is description",
    brief="This is brief"
)    
async def server(ctx):
    name = ctx.guild.name
    description = ctx.guild.description
    icon = ctx.guild.icon
    memberCount = ctx.guild.member_count
    owner = ctx.guild.owner
    
    embed = discord.Embed(
        title=name + " Server Information",
        description=description,
        color=discord.Color.dark_grey()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)
    
    await ctx.send(embed=embed)
    
    
async def setup(client):
    client.add_command(server)
    