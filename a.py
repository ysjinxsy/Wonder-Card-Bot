import asyncio
import aiosqlite

# Function to create the 'cards' table if it does not exist
async def create_cards_table():
    async with aiosqlite.connect('soccer_cards.db') as db:
        # Check if the table exists
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'") as cursor:
            table_exists = await cursor.fetchone()

        if not table_exists:
            # Create the table if it does not exist
            await db.execute('''
                CREATE TABLE cards (
                    card_id INTEGER PRIMARY KEY,
                    name TEXT,
                    pace INTEGER,
                    shot INTEGER,
                    passing INTEGER,
                    dribbling INTEGER,
                    defending INTEGER,
                    physical INTEGER,
                    image_url TEXT,
                    position TEXT,
                    price INTEGER
                )
            ''')
            await db.commit()
            print("Table 'cards' created.")
        else:
            print("Table 'cards' already exists.")

# Function to create the 'user_collections' table if it does not exist
async def create_user_collections_table():
    async with aiosqlite.connect('soccer_cards.db') as db:
        # Check if the table exists
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_collections'") as cursor:
            table_exists = await cursor.fetchone()

        if not table_exists:
            # Create the table if it does not exist
            await db.execute('''
                CREATE TABLE user_collections (
                    user_id TEXT,
                    card_id INTEGER,
                    FOREIGN KEY (card_id) REFERENCES cards (card_id)
                )
            ''')
            await db.commit()
            print("Table 'user_collections' created.")
        else:
            print("Table 'user_collections' already exists.")

# Function to clear all user collections
async def clear_user_collections():
    async with aiosqlite.connect('soccer_cards.db') as db:
        await db.execute('DELETE FROM user_collections')
        await db.commit()
        print("All user collections cleared.")

# Function to clear all cards
async def clear_all_cards():
    async with aiosqlite.connect('soccer_cards.db') as db:
        await db.execute('DELETE FROM cards')
        await db.commit()
        print("All cards cleared.")

# Main function to run the setup
async def main():
    await create_cards_table()
    await create_user_collections_table()
    await clear_user_collections()
    await clear_all_cards()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
