import discord
from discord.ext import commands
import random


player1 = ""
player2 = ""
turn = ""
gameOver = True

board = []


@commands.group(
    help="Initiates TicTacToe Game",
    description="Command: tictactoe",
    brief="Command to play tictactoe"
)
        
async def tictactoe (ctx, p1: discord.Member, p2: discord.Member):
    await ctx.send("Tictactoe game")
    
    
async def setup(client):
    client.add_command(tictactoe)
