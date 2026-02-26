import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")  # Railway env variable

# =======================
# SUNUCU ve LOG AYARLARI
# =======================
SUNUCU_ID = 1384288019426574367
LOG_CHANNEL_ID = 1474827965643886864

# Yetkili roller (ticketleri onay/red ve kapatma yetkisi olan roller)
YETKILI_ROLLER = [
    1474831393644220599,
    1384294618195169311,
    1474830960393453619,
    1474831019017371678,
    1474831132062122005,
    1474831344273068063
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =======================
# Ticket view ve onay/red
# =======================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Ekip Alım", style=discord.ButtonStyle.green, custom_id="ekip_alim"))
        self.add_item(Button(label="Yetkili Alım", style=discord.ButtonStyle.blurple, custom_id="yetkili_alim"))
        self.add_item(Button(label="Diğer", style=discord.ButtonStyle.gray, custom_id="diger"))

class CloseTicket(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🔒 Ticket Kapat", style=discord.ButtonStyle.danger, custom_id="ticket_kapat"))

class ApprovalView(View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.add_item(Button(label="✅ Onayla", style=discord.ButtonStyle.green, custom_id=f"onay_{user.id}"))
        self.add_item(Button(label="❌ Reddet", style=discord.ButtonStyle.red, custom_id=f"red_{user.id}"))

# =======================
# Ticket açma komutu
# =======================
@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title="🎫 Ticket Aç",
        description=(
            "Aşağıdaki butonlardan başvurun türünü seçebilirsin:\n\n"
            "🟩 **Ekip Alım**: Sunucuda ekibin bir parçası olmak istiyorsan.\n"
            "🟦 **Yetkili Alım**: Sunucuda yetkili olmak istiyorsan.\n"
            "⬜ **Diğer**: Farklı sorun veya talepler için."
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed, view=TicketView())

# =======================
# Etkileşim (button) işlemleri
# =======================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data["custom_id"]
    guild = bot.get_guild(SUNUCU_ID)
    log_channel = guild.get_channel(LOG_CHANNEL_ID)

    if custom_id in ["ekip_alim", "yetkili_alim", "diger"]:
        kanal_adi = f"ticket-{interaction.user.name}".lower()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for rol_id in YETKILI_ROLLER:
            rol = guild.get_role(rol_id)
            if rol:
                overwrites[rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=kanal_adi, overwrites=overwrites)

        if custom_id == "ekip_alim":
            baslik = "🟩 Ekip Alım Başvurusu"
            aciklama = (
                f"Merhaba {interaction.user.mention}! 👋\n\n"
                "Sunucuda ekibin bir parçası olmak istiyorsan buradan başvurabilirsin.\n\n"
                "**Bilgileri doldur:**\n1️⃣ Discord Tag:\n2️⃣ Yaş:\n3️⃣ Deneyim / Bilgi:\n4️⃣ Neden ekibe katılmak istiyorsun?\n\n"
                "Başvurunuz işleniyor… 🔄"
            )
        elif custom_id == "yetkili_alim":
            baslik = "🟦 Yetkili Başvurusu"
            aciklama = (
                f"Merhaba {interaction.user.mention}! 👋\n\n"
                "Sunucuda yetkili olmak istiyorsan başvurunu buradan yapabilirsin.\n\n"
                "**Bilgileri doldur:**\n1️⃣ Discord Tag:\n2️⃣ Yaş:\n3️⃣ Deneyim / Bilgi:\n4️⃣ Sunucuyu nasıl yönetirsin?\n\n"
                "Başvurunuz işleniyor… 🔄"
            )
        else:
            baslik = "⬜ Genel Ticket"
            aciklama = f"Merhaba {interaction.user.mention}! 👋\nSunucu ile ilgili sorun veya taleplerinizi buradan iletebilirsiniz.\nBaşvurunuz işleniyor… 🔄"

        embed = discord.Embed(title=baslik, description=aciklama, color=discord.Color.green())
        await channel.send(embed=embed, view=ApprovalView(interaction.user))

        if log_channel:
            await log_channel.send(f"🟢 Ticket açıldı: {channel.mention} | Kullanıcı: {interaction.user.mention} | Tür: {baslik}")

        await interaction.response.send_message(f"Ticket oluşturuldu: {channel.mention}", ephemeral=True)

    elif custom_id == "ticket_kapat":
        if log_channel:
            await log_channel.send(
                f"🔴 Ticket kapatıldı: {interaction.channel.name} | Kullanıcı: {interaction.user.mention} | Zaman: {datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')} UTC"
            )
        await interaction.channel.send("Ticket kapatılıyor… ⛔")
        await interaction.channel.delete()

    elif custom_id.startswith("onay_") or custom_id.startswith("red_"):
        user_id = int(custom_id.split("_")[1])
        member = guild.get_member(user_id)
        if not member:
            await interaction.response.send_message("Kullanıcı bulunamadı.", ephemeral=True)
            return

        if custom_id.startswith("onay_"):
            mesaj = f"🎉 Başvurunuz onaylandı! Tebrikler {member.mention}."
            renk = discord.Color.green()
        else:
            mesaj = f"❌ Başvurunuz reddedildi {member.mention}."
            renk = discord.Color.red()

        await interaction.channel.send(embed=discord.Embed(description=mesaj, color=renk))
        try:
            await member.send(mesaj)
        except:
            pass

        if log_channel:
            await log_channel.send(
                f"📌 Başvuru durumlandı: {member.mention} | Kanal: {interaction.channel.name} | Durum: {'Onaylandı' if custom_id.startswith('onay_') else 'Reddedildi'}"
            )

bot.run(TOKEN)
