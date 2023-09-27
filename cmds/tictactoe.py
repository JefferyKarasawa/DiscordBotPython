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
    #make the variables and players global
    global count
    global player1
    global player2
    global turn
    global gameOver
    
    #checking if the game is over first
    if gameOver:
        global board
    #set the board into an array, input discord emoji of white_large_square
        board = [":white_large_square:", ":white_large_square:", ":white_large_square:"
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"]
    
    
async def setup(client):
    client.add_command(tictactoe)
