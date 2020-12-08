# bot.py
import os
import random

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
  print('Logged in as ScytheBot')
  print('ScytheBot alpha003')
  print('----------')

fact_ori = ['Rusviet', 'Crimean', 'Polania', 'Nordic', 'Saxony']
fact_add = ['Albion', 'Togawa']
fact_full = fact_ori + fact_add
mats_ori = ['Industrial', 'Engineering', 'Patriotic', 'Mechanical', 'Agricultural']
mats_add = ['Militant', 'Innovative']
mats_full = mats_ori + mats_add
rank_names = ['F', 'D', 'C', 'B', 'A', 'S', 'SS', 'BANNED']
rank_industrial = [8,6,5,5,5,1,2]
rank_engineering = [6,5,3,4,2,2,2]
rank_patriotic = [5,8,4,4,4,3,3]
rank_mechanical = [6,6,4,3,4,1,1]
rank_agricultural = [5,4,4,3,2,2,3]
rank_militant = [7,7,5,3,4,4,3]
rank_innovative = [7,7,6,5,6,4,4]
joinlist = []

async def generate(g_players, g_penalty: int, g_full: int, banned_rank: int):
  if (g_full == 1):
    factions = fact_full
  else:
    factions = fact_ori
  if (g_full == 1):
    mats = mats_full
  else:
    mats = mats_ori
  random.shuffle(g_players)
  random.shuffle(factions)
  random.shuffle(mats)
  rank_index = []
  rank = []
  penalty_list = []
  message = {}
  for i in range(len(g_players)):
    rank_list =  await det_ranklist(mats[i])
    rank_index.append(rank_list[fact_full.index(factions[i])])
    rank.append(rank_names[rank_index[i]-1])
    penalty_list.append(g_penalty * rank_index[i])
  penalty_offset = [pen - min(penalty_list) for pen in penalty_list]
  if (max(rank_index) >= banned_rank):
    generate(g_players, g_penalty, g_full, banned_rank)
    return
  for i in range(len(g_players)):
    message[i] = ('{}: {} {}; rank {} ({}); penalty {} points'.format(g_players[i], factions[i], mats[i], rank[i], rank_index[i], penalty_offset[i]))
  return message

async def det_ranklist(mat):
  if (mat == 'Industrial'):
    return rank_industrial
  elif (mat == 'Engineering'):
    return rank_engineering
  elif (mat == 'Patriotic'):
    return rank_patriotic
  elif (mat == 'Mechanical'):
    return rank_mechanical
  elif (mat == 'Agricultural'):
    return rank_agricultural
  elif (mat == 'Militant'):
    return rank_militant
  elif (mat == 'Innovative'):
    return rank_innovative

@bot.command (name='join', help='Join the player list for the next game round. As is to add own name or pass (multiple) arguments for each player name.')
async def join(ctx, *args):
  global joinlist
  if not args:
    joinlist.append(ctx.author.name)
  elif (args[0] == '$channel'):
    voice_channel = discord.utils.get(ctx.message.server.channels, name="General", type=discord.ChannelType.voice)
    members = voice_channel.voice_members
    joinlist.append(members)
  else:
    for name in args:
     joinlist.append(name)
  await ctx.send(joinlist)

@bot.command (name='list', help = 'Show current list of players joined.')
async def list(ctx):
  await ctx.send(joinlist)

@bot.command (name='start', help='Start generating based on the list of joined players from the join command')
async def start(ctx):
  global joinlist
  response = await generate(joinlist, 7, 0, 8)
  joinlist = []
  for set in response:
    await ctx.send(response[set])
  return

@bot.command (name='js', help='Joins+Start [list of names]. Generate random faction/mat combo\'s based on base game only.')
async def js(ctx, *args):
  if not args:
    response = await generate(range(5), 7, 0, 8)
    await ctx.send('No arguments passed, assuming 5 players.')
    for set in response:
      await ctx.send(response[set])
  else:
    joinlist = []
    for arg in args:
      joinlist.append(arg)
    response = await generate(joinlist, 7, 0, 8)
    for set in response:
      await ctx.send(response[set])
  return

@bot.command (name='jsf', help='Join+Start+Full [list of names]. Generate random faction/mat combo\'s based on base game and expansion')
async def jsf(ctx, *args):
  if not args:
    response = await generate(range(5), 7, 1, 8)
    await ctx.send('No arguments passed, assuming 5 players.')
    for set in response:
      await ctx.send(response[set])
  else:
    joinlist = []
    for arg in args:
      joinlist.append(arg)
    response = await generate(joinlist, 7, 1, 8)
    for set in response:
      await ctx.send(response[set])
  return

@bot.command(name='roll_dice', help='Simulates rolling dice. Example: "roll_dice 3 6" will roll 3 dice of 6 sides.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

bot.run(TOKEN)
