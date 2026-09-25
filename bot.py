import sys
import os
import asyncio
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import defaultdict
import discord
from discord import app_commands
from discord.ext import commands

# --- KONFIGURACE SOUBORU CONFIGU ---
CONFIG_FILE = "bot_config.json"

DEFAULT_ROLES_MSG = """# role

<@&1539241329899474954> - **je vlastník serveru, který rozhoduje, co se na server přidá**

<@&1552268147179135046> - **je člen A-Teamu, který s majitelem dělá změny na serveru a hlídá ho**

<@&1539240450810978364> - **je člen A-Teamu, který může také provádět změny na serveru (na žádost majitele) a hlídá server**

<@&1552391311754133555> - **je člen A-Teamu, který testuje, zda všechno funguje**

<@&1549866576029814784> - **je role pro členy, kteří jsou aktivní na serveru a ve voice chatu (VC)**

<@&1539242304013992048> - **je role, kterou mají všichni na serveru**

<@&1543385078992871524> / <@&1543385813943984239> - **je pro členy, kteří si o roli požádají**

<@&1540028254885257256> / <@&1540028432614817862> / <@&1540028872312225914> / <@&1540028968273449002> / <@&1553041371986927657> - **je pro členy, kteří si požádají o barvu přezdívky na serveru**

<@&1553032262696566915> / <@&1553032409073586186> - **je pro členy, kteří si požádají o zobrazení svého věku**

<@&1549872649877069924> - **je pro členy, kteří dají serveru Server Boost**

👇 **Vyber si své role v menu níže:**"""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "token": "Discord Token",
        "anti_link": True,
        "anti_spam": True,
        "spam_msg_limit": 5,
        "spam_time_frame": 5,
        "anti_caps": False,
        "caps_threshold": 70,
        "anti_mentions": True,
        "max_mentions": 5,
        "bad_words_enabled": False,
        "bad_words": "badword1, badword2",
        "roles_channel_id": "1553012918906392630",
        "roles_message_text": DEFAULT_ROLES_MSG
    }

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- DISCORD SELECT MENU PRO ROLE ---
class RoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id_str: str):
        if not role_id_str.isdigit():
            await interaction.followup.send("⚠️ Zadané ID role není číslo.", ephemeral=True)
            return

        role = interaction.guild.get_role(int(role_id_str))
        if not role:
            await interaction.followup.send(f"⚠️ Role s ID `{role_id_str}` nebyla na serveru nalezena.", ephemeral=True)
            return

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.followup.send(f"❌ Role **{role.name}** ti byla odebrána.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.followup.send(f"✅ Role **{role.name}** ti byla přidána!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ **Chyba Oprávnění:** Bot nemá práva upravit tuto roli! Posuňte roli bota v nastavení serveru výše než je cílová role.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Nepodařilo se upravit roli: {e}", ephemeral=True)

    @discord.ui.select(
        placeholder="🎨 Vyber si barvu jména...",
        custom_id="select_color_role",
        options=[
            discord.SelectOption(label="Červená", value="1540028254885257256", description="Červená barva přezdívky", emoji="🔴"),
            discord.SelectOption(label="Modrá", value="1540028432614817862", description="Modrá barva přezdívky", emoji="🔵"),
            discord.SelectOption(label="Zelená", value="1540028872312225914", description="Zelená barva přezdívky", emoji="🟢"),
            discord.SelectOption(label="Fialová", value="1540028968273449002", description="Fialová barva přezdívky", emoji="🟣"),
            discord.SelectOption(label="Žlutá", value="1553041371986927657", description="Žlutá barva přezdívky", emoji="🟡"),
        ]
    )
    async def color_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        await self.toggle_role(interaction, select.values[0])

    @discord.ui.select(
        placeholder="🎂 Vyber si svůj věk...",
        custom_id="select_age_role",
        options=[
            discord.SelectOption(label="13-17+", value="1553032262696566915", description="Věková skupina 13-17+", emoji="🔞"),
            discord.SelectOption(label="18+", value="1553032409073586186", description="Věková skupina 18+", emoji="🔞"),
        ]
    )
    async def age_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        await self.toggle_role(interaction, select.values[0])

# --- TŘÍDA DISCORD BOTA ---
class DiscordBot(commands.Bot):
    def __init__(self, gui_app):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.gui_app = gui_app
        self.user_message_timestamps = defaultdict(list)

    async def setup_hook(self):
        self.add_view(RoleSelectView())

    async def on_ready(self):
        self.gui_app.log(f"[BOT] Přihlášen jako: {self.user} (ID: {self.user.id})")
        self.gui_app.update_status(True)

    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Ignorovat administrátory
        if message.author.guild_permissions.administrator:
            await self.process_commands(message)
            return

        cfg = self.gui_app.config

        # 1. Anti-Link Ochrana
        if cfg.get("anti_link", True):
            if "http://" in message.content.lower() or "https://" in message.content.lower() or "discord.gg/" in message.content.lower():
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, posílání odkazů je zakázáno!", delete_after=5)
                    self.gui_app.log(f"[BEZPEČNOST] Smazán odkaz od {message.author} v #{message.channel}")
                    self.gui_app.inc_stat("links")
                    return
                except Exception as e:
                    self.gui_app.log(f"[CHYBA] Nelze smazat odkaz: {e}")

        # 2. Anti-Spam Ochrana
        if cfg.get("anti_spam", True):
            now = time.time()
            limit_msg = int(cfg.get("spam_msg_limit", 5))
            time_frame = int(cfg.get("spam_time_frame", 5))
            
            user_timestamps = self.user_message_timestamps[message.author.id]
            user_timestamps.append(now)
            self.user_message_timestamps[message.author.id] = [t for t in user_timestamps if now - t <= time_frame]

            if len(self.user_message_timestamps[message.author.id]) > limit_msg:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, nepřestávej spamovat!", delete_after=5)
                    self.gui_app.log(f"[BEZPEČNOST] Zaznamenán spam od {message.author} v #{message.channel}")
                    self.gui_app.inc_stat("spam")
                    return
                except Exception as e:
                    self.gui_app.log(f"[CHYBA] Nelze smazat spam: {e}")

        # 3. Anti-Caps Lock Ochrana
        if cfg.get("anti_caps", False) and len(message.content) > 6:
            threshold = int(cfg.get("caps_threshold", 70))
            uppercase_chars = sum(1 for c in message.content if c.isupper())
            percentage = (uppercase_chars / len(message.content)) * 100

            if percentage >= threshold:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, nepoužívej příliš mnoho velkých písmen (Caps Lock)!", delete_after=5)
                    self.gui_app.log(f"[BEZPEČNOST] Smazána zpráva s příliš mnoha Caps Locky od {message.author}")
                    self.gui_app.inc_stat("caps")
                    return
                except Exception as e:
                    self.gui_app.log(f"[CHYBA] Nelze smazat Caps Lock zprávu: {e}")

        # 4. Anti-Mass Mentions Ochrana
        if cfg.get("anti_mentions", True):
            max_mentions = int(cfg.get("max_mentions", 5))
            total_mentions = len(message.mentions) + len(message.role_mentions)

            if total_mentions > max_mentions:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, neoznačuj příliš mnoho lidí/rolí najednou!", delete_after=5)
                    self.gui_app.log(f"[BEZPEČNOST] Smazána zpráva s nadměrným označováním od {message.author}")
                    self.gui_app.inc_stat("mentions")
                    return
                except Exception as e:
                    self.gui_app.log(f"[CHYBA] Nelze smazat zprávu s označením: {e}")

        # 5. Bad Words / Zakázaná slova Filter
        if cfg.get("bad_words_enabled", False):
            raw_bad_words = cfg.get("bad_words", "")
            bad_words_list = [w.strip().lower() for w in raw_bad_words.split(",") if w.strip()]
            
            content_lower = message.content.lower()
            if any(word in content_lower for word in bad_words_list):
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, tvá zpráva obsahovala zakázané slovo!", delete_after=5)
                    self.gui_app.log(f"[BEZPEČNOST] Smazána zpráva se zakázaným slovem od {message.author}")
                    self.gui_app.inc_stat("badwords")
                    return
                except Exception as e:
                    self.gui_app.log(f"[CHYBA] Nelze smazat zprávu se zakázaným slovem: {e}")

        await self.process_commands(message)

# --- GRAFICKÉ ROZHRANÍ (TKINTER DASHBOARD) ---
class ModernBotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Bot Management & Security Dashboard")
        self.root.geometry("1000x720")
        self.root.minsize(850, 600)

        self.config = load_config()

        self.bg_dark = "#1e1e2e"
        self.bg_sidebar = "#181825"
        self.bg_card = "#313244"
        self.fg_text = "#cdd6f4"
        self.fg_subtle = "#a6adc8"
        self.accent_color = "#89b4fa"

        self.root.configure(bg=self.bg_dark)

        self.bot_thread = None
        self.bot_loop = None
        self.bot = None
        self.is_running = False

        self.stats = {"links": 0, "spam": 0, "caps": 0, "mentions": 0, "badwords": 0}

        self.anti_link_var = tk.BooleanVar(value=self.config.get("anti_link", True))
        self.anti_spam_var = tk.BooleanVar(value=self.config.get("anti_spam", True))
        self.anti_caps_var = tk.BooleanVar(value=self.config.get("anti_caps", False))
        self.anti_mentions_var = tk.BooleanVar(value=self.config.get("anti_mentions", True))
        self.bad_words_var = tk.BooleanVar(value=self.config.get("bad_words_enabled", False))

        self.build_gui()

    def build_gui(self):
        self.sidebar = tk.Frame(self.root, bg=self.bg_sidebar, width=200)
        self.sidebar.pack(side="left", fill="y")

        self.main_area = tk.Frame(self.root, bg=self.bg_dark)
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        lbl_brand = tk.Label(self.sidebar, text="🤖 Bot Panel", font=("Segoe UI", 14, "bold"), bg=self.bg_sidebar, fg=self.accent_color)
        lbl_brand.pack(padx=15, pady=20, anchor="w")

        self.lbl_status = tk.Label(self.sidebar, text="● Offline", font=("Segoe UI", 10, "bold"), bg=self.bg_sidebar, fg="#f38ba8")
        self.lbl_status.pack(padx=15, pady=(0, 20), anchor="w")

        self.notebook = ttk.Notebook(self.main_area)
        self.notebook.pack(fill="both", expand=True)

        self.page_dashboard = tk.Frame(self.notebook, bg=self.bg_dark)
        self.page_security = tk.Frame(self.notebook, bg=self.bg_dark)
        self.page_roles = tk.Frame(self.notebook, bg=self.bg_dark)
        self.page_settings = tk.Frame(self.notebook, bg=self.bg_dark)
        self.page_logs = tk.Frame(self.notebook, bg=self.bg_dark)

        self.notebook.add(self.page_dashboard, text=" Dashboard ")
        self.notebook.add(self.page_security, text=" 🛡️ Ochrana Serveru ")
        self.notebook.add(self.page_roles, text=" Role & Zprávy ")
        self.notebook.add(self.page_settings, text=" Nastavení ")
        self.notebook.add(self.page_logs, text=" Živé Logy ")

        self.build_dashboard_page()
        self.build_security_page()
        self.build_roles_page()
        self.build_settings_page()
        self.build_logs_page()

    def build_dashboard_page(self):
        card_control = tk.Frame(self.page_dashboard, bg=self.bg_card, padx=15, pady=15)
        card_control.pack(fill="x", pady=10)

        tk.Label(card_control, text="Ovládání Bota", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w")

        self.btn_toggle = tk.Button(card_control, text="🚀 Spustit Bota", font=("Segoe UI", 10, "bold"), bg="#a6e3a1", fg="#11111b", command=self.toggle_bot, relief="flat", padx=15, pady=5)
        self.btn_toggle.pack(anchor="w", pady=(10, 0))

        card_stats = tk.Frame(self.page_dashboard, bg=self.bg_card, padx=15, pady=15)
        card_stats.pack(fill="x", pady=10)

        tk.Label(card_stats, text="Statistiky Zásahů Ochrany", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w", pady=(0, 10))

        self.lbl_stat_links = tk.Label(card_stats, text="🔗 Zablokované odkazy: 0", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text)
        self.lbl_stat_links.pack(anchor="w", pady=2)

        self.lbl_stat_spam = tk.Label(card_stats, text="🚫 Zablokovaný spam: 0", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text)
        self.lbl_stat_spam.pack(anchor="w", pady=2)

        self.lbl_stat_caps = tk.Label(card_stats, text="🔤 Smazané Caps-Lock zprávy: 0", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text)
        self.lbl_stat_caps.pack(anchor="w", pady=2)

        self.lbl_stat_badwords = tk.Label(card_stats, text="🤬 Smazaná zakázaná slova: 0", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text)
        self.lbl_stat_badwords.pack(anchor="w", pady=2)

    def build_security_page(self):
        card_sec1 = tk.Frame(self.page_security, bg=self.bg_card, padx=15, pady=15)
        card_sec1.pack(fill="x", pady=10)

        tk.Label(card_sec1, text="🛡️ Nastavení Ochranných Modulů", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w", pady=(0, 10))

        cb_link = tk.Checkbutton(card_sec1, text="Blokovat nepovolené odkazy (Anti-Link)", variable=self.anti_link_var, bg=self.bg_card, fg=self.fg_text, selectcolor=self.bg_dark, activebackground=self.bg_card, activeforeground=self.fg_text)
        cb_link.pack(anchor="w", pady=2)

        f_spam = tk.Frame(card_sec1, bg=self.bg_card)
        f_spam.pack(fill="x", pady=5)
        cb_spam = tk.Checkbutton(f_spam, text="Ochrana proti Spamu (Anti-Spam)", variable=self.anti_spam_var, bg=self.bg_card, fg=self.fg_text, selectcolor=self.bg_dark, activebackground=self.bg_card, activeforeground=self.fg_text)
        cb_spam.pack(side="left")

        tk.Label(f_spam, text=" Limit:", bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_spam_limit = tk.Entry(f_spam, width=4, font=("Consolas", 9), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat")
        self.entry_spam_limit.pack(side="left", padx=2)
        self.entry_spam_limit.insert(0, str(self.config.get("spam_msg_limit", 5)))

        tk.Label(f_spam, text="zpráv za", bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_spam_time = tk.Entry(f_spam, width=4, font=("Consolas", 9), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat")
        self.entry_spam_time.pack(side="left", padx=2)
        self.entry_spam_time.insert(0, str(self.config.get("spam_time_frame", 5)))
        tk.Label(f_spam, text="sekund", bg=self.bg_card, fg=self.fg_text).pack(side="left")

        f_caps = tk.Frame(card_sec1, bg=self.bg_card)
        f_caps.pack(fill="x", pady=5)
        cb_caps = tk.Checkbutton(f_caps, text="Ochrana proti Caps Locku", variable=self.anti_caps_var, bg=self.bg_card, fg=self.fg_text, selectcolor=self.bg_dark, activebackground=self.bg_card, activeforeground=self.fg_text)
        cb_caps.pack(side="left")

        tk.Label(f_caps, text=" Hranice (% velkých písmen):", bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_caps_threshold = tk.Entry(f_caps, width=4, font=("Consolas", 9), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat")
        self.entry_caps_threshold.pack(side="left", padx=2)
        self.entry_caps_threshold.insert(0, str(self.config.get("caps_threshold", 70)))

        f_mentions = tk.Frame(card_sec1, bg=self.bg_card)
        f_mentions.pack(fill="x", pady=5)
        cb_mentions = tk.Checkbutton(f_mentions, text="Ochrana proti Hromadnému Označování", variable=self.anti_mentions_var, bg=self.bg_card, fg=self.fg_text, selectcolor=self.bg_dark, activebackground=self.bg_card, activeforeground=self.fg_text)
        cb_mentions.pack(side="left")

        tk.Label(f_mentions, text=" Max. označení v zprávě:", bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_max_mentions = tk.Entry(f_mentions, width=4, font=("Consolas", 9), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat")
        self.entry_max_mentions.pack(side="left", padx=2)
        self.entry_max_mentions.insert(0, str(self.config.get("max_mentions", 5)))

        card_sec2 = tk.Frame(self.page_security, bg=self.bg_card, padx=15, pady=15)
        card_sec2.pack(fill="x", pady=10)

        cb_badwords = tk.Checkbutton(card_sec2, text="Zapnout Filtr Zakázaných Slov", variable=self.bad_words_var, bg=self.bg_card, fg=self.fg_text, selectcolor=self.bg_dark, activebackground=self.bg_card, activeforeground=self.fg_text)
        cb_badwords.pack(anchor="w")

        tk.Label(card_sec2, text="Seznam zakázaných slov (oddělené čárkou):", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_subtle).pack(anchor="w", pady=(5, 2))

        self.entry_bad_words = tk.Entry(card_sec2, font=("Consolas", 10), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat", width=60)
        self.entry_bad_words.pack(anchor="w", pady=5, ipady=3)
        self.entry_bad_words.insert(0, self.config.get("bad_words", ""))

        btn_save_sec = tk.Button(self.page_security, text="💾 Uložit Nastavení Ochrany", font=("Segoe UI", 9, "bold"), bg=self.accent_color, fg="#11111b", command=self.save_settings, relief="flat", padx=15, pady=6)
        btn_save_sec.pack(anchor="e", pady=10)

    def build_roles_page(self):
        card_channel = tk.Frame(self.page_roles, bg=self.bg_card, padx=15, pady=15)
        card_channel.pack(fill="x", pady=10)

        tk.Label(card_channel, text="ID Kanálu pro zprávu s rolemi", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w")
        
        self.entry_channel = tk.Entry(card_channel, font=("Consolas", 10), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat", width=35)
        self.entry_channel.pack(anchor="w", pady=5, ipady=3)
        self.entry_channel.insert(0, self.config.get("roles_channel_id", "1553012918906392630"))

        card_msg = tk.Frame(self.page_roles, bg=self.bg_card, padx=15, pady=15)
        card_msg.pack(fill="both", expand=True, pady=10)

        tk.Label(card_msg, text="Text zprávy k rolím", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w")

        self.txt_roles_msg = scrolledtext.ScrolledText(card_msg, font=("Consolas", 9), bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat", height=10)
        self.txt_roles_msg.pack(fill="both", expand=True, pady=10)
        self.txt_roles_msg.insert(tk.END, self.config.get("roles_message_text", DEFAULT_ROLES_MSG))

        btn_send_roles = tk.Button(card_msg, text="📤 Odeslat Zprávu s Rolemi na Discord", font=("Segoe UI", 9, "bold"), bg=self.accent_color, fg="#11111b", command=self.send_roles_message, relief="flat", padx=15, pady=5)
        btn_send_roles.pack(anchor="e")

    def build_settings_page(self):
        card_token = tk.Frame(self.page_settings, bg=self.bg_card, padx=15, pady=15)
        card_token.pack(fill="x", pady=10)

        tk.Label(card_token, text="Discord Bot Token", font=("Segoe UI", 11, "bold"), bg=self.bg_card, fg=self.fg_text).pack(anchor="w")

        self.entry_token = tk.Entry(card_token, font=("Consolas", 10), show="*", bg=self.bg_dark, fg=self.fg_text, insertbackground=self.fg_text, relief="flat", width=55)
        self.entry_token.pack(anchor="w", pady=(5, 10), ipady=4)
        self.entry_token.insert(0, self.config.get("token", ""))

        btn_save = tk.Button(card_token, text="💾 Uložit Nastavení", font=("Segoe UI", 9, "bold"), bg=self.accent_color, fg="#11111b", command=self.save_settings, relief="flat", padx=10, pady=3)
        btn_save.pack(anchor="w")

    def build_logs_page(self):
        self.log_area = scrolledtext.ScrolledText(self.page_logs, font=("Consolas", 9), bg=self.bg_sidebar, fg=self.fg_text, insertbackground=self.fg_text, relief="flat")
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("[SYSTEM] Aplikace spuštěna. Připravena k provozu.")

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)

    def inc_stat(self, key):
        if key in self.stats:
            self.stats[key] += 1
            self.lbl_stat_links.config(text=f"🔗 Zablokované odkazy: {self.stats['links']}")
            self.lbl_stat_spam.config(text=f"🚫 Zablokovaný spam: {self.stats['spam']}")
            self.lbl_stat_caps.config(text=f"🔤 Smazané Caps-Lock zprávy: {self.stats['caps']}")
            self.lbl_stat_badwords.config(text=f"🤬 Smazaná zakázaná slova: {self.stats['badwords']}")

    def save_settings(self):
        self.config["token"] = self.entry_token.get().strip()
        self.config["anti_link"] = self.anti_link_var.get()
        self.config["anti_spam"] = self.anti_spam_var.get()
        self.config["spam_msg_limit"] = self.entry_spam_limit.get().strip()
        self.config["spam_time_frame"] = self.entry_spam_time.get().strip()
        self.config["anti_caps"] = self.anti_caps_var.get()
        self.config["caps_threshold"] = self.entry_caps_threshold.get().strip()
        self.config["anti_mentions"] = self.anti_mentions_var.get()
        self.config["max_mentions"] = self.entry_max_mentions.get().strip()
        self.config["bad_words_enabled"] = self.bad_words_var.get()
        self.config["bad_words"] = self.entry_bad_words.get().strip()
        self.config["roles_channel_id"] = self.entry_channel.get().strip()
        self.config["roles_message_text"] = self.txt_roles_msg.get("1.0", tk.END).strip()
        
        save_config(self.config)
        self.log("[SYSTEM] Nastavení uloženo.")

    def send_roles_message(self):
        if not self.is_running or not self.bot:
            messagebox.showerror("Chyba", "Bot musí nejprve běžet! Spusťte ho na záložce Dashboard.")
            return

        channel_id = self.entry_channel.get().strip()
        if not channel_id.isdigit():
            messagebox.showwarning("Chyba ID", "Zadejte platné číselné ID Discord kanálu.")
            return

        self.save_settings()
        msg_text = self.config["roles_message_text"]

        async def _send():
            try:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    channel = await self.bot.fetch_channel(int(channel_id))
                
                view = RoleSelectView()
                await channel.send(content=msg_text, view=view)
                self.log(f"[ROLES] Zpráva odeslána do kanálu {channel.name}.")
                messagebox.showinfo("Úspěch", "Zpráva s rolemi byla úspěšně odeslána na Discord!")
            except Exception as e:
                self.log(f"[CHYBA ODESLÁNÍ] {e}")
                messagebox.showerror("Chyba při odesílání", f"Odeslání selhalo:\n{e}")

        asyncio.run_coroutine_threadsafe(_send(), self.bot_loop)

    def update_status(self, running):
        self.is_running = running
        if running:
            self.lbl_status.config(text="● Online", fg="#a6e3a1")
            self.btn_toggle.config(text="🛑 Zastavit Bota", bg="#f38ba8")
        else:
            self.lbl_status.config(text="● Offline", fg="#f38ba8")
            self.btn_toggle.config(text="🚀 Spustit Bota", bg="#a6e3a1")

    def toggle_bot(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        token = self.entry_token.get().strip()
        if not token:
            messagebox.showwarning("Chyba Tokenu", "Před spuštěním bota musíte zadat Token v záložce Nastavení!")
            return

        self.save_settings()
        self.log("[SYSTEM] Spouštění bota...")

        self.bot_loop = asyncio.new_event_loop()
        self.bot = DiscordBot(gui_app=self)

        def run_loop():
            asyncio.set_event_loop(self.bot_loop)
            try:
                self.bot_loop.run_until_complete(self.bot.start(token))
            except Exception as e:
                self.log(f"[CHYBA SPUŠTĚNÍ] {e}")
                self.root.after(0, lambda: self.update_status(False))

        self.bot_thread = threading.Thread(target=run_loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.log("[SYSTEM] Zastavování bota...")
        if self.bot and self.bot_loop:
            asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot_loop)
        self.update_status(False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernBotDashboard(root)
    root.mainloop()
