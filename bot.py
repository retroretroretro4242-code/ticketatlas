import discord
from discord.ext import commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

SUNUCU_ID = 1384288019426574367
LOG_KANAL_ID = 1474827965643886864  # BURAYA LOG KANAL ID

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
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ticket_counter = 0
open_tickets = {}


# =========================
# CLAIM BUTTON
# =========================

class ClaimButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Claim",
            style=discord.ButtonStyle.success,
            custom_id="claim_ticket"
        )

    async def callback(self, interaction: discord.Interaction):

        if not any(role.id in YETKILI_ROLLER for role in interaction.user.roles):
            return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

        channel = interaction.channel
        open_tickets[channel.id]["claimed_by"] = interaction.user.id

        await interaction.response.send_message(
            f"🎯 Ticket {interaction.user.mention} tarafından claim edildi."
        )


# =========================
# CLOSE BUTTON
# =========================

class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Kapat",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket"
        )

    async def callback(self, interaction: discord.Interaction):

        if not any(role.id in YETKILI_ROLLER for role in interaction.user.roles):
            return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

        channel = interaction.channel
        messages = []

        async for msg in channel.history(limit=None, oldest_first=True):
            messages.append(f"[{msg.created_at}] {msg.author}: {msg.content}")

        transcript = "\n".join(messages)

        with open(f"transcript-{channel.id}.txt", "w", encoding="utf-8") as f:
            f.write(transcript)

        log_channel = bot.get_channel(LOG_KANAL_ID)
        if log_channel:
            await log_channel.send(
                f"📁 Transcript for {channel.name}",
                file=discord.File(f"transcript-{channel.id}.txt")
            )

        await channel.delete()


class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ClaimButton())
        self.add_item(CloseButton())


# =========================
# TICKET SELECT
# =========================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Destek", emoji="🎫"),
            discord.SelectOption(label="Şikayet", emoji="⚠️"),
            discord.SelectOption(label="Satın Alım", emoji="💎")
        ]

        super().__init__(
            placeholder="Kategori seç...",
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        if interaction.user.id in open_tickets:
            return await interaction.followup.send(
                "Zaten açık bir ticketin var.",
                ephemeral=True
            )

        global ticket_counter
        ticket_counter += 1

        kategori = discord.utils.get(interaction.guild.categories, name="ATLAS SUPPORT")
        if not kategori:
            kategori = await interaction.guild.create_category("ATLAS SUPPORT")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for rol_id in YETKILI_ROLLER:
            rol = interaction.guild.get_role(rol_id)
            if rol:
                overwrites[rol] = discord.PermissionOverwrite(read_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{ticket_counter}",
            category=kategori,
            overwrites=overwrites
        )

        open_tickets[interaction.user.id] = channel.id
        open_tickets[channel.id] = {"owner": interaction.user.id, "claimed_by": None}

        embed = discord.Embed(
            title=f"🎟 Ticket #{ticket_counter}",
            description=f"Sahibi: {interaction.user.mention}\nKategori: {self.values[0]}",
            color=0x5865F2
        )

        await channel.send(embed=embed, view=TicketButtons())

        await interaction.followup.send(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =========================
# SLASH KOMUT
# =========================

@bot.tree.command(
    name="ticketpanel",
    description="Atlas Ultra Support Panel",
    guild=discord.Object(id=SUNUCU_ID)
)
async def ticketpanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🚀 Atlas Project Ultra Support",
        description="Aşağıdan kategori seçerek ticket oluşturabilirsiniz.",
        color=0x5865F2
    )

    await interaction.response.send_message(embed=embed, view=TicketView())


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user}")
    await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
    bot.add_view(TicketView())
    bot.add_view(TicketButtons())


bot.run(TOKEN)
