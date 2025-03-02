import os
import random

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="k!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    # Affichage du « Joue à ... »
    games = ["Koleka Flight Simulator", "Koleka Truck Simulator", "Koleka Cooking Simulator", "Koleka Driving School", "Koleka For Speed"]
    await bot.change_presence(activity=discord.Game(random.choice(games)))

    # Chargement des cogs
    for file in os.listdir('./cogs'):
        await bot.load_extension(f'cogs.{file[:-3]}')


bot.run(os.getenv('DISCORD_TOKEN'))