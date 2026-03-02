import discord
from discord.ext import commands


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Remove the built-in help command so ours takes over
        self.bot.remove_command("help")

    @commands.command(name="help", description="Shows all available bot commands")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Bot Commands",
            description="All commands use the `!` prefix.",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="General",
            value=(
                "`!ping` — Responds with pong\n"
                "`!pingme` — Shows your latency\n"
                "`!whoami` — Bot information\n"
                "`!server` — Server information\n"
                "`!eightball <question>` — Ask the magic 8-ball\n"
                "`!checking` — Check bot status *(Moderator/Owner only)*"
            ),
            inline=False
        )

        embed.add_field(
            name="Math",
            value=(
                "`!math add <a> <b>` — Add two numbers\n"
                "`!math multiply <a> <b>` — Multiply two numbers\n"
                "`!math divide <a> <b>` — Divide two numbers\n"
                "`!math minus <a> <b>` — Subtract two numbers\n"
                "`!math squareroot <n>` — Square of a number"
            ),
            inline=False
        )

        embed.add_field(
            name="Weather",
            value=(
                "`!weather currentweather <city> <state> <country>` — Current weather\n"
                "`!weather city <city>` — Current weather by city"
            ),
            inline=False
        )

        embed.add_field(
            name="Moderation *(Moderator role required)*",
            value=(
                "`!moderation clear <amount>` — Clear messages\n"
                "`!moderation kick <@member> <reason>` — Kick a member\n"
                "`!moderation ban <@member> <reason>` — Ban a member\n"
                "`!moderation unban <member>` — Unban a member"
            ),
            inline=False
        )

        embed.add_field(
            name="TicTacToe",
            value=(
                "`!tictactoe start <@p1> <@p2>` — Start a game\n"
                "`!tictactoe place <1-9>` — Place your mark\n"
                "`!tictactoe stop` — Stop the current game"
            ),
            inline=False
        )

        embed.add_field(
            name="FFXIV",
            value=(
                "`!item <name>` — Search for an item (EN/JP auto-detect)\n"
                "`!translate_item <en|ja> <name>` — Translate an item name\n"
                "`!market <item_id> <world>` — Market board pricing via Universalis"
            ),
            inline=False
        )

        embed.set_footer(text="Use !help to view this again.")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
