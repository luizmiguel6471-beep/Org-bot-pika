import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(e)

@bot.command()
async def org(ctx):
    await ctx.send("🏆 **Org Pika ON!** Bot hospedado 24/7 na Discloud!")

@bot.hybrid_command(name="ping", description="Ver latência do bot")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency*1000)}ms")

@bot.hybrid_command(name="recrutar", description="Anúncio de recrutamento")
async def recrutar(ctx):
    await ctx.send("@everyone 🚀 **Org Pika recrutando!** Interessados abram ticket ou chamem a gerência!")

bot.run(os.getenv("DISCORD_TOKEN"))
