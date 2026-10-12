import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os, asyncio, json

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

def salvar_filas():
    try:
        with open("filas.json","w") as f:
            json.dump(filas, f)
    except: pass

try:
    with open("filas.json","r") as f:
        filas = json.load(f)
        filas = {k: [int(x) for x in v] for k,v in filas.items()}
except:
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
            return await interaction.response.send_message("Só ADM pode encerrar!", ephemeral=True)
        embed = discord.Embed(title=f"FINALIZADO - {self.formato} R$ {self.valor}", description=f"Vencedor: {vencedor.mention}\nApagando em 10s!", color=0xFFD700)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        try: await interaction.channel.delete()
        except: pass

    @discord.ui.button(label="Vitoria TIME 1", style=discord.ButtonStyle.success, custom_id="v1")
    async def v1(self, interaction, button):
        await self.finalizar(interaction, self.u1)

    @discord.ui.button(label="Vitoria TIME 2", style=discord.ButtonStyle.success, custom_id="v2")
    async def v2(self, interaction, button):
        await self.finalizar(interaction, self.u2)

    @discord.ui.button(label="Cancelar AP", style=discord.ButtonStyle.danger, custom_id="cancel")
    async def cancelar(self, interaction, button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Só ADM!", ephemeral=True)
        await interaction.response.send_message("Cancelado...")
        await asyncio.sleep(2)
        try: await interaction.channel.delete()
        except: pass

class ApView(discord.ui.View):
    def __init__(self, valor, formato):
        super().__init__(timeout=None)
        self.valor = valor
        self.formato = formato

    def get_key(self, modo):
        return f"{self.valor}_{self.formato}_{modo}"

    def get_lista_nomes(self, guild, key):
        lista = filas.get(key, [])
        if not lista:
            return "Nenhum jogador na fila."
        txt = ""
        for uid in lista:
            m = guild.get_member(uid)
            if m:
                txt += f"• {m.mention} ({m.display_name})\n"
            else:
                txt += f"• <@{uid}>\n"
        return txt

    async def entrar_fila(self, interaction: discord.Interaction, modo, nome_modo):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        key = self.get_key(modo)

        for k in list(filas.keys()):
            if user.id in filas[k]:
                filas[k].remove(user.id)

        if key not in filas:
            filas[key] = []

        if user.id in filas[key]:
            return await interaction.followup.send("Você já está nessa fila!", ephemeral=True)

        filas[key].append(user.id)
        salvar_filas()

        if len(filas[key]) < 2:
            try:
                emb = interaction.message.embeds[0]
                emb.description = f"**Jogadores na fila ({len(filas[key])}/2) - {nome_modo}:**\n" + self.get_lista_nomes(interaction.guild, key)
                emb.color = 0xF1C40F
                await interaction.message.edit(embed=emb)
            except: pass
            return await interaction.followup.send(f"Entrou na fila {self.formato} R$ {self.valor} ({nome_modo}) - 1/2", ephemeral=True)
        else:
            guild = interaction.guild
            u1 = guild.get_member(filas[key][0])
            u2 = guild.get_member(filas[key][1])
            if not u1 or not u2:
                filas[key] = []
                return await interaction.followup.send("Um saiu do servidor, fila resetada.", ephemeral=True)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                u1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                u2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            cat = discord.utils.get(guild.categories, name="APS ROLANDO")
            if not cat:
                cat = await guild.create_category("APS ROLANDO")

            nome_canal = f"ap-{self.formato}-{self.valor}-{u1.display_name}".lower().replace(" ","-")[:90]
            canal = await guild.create_text_channel(name=nome_canal, overwrites=overwrites, category=cat)

            emb_canal = discord.Embed(title=f"AP {self.formato} R$ {self.valor} - {nome_modo}", description=f"{u1.mention} VS {u2.mention}\nTragam o time! ADM encerra.", color=0x2ECC71)
            await canal.send(f"{u1.mention} {u2.mention}", embed=emb_canal, view=EncerrarApView(u1, u2, self.valor, self.formato))

            try:
                emb = interaction.message.embeds[0]
                emb.description = "**Jogadores na fila:**\nNenhum jogador na fila."
                emb.color = 0x2B2D31
                await interaction.message.edit(embed=emb)
            except: pass

            filas[key] = []
            salvar_filas()
            return await interaction.followup.send(f"AP FECHOU! {canal.mention}", ephemeral=True)

    @discord.ui.button(label="Full ump e xm8", style=discord.ButtonStyle.secondary, custom_id="full")
    async def full(self, interaction, button):
        await self.entrar_fila(interaction, "full", "Full ump e xm8")

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.secondary, custom_id="normal")
    async def normal(self, interaction, button):
        await self.entrar_fila(interaction, "normal", "Normal")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="sair")
    async def sair(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        removed = False
        for k in list(filas.keys()):
            if interaction.user.id in filas[k]:
                filas[k].remove(interaction.user.id)
                removed = True
                try:
                    emb = interaction.message.embeds[0]
                    emb.description = f"**Jogadores na fila:**\n" + (self.get_lista_nomes(interaction.guild, k) if filas[k] else "Nenhum jogador na fila.")
                    await interaction.message.edit(embed=emb)
                except: pass
        salvar_filas()
        if removed:
            await interaction.followup.send("Saiu da fila!", ephemeral=True)
        else:
            await interaction.followup.send("Você não estava na fila.", ephemeral=True)

@bot.hybrid_command(name="painel_ap", description="Painel 1v1")
async def painel_ap(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer()
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"1v1 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0x2B2D31)
        await ctx.send(embed=emb, view=ApView(v, "1v1"))
    await ctx.send("✅ Painel 1v1 criado!", ephemeral=True)

@bot.hybrid_command(name="painel_2v2", description="Painel 2v2")
async def painel_2v2(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer()
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"2v2 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0x3498DB)
        await ctx.send(embed=emb, view=ApView(v, "2v2"))
    await ctx.send("✅ Painel 2v2 criado!", ephemeral=True)

@bot.hybrid_command(name="painel_3v3", description="Painel 3v3")
async def painel_3v3(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer()
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"3v3 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0x9B59B6)
        await ctx.send(embed=emb, view=ApView(v, "3v3"))
    await ctx.send("✅ Painel 3v3 criado!", ephemeral=True)

@bot.hybrid_command(name="painel_4v4", description="Painel 4v4")
async def painel_4v4(ctx):
    if not ctx.author.guild_permissions.administrator: return
    await ctx.defer()
    valores = ["10,00", "5,00", "3,00", "2,00", "1,00", "0,60", "0,40", "0,20"]
    for v in valores:
        emb = discord.Embed(title=f"4v4 Mobile • R$ {v}", description="**Jogadores na fila:**\nNenhum jogador na fila.", color=0xE74C3C)
        await ctx.send(embed=emb, view=ApView(v, "4v4"))
    await ctx.send("✅ Painel 4v4 criado!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    await bot.tree.sync()

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
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
            t+=f"• {m.mention if m else f'<@{uid}>'} - ({m.display_name if m else 'saiu'})\n"
        return t

    async def entrar(self, interaction: discord.Interaction, modo, nome_modo):
        try:
            await interaction.response.defer(ephemeral=True) # ESSA LINHA TIRA O VERMELHO
        except: pass

        uid = interaction.user.id
        k = self.key(modo)

        # tira de outras filas
        for x in list(filas.keys()):
            filas[x] = [int(i) for i in filas.get(x,[])]
            if uid in filas[x]:
                filas[x].remove(uid)

        if k not in filas: filas[k]=[]
        if uid not in filas[k]:
            filas[k].append(uid)
            salvar()

        # atualiza embed
        try:
            emb = interaction.message.embeds[0]
            emb.description = f"**Jogadores na fila ({len(filas[k])}/2) - {nome_modo}:**\n" + self.lista(interaction.guild, k)
            emb.color = 0xF1C40F
            await interaction.message.edit(embed=emb)
        except Exception as e:
            print(f"Erro edit: {e}")

        if len(filas[k]) < 2:
            return await interaction.followup.send(f"Você entrou na fila {nome_modo}! Fica ali em cima travado até achar oponente.", ephemeral=True)
        else:
            # cria canal
            g = interaction.guild
            u1 = g.get_member(filas[k][0]); u2 = g.get_member(filas[k][1])
            if not u1 or not u2:
                filas[k]=[]; return await interaction.followup.send("Um saiu, fila resetada", ephemeral=True)

            overw = {g.default_role:discord.PermissionOverwrite(view_channel=False), u1:discord.PermissionOverwrite(view_channel=True,send_messages=True), u2:discord.PermissionOverwrite(view_channel=True,send_messages=True), g.me:discord.PermissionOverwrite(view_channel=True,send_messages=True)}
            for r in g.roles:
                if r.permissions.administrator: overw[r]=discord.PermissionOverwrite(view_channel=True,send_messages=True)

            cat = discord.utils.get(g.categories, name="APS ROLANDO")
            if not cat: cat = await g.create_category("APS ROLANDO")

            canal = await g.create_text_channel(name=f"ap-{self.formato}-{self.valor}-{u1.display_name}"[:90].lower().replace(" ","-"), overwrites=overw, category=cat)
            await canal.send(f"{u1.mention} {u2.mention}", embed=discord.Embed(title=f"AP {self.formato} R$ {self.valor} - {nome_modo}", description=f"{u1.mention} VS {u2.mention}", color=0x2ECC71), view=EncerrarApView(u1,u2,self.valor,self.formato))

            try:
                emb = interaction.message.embeds[0]
                emb.description="**Jogadores na fila:**\nNenhum jogador na fila."
                emb.color=0x2B2D31
                await interaction.message.edit(embed=emb)
            except: pass

            filas[k]=[]; salvar()
            return await interaction.followup.send(f"Fechou! {canal.mention}", ephemeral=True)

    @discord.ui.button(label="Full ump e xm8", style=discord.ButtonStyle.secondary, custom_id="full_btn")
    async def full(self,i,b): await self.entrar(i,"full","Full ump e xm8")

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.secondary, custom_id="normal_btn")
    async def normal(self,i,b): await self.entrar(i,"normal","Normal")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="sair_btn")
    async def sair(self,i,b):
        try: await i.response.defer(ephemeral=True)
        except: pass
        for k in list(filas.keys()):
            if i.user.id in [int(x) for x in filas.get(k,[])]:
                filas[k]=[x for x in filas[k] if int(x)!=i.user.id]
                try:
                    emb=i.message.embeds[0]
                    emb.description="**Jogadores na fila:**\n"+(self.lista(i.guild,k) if filas[k] else "Nenhum jogador na fila.")
                    await i.message.edit(embed=emb)
                except: pass
        salvar()
        await i.followup.send("Saiu da fila!", ephemeral=True)
