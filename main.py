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

# --- VIEW QUE FECHA O CANAL ---
class EncerrarApView(discord.ui.View):
    def __init__(self, u1, u2, valor):
        super().__init__(timeout=None)
        self.u1 = u1
        self.u2 = u2
        self.valor = valor

    async def finalizar(self, interaction, vencedor):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Só ADM pode encerrar!", ephemeral=True)

        perdedor = self.u2 if vencedor.id == self.u1.id else self.u1

        embed = discord.Embed(
            title="🏆 AP FINALIZADO",
            description=f"**Vencedor:** {vencedor.mention}\n**Perdedor:** {perdedor.mention}\n**Valor:** R$ {self.valor}\n\nCanal vai ser apagado em 10 segundos!",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(label="Vitória Player 1", style=discord.ButtonStyle.success, emoji="👑")
    async def v1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalizar(interaction, self.u1)

    @discord.ui.button(label="Vitória Player 2", style=discord.ButtonStyle.success, emoji="👑")
    async def v2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalizar(interaction, self.u2)

    @discord.ui.button(label="Cancelar AP", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Só ADM!", ephemeral=True)
        await interaction.response.send_message("AP cancelado, apagando canal...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- VIEW DA FILA ---
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
        if key not in filas: filas[key] = []
        if user.id in filas[key]:
            return await interaction.response.send_message("Já tá na fila!", ephemeral=True)
        filas[key].append(user.id)

        if len(filas[key]) == 1:
            await interaction.response.send_message(f"Entrou na fila **{nome_modo} R$ {self.valor}** (1/2)", ephemeral=True)
            try:
                embed = interaction.message.embeds[0]
                embed.description = f"**Jogadores**\n{user.mention} - {nome_modo}"
                await interaction.message.edit(embed=embed)
            except: pass
        else:
            id1, id2 = filas[key]
            guild = interaction.guild
            u1 = guild.get_member(id1)
            u2 = guild.get_member(id2)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                u1: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                u2: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            categoria = discord.utils.get(guild.categories, name="🔴・APS ROLANDO")
            if not categoria: categoria = await guild.create_category("🔴・APS ROLANDO")
            canal = await guild.create_text_channel(name=f"ap-{self.valor.replace(',','')}-{u1.display_name}", overwrites=overwrites, category=categoria)

            embed_ap = discord.Embed(
                title=f"💰 AP CRIADO - R$ {self.valor}",
                description=f"**Modo:** {nome_modo}\n**Jogadores:** {u1.mention} vs {u2.mention}\n\n📸 Mandem o comprovante\n👑 ADM clica no vencedor abaixo pra finalizar",
                color=0x00FF00
            )

            # BOTÃO MUDA DE NOME COM NOME DOS PLAYERS
            view_final = EncerrarApView(u1, u2, self.valor)
            view_final.children[0].label = f"Vitória: {u1.display_name[:15]}"
            view_final.children[1].label = f"Vitória: {u2.display_name[:15]}"

            await canal.send(f"{u1.mention} {u2.mention}", embed=embed_ap, view=view_final)
            await interaction.response.send_message(f"AP fechado! {canal.mention}", ephemeral=True)
            filas[key] = []
            try:
                embed = interaction.message.embeds[0]
                embed.description = "**Jogadores**\nNenhum jogador na fila."
                await interaction.message.edit(embed=embed)
            except: pass

    @discord.ui.button(label="Gelo Infinito", style=discord
