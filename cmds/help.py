import discord
from discord.ext import commands


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command(
        name="help",
        aliases=["ヘルプ", "helpjp"],
        description="Shows all available bot commands"
    )
    async def help_command(self, ctx, lang: str | None = None):
        jp_keywords = {"ja", "jp", "japanese", "日本語"}
        invoked = (ctx.invoked_with or "").lower()
        use_ja = (lang or "").lower() in jp_keywords or invoked in {"ヘルプ", "helpjp"}

        if use_ja:
            embed = discord.Embed(
                title="ボットコマンド一覧",
                description="すべてのコマンドは `!` または `！` プレフィックスを使います。",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="一般",
                value=(
                    "`!ping` — pong を返します\n"
                    "`!pingme` — レイテンシを表示\n"
                    "`!whoami` — ボット情報\n"
                    "`!server` — サーバー情報\n"
                    "`!eightball <質問>` — マジック8ボール\n"
                    "`!checking` — ボットの動作確認（モデレーター以上）"
                ),
                inline=False
            )
            embed.add_field(
                name="数学 (`!math`)",
                value=(
                    "`!math add <数1> <数2>` — 足し算\n"
                    "`!math multiply <数1> <数2>` — 掛け算\n"
                    "`!math divide <数1> <数2>` — 割り算\n"
                    "`!math minus <数1> <数2>` — 引き算\n"
                    "`!math squareroot <数>` — 平方根"
                ),
                inline=False
            )
            embed.add_field(
                name="天気 (`!weather`)",
                value=(
                    "`!weather currentweather <都市> [州] [国]` — 現在の天気\n"
                    "`!weather city <都市>` — 都市情報"
                ),
                inline=False
            )
            embed.add_field(
                name="モデレーション (`!moderation`)",
                value=(
                    "`!moderation clear <件数> [月] [日] [年]` — メッセージ削除\n"
                    "`!moderation kick <メンバー> <理由>` — キック\n"
                    "`!moderation ban <メンバー> <理由>` — バン\n"
                    "`!moderation unban <メンバー>` — バン解除"
                ),
                inline=False
            )
            embed.add_field(
                name="FFXIV",
                value=(
                    "`!item <アイテム名>` — アイテム検索\n"
                    "`!translate_item <言語> <アイテム名>` — アイテム名翻訳\n"
                    "`!market <サーバー> <アイテム名>` — マーケットボード価格"
                ),
                inline=False
            )
            embed.add_field(
                name="翻訳",
                value=(
                    "`!translate <テキスト>` — 英語↔日本語の自動翻訳（言語を自動検出）\n"
                    "日本語に翻訳する場合は漢字とひらがな読みを表示"
                ),
                inline=False
            )
            embed.add_field(
                name="ゲーム (`!tictactoe`)",
                value=(
                    "`!tictactoe start <プレイヤー1> <プレイヤー2>` — ゲーム開始\n"
                    "`!tictactoe place <位置>` — 駒を置く（1〜9）\n"
                    "`!tictactoe stop` — ゲーム中止\n"
                    "`!tictactoe finish` — ゲーム終了"
                ),
                inline=False
            )
            embed.set_footer(text="英語: !help en")
        else:
            embed = discord.Embed(
                title="Bot Commands",
                description="All commands use `!` or `！` prefix.",
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
                    "`!checking` — Check the bot in (moderator+ only)"
                ),
                inline=False
            )
            embed.add_field(
                name="Math (`!math`)",
                value=(
                    "`!math add <num1> <num2>` — Addition\n"
                    "`!math multiply <num1> <num2>` — Multiplication\n"
                    "`!math divide <num1> <num2>` — Division\n"
                    "`!math minus <num1> <num2>` — Subtraction\n"
                    "`!math squareroot <num>` — Square root"
                ),
                inline=False
            )
            embed.add_field(
                name="Weather (`!weather`)",
                value=(
                    "`!weather currentweather <city> [state] [country]` — Current weather\n"
                    "`!weather city <city>` — City information"
                ),
                inline=False
            )
            embed.add_field(
                name="Moderation (`!moderation`)",
                value=(
                    "`!moderation clear <amount> [month] [day] [year]` — Delete messages\n"
                    "`!moderation kick <member> <reason>` — Kick a member\n"
                    "`!moderation ban <member> <reason>` — Ban a member\n"
                    "`!moderation unban <member>` — Unban a member"
                ),
                inline=False
            )
            embed.add_field(
                name="FFXIV",
                value=(
                    "`!item <name>` — Search for an FFXIV item\n"
                    "`!translate_item <lang> <name>` — Translate an item name\n"
                    "`!market <server> <item name>` — Market board prices"
                ),
                inline=False
            )
            embed.add_field(
                name="Translation",
                value=(
                    "`!translate <text>` — Auto-translate between English and Japanese (direction auto-detected)\n"
                    "Shows kanji and hiragana reading when translating to Japanese"
                ),
                inline=False
            )
            embed.add_field(
                name="Games (`!tictactoe`)",
                value=(
                    "`!tictactoe start <player1> <player2>` — Start a game\n"
                    "`!tictactoe place <pos>` — Place your piece (1–9)\n"
                    "`!tictactoe stop` — Forfeit the game\n"
                    "`!tictactoe finish` — End the game"
                ),
                inline=False
            )
            embed.set_footer(text="Japanese: !help ja / ！ヘルプ")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))