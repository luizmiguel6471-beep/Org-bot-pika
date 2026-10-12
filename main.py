import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import asyncio

app = Flask('')
@app.route('/')
def home(): return "Bot AP online!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

filas = {}

class EncerrarApView(discord.ui.View):
    def __init__(self, u1, u2, valor, formato):
        super().__init__(timeout=None)
        self.u1 = u1
        self.u2 = u2
        self.valor = valor
        self.formato = formato
    async def finalizar(self, interaction, vencedor):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("So ADM pode encerrar!", ephemeral=True)
        embed = discord.Embed(title="AP FINALIZADO - " + self.formato, description=f"Vencedor: {vencedor.mention} - R$ {self.valor} Apagando em 10s!", color=0xFFD700)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        try: await interaction.channel.delete()
        except: pass
    @discord.ui.button(label="Vitoria TIME 1", style=discord.ButtonStyle.success)
    async def v1(self, interaction, button):
        await self.finalizar(interaction, self.u1)
    @discord.ui.button(label="Vitoria TIME 2", style=discord.ButtonStyle.success)
    async def v2(self, interaction, button):
        await self.finalizar(interaction, self.u2)
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction, button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("So ADM!", ephemeral=True)
        await interaction.response.send_message("Cancelado, apagando...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class ApView(discord.ui.View):
    def __init__(self, valor, formato):
        super().__init__(timeout=None)
        self.valor = valor
        self.formato = formato
    def get_key(self, modo):
        return self.valor + "_" + self.formato + "_" + modo
    async def entrar_fila(self, interaction, modo, nome_modo):
        user = interaction.user
        key = self.get_key(modo)
        for k in list(filas.keys()):
            if user.id in filas[k]:
                filas[k].remove(user.id)
        if key not in filas:
            filas[key] = []
        if user.id in filas[key]:
            return await interaction.response.send_message("Ja ta na fila!", ephemeral=True)
        filas[key].append(user.id)
        if len(filas[key]) == 1:
            await interaction.response.send_message(f"Entrou na fila {self.formato} R$ {self.valor} (1/2)", ephemeral=True)
            try:
                e = interaction.message.embeds[0]
                e.description = "**Jogadores**\n" + user.mention + " - " + nome_modo
                await interaction.message.edit(embed=e)
            except: pass
        else:
            guild = interaction.guild
            u1 = guild.get_member(filas[key][0])
            u2 = guild.get_member(filas[key][1])
            overw = {guild.default_role: discord.PermissionOverwrite(view_channel=False), u1: discord.PermissionOverwrite(view_channel=True, send_messages=True), u2: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
            cat = discord.utils.get(guild.categories, name="APS ROLANDO")
            if not cat:
                cat = await guild.create_category("APS ROLANDO")
            nome_canal = "ap-" + self.formato + "-" + self.valor + "-" + u1.display_name
            nome_canal = nome_canal.replace(",", "").replace(".", "").replace(" ", "-").lower()[:90]
            canal = await guild.create_text_channel(name=nome_canal, overwrites=overw, category=cat)
            emb = discord.Embed(title=f"AP {self.formato} R$ {self.valor} - {nome_modo}", description=f"{u1.mention} vs {u2.mention}\nTragam o time! ADM clique no vencedor", color=0x00FF00)
            await canal.send(f"{u1.mention} {u2.mention}", embed=emb, view=EncerrarApView(u1, u2, self.valor, self.formato))
            await interaction.response.send_message(f"AP fechado! {canal.mention}", ephemeral=True)
            filas[key] = []
            try:
                e = interaction.message.embeds[0]
                e.description = "**Jogadores**\nNenhum na fila."
                await interaction.message.edit(embed=e)
            except: pass

    @discord.ui.button(label="Full ump e xm8", style=discord.ButtonStyle.secondary)
    async def full(self, interaction, button):
        await self.entrar_fila(interaction, "full", "Full ump e xm8")

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.secondary)
    async def normal(self, interaction, button):
        await self.entrar_fila(interaction, "normal", "Normal")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger)
    async def sair(self, interaction, button):
        for k in list(filas.keys()):
            if interaction.user.id in filas[k]:
                filas[k].remove(interaction.user.id)
        await interaction.response.send_message("Saiu da fila!", ephemeral=True)

@bot.hybrid_command(name="painel_ap", description="Painel 1v1")
async def painel_ap(ctx):
    if not ctx.author.guild_permissions.administrator: return
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title="1v1 Mobile - R$ " + v, description="**Jogadores**\nNenhum na fila.", color=0x2B2D31)
        await ctx.send(embed=emb, view=ApView(v, "1v1"))

@bot.hybrid_command(name="painel_2v2", description="Painel 2v2")
async def painel_2v2(ctx):
    if not ctx.author.guild_permissions.administrator: return
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title="2v2 Mobile - R$ " + v, description="**Jogadores**\nNenhum na fila. (2 donos fecha)", color=0x3498DB)
        await ctx.send(embed=emb, view=ApView(v, "2v2"))

@bot.hybrid_command(name="painel_3v3", description="Painel 3v3")
async def painel_3v3(ctx):
    if not ctx.author.guild_permissions.administrator: return
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title="3v3 Mobile - R$ " + v, description="**Jogadores**\nNenhum na fila.", color=0x9B59B6)
        await ctx.send(embed=emb, view=ApView(v, "3v3"))

@bot.hybrid_command(name="painel_4v4", description="Painel 4v4")
async def painel_4v4(ctx):
    if not ctx.author.guild_permissions.administrator: return
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title="4v4 Mobile - R$ " + v, description="**Jogadores**\nNenhum na fila.", color=0xE74C3C)
        await ctx.send(embed=emb, view=ApView(v, "4v4"))

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    await bot.tree.sync()

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
