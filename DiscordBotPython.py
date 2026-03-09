import discord
import os
import settings
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logger = settings.logging.getLogger("client")

token = os.getenv("DISCORD_TOKEN")
prefix = os.getenv("DISCORD_PREFIX", "!")

if not token:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")

#intents and bot start command
intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix=["!", "！"], intents=intents)


#logging info
@client.event
async def on_ready():
    logger.info(f"User: {client.user} (ID: {client.user.id})")

    for cmd_file in settings.CMDS_DIR.glob("*.py"):
        if cmd_file.name != "__init__.py":
            await client.load_extension(f"cmds.{cmd_file.name[:-3]}")

    await client.tree.sync()
    logger.info("Slash commands synced.")


#start the bot
client.run(token, root_logger=True)
