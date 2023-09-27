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
        board = [":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"]
        
        turn = ""
        gameOver = False
        count = 0
        
        player1 = p1
        player2 = p2
        
    #print out the board to discord channel so the game can start

        line = ""
        #for loop for the length of board
        for x in range (len(board)):
            #if end of line then create new line
            if x == 2 or x == 5 or x == 8:
                line += " " + board[x]
                await ctx.send(line)
                line = ""
            else:
                line += " " + board[x]
                
        #lets determine who goes first
        num = random.randint(1, 2)
        if num == 1:
            turn = player1
            await ctx.send("<@" + str(player1.id) +">'s turn, you may start the game!")
        elif num == 2:
            turn = player2
            await ctx.send("<@" + str(player2.id) +">'s turn, you may start the game!")
            
    #create an else statement just incase there is already a game in progress
    else:
        await ctx.send("A game is already in progress, please finish the current game in order to start a new game!")
    
    
async def setup(client):
    client.add_command(tictactoe)
