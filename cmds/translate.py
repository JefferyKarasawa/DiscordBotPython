import os
import re
import aiohttp
from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()

MINHON_API_KEY = os.getenv("MINHON_API_KEY")
MINHON_API_SECRET = os.getenv("MINHON_API_SECRET")
MINHON_LOGIN_ID = os.getenv("MINHON_LOGIN_ID")

TOKEN_URL = "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/oauth2/token.php"
API_URL = "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/"

JAPANESE_PATTERN = re.compile(
    r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]'
)


def detect_language(text: str) -> str:
    """Return 'ja' if text contains Japanese characters, otherwise 'en'."""
    return "ja" if JAPANESE_PATTERN.search(text) else "en"


async def get_access_token() -> str:
    async with aiohttp.ClientSession() as session:
        data = {
            "grant_type": "client_credentials",
            "client_id": MINHON_API_KEY,
            "client_secret": MINHON_API_SECRET,
        }
        async with session.post(TOKEN_URL, data=data) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result["access_token"]


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    access_token = await get_access_token()
    async with aiohttp.ClientSession() as session:
        data = {
            "access_token": access_token,
            "key": MINHON_API_KEY,
            "api_name": "mt",
            "api_param": f"generalNT_{source_lang}_{target_lang}",
            "name": MINHON_LOGIN_ID,
            "type": "json",
            "text": text,
        }
        async with session.post(API_URL, data=data) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)
            return result["resultset"]["result"]["text"]


@commands.command(
    help="Translates text between English and Japanese. Automatically detects the language direction.\nUsage: !translate <text>",
    description="Command: !translate <text>",
    brief="Translates between English and Japanese"
)
@commands.cooldown(3, 5, commands.BucketType.default)
async def translate(ctx, *, text: str):
    source_lang = detect_language(text)
    target_lang = "en" if source_lang == "ja" else "ja"
    lang_labels = {"en": "English", "ja": "Japanese"}

    async with ctx.typing():
        try:
            translated = await translate_text(text, source_lang, target_lang)
        except Exception:
            await ctx.send("Translation failed. Please check your API credentials or try again later.")
            return

    embed = discord.Embed(title="Translation", color=discord.Color.green())
    embed.add_field(name=f"Original ({lang_labels[source_lang]})", value=text, inline=False)
    embed.add_field(name=f"Translation ({lang_labels[target_lang]})", value=translated, inline=False)
    await ctx.send(embed=embed)


@translate.error
async def translate_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please wait a few seconds.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide text to translate. Usage: `!translate <text>`")


async def setup(client):
    client.add_command(translate)
