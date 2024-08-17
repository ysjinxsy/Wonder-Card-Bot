import nextcord
from nextcord.ext import commands 
from nextcord import Interaction, SelectOption, ui, SlashOption, TextInputStyle, ChannelType
from nextcord.ui import Button, View, Modal, TextInput, RoleSelect, ChannelSelect, Select
import aiosqlite 
import re
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import io
from nextcord.utils import utcnow 
from db import get_config, get_teams
import logging
import aiohttp
import datetime
from shared import guild_id
from datetime import datetime
import requests
import random
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.StreamHandler()          # Log to console
    ]
)

intents = nextcord.Intents.all()
guild_id = 1266153230300090450
client = commands.Bot(command_prefix="?", intents=intents)
DATABASE_PATH = "database.db"


@client.slash_command(name="addcard", description="Add a new card to the database.", guild_ids=[guild_id])
async def addcard(
    interaction: Interaction,
    name: str = SlashOption(description="Name of the player"),
    pace: int = SlashOption(description="Pace stat"),
    shot: int = SlashOption(description="Shot stat"),
    passing: int = SlashOption(description="Passing stat"),
    dribbling: int = SlashOption(description="Dribbling stat"),
    defending: int = SlashOption(description="Defending stat"),
    physical: int = SlashOption(description="Physical stat"),
    image_url: str = SlashOption(description="URL of the player's image"),
    price: int = SlashOption(description="Price of the card"),
    position: str = SlashOption(description="Position of the player")
):
    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            await db.execute('''
                INSERT INTO cards (name, pace, shot, passing, dribbling, defending, physical, image_url, price, position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, pace, shot, passing, dribbling, defending, physical, image_url, price, position))
            await db.commit()
            await interaction.response.send_message(f"Card '{name}' has been added to the database with a price of {price} coins and position {position}!")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}")

@client.slash_command(name="claim", description="Claim a random card and add it to your collection.", guild_ids=[guild_id])
async def claim(interaction: Interaction):
    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            async with db.execute('''
                SELECT card_id, name, pace, shot, passing, dribbling, defending, physical, image_url, price 
                FROM cards 
                WHERE card_id NOT IN (SELECT card_id FROM user_collections WHERE user_id = ?)
            ''', (user_id,)) as cursor:
                available_cards = await cursor.fetchall()

            if not available_cards:
                await interaction.response.send_message("There are no available cards left to claim!")
                return

            selected_card = random.choice(available_cards)
            card_id, card_name, pace, shot, passing, dribbling, defending, physical, image_url, card_price = selected_card

            view = View()

            async def claim_card(interaction: Interaction):
                try:
                    async with aiosqlite.connect('soccer_cards.db') as db:
                        await db.execute('INSERT INTO user_collections (user_id, card_id) VALUES (?, ?)', (user_id, card_id))
                        await db.commit()
                    await interaction.response.edit_message(content=f"You've claimed the card '{card_name}'!", view=None)
                except Exception as e:
                    await interaction.response.edit_message(content=f"An error occurred: {e}", view=None)

            async def sell_card(interaction: Interaction):
                try:
                    async with aiosqlite.connect('soccer_cards.db') as db:
                        await db.execute('''
                            INSERT INTO user_balances (user_id, balance)
                            VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
                        ''', (user_id, card_price, card_price))
                        await db.commit()
                    await interaction.response.edit_message(content=f"You've sold the card '{card_name}' for {card_price} coins!", view=None)
                except Exception as e:
                    await interaction.response.edit_message(content=f"An error occurred: {e}", view=None)

            claim_button = Button(label="Claim", style=nextcord.ButtonStyle.green)
            claim_button.callback = claim_card

            sell_button = Button(label="Sell", style=nextcord.ButtonStyle.red)
            sell_button.callback = sell_card

            view.add_item(claim_button)
            view.add_item(sell_button)

            embed = nextcord.Embed(
                title="Card Available",
                description=(
                    f"**Name:** {card_name}\n"
                    f"**Pace:** {pace}\n"
                    f"**Shot:** {shot}\n"
                    f"**Passing:** {passing}\n"
                    f"**Dribbling:** {dribbling}\n"
                    f"**Defending:** {defending}\n"
                    f"**Physical:** {physical}\n"
                    f"**Price:** {card_price} coins"
                ),
                color=nextcord.Color.blue()
            )
            embed.set_thumbnail(url=image_url)

            await interaction.response.send_message(embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}")

async def download_image(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                if not data:
                    raise Exception("No data returned from image download.")
                return data
            else:
                raise Exception(f"Failed to download image, status code: {response.status}")



async def upload_image(image_data: bytes) -> str:
    async with aiohttp.ClientSession() as session:
        upload_url = 'https://api.imgur.com/3/image'  # Replace with actual URL
        headers = {'Authorization': 'Bearer YOUR_ACCESS_TOKEN'}  # Replace with actual token
        data = aiohttp.FormData()
        data.add_field('image', image_data, content_type='image/png', filename='lineup.png')

        async with session.post(upload_url, headers=headers, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result['data']['link']
            else:
                raise Exception(f"Failed to upload image, status code: {response.status}")

import io
import aiosqlite
from PIL import Image, ImageDraw, ImageFont
import nextcord
from nextcord import Interaction

@client.slash_command(name="lineup", description="View your card collection in a lineup image.", guild_ids=[guild_id])
async def lineup(interaction: Interaction):
    await interaction.response.defer()

    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            async with db.execute('''
                SELECT cards.name, cards.pace, cards.shot, cards.passing, cards.dribbling, 
                       cards.defending, cards.physical, cards.image_url, cards.position, cards.price
                FROM cards 
                INNER JOIN user_collections ON cards.card_id = user_collections.card_id 
                WHERE user_collections.user_id = ?
            ''', (user_id,)) as cursor:
                cards = await cursor.fetchall()

            if not cards:
                await interaction.followup.send("You don't have any cards yet.")
                return

            background_url = "https://cdn.discordapp.com/attachments/1273397560106680421/1274038333101838482/https___cdn.png?ex=66c0cc29&is=66bf7aa9&hm=3391562c99b95da428137ed057d2a29d756512e2ab3734e86cc61b5a6c8accf4&"

            try:
                background_image_data = await download_image(background_url)
                background_image = Image.open(io.BytesIO(background_image_data))
            except Exception as e:
                await interaction.followup.send("Failed to load background image.")
                return

            lineup_width, lineup_height = 892, 725
            card_width, card_height = 165, 209

            lineup_image = background_image.resize((lineup_width, lineup_height))
            draw = ImageDraw.Draw(lineup_image)

            try:
                font = ImageFont.truetype("FFGoodProCond-Black.ttf", 24)
            except IOError:
                font = ImageFont.load_default()

            draw.text((10, 10), interaction.user.name, fill='white', font=font)

            position_coords = {
                'ST': (367, 55),
                'CAM': (368, 273),
                'GK': (368, 472),
                'LW': (97, 10),
                'RW': (97, 674),
                'RCM': (663, 193),
                'LFC': (102, 193)
            }

            for card in cards:
                try:
                    name, pace, shot, passing, dribbling, defending, physical, image_url, position, price = card
                    coords = position_coords.get(position, (0, 0))

                    card_image_data = await download_image(image_url)
                    card_image = Image.open(io.BytesIO(card_image_data)).resize((card_width, card_height))
                    lineup_image.paste(card_image, coords, card_image.convert("RGBA"))

                except Exception as e:
                    print(f"Error processing card {card}: {e}")
                    continue



            embed = nextcord.Embed(
                description=f"# Lineup"
            )
            embed.set_image(url="attachment://lineup.png")

            try:
                with io.BytesIO() as buffer:
                    lineup_image.save(buffer, format="PNG")
                    buffer.seek(0)
                    await interaction.followup.send(embed=embed, file=nextcord.File(fp=buffer, filename="lineup.png"))
            except Exception as e:
                await interaction.followup.send(f"Failed to generate lineup image: {e}")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



@client.slash_command(name="deletecard", description="Delete a card from the database.", guild_ids=[guild_id])
async def deletecard(interaction: Interaction, card_id: int):
    await interaction.response.defer()

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            # Check if the card exists in the database
            async with db.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,)) as cursor:
                card = await cursor.fetchone()
                
            if card is None:
                await interaction.followup.send(f"No card found with ID {card_id}.")
                return
            
            # Delete the card from the database
            async with db.execute('DELETE FROM cards WHERE card_id = ?', (card_id,)):
                await db.commit()

            await interaction.followup.send(f"Card with ID {card_id} has been deleted successfully.")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

@client.slash_command(name="changepose", description="Change the position of a card in your collection.", guild_ids=[guild_id])
async def changepose(interaction: Interaction, card_name: str, new_position: str):
    await interaction.response.defer()

    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            # Check if the card exists in the user's collection
            async with db.execute('''
                SELECT 1 
                FROM user_collections 
                INNER JOIN cards ON user_collections.card_id = cards.card_id
                WHERE user_collections.user_id = ? AND cards.name = ?
            ''', (user_id, card_name)) as cursor:
                result = await cursor.fetchone()

            if not result:
                await interaction.followup.send("You do not own a card with that name.")
                return

            # Update the position of the card
            async with db.execute('''
                UPDATE cards 
                SET position = ?
                WHERE card_id = (
                    SELECT cards.card_id 
                    FROM user_collections 
                    INNER JOIN cards ON user_collections.card_id = cards.card_id
                    WHERE user_collections.user_id = ? AND cards.name = ?
                )
            ''', (new_position, user_id, card_name)):
                await db.commit()

            await interaction.followup.send(f"The position of the card '{card_name}' has been updated to '{new_position}'.")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")


@client.slash_command(name="sell", description="Sell a card from your collection.", guild_ids=[guild_id])
async def sell(interaction: Interaction, card_name: str):
    await interaction.response.defer()

    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            # Check if the card exists in the user's collection
            async with db.execute('''
                SELECT cards.card_id, cards.price
                FROM cards
                INNER JOIN user_collections ON cards.card_id = user_collections.card_id
                WHERE user_collections.user_id = ? AND cards.name = ?
            ''', (user_id, card_name)) as cursor:
                result = await cursor.fetchone()

            if not result:
                await interaction.followup.send("You do not own a card with that name.")
                return

            card_id, price = result

            # Remove the card from the user's collection
            async with db.execute('''
                DELETE FROM user_collections
                WHERE user_id = ? AND card_id = ?
            ''', (user_id, card_id)):
                await db.commit()

            # Check if the user has a balance record
            async with db.execute('''
                SELECT balance
                FROM user_balances
                WHERE user_id = ?
            ''', (user_id,)) as cursor:
                balance_result = await cursor.fetchone()

            if balance_result:
                # Update user's balance
                async with db.execute('''
                    UPDATE user_balances
                    SET balance = balance + ?
                    WHERE user_id = ?
                ''', (price, user_id)):
                    await db.commit()
            else:
                # Insert a new balance record if it does not exist
                async with db.execute('''
                    INSERT INTO user_balances (user_id, balance)
                    VALUES (?, ?)
                ''', (user_id, price)):
                    await db.commit()

            await interaction.followup.send(f"You have successfully sold the card '{card_name}' for {price}.")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



@client.slash_command(name="buy", description="Buy a card from the shop.", guild_ids=[guild_id])
async def buy(interaction: Interaction, card_name: str):
    await interaction.response.defer()

    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            # Fetch card details
            async with db.execute('''
                SELECT card_id, price
                FROM cards
                WHERE name = ?
            ''', (card_name,)) as cursor:
                result = await cursor.fetchone()

            if not result:
                await interaction.followup.send("Card not found.")
                return

            card_id, price = result

            # Check if user has enough balance
            async with db.execute('''
                SELECT balance
                FROM user_balances
                WHERE user_id = ?
            ''', (user_id,)) as cursor:
                balance_result = await cursor.fetchone()

            if not balance_result or balance_result[0] < price:
                await interaction.followup.send("Insufficient balance.")
                return

            # Add card to the user's collection
            async with db.execute('''
                INSERT INTO user_collections (user_id, card_id)
                VALUES (?, ?)
            ''', (user_id, card_id)):
                await db.commit()

            # Update user's balance
            async with db.execute('''
                UPDATE user_balances
                SET balance = balance - ?
                WHERE user_id = ?
            ''', (price, user_id)):
                await db.commit()

            await interaction.followup.send(f"You have successfully bought the card '{card_name}' for {price}.")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")


@client.slash_command(name="balance", description="Check your current balance.", guild_ids=[guild_id])
async def balance(interaction: Interaction):
    await interaction.response.defer()

    user_id = str(interaction.user.id)

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            # Fetch the user's balance
            async with db.execute('''
                SELECT balance
                FROM user_balances
                WHERE user_id = ?
            ''', (user_id,)) as cursor:
                result = await cursor.fetchone()

            if result:
                balance = result[0]
                await interaction.followup.send(f"Your current balance is {balance}.")
            else:
                await interaction.followup.send("You don't have a balance record. Please check with the administrator.")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

@client.slash_command(name="view_cards", description="View all available cards for purchase and their prices.", guild_ids=[guild_id])
async def view_cards(interaction: Interaction):
    await interaction.response.defer()

    async with aiosqlite.connect('soccer_cards.db') as db:
        try:
            async with db.execute('''
                SELECT name, price
                FROM cards
            ''') as cursor:
                cards = await cursor.fetchall()

            if not cards:
                await interaction.followup.send("No cards are available for purchase at the moment.")
                return

            # Format the card list
            card_list = "\n".join([f"{name}: {price} coins" for name, price in cards])
            
            # Send the response
            await interaction.followup.send(f"Available cards for purchase:\n{card_list}")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
