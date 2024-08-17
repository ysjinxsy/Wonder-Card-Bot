import nextcord
from nextcord.ext import commands
import logging
import asyncio
import webserver
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DISCORD_TOKEN = os.environ['discordkey']

# Discord bot setup
intents = nextcord.Intents.all()
client = commands.Bot(command_prefix="?", intents=intents)

# Import commands from commands.py


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
webserver.keep_alive()
from commands import *
client.run(DISCORD_TOKEN)  # Replace with your actual token

