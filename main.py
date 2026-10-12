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

    def key(self, modo): return f"{self.valor}_{self.formato}_{modo}"

    def lista(self, guild, key):
        if key not in filas or not filas[key]: return "Nenhum jogador na fila."
        t=""
        for uid in filas[key]:
            m=guild.get_member(int(uid))
            t+=f"• {m.mention if m else f'<@{uid}>'} - {m.display_name if m else ''}\n"
        return t

    async def entrar(self, interaction: discord.Interaction, modo, nome_modo):
        # CORREÇÃO DO ERRO DA SUA PRINT - RESPONDE NA HORA
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass

        uid = interaction.user.id
        k = self.key(modo)

        # tira de outras filas
        for x in list(filas.keys()):
            filas[x] = [int(i) for i in filas.get(x,[])]
            if uid in filas[x]:
                filas[x].remove(uid)

        if k not in filas: filas[k]=[]
        filas[k]=[int(i) for i in filas[k]]

        if uid in filas[k]:
            return await interaction.followup.send("Você já está nessa fila!",ephemeral=True)

        filas[k].append(uid)
        salvar()

        # atualiza o embed
        try:
            emb=interaction.message.embeds[0]
            emb.description=f"**Jogadores na fila ({len(filas[k])}/2) - {nome_modo}:**\n"+self.lista(interaction.guild,k)
            emb.color=0xF1C40F
            await interaction.message.edit(embed=emb)
        except: pass

        if len(filas[k])<2:
            return await interaction.followup.send(f"Entrou na fila {nome_modo}! Seu nome ficou travado até achar oponente.",ephemeral=True)
        else:
            g=interaction.guild
            u1=g.get_member(filas[k][0]); u2=g.get_member(filas[k][1])
            if not u1 or not u2:
                filas[k]=[]; salvar()
                return await interaction.followup.send("Um saiu, resetado",ephemeral=True)

            overw={g.default_role:discord.PermissionOverwrite(view_channel=False), u1:discord.PermissionOverwrite(view_channel=True,send_messages=True), u2:discord.PermissionOverwrite(view_channel=True,send_messages=True), g.me:discord.PermissionOverwrite(view_channel=True,send_messages=True)}
            for r in g.roles:
                if r.permissions.administrator: overw[r]=discord.PermissionOverwrite(view_channel=True,send_messages=True)

            cat=discord.utils.get(g.categories,name="APS ROLANDO")
            if not cat: cat=await g.create_category("APS ROLANDO")

            canal=await g.create_text_channel(name=f"ap-{self.formato}-{self.valor}-{u1.display_name}"[:90].lower().replace(" ","-"), overwrites=overw, category=cat)
            await canal.send(f"{u1.mention} {u2.mention}", embed=discord.Embed(title=f"AP {self.formato} R$ {self.valor} - {nome_modo}", description=f"{u1.mention} VS {u2.mention}", color=0x2ECC71), view=EncerrarApView(u1,u2,self.valor,self.formato))

            try:
                emb=interaction.message.embeds[0]
                emb.description="**Jogadores na fila:**\nNenhum jogador na fila."
                emb.color=0x2B2D31
                await interaction.message.edit(embed=emb)
            except: pass

            filas[k]=[]; salvar()
            return await interaction.followup.send(f"AP FECHOU! {canal.mention}",ephemeral=True)

    @discord.ui.button(label="Full ump e xm8", style=discord.ButtonStyle.secondary, custom_id="full_btn")
    async def full(self,i,b): await self.entrar(i,"full","Full ump e xm8")

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.secondary, custom_id="normal_btn")
    async def normal(self,i,b): await self.entrar(i,"normal","Normal")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="sair_btn")
    async def sair(self,i,b):
        try: await i.response.defer(ephemeral=True)
        except: pass
        for k in list(filas.keys()):
            filas[k]=[int(x) for x in filas.get(k,[])]
            if i.user.id in filas[k]:
                filas[k].remove(i.user.id)
        salvar()
        try:
            emb=i.message.embeds[0]
            # tenta achar a key correta pra atualizar
            for key_teste in filas:
                if key_teste.startswith(self.valor):
                    emb.description=f"**Jogadores na fila:**\n"+ (self.lista(i.guild,key_teste) if filas.get(key_teste) else "Nenhum jogador na fila.")
                    break
            await i.message.edit(embed=emb)
        except: pass
        await i.followup.send("Saiu da fila!", ephemeral=True)

# --- COMANDOS ---

@bot.tree.command(name="criar_painel", description="Cria UM painel (sem erro)")
@discord.app_commands.describe(formato="1v1, 2v2, 3v3, 4v4", valor="Ex: 10,00 ou 0,20")
async def criar_painel(interaction: discord.Interaction, formato: str, valor: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("Só ADM!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    cores = {"1v1":0x2B2D31, "2v2":0x3498DB, "3v3":0x9B59B6, "4v4":0xE74C3C}
    emb = discord.Embed(title=f"{formato.upper()} Mobile • R$ {valor}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=cores.get(formato.lower(),0x2B2D31))
    await interaction.channel.send(embed=emb, view=ApView(valor, formato))
    await interaction.followup.send(f"✅ Painel {formato} R$ {valor} criado!", ephemeral=True)

@bot.hybrid_command(name="painel_ap", description="Cria os 8 painéis 1v1")
async def painel_ap(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer(ephemeral=True)
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"1v1 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0x2B2D31)
        await ctx.send(embed=emb, view=ApView(v, "1v1"))
        await asyncio.sleep(0.7)
    await ctx.send("✅ Painel 1v1 criado!", ephemeral=True)

@bot.hybrid_command(name="painel_2v2", description="Cria os 8 painéis 2v2")
async def painel_2v2(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer(ephemeral=True)
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"2v2 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0x3498DB)
        await ctx.send(embed=emb, view=ApView(v, "2v2"))
        await asyncio.sleep(0.7)
    await ctx.send("✅ Painel 2v2 criado!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"ON {bot.user}")
    # FAZ OS BOTÕES ANTIGOS FUNCIONAREM DE NOVO PARA OS OUTROS USUÁRIOS
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    formatos = ["1v1","2v2","3v3","4v4"]
    for fmt in formatos:
        for v in valores:
            bot.add_view(ApView(v, fmt))

    try:
        await bot.tree.sync()
        print("Comandos sincronizados e views persistentes ativas")
    except Exception as e:
        print(e)

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
