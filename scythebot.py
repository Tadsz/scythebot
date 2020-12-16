# bot.py
import os
import random
import discord
import numpy as np
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
sourcelink = 'https://github.com/tariqdam/scythebot/'
botversion = 'alpha006'

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
  print('Logged in as ScytheBot')
  print('ScytheBot {}'.format(botversion))
  print('----------')

# Initialize factions, mats, and rank lists ordered according to factions list
dfact = {'original': ('Rusviet', 'Crimean', 'Polania', 'Nordic', 'Saxony'), 'add-on': ('Albion', 'Togawa')}
dfact_full = sum(dfact.values(), ())
dmats = {'original': ('Industrial', 'Engineering', 'Patriotic', 'Mechanical', 'Agricultural'), 'add-on': ('Militant', 'Innovative')}
dmats_full = sum(dmats.values(), ())
rank_names = ('F', 'D', 'C', 'B', 'A', 'S', 'SS', 'BANNED')
drank = {'Industrial'  : (8,6,5,5,5,1,2),\
	 'Engineering' : (6,5,3,4,2,2,2),\
	 'Patriotic'   : (5,8,4,4,4,3,3),\
	 'Mechanical'  : (6,6,4,3,4,1,1),\
	 'Agricultural': (5,4,4,3,2,2,3),\
	 'Militant'    : (7,7,5,3,4,4,3),\
	 'Innovative'  : (7,7,6,5,6,4,4)}

#default penalty and ban levels
dpen = 7
dban = 8
dfull = 0
vfact, vmat, vpen, vban, vfull, vjoin = {}, {}, {}, {}, {}, {}

async def generate(g_players, g_penalty: int, banned_rank: int, g_full: int):
  if (g_full == 1):
    factions = dfact_full.copy()
    mats = dmats_full.copy()
  elif (g_full == 2):
    factions = dfact['add-on']
    mats = dmats['add-on']
  else:
    factions = dfact['original']
    mats = dmats['original']
  if (len(g_players) > len(factions)):
    g_players = g_players[0:len(factions)]
  random.shuffle(g_players)
  random.shuffle(factions)
  random.shuffle(mats)
  rank_index, rank, penalty_list = [], [], []
  message = {}
  for i in range(len(g_players)):
    rank_index.append(drank[mats[i]][dfact_full.index(factions[i])])
    rank.append(rank_names[rank_index[i]-1])
    penalty_list.append(g_penalty * rank_index[i])
  penalty_offset = [pen - min(penalty_list) for pen in penalty_list]
  if (max(rank_index) >= banned_rank):
    message = await generate(g_players, g_penalty, banned_rank, g_full)
    return message
  for i in range(len(g_players)):
    message[i] = ('{}: {} {}; rank {} ({}); penalty {} points'.format(g_players[i], factions[i], mats[i], rank[i], rank_index[i], penalty_offset[i]))
  return message

async def levdist(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y
    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix[x,y] = min(matrix[x-1, y] + 1, matrix[x-1, y-1], matrix[x, y-1] + 1)
            else:
                matrix[x,y] = min(matrix[x-1,y] + 1, matrix[x-1,y-1] + 1, matrix[x,y-1] + 1)
    return (matrix[size_x - 1, size_y - 1])

@bot.command (name='join', help='Join the player list for the next game round. As is to add own name or pass (multiple) arguments for each player name.')
async def join(ctx, *args):
  global vjoin
  if (ctx.guild.id not in vjoin):
      vjoin[ctx.guild.id] = []
  if not args:
    vjoin[ctx.guild.id].append(ctx.author.name)
  elif (args[0] == '$c'):
    #voice_channel = discord.utils.get(ctx.guild.voice_channels, name="General")
    if ctx.author.voice and ctx.author.voice.channel:
      voice_channel = ctx.author.voice.channel
      members = [user.name for user in voice_channel.members]
      vjoin[ctx.guild.id].extend(members)
    elif len(args) > 1:
      voice_channel = discord.utils.get(ctx.guild.voice_channels, name=args[1])
      members = [user.name for user in voice_channel.members]
      if len(members) >= 1:
        vjoin[ctx.guild.id].extend(members)
    else:
      await ctx.send('Join a voice channel to indicate which channel to use')
  else:
    for name in args:
     vjoin[ctx.guild.id].append(name)
  await ctx.send(vjoin[ctx.guild.id])
  return

@bot.command (name='list', help = 'Show current list of players joined.')
async def list(ctx):
  await ctx.send(vjoin[ctx.guild.id])
  return

@bot.command (name='start', help='Start generating based on the list of joined players')
async def start(ctx):
  l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
  l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
  l_full = vfull[ctx.guild.id] if ctx.guild.id in vfull else dfull
  if (ctx.guild.id) not in vjoin:
    await ctx.send('No names provided; use join first.')
    return
  response = await generate(vjoin[ctx.guild.id], l_pen, l_ban, l_full)
  vjoin[ctx.guild.id] = []
  for set in response:
    await ctx.send(response[set])
  return

@bot.command (name='js', help='Join+Start [optional options] [list of names]')
async def js(ctx, *args):
  userlist = []
  l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
  l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
  l_full = vfull[ctx.guild.id] if ctx.guild.id in vfull else dfull
  if not args:
    if ctx.author.voice and ctx.author.voice.channel:
      userlist = [user.name for user in ctx.author.voice.channel.members]
      if (len(userlist) >= 1):
        response = await generate(userlist, l_pen, l_ban, l_full)
      else:
        await ctx.send('No players found in voice chat')
        return
  if (args[0] == '$c') and (len(args) > 1):
    voice_channel = discord.utils.get(ctx.guild.voice_channels, name=args[1])
    if voice_channel:
      userlist = [user.name for user in voice_channel.members]
      if len(userlist) >= 1:
        response = await generate(userlist, l_pen, l_ban, l_full)
      elif len(userlist) == 0:
        await ctx.send('No players found in voice chat')
        return
    else:
      voice_list = [x.name for x in ctx.guild.voice_channels]
      levdistlist = []
      for x in voice_list:
        levdistlist.append(await levdist(args[1], x))
      await ctx.send(voice_list)
      if min(levdistlist) < 4:
        voice_channel = discord.utils.get(ctx.guild.voice_channels, name=voice_list[levdistlist.index(min(levdistlist))])
        userlist = [user.name for user in voice_channel.members]
        if len(userlist) >= 1:
          response = await generate(userlist, l_pen, l_ban, l_full)
        elif len(userlist) == 0:
          await ctx.send('No players found in voice chat')
          return
      else:
        await ctx.send('Voice channel not found')
        return
  else:
    argstart = 0
    if args[0][0] == '$':
      l_pen = int(args[0][1])
      l_ban = int(args[0][2])
      l_full = int(args[0][3])
      argstart = 1
    for arg in args[argstart:]:
      userlist.append(arg)
    response = await generate(userlist, l_pen, l_ban, l_full)
  message = ''
  for set in response:
    message += '\n' + response[set]
  await ctx.send(message.strip('\n'))
  return

@bot.command (name='jsf', help='Join+Start+Full [list of names]. Generate random faction/mat combo\'s based on base game and expansion')
async def jsf(ctx, *args):
  userlist = []
  l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
  l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
  if not args:
    userlist = [user.name for user in discord.utils.get(ctx.guild.voice_channels, name="General").members]
    if (len(userlist) >= 1):
      response = await generate(userlist, l_pen, l_ban, 1)
    else:
      await ctx.send('No players found in voice chat General')
      return
  else:
    for arg in args:
      userlist.append(arg)
    response = await generate(userlist, l_pen, l_ban, 1)
  message = ''
  for set in response:
    message += '\n' + response[set]
  await ctx.send(message.strip('\n'))
  return

@bot.command (name='jsa', help='Join+Start+Add-on Only [list of names]. Generate random faction/mat combo\'s based on base game and expansion')
async def jsa(ctx, *args):
  userlist = []
  l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
  l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
  if not args:
    userlist = [user.name for user in discord.utils.get(ctx.guild.voice_channels, name="General").members]
    if (len(userlist) >= 1):
      response = await generate(userlist, l_pen, l_ban, 2)
    else:
      await ctx.send('No players found in voice chat General')
      return
  else:
    for arg in args:
      userlist.append(arg)
    response = await generate(userlist, l_pen, l_ban, 2)
    message = ''
    for set in response:
      message += '\n' + response[set]
    await ctx.send(message.strip('\n'))
  return

@bot.command (name='pen', help='Set the penalty multiplier.')
async def pen(ctx, set_penalty: int):
  vpen[ctx.guild.id] = set_penalty
  await ctx.send('Penalty multiplier set to {}'.format(set_penalty))
  return

@bot.command (name='ban', help='Set the banned level')
async def ban(ctx, set_ban: int):
  vban[ctx.guild.id] = set_ban
  await ctx.send('Ban level set to {}'.format(set_ban))
  return

@bot.command (name='full', help='Set which factions/mats to use: 0=original, 1=full, 2=addon only')
async def full(ctx, set_full: int):
  vfull[ctx.guild.id] = set_full
  await ctx.send('Faction/mat selection set to {}'.format(set_full))
  return

@bot.command(name='roll_dice', help='Simulates rolling dice. Example: "roll_dice 3 6" will roll 3 dice of 6 sides.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

@bot.command(name='v', help='Get current version')
async def version(ctx):
  await ctx.send('Current version {}. Source code available at {}'.format(botversion, sourcelink))
  return

@bot.command(name='showdata', help='Show used data')
async def showdata(ctx):
  l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
  l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
  l_full = vfull[ctx.guild.id] if ctx.guild.id in vfull else dfull
  message = {'Factions':dfact_full, 'Mats':dmats_full, 'Ranks (ordered)':drank, 'Penalty':l_pen, 'Banned level': l_ban, 'Full':l_full}
  await ctx.send(message)

@bot.command(name='reset', help='Resets servers specific saved parameters')
async def reset(ctx):
  del vpen[ctx.guild.id]
  del vban[ctx.guild.id]
  del vfull[ctx.guild.id]
  del vjoin[ctx.guild.id]
  return

bot.run(TOKEN)
