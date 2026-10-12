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
    def __init__(self, u1, u2, valor):
        super().__init__(timeout=None)
        self.u1 = u1
        self.u2 = u2
        self.valor = valor

    async def finalizar(self, interaction, vencedor):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("So ADM pode encerrar!", ephemeral=True)
        perdedor = self.u2 if vencedor.id == self.u1.id else self.u1
        embed = discord.Embed(title="AP FINALIZADO", description=f"Vencedor: {vencedor.mention}\nValor: R$ {self.valor}\nApagando em 10s!", color=0xFFD700)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        try: await interaction.channel.delete()
        except: pass

    @discord.ui.button(label="Vitoria P1", style=discord.ButtonStyle.success, emoji="👑")
    async def v1(self, interaction, button):
        await self.finalizar(interaction, self.u1)

    @discord.ui.button(label="Vitoria P2", style=discord.ButtonStyle.success, emoji="👑")
    async def v2(self, interaction, button):
        await self.finalizar(interaction, self.u2)

    @discord.ui.button(label="Cancelar AP", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def cancelar(self, interaction, button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("So ADM!", ephemeral=True)
        await interaction.response.send_message("Cancelado, apagando...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class ApView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=None)
        self.valor = valor
    def get_key(self, modo):
        return f"{self.valor}_{modo}"

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
            await interaction.response.send_message(f"Entrou na fila {nome_modo} R$ {self.valor} (1/2)", ephemeral=True)
            try:
                e = interaction.message.embeds[0]
                e.description = f"**Jogadores**\n{user.mention} - {nome_modo}"
                await interaction.message.edit(embed=e)
            except: pass
        else:
            id1, id2 = filas[key]
            guild = interaction.guild
            u1 = guild.get_member(id1)
            u2 = guild.get_member(id2)
            overw = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                u1: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                u2: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            cat = discord.utils.get(guild.categories, name="APS ROLANDO")
            if not cat:
                cat = await guild.create_category("APS ROLANDO")
            canal = await guild.create_text_channel(name=f"ap
