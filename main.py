import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Servidor fake pro Render não derrubar
app = Flask('')
@app.route('/')
def home():
    return "Org Pika ONLINE 24/7"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos")
    except Exception as e:
        print(e)

@bot.command()
async def org(ctx):
    await ctx.send("🏆 **Org Pika ON!** Bot hospedado 24/7 no Render!")

@bot.hybrid_command(name="ping", description="Ver latência do bot")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency*1000)}ms")

@bot.hybrid_command(name="recrutar", description="Anúncio de recrutamento")
async def recrutar(ctx):
    await ctx.send("@everyone 🚀 **Org Pika recrutando!** Interessados abram ticket ou chamem a gerência!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
