import discord
from discord.ext import commands
import os
import asyncio
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


# ================= YARDIMCI =================

def yetkili_mi(member):
    return any(role.id in YETKILI_ROLLER for role in member.roles)


async def log_yaz(guild, mesaj):
    kanal = discord.utils.get(guild.text_channels, name=LOG_KANAL)
    if not kanal:
        kanal = await guild.create_text_channel(LOG_KANAL)
    await kanal.send(mesaj)


# ================= DROPDOWN =================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Ücretsiz Pack",
                description="Özel başvuru işlemleri",
                emoji="📦",
                value="pack"
            ),
            discord.SelectOption(
                label="Şikayet",
                description="Şikayet ve geri bildirim",
                emoji="⚠️",
                value="sikayet"
            ),
            discord.SelectOption(
                label="Talep",
                description="Genel sorular ve yardım",
                emoji="🎫",
                value="talep"
            )
        ]

        super().__init__(
            placeholder="Talep türünü seçin...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        secim = self.values[0]
        await create_ticket(interaction, secim)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ================= TICKET OLUŞTUR =================

async def create_ticket(interaction, tip):
    guild = interaction.guild
    kategori = discord.utils.get(guild.categories, name=KATEGORI_ADI)

    if not kategori:
        kategori = await guild.create_category(KATEGORI_ADI)

    # Aynı kullanıcı tekrar açamasın
    for channel in kategori.text_channels:
        if interaction.user.name in channel.name:
            await interaction.response.send_message(
                "Zaten açık bir ticketın var.",
                ephemeral=True
            )
            return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    for role_id in YETKILI_ROLLER:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    kanal = await guild.create_text_channel(
        name=f"{tip}-{interaction.user.name}",
        category=kategori,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title=f"{ATLAS_TAG} | {tip.upper()}",
        description="Yetkililer en kısa sürede sizinle ilgilenecektir.",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )

    embed.set_footer(text="Ticket kapatmak için 🔒 butonunu kullanın.")

    await kanal.send(interaction.user.mention, embed=embed, view=CloseView())
    await interaction.response.send_message("Ticket oluşturuldu.", ephemeral=True)

    await log_yaz(guild, f"📌 Yeni ticket açıldı: {kanal.mention}")


# ================= KAPAT BUTONU =================

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Kapat", style=discord.ButtonStyle.danger)
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not yetkili_mi(interaction.user):
            await interaction.response.send_message(
                "Sadece yetkililer ticket kapatabilir.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("Ticket kapanıyor...", ephemeral=True)
        await asyncio.sleep(2)

        await log_yaz(interaction.guild, f"📁 Ticket kapatıldı: {interaction.channel.name}")
        await interaction.channel.delete()


# ================= SLASH PANEL =================

@bot.tree.command(name="ticketpanel", description="Ticket panelini gönderir.")
async def ticketpanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="ATLAS PROJECT",
        description="Aşağıdaki 'Destek Talebini Oluştur' butonuna basarak talebini oluşturabilirsin.",
        color=discord.Color.blue()
    )

    embed.set_image(url="BURAYA_BANNER_URL")  # Banner URL ekle

    await interaction.response.send_message(embed=embed, view=TicketView())


# ================= READY =================

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")
    await bot.tree.sync()
    bot.add_view(TicketView())
    bot.add_view(CloseView())


bot.run(TOKEN)
