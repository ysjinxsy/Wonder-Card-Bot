import aiosqlite #type: ignore

DATABASE_PATH = "database.db"
async def get_config(guild_id: int):
    async with aiosqlite.connect("database.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT * FROM config WHERE guild_id = ?', (guild_id,))
            result = await cursor.fetchone()
            if result:
                return {
                    'guild_id': result[0],
                    'manager_role_id': result[1],
                    'assistant_manager_role_id': result[2],
                    'channel_id': result[3],
                    'roster': result[4]
                }
            else:
                return None

            
async def get_teams():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT roleid, emoji,server_id FROM teams')
            return await cursor.fetchall()
