import discord
from discord.ext import commands
import random


player1 = ""
player2 = ""
turn = ""
gameOver = True

board = []

#create new variable with array inside an array 2d arrays
winningConditions = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [6, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
    
]


@commands.group(
    help="Initiates TicTacToe Game",
    description="Command: tictactoe",
    brief="Command to play tictactoe"
)
        
async def tictactoe (ctx):
    
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to the tictactoe command")
        
@tictactoe.command()
async def start (ctx, p1: discord.Member, p2: discord.Member):

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
    
#lets create a command to place the mark
@tictactoe.command()
async def place(ctx, pos: int):
    global turn
    global player1
    global player2
    global board
    global count
    global gameOver
    
    #checking if game is over or not
    
    if not gameOver:
        mark = ""
        #checking if its the players turn
        if turn == ctx.author:
            #now checking which players turn it is
            if turn == player1:
                mark = ":regional_indicator_x:"
                #putting in elif statement for player2
            elif turn == player2:
                mark = ":o2:"
            #creating another if statement to check the board square is valid and doesn't have a mark in it already
            if 0 < pos < 10 and board[pos - 1] == ":white_large_square:":
                #set the board's element equal to the mark that is put in
                board [pos - 1] = mark
                count += 1
                
                #lets print the board to the discord channel again with the updated mark
                line = ""
                for x in range (len(board)):
                    if x == 2 or x == 5 or x == 8:
                        line += " " + board[x]
                        await ctx.send(line)
                        line = ""
                    else:
                        line += " " + board[x]
            #check winner with winningConditions
                checkWinner(winningConditions, mark)
            
                if gameOver == True:
                    await ctx.send(mark + "wins!")
                
            #checking if the game is a tie or not
            
                elif count >= 9:
                    gameOver = True
                    await ctx.send("Game is a tie! Use !tictactoe to play again!")

            #switching turns between player1 and player2
                if turn == player1:
                    turn = player2
                elif turn == player2:
                    turn = player1
            #making sure the players choose and unmarked tile and its between 1 and 9 (within the board parameters)
            else:
                await ctx.send("Please choose an integer between 1 and 9 and make sure it's an unmarked tile!")
                
        #else statement incase they try to go when it's not their turn
        else:
            await ctx.send("Please wait for your turn!")
            
    #this else statement makes sure the game has been started
    else:
        await ctx.send ("Please start a new game with the !tictactoe command!")
#create a function to check if there is a winner of the game

def checkWinner(winningConditions, mark):
    global gameOver
    #create a for loop to check the winningConditions
    for condition in winningConditions:
        if board[condition[0]] == mark and board[condition[1]] == mark and board [condition[2]] == mark:
            gameOver = True
            
@tictactoe.error
async def tictactoe_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please mention 2 player for this command")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please make sure to mention the players")
        
@place.error
async def place_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please make sure to input an integer!")


  
async def setup(client):
    client.add_command(tictactoe)
