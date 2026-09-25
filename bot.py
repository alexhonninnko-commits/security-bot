import os
import time
import sqlite3
from collections import defaultdict
import discord
from discord.ext import commands

from keep_alive import keep_alive

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            joined_at TEXT,
            warnings INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    print("[DATABÁZE] SQLite databáze byla úspěšně inicializována.")

init_db()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.user_message_timestamps = defaultdict(list)

    async def on_ready(self):
        print(f"[BOT] Přihlášen jako: {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if message.author.guild_permissions.administrator:
            await self.process_commands(message)
            return

        if any(link in message.content.lower() for link in ["http://", "https://", "discord.gg/"]):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, posílání odkazů je zakázáno!", delete_after=5)
                return
            except Exception:
                pass

        now = time.time()
        user_timestamps = self.user_message_timestamps[message.author.id]
        user_timestamps.append(now)
        self.user_message_timestamps[message.author.id] = [t for t in user_timestamps if now - t <= 5]

        if len(self.user_message_timestamps[message.author.id]) > 5:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, nepřestávej spamovat!", delete_after=5)
                return
            except Exception:
                pass

        await self.process_commands(message)

bot = DiscordBot()

@bot.command(name="setup_roles")
@commands.has_permissions(administrator=True)
async def setup_roles(ctx):
    msg_text = """# role

<@&1539241329899474954> - **je vlastník serveru který rozhoduje co se přidá na server**
<@&1552268147179135046> - **je člen A-Teamu který dělá s majitelem změny na serveru a hlídá server**
<@&1539240450810978364> - **je člen A-Teamu který taky může změny na serveru ale na žádost majitele a hlídá server**
<@&1552391311754133555> - **je člen A-Teamu který testuje jestli všechno funguje**
<@&1549866576029814784> - **je role pro členy který jsou aktivní na serveru a na vc**
<@&1539242304013992048> - **je role který maji všechny na serveru**
<@&1543385078992871524> / <@&1543385813943984239> - **je pro členy který si požádaji o roli**
<@&1540028254885257256> / <@&1540028432614817862> / <@&1540028872312225914> / <@&1540028968273449002> / <@&1553041371986927657> - **je členy který si požádaji o barvu kterou chci na nicku na serveru**
<@&1553032262696566915> / <@&1553032409073586186> - **je členy který si požádaji o věk který chtějí mít na serveru**
<@&1549872649877069924> - **je pro členy který dají booster na server**"""
    
    await ctx.send(content=msg_text)
    await ctx.message.delete()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[CHYBA] Proměnná DISCORD_TOKEN nebyla nalezena!")
