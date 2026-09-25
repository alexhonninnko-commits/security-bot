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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            role_id INTEGER,
            PRIMARY KEY (user_id, role_id)
        )
    """)
    conn.commit()
    conn.close()
    print("[DATABÁZE] SQLite databáze byla úspěšně inicializována.")

init_db()

class RoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id_str: str):
        if not role_id_str.isdigit():
            await interaction.followup.send("⚠️ Zadané ID role není číslo.", ephemeral=True)
            return

        role_id = int(role_id_str)
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.followup.send(f"⚠️ Role s ID `{role_id_str}` nebyla na serveru nalezena.", ephemeral=True)
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                cursor.execute("DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (interaction.user.id, role_id))
                await interaction.followup.send(f"❌ Role **{role.name}** ti byla odebrána.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (interaction.user.id, role_id))
                await interaction.followup.send(f"✅ Role **{role.name}** ti byla přidána!", ephemeral=True)
            
            conn.commit()
        except discord.Forbidden:
            await interaction.followup.send("❌ **Chyba Oprávnění:** Bot nemá práva upravit tuto roli!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Nepodařilo se upravit roli: {e}", ephemeral=True)
        finally:
            conn.close()

    @discord.ui.select(
        placeholder="🎨 Vyber si barvu jména...",
        custom_id="select_color_role",
        options=[
            discord.SelectOption(label="Červená", value="1540028254885257256", emoji="🔴"),
            discord.SelectOption(label="Modrá", value="1540028432614817862", emoji="🔵"),
            discord.SelectOption(label="Zelená", value="1540028872312225914", emoji="🟢"),
            discord.SelectOption(label="Fialová", value="1540028968273449002", emoji="🟣"),
            discord.SelectOption(label="Žlutá", value="1553041371986927657", emoji="🟡"),
        ]
    )
    async def color_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        await self.toggle_role(interaction, select.values[0])

    @discord.ui.select(
        placeholder="🎂 Vyber si svůj věk...",
        custom_id="select_age_role",
        options=[
            discord.SelectOption(label="13-17+", value="1553032262696566915", emoji="🔞"),
            discord.SelectOption(label="18+", value="1553032409073586186", emoji="🔞"),
        ]
    )
    async def age_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        await self.toggle_role(interaction, select.values[0])

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.user_message_timestamps = defaultdict(list)

    async def setup_hook(self):
        self.add_view(RoleSelectView())

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
<@&1549872649877069924> - **je pro členy který dají booster na server**

👇 **Vyber si své role v menu níže:**"""
    
    await ctx.send(content=msg_text, view=RoleSelectView())
    await ctx.message.delete()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[CHYBA] Proměnná DISCORD_TOKEN nebyla nalezena!")
