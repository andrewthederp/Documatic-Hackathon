import discord
from discord.ext import commands
import copy
import os
import random
import asyncio
import aiosqlite
import json
from dotenv import load_dotenv

load_dotenv()

with open("cache.json", "r") as f:
    cache = json.load(f)

def update_cache(ctx):
	try:
		if ctx.command.name not in cache[str(ctx.author.id)]:
			cache[str(ctx.author.id)] += [ctx.command.name]
	except KeyError:
		cache[str(ctx.author.id)] = [ctx.command.name]

bot = commands.Bot(command_prefix='%', intents=discord.Intents.all(), case_insenstive=True)

class BotHelp(commands.MinimalHelpCommand): # A very simple help command
	async def send_pages(self):
		des = self.get_destination()
		for i in self.paginator.pages:
			emb = discord.Embed(title=f'{bot.user.name} Help', description=f"\n{i}", color=discord.Color.dark_theme())
			await des.send(embed=emb)

bot.help_command=BotHelp()

words = ['gun','game','end','spaceship','zombies','john','caroline','rapheal','adam','maze','flushed']

# very useful global variables
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
conversion = {'⬆':UP,'⬅':LEFT,'➡':RIGHT,'⬇':DOWN}
directions = [UP, DOWN, LEFT, RIGHT]


# Classes
class Bullet:
	"""The bullet's the player shoots"""
	def __init__(self, direction, index):
		self.index = index
		self.direction = direction

	def move(self):
		self.index[0] += self.direction[0]
		self.index[1] += self.direction[1]

class Zombie:
	"""Zombie logic"""
	def __init__(self, direction):
		if direction == DOWN:
			self.index = [-1,5]
		elif direction == LEFT:
			self.index = [5, 11]
		elif direction == UP:
			self.index = [11, 5]
		else:
			self.index = [5, -1]
		self.direction = direction

	def move(self):
		self.index[0] += self.direction[0]
		self.index[1] += self.direction[1]

class Alien:
	"""Alien logic"""
	def __init__(self):
		self.index = [-1, random.randint(0, 4)]
		self.direction = DOWN

	def move(self):
		self.index[0] += self.direction[0]
		self.index[1] += self.direction[1]

def summon_blocks(board):
	"""Place 1-8 circles in random places on the speed board"""
	for _ in range(random.randint(1, 8)):
		x = random.randint(0, 4)
		y = random.randint(0, 4)
		while board[x][y] != 'g':
			x = random.randint(0, 4)
			y = random.randint(0, 4)
		board[x][y] = 'b'
	return board

def convert(coordinates):
	"""Convert the speed coordinates into x, y coordinates, this way you could do both "a1" or "1a"""
	for coor in coordinates.split(' '):
		if len(coor) != 2:
			continue

		coor = coor.lower()
		if coor[0].isalpha():
			digit = coor[1:]
			letter = coor[0]
		else:
			digit = coor[:-1]
			letter = coor[-1]

		if not digit.isdecimal():
			continue

		x = int(digit) - 1
		y = ord(letter) - ord("a")

		if (not x in range(5)) or (not y in range(5)):
			continue
		yield x, y

def format_board(board):
	"""A nested list formater, uses a dict to turn letters into emojis"""
	lst = []
	dct = {'g':'⬛','G':'🟩','q':'🟦','p':'😳','L':'📍','z':'🧟','e':random.choice(['🌎','🌍','🌏']),'B':'💥', 's':'🚀', 'a':'👾', 'o':'💣', 'w':'🟥', 'x':'❌',' ':'⬛','u':'⏫','l':'⏪','r':'⏩','d':'⏬','b':'🔲'}
	for row in board:
		lst.append(''.join([dct[i] for i in row]))
	return '\n'.join(lst)

def format_speed_board(board):
	"""Speed board requires coordinates a boarder so i made a different function for it"""
	dct = {'g':'⬛','b':'b'}
	for i in range(1, 6):
		dct[i] = f"{i}\N{variation selector-16}\N{combining enclosing keycap}"
	lst = [f":stop_button::regional_indicator_a::regional_indicator_b::regional_indicator_c::regional_indicator_d::regional_indicator_e:"]
	for num, row in enumerate(board, start=1):
		lst.append(dct[num]+''.join([dct[column] if column != 'b' else random.choice(['🔴','🟠','🟡','🟢','🔵','🟣','🟤']) for column in row]))
	return "\n".join(lst)

def check_zombie_collides(board, bullets, enemies, score):
	"""Check if a zombie collided with a bullet"""
	for enemy in enemies:
		for bullet in bullets:
			collide = False
			try:
				if bullet.index == enemy.index:
					board[bullet.index[0]][bullet.index[1]] = 'G'
					collide = True
				elif bullet.index == [enemy.index[0]+1,enemy.index[1]]:
					board[enemy.index[0]][enemy.index[1]] = 'G'
					board[enemy.index[0]+1][enemy.index[1]] = 'G'
					collide = True
				elif bullet.index == [enemy.index[0]-1, enemy.index[1]]:
					board[enemy.index[0]][enemy.index[1]] = 'G'
					board[enemy.index[0]-1][enemy.index[1]] = 'G'
					collide = True
				elif bullet.index == [enemy.index[0], enemy.index[1]+1]:
					board[enemy.index[0]][enemy.index[1]] = 'G'
					board[enemy.index[0]][enemy.index[1]+1] = 'G'
					collide = True
				elif bullet.index == [enemy.index[0], enemy.index[1]-1]:
					board[enemy.index[0]][enemy.index[1]] = 'G'
					board[enemy.index[0]][enemy.index[1]-1] = 'G'
					collide = True
			except IndexError:
				collide = True
			if collide:
				try:
					bullets.remove(bullet)
				except ValueError:
					pass
				try:
					enemies.remove(enemy)
				except ValueError:
					pass
				score += 1
	return board, bullets, enemies, score

async def scene_1(ctx, msg):
	"""Scene 1, played when you use the zombie command"""
	embed = discord.Embed(title='Chapter 1: What happened', description=f"**???:** *WAKE UP KID*", color=discord.Color.dark_theme())
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += f"\n**{ctx.author.display_name}:** *what's happening... wait Raphael? what happened?*"
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**Raphael:** *ZOMBIES ARE SURROINDING US, TAKE THIS GUN*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f"\n**{ctx.author.display_name}:** *AAAAAAAAAA, THE ZOMBIES ARE EVERYWHERE!*"
	await msg.edit(embed=embed)
	await ctx.send('__**Instructions:**__\nThis is you: 😳\nThese are bullets: 📍\nThese are zombies: 🧟\n\n**How to play:** wait till all the reactions have been added, then react to reactions pointing in the direction you want to shoot a bullet in, make sure the zombies don\'t touch you and goodluck!')
	await asyncio.sleep(.5)

async def scene_2(ctx, msg):
	"""Scene 2, played when you use the spaceshooter command"""
	embed = discord.Embed(title='Chapter 2: The spaceship',description='' ,color=discord.Color.dark_theme())
	await msg.edit(embed=embed)
	await asyncio.sleep(.5)
	embed.description = "**John:** *THERE ARE SO MANY ZOMBIES, WE NEED TO GO NOW*"
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += "\n**Raphael:** *CMON, LET'S GO, ADAM PROBABLY FINISHED WORKING ON THE SPACESHIP*"
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f"\n**{ctx.author.display_name}:** *??? WHAT SPACESHIP, CAN ANYONE PLEASE EXPLAIN TO ME WHAT'S HAPPENING*"
	await msg.edit(embed=embed)
	for i in range(1, 7):
		await msg.edit(embed=discord.Embed(title='Chapter 2: The spaceship', description=embed.description+"\n"+'.'*(i if i < 4 else i-3), color=discord.Color.dark_theme()))
		await asyncio.sleep(.3)
	embed.description += "\n**Raphael:** *okay, we are safe **for now**, how's the ship's status Adam?*"
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += "\n**Adam:** *I was able to fix the spaceship for the most part but the spaceship could only have 4 people onboard, someone has to be left behind...*"
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += "\n**John:** *I will do it, it was a great run guys but this is where my story ends, goodluck!*"
	await msg.edit(embed=embed)
	await asyncio.sleep(3)
	bord = [['g']*7 for i in range(7)]
	bord[3][0] = 'e'
	index = [3,1]
	bord[index[0]][index[1]] = 's'
	for i in range(5):
		embed = discord.Embed(title='Chapter 2: The spaceship', description=format_board(bord), color=discord.Color.dark_theme())
		await msg.edit(embed=embed)
		bord[index[0]][index[1]] = 'g'
		index[1] += 1
		if i == 2:
			bord[3][0] = 'B'
		bord[index[0]][index[1]] = 's'
		await asyncio.sleep(.5)
	await ctx.send('__**Part 2:**__ you and the rest of the group were able to leave earth just in time before it (for some reason) dramatically exploded, now that you\'re in space a new threat arises **aliens**\n**How to play:** The goal is to get the highest score possible, move right or left then press ⏹ to shoot a laser, the higher your score the higher you\'ll be on the leaderboard\n\nif you get hit by get hit by an alien you\'ll loose a life (you have 3 lifes), goodluck!\n\nThis is you: 🚀\nThese are your bullets: 📍\nThese are aliens: 👾')

async def scene_3(ctx):
	"""Scene 3, played when you hit 50 score in spaceshooter"""
	embed = discord.Embed(title='Chapter 3: The Crew', description='', color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	embed.description += '**???**: *Hey, i didn\'t introduce myself*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += '\n**Caroline:** *My name is Caroline! what\'s your name?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Oh, hello. My name is {ctx.author.display_name}*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Caroline:** *Very nice to meet you {ctx.author.name}*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Nice to meet you too.*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	emojis = ['⬅','🏳','➡']
	for emoji in emojis:
		await msg.add_reaction(emoji)
	return msg

async def scene_4(ctx):
	"""Scene 4, played when you use the maze command on storyline mode"""
	embed = discord.Embed(title='Chapter 4: The Crash', description='', color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	embed.description += '*Siren noises*\n**Raphael:** *EVERYBODY WAKE UP, WE NEED TO GO NOW*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** *WHAT\'S HAPPENING NOW???*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Raphael:** *THE SHIP GOT BADLEY DAMAGED, HERE EVERYONE TAKE THESE SUITS*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *OH NO!!!*\n**Adam:** *MY SHIP D:*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += '\n**Raphael:** *WE NEED TO GET ONTO THAT PLANET*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** *... okay we landed safely, what now*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Raphael:** *Be careful guys, this planet\'s gravity is really messed up*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Adam:** *crying*'
	await msg.edit(embed=embed)
	await ctx.send("__**Instructions:**__\nThis is you: :flushed:\nThese are walls: 🟥\nThis is an exit point: :x:\nThese are direction changer blocks: ⏫⏪⏩⏬ (changes the direction of the player to the direction it's pointing at)\nthis is a breaking block: 🔲 (it stops the player and breaks when he player touches it)\n\n**Part 3:** Now that you landed on the planet your goal is to hit the :x:, react to the reaction pointing in the direction you want to move. You will keep moving until you hit a wall be careful to not fall of the planet and as always, *goodluck!*")
	await asyncio.sleep(1.5)
	return msg

async def scene_5(ctx):
	embed = discord.Embed(title='chapter 5: The end', description=f'**{ctx.author.display_name}:** *Hmm, where am i... Where are the others, what even is this place*')
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**???:** *IS ANYONE THERE*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** (in your mind) *... that sounds like Raphael, maybe i should say hi*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	await ctx.send("Should you go meet Raphael or stay where you are?\n1. Yes\n2. No\n3. Wait a bit first")
	msg = await bot.wait_for('message', check =  lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1','2','3'])
	return int(msg.content)

async def credits(msg):
	embed = msg.embeds[0]
	embed.title = '**Credits**'
	embed.color = discord.Color.blurple()
	embed.description = f'Code created by: andreawthaderp#3031\nThank everyone that allowed me to make this bot and thank **you** for playing!'
	await msg.edit(embed=embed)

async def good_ending(ctx):
	embed = discord.Embed(title="Good ending", description="**Caroline:**: *SHOOT HIM*", color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**{ctx.author.display_name}:** *(Shoots Raphael)*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += f'\n...'
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += f'\n...'
	await msg.edit(embed=embed)
	await asyncio.sleep(1)
	embed.description += f'\n**You start loosing conscious and you somehow know that you will never wake up again, but you don\'t mind**'
	await msg.edit(embed=embed)
	await asyncio.sleep(3)
	await credits(msg)

async def bad_ending(ctx):
	embed = discord.Embed(title="Bad ending", description="**Caroline:** *RUUUUUN*", color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**Raphael:** *There is no where to run, Just give up and make this easy for the both of us*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**Raphael:** *(shoots you and Caroline)*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**Raphael:** *I didn\'t want to do this to you but you just had to force me*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += '\n*The world starts fading away, everything you did in your life, it all ends right here, you\'re filled with anger but there isn\'t much you could do*'
	await msg.edit(embed=embed)
	await asyncio.sleep(5)
	await credits(msg)

def back_home(ctx):
	embed = discord.Embed(title='Going back home', description=f'**{ctx.author.display_name}:** *(shoots Rapheal)*', color=discord.Color.blurple())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n...'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Adam:** *Well that that\'s over, I think i could re-build the spaceship*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Caroline:** *Where will we even go?*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Adam:** *Home ofcourse*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(1)
	embed.description += f'\n**{ctx.author.display_name}:** *But earth exploded, don\'t you remember?*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n**Adam:** *True, but it hasn\'t exploded in other univereses*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	embed.description += '\nYou, Caroline, and Adam start gathering scrap parts from around the planet and adam goes to work\n18 months later'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Adam:** *FINALLY, THE SPACESHIP IN ALL OF IT\'S GLORY*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n*3.5 months of travelling later*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n**{ctx.author.display_name}:** *OMG GUYS, WE FINALLT ARIVED*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n**Caroline:** *I cannot believe it, after all this time*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3)
	await credits(msg)

async def betray_carolin(ctx):
	embed = discord.Embed(title='Betray Caroline', description='**Bang Bang**', color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Caroline:** *Whyyy*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Raphael:** *Good job, knew you would take the right choice*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Rapheal:** *gn (Raphael goes up to you and snaps your neck)*'
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2.5)
	await credits(msg)

async def rapheal_betrayel_2(ctx):
	embed = discord.Embed(description=f"**{ctx.author.display_name}:** *Hmm, i think i am gonna stay away from Rapheal for now*")
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**???:** *PST PSSST*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**{ctx.author.display_name}:** *WHO\'S THERE... SHOW YOURSELF*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**???:** *SHHHHH, you don\'t want him to hear you*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Who will hear me? who even are you*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**???:** *It\'s me... Caroline*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Why are you hiding*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *I am hiding from Rapheal*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Caroline:** *He wants to kill us*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n*(in a distance) YOU MOTHERFUCKER... YOU\'RE THE REASON MY SHIP GOT DESTROYED*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *Oh no, Adam stands no chance against Raphael*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *We should go and try to help him*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Caroline:** *...\n\nWe were too late, he is already dead*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.4)
	embed.description += f'\n**Raphael:** *Well well well, would you look who it is*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n**Caroline:** *YOU WON\'T GET AWAY WITH WHAT YOU"VE DONE*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**Raphael:** *And who is gonna stop me*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**{ctx.author.display_name}:** *ME. WITH THE GUN YOU GAVE ME*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	await ctx.send("Shoot Raphael with your gun? (You have 5 seconds to decide)\n1. Yes\n2. No\n3. ...")
	try:
		inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1','2','3'], timeout=5)
		inp = inp.content
	except asyncio.TimeoutError:
		inp = '3'
	if inp == '1':
		await good_ending(ctx)
	else:
		embed.description = '*Raphael Snatches the gun from your hands*'
		await msg.edit(embed=embed)
		await asyncio.sleep(2)
		await bad_ending(ctx)

async def caroline_and_adam(ctx):
	embed = discord.Embed(description=f'**{ctx.author.display_name}:** *I will wait a bit*', color=discord.Color.blurple())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2)
	embed.description += '\n**???:** *PST PSSST*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f"\n**???:** *It's us caroline and adam*"
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f"\n**{ctx.author.display_name}:** *Why are you guys hiding?*"
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *We are hiding from Rapheal*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Caroline:** *He wants to kill us*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'**Adam:** *That motherfucker destroyed my ship on purpose*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'**{ctx.author.display_name}:** *So what should we do now*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'**Caroline:** *I say we all attack him at the same time*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'**Adam:** *Orrrr {ctx.author.display_name} could go fight him alobe considering he has the gun*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	await ctx.send('Fight rapheal alone?\n1. Yes\n2. No')
	try:
		inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1','2'], timeout=5)
		inp = inp.content
	except asyncio.TimeoutError:
		inp = '1'
	if inp == '1':
		embed = discord.Embed(description=f'**{ctx.author.display_name}**: *Yea, Adam has a point*')
		msg = await ctx.send(embed=embed)
		embed.description += f'\n**Raphael:** *Oh {ctx.author.display_name} what are you doing there*'
		for _ in range(3):
			sword = list(random.choice(words))
			word = sword
			sword.shuffle()
			sword = ''.join(sword)
			await ctx.send(f'You have 5 seconds to unscramble the word {sword}')
			try:
				inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content == ''.join(word), timeout=5)
			except asyncio.TimeoutError:
				pass
			else:
				return back_home(ctx)
		return bad_ending(ctx)
	else:
		adam_alive = True
		embed = discord.Embed(description=f'**{ctx.author.display_name}**: *Eh, i would rather not be alone against Raphael even with a gun*')
		msg = await ctx.send(embed=embed)
		await asyncio.sleep(2)
		embed.description += f'\n**Raphael:** *Exactly, even with a gun you won\'t be able to scratch me*'
		await asyncio.sleep(3)
		for _ in range(5):
			sword = list(random.choice(words))
			word = sword
			sword.shuffle()
			sword = ''.join(sword)
			await ctx.send(f'You have 5 seconds to unscramble the word {sword}')
			try:
				inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=5)
			except asyncio.TimeoutError:
				pass
			else:
				if inp.content == ''.join(word):
					if adam_alive:
						return back_home(ctx)
					else:
						return good_ending(ctx)
				else:
					if adam_alive:
						embed.description += '\n*Raphael was able to snap adam\'s neck killing him instantly'
						await msg.edit(embed=embed)

		return bad_ending(ctx)

async def rapheal_betrayel_1(ctx):
	has_gun = True
	embed = discord.Embed(description=f"**{ctx.author.display_name}:** *Raphael, is that you?*", color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Raphael:** *Oh yes. {ctx.author.display_name}?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Yea it\'s me, where are we?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Raphael:** *I don\'t know, do you still have that gun i gave you?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Yea, why?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.75)
	embed.description += f'\n**Raphael:** *Well you could give it to me now.*'
	await msg.edit(embed=embed)
	await ctx.send('Give rapheal your gun?\n1. Yes\n2. No')
	inp = await bot.wait_for('message', check=lambda m: m.content in ['1','2'] and m.author == ctx.author and m.channel == ctx.channel)
	if inp.content == '1':
		has_gun = False
		embed.description += f'\n**Raphael:** *Thank you, this will be useful lat-*'
		await msg.edit(embed=embed)
	else:
		embed.description += f'\n**Raphael:** *What do you mean no? just give me th-*'
		await msg.edit(embed=embed)
	embed.description += f'\n**Adam:** *YOU MOTHERFUCKER... YOU\'RE THE REASON MY SHIP GOT DESTROYED*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.5)
	embed.description += f'\n**Raphael:** *STAY RIGHT THERE*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.3)
	embed.description += f'\n**Adam:** (charges at Raphael) *I AM GONNA KILL YOU*'
	await msg.edit(embed=embed)
	await asyncio.sleep(1.7)
	if has_gun:
		embed.description += f'\n**Raphael:** *SHOOT HIM*'
		await ctx.send('Shoot Adam? (you have 8 seconds to decide)\n1. Yes\n2. No')
		try:
			inp = await bot.wait_for('message', check=lambda m: m.content in ['1','2'] and m.author == ctx.author and m.channel == ctx.channel, timeout=8)
		except asyncio.TimeoutError:
			inp = ctx.message
			inp.content = '2'
		if inp.content == '1':
			embed.description += f'\n...'
			await msg.edit(embed=embed)
			await asyncio.sleep(1.3)
			embed.description += '\n**Raphael:** *Thank you*'
		else:
			embed.description += f'\n**Raphael:** *WHAT ARE YOU DOING, SHOOT HIM ALREADY*'
			await msg.edit(embed=embed)
			await asyncio.sleep(1.5)
			embed.description += f'\n**Raphael:** *(chokes Adam to death)*'
			await msg.edit(embed=embed)
			await asyncio.sleep(1.5)
			embed.description += f'\n**Raphael:** *Thank you for nothing moron*'
	else:
		embed.description += f'\n**Raphael:** *(shoots Adam)*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed = discord.Embed(description = f'\n**Raphael:** *Let\'s continue looking for Caroline, let\'s hope she doesn\'t go crazy like Adam*', color=discord.Color.dark_theme())
	msg = await ctx.send(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Hey, What about we split so we can cover more area*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**Raphael:** *Good idea*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**???:** *pst... pst... PST*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**{ctx.author.display_name}:** *WHO\'S THERE*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2)
	embed.description += f'\n**???:** *SHHHHHH, don\'t let him hear you*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *him? wha, who are you?*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *I am Caroline and i am talking about Raphael*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Oh Caroline, didn\'t recognize your voice*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**{ctx.author.display_name}:** *Why do you not want Raphael to hear us? he\'s been searching for you*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**Caroline:** *Do you seriously not see anything wrong with him killing Adam???*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3.5)
	embed.description += f'\n**{ctx.author.display_name}:** *I mean, Adam attacked him first*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Raphael:** *Good job, you found her!*'
	await msg.edit(embed=embed)
	await asyncio.sleep(2.5)
	embed.description += f'\n**Caroline:** *STAY RIGHT THERE, DON\'T GET ANY CLOSER*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3)
	embed.description += f'\n**Raphael:** *Why would i do that*'
	await msg.edit(embed=embed)
	await asyncio.sleep(3)
	if has_gun:
		embed.description += f'\n**{ctx.author.display_name}:** *Because i have the gun*'
		await msg.edit(embed=embed)
		await asyncio.sleep(3)
		embed.description += f'\n**Raphael:** *You wouldn\'t have the guts*'
		await msg.edit(embed=embed)
		await asyncio.sleep(3)
		embed.description += f'\n**Caroline:** *SHOOT HIM, HE CRASHED THE SHIP ON PURPOSE*'
		await msg.edit(embed=embed)
		await asyncio.sleep(2.5)
		embed.description += f'\n**Caroline:** *HE WANTS TO KILL US*'
		await msg.edit(embed=embed)
		await asyncio.sleep(2.5)
		await ctx.send("Shoot Raphael? (You have 5 seconds to decide)\n1. Yes\n2. Shoot Caroline instead\n3. ...")
		try:
			inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1','2','3'], timeout=5)
			inp = inp.content
		except asyncio.TimeoutError:
			inp = '3'
		if inp == '1':
			await good_ending(ctx)
		elif inp == '2':
			await betray_carolin(ctx)
		else:
			embed.description += '\n**Rapheal:** *Knew you wouldn\'t dare, Now give me the gun before someone gets hurt*'
			await msg.edit(embed=embed)
			await asyncio.sleep(3)
			embed.description += f'\n**{ctx.author.display_name}:** *Explain yourself first*'
			await msg.edit(embed=embed)
			await asyncio.sleep(3)
			embed.description += f'\n**Raphael:** *I SAID GIVE ME THE GUN* (Starts running at you)'
			await msg.edit(embed=embed)
			await asyncio.sleep(2.5)
			await ctx.send("Shoot Raphael? (You have 3 second to decide)\n1. Yes\n2. ...")
			try:
				inp = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ['1','2','3'], timeout=3)
				inp = inp.content
			except asyncio.TimeoutError:
				inp = '2'
			if inp == '1':
				await good_ending(ctx)
			elif inp == '2':
				await bad_ending(ctx)
	else:
		embed.description += '\n**Raphael:** *Guess who has the gun* (he says with a smug grin)'
		await msg.edit(embed=embed)
		await asyncio.sleep(3)
		await bad_ending(ctx)

def get_player(lst):
	"""Returns the x, y coordinates of the player on the board"""
	for x, row in enumerate(lst):
		for y, column in enumerate(row):
			if column == 'p':
				return x, y

def go_direction(lst, direction, player_index):
	"""Moves the player into a direction and makes sure the player isn't in an infinite loop/off screen"""
	x, y = player_index
	moves = 0
	while True:
		moves += 1
		x += direction[0]
		y += direction[1]
		if x < 0 or y < 0:
			return None, "Dead"
		try:
			if lst[x][y] == 'w':
				x -= direction[0]
				y -= direction[1]
				break
			elif lst[x][y] == 'u':
				x -= direction[0]
				y -= direction[1]
				direction = UP
			elif lst[x][y] == 'd':
				x -= direction[0]
				y -= direction[1]
				direction = DOWN
			elif lst[x][y] == 'l':
				x -= direction[0]
				y -= direction[1]
				direction = LEFT
			elif lst[x][y] == 'r':
				x -= direction[0]
				y -= direction[1]
				direction = RIGHT
			elif lst[x][y] == 'b':
				lst[x][y] = 'g'
				x -= direction[0]
				y -= direction[1]
				break
		except IndexError:
			return None, "Dead"
		if moves > 150:
			return 'Infinite loop', "Dead"
	return lst, x, y

def save_maze(maze):
	"""Saves the player made maze, only saves it if the player was able to beat it to prove that the maze was actually possible"""
	if not 'levels.txt' in os.listdir():
		f = open('levels.txt', mode='x')
		f.write(maze+'\n')
	else:
		f = open('levels.txt', mode='a')
		f.write(maze+'\n')

async def score_db():
	"""Creates "scores.db" which saves the scores for the leaderboard command"""
	await bot.wait_until_ready()
	bot.db = await aiosqlite.connect('scores.db')
	await bot.db.execute("CREATE TABLE IF NOT EXISTS scores (author_id int, score int, command_name text)")

async def save_score(ctx, score):
	"""Adds the player score into scores.db"""
	cursor = await bot.db.execute("SELECT score from scores WHERE author_id = ? AND command_name = ?", (ctx.author.id, ctx.command.name))
	data = await cursor.fetchone()
	if data:
		if data[0] < score:
			await bot.db.execute(f"UPDATE scores SET score = ? WHERE author_id = ? AND command_name = ?", (score, ctx.author.id, ctx.command.name))
	else:
		await bot.db.execute("INSERT OR IGNORE INTO scores (author_id, score, command_name) VALUES (?,?,?)", (ctx.author.id, score, ctx.command.name))
	await bot.db.commit()

def storyline_check():
	def predicate(ctx):
		try:
			if len(cache[str(ctx.author.id)]) >= 3: # it shouldn't be more than 3 but this is just in case it somehow is
				return True
		except KeyError:
			pass
		return False
	return commands.check(predicate)

# zombies board
board = [
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
['q','q','q','q','q','G','q','q','q','q','q'],
['G','G','G','G','G','p','G','G','G','G','G'],
['q','q','q','q','q','G','q','q','q','q','q'],
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
['g','g','g','g','q','G','q','g','g','g','g'],
]

@bot.event
async def on_ready():
	"""on_ready"""
	print('Online!')

@bot.command()
async def zombies(ctx):
	"""You're surrounded by zombies!!! don't worry tho, you have a gun. React to the reaction pointing in the direction you want *don't miss*"""
	board_copy = copy.deepcopy(board)
	update_cache(ctx)

	bullets = []
	zombies = []
	score = 0
	alive = True

	msg = await ctx.send(embed=discord.Embed(title='Chapter 1: What happened', color=discord.Color.dark_theme()))
	await scene_1(ctx, msg)
	emojis = ['⬆','⬅','➡','⬇','🏳']
	for emoji in emojis:
		await msg.add_reaction(emoji)
	while True:
		await msg.edit(content=f"Score: {score}\n", embed=discord.Embed(title='Zombies', description=format_board(board_copy), color=discord.Color.blurple()))
		if not len(bullets) == 5:
			try:
				inp, _ = await bot.wait_for('reaction_add', check = lambda r,u: str(r) in emojis and u == ctx.author and r.message == msg, timeout=3.5)
				try:
					await msg.remove_reaction(str(inp), ctx.author)
				except discord.Forbidden:
					pass
				if str(inp) == '🏳':
					await save_score(ctx, score)
					return await ctx.send('Ended the game!')
				bullets.append(Bullet(conversion[str(inp)], [5,5]))
			except asyncio.TimeoutError:
				pass
		for bullet in bullets:
			board_copy[bullet.index[0]][bullet.index[1]] = 'G'
			try:
				bullet.move()
				if bullet.index[0] < 0:
					bullets.remove(bullet)
					continue
				board_copy[bullet.index[0]][bullet.index[1]] = 'L'
			except IndexError:
				bullets.remove(bullet)
		board_copy, bullets, zombies, score = check_zombie_collides(board_copy, bullets, zombies, score)
		for zombie in zombies:
			try:
				board_copy[zombie.index[0]][zombie.index[1]] = 'G'
			except IndexError:
				pass
			zombie.move()
			board_copy[zombie.index[0]][zombie.index[1]] = 'z'
			if zombie.index == [5,5]:
				await save_score(ctx, score)
				return await ctx.send(f"The zombie ate {ctx.author.display_name}'s brain!!!\n\nScore: {score}")
		board_copy[5][5] = 'p'
		if len(zombies) < 5:
			zombie_number = random.choice([0,0,0,0,1,1,1,2,2,3])
			directions_copy = copy.copy(directions)
			for i in range(zombie_number):
				direction = random.choice(directions_copy)
				zombies.append(Zombie(direction))
				directions_copy.remove(direction)

@bot.command()
async def spaceshooter(ctx):
	"""You're in a spaceship now. move the spaceship to avoid and shoot at the aliens for score and make sure to net get hit"""
	update_cache(ctx)
	msg = await ctx.send(embed=discord.Embed(title='Chapter 2: The spaceship', color=discord.Color.dark_theme()))
	await scene_2(ctx, msg)
	bord = [['g']*5 for i in range(7)]
	emojis = ['⬅','🏳','➡']
	for emoji in emojis:
		await msg.add_reaction(emoji)
	index = 2
	bullets = []
	aliens = []
	lifes = 3
	bullet_limit = 5
	score = 0
	bord_copy = copy.deepcopy(bord)
	bord_copy[6][index] = 's'
	scene_3_done = False 
	while True:
		bord_copy = copy.deepcopy(bord)
		if score >= 30 and not scene_3_done:
			msg = await scene_3(ctx)
			scene_3_done = True
		try:
			inp, _ = await bot.wait_for('reaction_add', check = lambda r,u: str(r) in emojis and u == ctx.author and r.message == msg, timeout=2.5)
			try:
				await msg.remove_reaction(str(inp), ctx.author)
			except discord.Forbidden:
				pass
			if str(inp) == '⬅':
				if not len(bullets) == bullet_limit:
					bullets.append(Bullet(UP, [6, index]))
				index -= 1
				if index < 0:
					index = len(bord_copy[0])-1
			elif str(inp) == '➡':
				if not len(bullets) == bullet_limit:
					bullets.append(Bullet(UP, [6, index]))
				index += 1
				if index == len(bord_copy[0]):
					index = 0
			elif str(inp) == '🏳':
				await ctx.send('Ended the game!')
				await save_score(ctx, score)
				return
		except asyncio.TimeoutError:
			if not len(bullets) == bullet_limit:
				bullets.append(Bullet(UP, [6, index]))

		for bullet in bullets:
			bullet.move()
			if bullet.index[0] < 0:
				bullets.remove(bullet)
				continue
			bord_copy[bullet.index[0]][bullet.index[1]] = 'L'

		if random.randint(1, 10) >= 5 and len(aliens) <= 5:
			for _ in range(random.randrange(1,3)):
				alien = Alien()
				while alien.index in [a.index for a in aliens]:
					alien = Alien()
				aliens.append(alien)

		for alien in aliens:
			continue_ = False
			for bullet in bullets:
				if bullet.index == alien.index or [bullet.index[0]+bullet.direction[0], bullet.index[1]+bullet.direction[1]] == alien.index:
					bord_copy[bullet.index[0]][bullet.index[1]] = 'g'
					bullets.remove(bullet)
					aliens.remove(alien)
					continue_ = True
					score += 1
					break
			if continue_:
				continue
			alien.move()
			if alien.index == [6, index]:
				lifes -= 1
				await ctx.send(f"You have {lifes} lifes left")
				aliens.remove(alien)
				if lifes <= 0:
					await save_score(ctx, score)
					return await ctx.send(f"You don't have any more lifes!!!\n\nScore: {score}")
				continue
			elif alien.index[0] == len(bord_copy):
				aliens.remove(alien)
				continue
			bord_copy[alien.index[0]][alien.index[1]] = 'a'
		bord_copy[6][index] = 's'
		embed = discord.Embed(title='Aliens', description=format_board(bord_copy), color=discord.Color.blurple())
		await msg.edit(content=f"Score: {score}", embed=embed)

@bot.group(invoke_without_command=True)
async def maze(ctx, mode='storyline'):
	"""good and bad news, the bad news are that the spaceship is now destroyed the good news you're all on a planet with your space suits, the planet's gravity is messed up tho. Try to get to the :x: in the storyline mode" or play user made mazes in the usermade mode"""
	msg = None
	emojis = ['⬆','⬅','➡','⬇','🏳']
	if mode.lower() not in ['storyline', 'usermade']:
		return await ctx.send(f'{mode} isn\'t a valid mode, available modes: "storyline"/"usermade"')
	elif mode.lower() == 'storyline':
		mazes = ["wwwwwwwwww\nwp wx    w\nw        w\nwwwwwwwwww\n", "wwwwwwwwww\nwp wx    w\nw        w\nw wwwwwwww\n","w wwwwwwww\nwpw      w\nw w wwww w\nw w w  w w\nw w wx w w\nw w ww w w\nw w    w w\nw wwwwww w\nw        w\nwwwwwwwwww\n","ww        ww\nwp         w\n            \nww          \n          ww\n          xw\n  w         ","ww    www\nwp     ww\n         \n       ww\nww wx   w\nw       w\nw        \nw      ww\nww    www","wwwwwwww\nwp w   w\nw      w\nw      w\nww     w\nw   x  w\nw   w  w\n        ","wwwwwww\nwp    w\nw     w\nwbwwwbw\nw     w\nw    xw\nwwwwwww","    w       \nwpw        w\n     wwww   \n     w      \n            \n     wxw    \nw    www    \n w        ww","wwwwwlw\nwdd   w\ndpdx  w\nw www w\nw     u\nwrwwwww","wpw wwwwwwwwwww\nw u       ww   \nw www  ww ww  w\nw      ww ww  w\nwwwwwwwww ww  w\nww      w ww  w\nw  lw          \n    www wwwwwww\nw   wwx       w\nwwwwwww       w\n              w\n        wwwww w\nw              \nww     wwwwwwrw"]
		msg = await scene_4(ctx)
		for emoji in emojis:
			await msg.add_reaction(emoji)
	else:
		try:
			f = open('levels.txt', mode='r')
		except FileNotFoundError:
			return await ctx.send(f"No user made mazes :pensive:. You could be the first tho, use the `{ctx.prefix}maze add` command!")
		mazes = f.readlines()
		mazes = [maze[:-1] for maze in mazes]
		random.shuffle(mazes)
	usermade = False if mode.lower() == 'storyline' else True
	for maze in mazes:
		lst = []
		for line in maze.split(r'\n' if usermade else '\n'):
			lst.append(list(line))
		embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
		if msg:
			await msg.edit(embed=embed)
		else:
			msg = await ctx.send(embed=embed)
			for emoji in emojis:
				await msg.add_reaction(emoji)
		while True:
			await msg.edit(embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple()))
			inp, _ = await bot.wait_for('reaction_add', check = lambda r, u: str(r) in emojis and u == ctx.author and r.message == msg)
			try:
				await msg.remove_reaction(str(inp), ctx.author)
			except discord.Forbidden:
				pass
			x, y = get_player(lst)
			lst[x][y] = ' '
			if str(inp) == '🏳':
				return await ctx.send('Ended the game!')
			lst, x, y = go_direction(lst, conversion[str(inp)], (x, y))
			if x == None:
				embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
				await msg.edit(embed=embed)
				return await ctx.send("You died")
			if lst[x][y] == 'x':
				lst[x][y] = 'p'
				await ctx.send("You won!", delete_after=5)
				embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
				await msg.edit(embed=embed)
				await asyncio.sleep(1)
				break
			lst[x][y] = 'p'
	if not usermade:
		update_cache(ctx)

@maze.command()
async def add(ctx, *, maze):
	"""A way to add your very own maze"""
	maze = maze.lower()
	if maze.startswith('```') and maze.endswith('```'):
		maze = '\n'.join(maze.split('\n')[1:])[:3]
	if 'p' not in maze:
		return await ctx.send("There is no player")
	elif 'x' not in maze:
		return await ctx.send("There is no exit point")
	elif maze.count('p') > 1:
		return await ctx.send("Can't have multiple players at the same time")
	elif maze.count('x') > 1:
		return await ctx.send("Can't have multiple exit points at the same time")
	lst = []
	biggest_length = sorted([len(i) for i in maze.split('\n')])[-1]
	for line in maze.split('\n'):
		for char in line:
			if char not in ['w',' ', 'p','x','u','d','r','l','b']:
				return await ctx.send(f'Invalid syntax: unrecognized item "{char}"')
		if len(line) != biggest_length:
			line += ' '*(biggest_length-len(line))
		lst.append(list(line))
	if len(lst) < 3 or len(lst[0]) < 3:
		return await ctx.send("The maze must be atleast 3x3 big")
	embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
	try:
		msg = await ctx.send(embed=embed)
	except discord.HTTPException:
		return await ctx.send(f"The maze is too big ({len(embed.description)}/4096)")
	emojis = ['⬆','⬅','➡','⬇','🏳']
	for emoji in emojis:
		await msg.add_reaction(emoji)
	origin_lst = copy.deepcopy(lst)
	while True:
		await msg.edit(embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple()))
		inp, _ = await bot.wait_for('reaction_add', check = lambda r, u: str(r) in emojis and u == ctx.author and r.message == msg)
		try:
			await msg.remove_reaction(str(inp), ctx.author)
		except discord.Forbidden:
			pass
		lst, x, y = get_player(lst)
		lst[x][y] = ' '
		if str(inp) == '🏳':
			return await ctx.send('Ended the game!')
		x, y = go_direction(lst, conversion[str(inp)], (x, y))
		if x == None or isinstance(x, str):
			embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
			await msg.edit(embed=embed)
			return await ctx.send("You died!")
		if lst[x][y] == 'x':
			lst[x][y] = 'p'
			await ctx.send("You won! *saving maze*")
			save_maze(r'\n'.join([''.join(i) for i in origin_lst]))
			embed = discord.Embed(title='Maze', description=format_board(lst), color=discord.Color.blurple())
			await msg.edit(embed=embed)
			await asyncio.sleep(1)
			break
		lst[x][y] = 'p'

@bot.command()
async def speed(ctx, member:discord.Member=None):
	"""A simple game where you have 5 seconds to send the coordinates of the colored circles, if a member is selected it's a race to 30 points, otherwise it goes on until you send "end"/"stop"/"cancel\""""
	if member:
		if member.bot or member == ctx.author:
			member = None
			score = 0
		else:
			scores = {ctx.author:0,member:0}
	else:
		score = 0

	board = [['g']*5 for _ in range(5)]
	e = discord.Embed(title='Speed', description=(f"{ctx.author.display_name} score: {scores[ctx.author]} | {member.display_name} score: {scores[member]}" if member else f"Score: {score}")+'\n'+format_speed_board(board), color=discord.Color.blurple())
	msg = await ctx.send(embed=e)
	while True:
		board_copy = copy.deepcopy(board)
		board_copy = summon_blocks(board_copy)
		e = discord.Embed(title='Speed', description=(f"{ctx.author.display_name} score: {scores[ctx.author]} | {member.display_name} score: {scores[member]}" if member else f"Score: {score}")+'\n'+format_speed_board(board_copy), color=discord.Color.blurple())
		await msg.edit(embed=e)
		try:
			inp = await bot.wait_for('message', check = lambda m: m.author in [ctx.author, member] and m.channel == ctx.channel, timeout=5)
		except asyncio.TimeoutError:
			pass
		else:
			if inp.content.lower() in ['end','stop','cancel']:
				await ctx.send("Stopped the game!")
				return await save_score(ctx, score)
			try:
				await inp.delete()
			except discord.Forbidden:
				pass
			coors = convert(inp.content)
			for coor in coors:
				x, y = coor
				if board_copy[x][y] == 'b':
					if member:
						scores[inp.author] += 1
						if scores[inp.author] >= 30:
							return await ctx.send(f'{inp.author.mention} won!!!')
					else:
						score += 1
				else:
					if member:
						if scores[inp.author] > 0:
							scores[inp.author] -= 1
					else:
						if score > 0:
							score -= 1

@bot.command()
@storyline_check()
async def end(ctx):
	# del cache[str(ctx.author.id)] # The player will have to replay the game once again to be able to use the command again
	num = await scene_5(ctx)
	if num == 1:
		await rapheal_betrayel_1(ctx)
	if num == 2:
		await rapheal_betrayel_2(ctx)
	if num == 3:
		await caroline_and_adam(ctx)

@bot.command(aliases=['botinfo','about'])
async def info(ctx):
	"""Some generic info"""
	embed = discord.Embed(title='Bot Info', description=f'I am a discord bot made by andreawthaderp#3031 for the documatic hackathon', color=discord.Color.dark_theme())
	await ctx.send(embed=embed)

@bot.command(aliases=['lb'])
@commands.guild_only()
async def leaderboard(ctx, command_name, entries=5):
	"""a way to see the top x scores of a certain game"""
	cmd = bot.get_command(command_name)
	if not cmd:
		return await ctx.send(f'The command {command_name} does not exist')
	embed = discord.Embed(title=f"Leaderboard", description=f"Top {entries} {command_name} scores\n\n", colour=0x24e0db)

	index = 0
	async with bot.db.execute("SELECT author_id, score FROM scores WHERE command_name = ? ORDER BY score DESC LIMIT ?", (cmd.name, entries)) as cursor:
		async for entry in cursor:
			member_id, score = entry
			member = await bot.fetch_user(member_id)
			index += 1
			if index == 1:
				emoji = '🥇'
			elif index == 2:
				emoji = "🥈"
			elif index == 3:
				emoji = "🥉"
			else:
				emoji = "🔹"
			embed.description += f"**{emoji} #{index} {member.mention}**\nScore: `{score}`\n\n"
	if not index:
		return await ctx.send(f"No scores in the database for {command_name}")

	await ctx.send(embed=embed)

# Event for catching errors 
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CheckFailure):
		return await ctx.send('You need to play the "zombies" and "spaceshooter" and "maze" commands to be able to play the end command')
	elif isinstance(error, commands.NoPrivateMessage):
		return await ctx.send(f"The {ctx.command.name} command can only be used in a guild")
	else:
		raise error

# run the score_db function
bot.loop.create_task(score_db())
bot.run(os.getenv("TOKEN"))
asyncio.run(bot.db.close())
# Close the db

with open("cache.json", "w") as f:
    json.dump(cache, f, indent = 4)
# Saving the cache so we won't loose the date when if the bot restarts
