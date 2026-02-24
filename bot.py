import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")

SUNUCU_ID = 1384288019426574367  # BURAYA SUNUCU ID

YETKILI_ROLLER = [
    1474831393644220599,
    1384294618195169311,
    1474830960393453619,
    1474831019017371678,
    1474831132062122005,
    1474831344273068063
]

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# TICKET DROPDOWN
# =========================

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ücretsiz Pack", emoji="📦", description="Özel başvuru işlemleri"),
            discord.SelectOption(label="Şikayet", emoji="⚠️", description="Şikayet ve geri bildirim"),
            discord.SelectOption(label="Talep", emoji="🎫", description="Genel sorular ve yardım")
        ]

        super().__init__(
            placeholder="Talep türünü seçin...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        kategori = discord.utils.get(interaction.guild.categories, name="TICKETS")

        if not kategori:
            kategori = await interaction.guild.create_category("TICKETS")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for rol_id in YETKILI_ROLLER:
            rol = interaction.guild.get_role(rol_id)
            if rol:
                overwrites[rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        kanal = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=kategori,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Atlas Project Destek",
            description=f"{interaction.user.mention} destek talebi oluşturdu.\n\nYetkililer en kısa sürede ilgilenecek.",
            color=0x2f3136
        )

        embed.set_footer(text="Atlas Project Support System")

        await kanal.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=CloseView()
        )

        await interaction.followup.send(f"Ticket oluşturuldu: {kanal.mention}", ephemeral=True)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


# =========================
# CLOSE BUTTON
# =========================

class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ticket Kapat", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.delete()


class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseButton())


# =========================
# SLASH KOMUT
# =========================

@bot.tree.command(name="ticketpanel", description="Atlas Project Ticket Panel", guild=discord.Object(id=SUNUCU_ID))
async def ticketpanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎟 Atlas Project Destek Sistemi",
        description="Aşağıdaki menüden destek türünü seçerek ticket oluşturabilirsiniz.",
        color=0x2f3136
    )

    await interaction.response.send_message(embed=embed, view=TicketView())


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")

    try:
        guild = discord.Object(id=SUNUCU_ID)
        await bot.tree.sync(guild=guild)
        print("Komutlar sunucuya sync edildi.")
    except Exception as e:
        print(e)

    bot.add_view(TicketView())
    bot.add_view(CloseView())


bot.run(TOKEN)
