import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os, asyncio, json

# --- WEB SERVER PRO RENDER NÃO DORMIR ---
app = Flask('')
@app.route('/')
def home(): return "Bot AP online!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- CONFIG BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- FILAS COM SAVE ---
filas = {}
try:
    with open("filas.json","r") as f: 
        filas = json.load(f)
except: 
    filas = {}

def salvar():
    try:
        with open("filas.json","w") as f: json.dump(filas,f)
    except: pass

# --- VIEW DE ENCERRAR AP ---
class EncerrarApView(discord.ui.View):
    def __init__(self, u1, u2, valor, formato):
        super().__init__(timeout=None)
        self.u1, self.u2, self.valor, self.formato = u1, u2, valor, formato

    async def finalizar(self, inter, venc):
        if not inter.user.guild_permissions.administrator:
            return await inter.response.send_message("Só ADM!", ephemeral=True)
        await inter.response.send_message(embed=discord.Embed(title=f"FINALIZADO R$ {self.valor}", description=f"Vencedor: {venc.mention}\nApagando em 10s", color=0xFFD700))
        await asyncio.sleep(10)
        try: await inter.channel.delete()
        except: pass

    @discord.ui.button(label="Vitoria TIME 1", style=discord.ButtonStyle.success, custom_id="v1")
    async def v1(self,i,b): await self.finalizar(i,self.u1)
    @discord.ui.button(label="Vitoria TIME 2", style=discord.ButtonStyle.success, custom_id="v2")
    async def v2(self,i,b): await self.finalizar(i,self.u2)
    @discord.ui.button(label="Cancelar AP", style=discord.ButtonStyle.danger, custom_id="cc")
    async def cc(self,i,b):
        if not i.user.guild_permissions.administrator: return await i.response.send_message("Só ADM!",ephemeral=True)
        await i.response.send_message("Cancelado"); await asyncio.sleep(2)
        try: await i.channel.delete()
        except: pass

# --- VIEW DA FILA (PRINCIPAL) ---
class ApView(discord.ui.View):
    def __init__(self, valor, formato):
        super().__init__(timeout=None)
        self.valor, self.formato = valor, formato

    def key(self, modo): return f"{self.valor}_{self.formato}_{
