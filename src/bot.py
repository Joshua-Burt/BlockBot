import discord

bot = None

def create_bot():
    global bot
    bot = discord.Bot(intents=discord.Intents.all())
    return bot
