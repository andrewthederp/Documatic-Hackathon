import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='%')

@bot.event
async def on_ready():
	print('Online!')

@bot.command()
async def game(ctx):
	...

@bot.command(aliases=['lb'])
async def leaderboard(ctx, x=5):
	...

bot.run("ODA1OTcwMzYwMjA1OTY3Mzcw.YBioZA.P0ektwrva7KZyAVqknfaL59a6z0")