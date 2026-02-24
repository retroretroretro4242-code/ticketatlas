
import discord
from discord.ext import commands
import os
import asyncio
import sqlite3
import datetime

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN environment variable bulunamadı!")

YETKILI_ROLLER = [
    1474831393644220599,
    1384294618195169311,
    1474830960393453619,
    1474831019017371678,
    1474831132062122005,
    1474831344273068063
]

KATEGORI_ADI = "Tickets"
LOG_KANAL = "ticket-logs"
ATLAS_TAG = "Atlas Project"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# DATABASE
conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    user_id INTEGER,
    channel_id INTEGER,
    created_at TEXT
)
""")
conn.commit()

def yetkili_mi(member):
    return any(role.id in YETKILI_ROLLER for role in member.roles)

async def log_yaz(guild, mesaj):
    kanal = discord.utils.get(guild.text_channels, name=LOG_KANAL)
    if not kanal:
        kanal = await guild.create_text_channel(LOG_KANAL)
    await kanal.send(mesaj)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.primary, custom_id="ticket_ac")
    async def ticket_ac(self, interaction: discord.Interaction, button: discord.ui.Button):

        cursor.execute("SELECT * FROM tickets WHERE user_id = ?", (interaction.user.id,))
        if cursor.fetchone():
            await interaction.response.send_message("Zaten açık ticketın var.", ephemeral=True)
            return

        guild = interaction.guild
        kategori = discord.utils.get(guild.categories, name=KATEGORI_ADI)

        if not kategori:
            kategori = await guild.create_category(KATEGORI_ADI)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role_id in YETKILI_ROLLER:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        kanal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=kategori,
            overwrites=overwrites
        )

        cursor.execute(
            "INSERT INTO tickets VALUES (?, ?, ?)",
            (interaction.user.id, kanal.id, str(datetime.datetime.utcnow()))
        )
        conn.commit()

        embed = discord.Embed(
            title=f"{ATLAS_TAG} | Destek",
            description="Yetkililer sizinle ilgilenecek.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )

        await kanal.send(interaction.user.mention, embed=embed, view=CloseView())
        await interaction.response.send_message("Ticket oluşturuldu.", ephemeral=True)
        await log_yaz(guild, f"📌 Yeni ticket: {kanal.mention}")

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Kapat", style=discord.ButtonStyle.danger, custom_id="ticket_kapat")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not yetkili_mi(interaction.user):
            await interaction.response.send_message("Sadece yetkililer kapatabilir.", ephemeral=True)
            return

        cursor.execute("DELETE FROM tickets WHERE channel_id = ?", (interaction.channel.id,))
        conn.commit()

        await interaction.response.send_message("Ticket kapanıyor...", ephemeral=True)
        await asyncio.sleep(2)

        await log_yaz(interaction.guild, f"📁 Ticket kapatıldı: {interaction.channel.name}")
        await interaction.channel.delete()

@bot.tree.command(name="ticketpanel", description="Ticket panelini gönderir.")
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{ATLAS_TAG} | Ticket Panel",
        description="Butona basarak ticket oluşturabilirsiniz.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

    bot.add_view(TicketView())
    bot.add_view(CloseView())

bot.run(TOKEN)
