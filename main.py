import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# --- KEEP ALIVE PRO RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot AP online 24/7!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- CONFIG BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SISTEMA DE FILAS ---
filas = {} # {"2,00_gelo_inf": [id1, id2]}

class ApView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=None)
        self.valor = valor

    def get_key(self, modo):
        return f"{self.valor}_{modo}"

    async def entrar_fila(self, interaction, modo, nome_modo):
        user = interaction.user
        key = self.get_key(modo)

        # Remove de qualquer fila que estiver
        for k in list(filas.keys()):
            if user.id in filas[k]:
                filas[k].remove(user.id)

        if key not in filas:
            filas[key] = []

        if user.id in filas[key]:
            return await interaction.response.send_message("Você já tá na fila!", ephemeral=True)

        filas[key].append(user.id)

        # 1 pessoa na fila
        if len(filas[key]) == 1:
            await interaction.response.send_message(f"Entrou na fila **{nome_modo} - R$ {self.valor}** (1/2)", ephemeral=True)
            try:
                embed = interaction.message.embeds[0]
                embed.description = f"**Jogadores**\n{user.mention} - {nome_modo}"
                await interaction.message.edit(embed=embed)
            except:
                pass

        # 2 pessoas = cria canal
        else:
            id1, id2 = filas[key]
            guild = interaction.guild
            u1 = guild.get_member(id1)
            u2 = guild.get_member(id2)
            if not u1 or not u2:
                filas[key] = []
                return await interaction.response.send_message("Alguém saiu do servidor.", ephemeral=True)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                u1: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                u2: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }

            categoria = discord.utils.get(guild.categories, name="🔴・APS ROLANDO")
            if not categoria:
                categoria = await guild.create_category("🔴・APS ROLANDO")

            canal = await guild.create_text_channel(
                name=f"ap-{self.valor.replace(',','')}-{u1.display_name}",
                overwrites=overwrites,
                category=categoria
            )

            embed_ap = discord.Embed(
                title=f"💰 AP CRIADO - R$ {self.valor}",
                description=f"**Modo:** {nome_modo}\n**Jogadores:** {u1.mention} vs {u2.mention}\n\n📸 Mandem o comprovante do pix\n🏆 Quem ganhar marca o ADM",
                color=0x00FF00
            )
            await canal.send(f"{u1.mention} {u2.mention}", embed=embed_ap)
            await interaction.response.send_message(f"AP fechado! Vai pro canal {canal.mention}", ephemeral=True)

            filas[key] = []
            try:
                embed = interaction.message.embeds[0]
                embed.description = "**Jogadores**\nNenhum jogador na fila."
                await interaction.message.edit(embed=embed)
            except:
                pass

    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.secondary, emoji="🧊")
    async def gelo_inf(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_fila(interaction, "gelo_inf", "Gelo Infinito")

    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.secondary, emoji="❄️")
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_fila(interaction, "gelo_normal", "Gelo Normal")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, emoji="❌")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = False
        for k in list(filas.keys()):
            if interaction.user.id in filas[k]:
                filas[k].remove(interaction.user.id)
                removed = True
        if removed:
            await interaction.response.send_message("Você saiu da fila!", ephemeral=True)
        else:
            await interaction.response.send_message("Você nem tava na fila!", ephemeral=True)

# --- COMANDOS ---

@bot.hybrid_command(name="ping", description="Testa se o bot tá on")
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 Bot on, latência {round(bot.latency*1000)}ms")

@bot.hybrid_command(name="painel_ap", description="Cria painéis de AP")
async def painel_ap(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("Só gerência pode usar!", ephemeral=True)

    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]

    for valor in valores:
        embed = discord.Embed(
            title=f"1v1 Mobile • R$ {valor}",
            description="**Jogadores**\nNenhum jogador na fila.",
            color=0x2B2D31
        )
        await ctx.send(embed=embed, view=ApView(valor))

    await ctx.send("✅ Painéis criados com sucesso!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    print(f"Sincronizando comandos...")
    await bot.tree.sync()
    print("Comandos sincronizados!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
