import discord
from discord.ext import tasks, commands
from discord.ui import Button, View, Modal, TextInput
import datetime
import asyncio
import aiohttp
import hashlib
import struct
import os

# ==========================================================
# ⚙️ USTAWIENIA TWOJEGO BOTA - OCALENIRP (ZSYNCHRONIZOWANE)
# ==========================================================
CFT_API_KEY = os.environ.get("CFT_API_KEY")
CFT_APP_ID = "6ac8061a7e9c95b7738882da"
CFT_SERVER_ID = "5b8c5693-2dce-43b7-b1c9-27da85b28fea" # Aktualny Server ID z planszy API!

ID_STATUS_CHAN = 1558863458739421317
ID_GRACZE_CHAN = 1558863588829958334
ID_RESTART_CHAN = 1558863694073565284

# TWOJE SYSTEMOWE RANGI DISCORDA (ZGODNIE Z NOWĄ HIERARCHIĄ):
ID_ROLA_BRAK_WL = 1485342974698061915  # Ranga po regulaminie
ID_ROLA_OCALONY = 1558883363149054053  # Ranga po zdaniu rekrutacji (Pełny Dostęp)
ID_ROLA_ZBANOWANY = 1558883400000000000 # Ranga @Ban
ID_ROLA_WARN = 1558883500000000000      # Ranga @Warn / @Pod Obserwacją

ID_KANAL_PODANIA = 1558886423317455079
ID_KANAL_ADMIN = 1558887411935740014
ID_KATEGORIA_TICKETY = 1558887411935740014 

# Aktualny port i IP do gry przydzielone po wipe przez GTXGaming
SERVER_IP_PORT = "91.98.178.181:3247"

status_message_id = None
status_channel_id = None
ticket_counter = 1
spam_cooldown = {}
radio_cooldowns = {}
# ==========================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SYSTEM OCHRONY CZATU: ANTY-LINK I ANTY-SPAM ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    content_lower = message.content.lower()
    if "discord.gg/" in content_lower or "://discord.com" in content_lower or "http://" in content_lower or "https://" in content_lower:
        try:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, zakaz udostępniania linków i reklam zewnętrznych!", delete_after=5)
            return
        except: pass

    user_id = message.author.id
    now = datetime.datetime.utcnow()
    if user_id not in spam_cooldown: spam_cooldown[user_id] = []
    spam_cooldown[user_id] = [t for t in spam_cooldown[user_id] if (now - t).total_seconds() < 3]
    spam_cooldown[user_id].append(now)

    if len(spam_cooldown[user_id]) > 5:
        try:
            await message.author.timeout(datetime.timedelta(minutes=10), reason="Anty-Spam Protection")
            await message.channel.send(f"🤫 {message.author.mention} wyciszony automatycznie na 10 minut za flood na czacie!", delete_after=10)
            return
        except: pass
    await bot.process_commands(message)

# --- SYSTEM WITANIA NOWYCH GRACZY NA PW (NAPRAWIONY - UNIWERSALNY) ---
@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title="📦 Witaj na serwerze OcaleniRP!",
            description=(
                f"Cieszymy się, że chcesz dołączyć do naszej społeczności Survival RP w świecie DayZ, {member.mention}!\n\n"
                "**Oto co musisz zrobić krok po kroku, aby dołączyć do gry:**\n"
                "1️⃣ Przejdź na kanał z regulaminem, **dokładnie zapoznaj się z jego treścią**, a gdy już go przeczytasz, kliknij zielony przycisk **Akceptuję Regulamin** – otrzymasz rolę `@Brak WL`.\n"
                "2️⃣ Następnie przejdź na kanał rekrutacyjny, kliknij przycisk i wypełnij formularz podania WL.\n"
                "3️⃣ Po zatwierdzeniu formularza przez administrację, Twój WL Checker wezwie Cię na krótką rozmowę głosową z regulaminu!\n\n"
                "Życzymy powodzenia i do zobaczenia na szlaku! ☀️"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Bot OcaleniRP • Automatyczny system weryfikacji")
        await member.send(embed=embed)
    except: pass

# --- KLIMATYCZNY SYSTEM RADIA POLOWEGO IC ---
class RadioModal(Modal):
    def __init__(self):
        super().__init__(title="📻 Nadaj komunikat radiowy (IC)")
        self.message_input = TextInput(label="Treść komunikatu (Zasady IC)", style=discord.TextStyle.long, placeholder="Wpisz treść szumiącej transmisji radiowej...", min_length=10, max_length=400, required=True)
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        now = datetime.datetime.utcnow()
        if user_id in radio_cooldowns:
            time_passed = (now - radio_cooldowns[user_id]).total_seconds()
            if time_passed < 86400:
                hours_left = int((86400 - time_passed) // 3600)
                minutes_left = int(((86400 - time_passed) % 3600) // 60)
                await interaction.response.send_message(f"❌ Akumulator w Twoim radiu się ładuje. Następna transmisja za: **{hours_left}h i {minutes_left}min**.", ephemeral=True)
                return

        radio_cooldowns[user_id] = now
        await interaction.response.send_message("📡 *Trwa szukanie wolnej częstotliwości... Transmisja nadana!*", ephemeral=True)
        now_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).strftime("%H:%M")
        embed = discord.Embed(
            title="📻 [Poczta Polowa] Odbieranie sygnału...",
            description=f"*Trzaski... Szum... Słychać niewyraźny głos w głośniku...*\n\n**„** {self.message_input.value} **”**\n\n*Sygnał zanika... Odbiór bezpowrotny.*",
            color=discord.Color.dark_grey(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Częstotliwość 87.8 MHz • Nadano o {now_time}")
        if isinstance(interaction.channel, discord.TextChannel): await interaction.channel.send(embed=embed)

class RadioPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📻 Nadaj komunikat", style=discord.Style.primary, custom_id="radio_transmit")
    async def radio_transmit(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(RadioModal())

# --- ZAAWANSOWANY SYSTEM TICKETÓW (3 KATEGORIE) ---
class TicketPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    async def create_ticket_channel(self, interaction: discord.Interaction, prefix: str, category_name: str):
        global ticket_counter
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild: return
        category = guild.get_channel(ID_KATEGORIA_TICKETY)
        channel_name = f"{prefix}-{interaction.user.name.lower().replace(' ', '-')}-{ticket_counter:04d}"
        ticket_counter += 1
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category if isinstance(category, discord.CategoryChannel) else None, overwrites=overwrites)
        embed = discord.Embed(title=f"🎫 Nowe Zgłoszenie - Kategoria: {category_name}", description=f"Witaj {interaction.user.mention}! Opisz swój problem lub zgłoszenie. Administracja serwera OcaleniRP pojawi się tutaj tak szybko, jak to możliwe.", color=discord.Color.blue())
        await ticket_channel.send(embed=embed, view=TicketCloseView())
        await interaction.followup.send(f"✅ Twój prywatny ticket został pomyślnie otwarty: {ticket_channel.mention}", ephemeral=True)

    @discord.ui.button(label="🐛 Zgłoś Błąd", style=discord.Style.primary, custom_id="ticket_bug")
    async def ticket_bug(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket_channel(interaction, "blad", "Zgłoszenie Błędu")
    @discord.ui.button(label="👤 Zgłoś Gracza", style=discord.Style.danger, custom_id="ticket_player")
    async def ticket_player(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket_channel(interaction, "gracz", "Skarga na Gracza")
    @discord.ui.button(label="❓ Pomoc Ogólna", style=discord.Style.success, custom_id="ticket_help")
    async def ticket_help(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket_channel(interaction, "pomoc", "Pomoc Ogólna")

class TicketCloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Zamknij zgłoszenie", style=discord.Style.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Zgłoszenie zostanie zamknięte i usunięte za 5 sekund...**")
        await asyncio.sleep(5)
        if isinstance(interaction.channel, discord.TextChannel): await interaction.channel.delete()

# --- BEZPIECZNA INTEGRACJA Z API CFTOOLS ---
async def get_cftools_token(session):
    auth_url = "https://cftools.cloud"
    auth_payload = {"application_id": CFT_APP_ID, "secret": CFT_API_KEY}
    async with session.post(auth_url, json=auth_payload, timeout=5) as auth_resp:
        if auth_resp.status == 200:
            auth_data = await auth_resp.json()
            return auth_data.get("token")
    return None

async def add_player_to_cftools_wl(steam_id: str, character_name: str):
    try:
        async with aiohttp.ClientSession() as session:
            token = await get_cftools_token(session)
            if not token: return False
            wl_url = f"https://cftools.cloud{CFT_SERVER_ID}/whitelist"
