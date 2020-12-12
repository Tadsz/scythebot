# bot.py
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
  print('Logged in as ScytheBot')
  print('ScytheBot alpha005')
  print('----------')

# Initialize factions, mats, and rank lists ordered according to factions list
dfact = {'original': ['Rusviet', 'Crimean', 'Polania', 'Nordic', 'Saxony'], 'add-on': ['Albion', 'Togawa']}
dfact_full = sum(dfact.values(), [])
dmats = {'original': ['Industrial', 'Engineering', 'Patriotic', 'Mechanical', 'Agricultural'], 'add-on': ['Militant', 'Innovative']}
dmats_full = sum(dmats.values(), [])
rank_names = ['F', 'D', 'C', 'B', 'A', 'S', 'SS', 'BANNED']
drank = {'Industrial'  : [8,6,5,5,5,1,2],\
	 'Engineering' : [6,5,3,4,2,2,2],\
	 'Patriotic'   : [5,8,4,4,4,3,3],\
	 'Mechanical'  : [6,6,4,3,4,1,1],\
	 'Agricultural': [5,4,4,3,2,2,3],\
	 'Militant'    : [7,7,5,3,4,4,3],\
	 'Innovative'  : [7,7,6,5,6,4,4]}

#default penalty and ban levels
dpen = 7
dban = 8
dfull = 0
vfact, vmat, vpen, vban, vfull, vjoin = {}, {}, {}, {}, {}, {}

async def generate(g_players, g_penalty: int, banned_rank: int, g_full: int):
  if (g_full == 1):
    factions = dfact_full
    mats = dmats_full
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
#  if (max(rank_index) >= banned_rank):
#    message = await generate(g_players, g_penalty, g_full, banned_rank)
#    return message
  for i in range(len(g_players)):
    message[i] = ('{}: {} {}; rank {} ({}); penalty {} points'.format(g_players[i], factions[i], mats[i], rank[i], rank_index[i], penalty_offset[i]))
  return message

@bot.command (name='join', help='Join the player list for the next game round. As is to add own name or pass (multiple) arguments for each player name.')
async def join(ctx, *args):
  global vjoin
  if (ctx.guild.id not in vjoin):
      vjoin[ctx.guild.id] = []
  if not args:
    vjoin[ctx.guild.id].append(ctx.author.name)
  elif (args[0] == '$c'):
    voice_channel = discord.utils.get(ctx.guild.voice_channels, name="General")
    members = [user.name for user in voice_channel.members]
    vjoin[ctx.guild.id].extend(members)
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
    userlist = [user.name for user in discord.utils.get(ctx.guild.voice_channels, name="General").members]
    if (len(userlist) >= 1):
      response = await generate(userlist, l_pen, l_ban, l_full)
    else:
      await ctx.send('No players found in voice chat General')
      return
  else:
    argstart = 0
    if args[0][0] == '$':
      l_pen = int(args[0][1])
      l_ban = int(args[0][2])
      l_full = int(args[0][3])
      await ctx.send(l_pen)
      await ctx.send(l_ban)
      await ctx.send(l_full)
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

@bot.command(name='reset', help='Resets servers specific saved parameters')
async def reset(ctx):
  del vpen[ctx.guild.id]
  del vban[ctx.guild.id]
  del vfull[ctx.guild.id]
  del vjoin[ctx.guild.id]
  return

bot.run(TOKEN)
