import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# --- KEEP ALIVE PRO RENDER NÃO DERRUBAR ---
app = Flask('')
@app.route('/')
def home(): return "Bot de AP online!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIG BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SISTEMA DE FILAS ---
# formato: {"2.00_gelo_inf": [id1, id2]}
filas = {}
canais_ap = {} # guarda quem tá em ap

class ApView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=None)
        self.valor = valor # ex: "2,00"

    def get_key(self, modo):
        return f"{self.valor}_{modo}"

    async def entrar_fila(self, interaction, modo, nome_modo):
        user = interaction.user
        key = self.get_key(modo)

        # Remove de todas as filas antes
        for k in list(filas.keys()):
            if user.id in filas[k]:
                filas[k].remove(user.id)

        if key not in filas:
            filas[key] = []

        if user.id in filas[key]:
            return await interaction.response.send_message("Você já tá na fila!", ephemeral=True)

        filas[key].append(user.id)

        # Se só tem 1, mostra na fila
        if len(filas[key]) == 1:
            await interaction.response.send_message(f"Você entrou na fila **{nome_modo} - R$ {self.valor}**! Aguardando oponente... (1/2)", ephemeral=True)
            # Atualiza o embed da mensagem original
            try:
                embed = interaction.message.embeds[0]
                embed.description = f"**Jogadores**\n{user.mention} - {nome_modo}"
                await interaction.message.edit(embed=embed)
            except: pass

        # Se tem 2, CRIA O CANAL DO AP
        elif len(filas[key]) == 2:
            id1, id2 = filas[key]
            guild = interaction.guild
            u1 = guild.get_member(id1)
            u2 = guild.get_member(id2)

            # Cria canal privado
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                u1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                u2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }

            categoria = discord.utils.get(guild.categories, name="🔴・APS ROLANDO") # cria essa categoria no seu discord
            if not categoria:
                categoria = await guild.create_category("🔴・APS ROLANDO")

            canal = await guild.create_text_channel(
                name=f"ap-{self.valor.replace(',','')}-{u1.name}",
                overwrites=overwrites,
                category=categoria
            )

            embed_ap = discord.Embed(
                title=f"💰 AP CRIADO - R$ {self.valor}",
                description=f"**Modo:** {nome_modo}\n**Jogadores:** {u1.mention} vs {u2.mention}\n\nMande o comprovante do pix e chamem o juiz!",
                color=0x00FF00
            )
            await canal.send(f"{u1.mention} {u2.mention}", embed=embed_ap)

            await interaction.response.send_message(f"AP encontrado! Vai pro canal {canal.mention}", ephemeral=True)

            # Limpa fila
            filas[key] = []
            try:
                embed = interaction.message.embeds[0]
                embed.description = "**Jogadores**\nNenhum jogador na fila."
                await interaction.message.edit(embed=embed)
            except: pass

    @discord.ui.button(label="Gelo Infinito", style=discord.ButtonStyle.secondary, emoji="🧊")
    async def gelo_inf(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_fila(interaction, "gelo_inf", "Gelo Infinito")

    @discord.ui.button(label="Gelo Normal", style=discord.ButtonStyle.secondary, emoji="🧊")
    async def gelo_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_fila(interaction, "gelo_normal", "Gelo Normal")

    @discord.ui.button(label="FF 2022", style=discord.ButtonStyle.secondary, emoji="🔫")
    async def ff2022(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.entrar_fila(interaction, "ff2022", "FF 2022")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, emoji="❌")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = False
        for k in filas:
            if interaction.user.id in filas[k]:
                filas[k].remove(interaction.user.id)
                removed = True
        if removed:
            await interaction.response.send_message("Você saiu da fila!", ephemeral=True)
        else:
            await interaction.response.send_message("Você nem tava na fila!", ephemeral=True)

@bot.hybrid_command(name="painel_ap", description="Cria os 3 painéis de AP igual da print")
async def painel_ap(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("Só adm!", ephemeral=True)

    for valor in ["2,00", "1,00", "0,60"]:
        embed = discord.Embed(
            title=f"1v1 Mobile • R$ {valor}",
            description="**Jogadores**\nNenhum jogador na fila.",
            color=0x2B2D31
        )
        # borda vermelha igual da print é o embed com cor escura
        await ctx.send(embed=embed, view=ApView(valor))

    await ctx.send("Painéis criados!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    await bot.tree.sync()

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
