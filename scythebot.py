# bot.py
import os
import random
import discord
import numpy as np
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from asyncio import sleep
from datetime import datetime
import socket
from proverbs import use_proverb, get_proverb_history, get_proverb_numericals

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VALHEIM_HOST = os.getenv('VALHEIM_HOST')
VALHEIM_PORT = os.getenv('VALHEIM_PORT')
sourcelink = 'https://github.com/tadsz/scythebot/'
botversion = 'alpha009a'

loop_proverb = {}
loop_proverb_id = {}

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print('Logged in as ScytheBot')
    print('ScytheBot {}'.format(botversion))
    print('----------')


@bot.event
async def on_message(message):
    if len(message.content) > 25 or message.author.bot:
        return
    if any(x in message.content for x in thanks_notation):
        ctx = await bot.get_context(message)
        bot_active = 0
        history = await ctx.message.channel.history(limit=3).flatten()
        for message in history:
            if message.author.bot:
                bot_active = 1
        if bot_active == 1:
            resp = random.choice(range(0, len(thanks_responses)))
            await ctx.send(thanks_responses[resp])
            thanks_responded[ctx.guild.id] = 1
            await asyncio.sleep(60)
            thanks_responded[ctx.guild.id] = 0
            return
    if any(x in message.content for x in response_notation):
        ctx = await bot.get_context(message)
        thanks_activity = thanks_responded.get(ctx.guild.id)
        if (thanks_activity is not None) and thanks_activity == 1:
            resp = random.choice(range(0, len(response_responses)))
            await ctx.send(response_responses[resp])
            return
    await bot.process_commands(message)
    return


# Initialize factions, mats, and rank lists ordered according to factions list
dfact = {'original': ['Rusviet', 'Crimean', 'Polania', 'Nordic', 'Saxony'], 'add-on': ['Albion', 'Togawa']}
dfact_full = sum(dfact.values(), [])
dmats = {'original': ['Industrial', 'Engineering', 'Patriotic', 'Mechanical', 'Agricultural'],
         'add-on': ['Militant', 'Innovative']}
dmats_full = sum(dmats.values(), [])
rank_names = ['F', 'D', 'C', 'B', 'A', 'S', 'SS', 'BANNED']
drank = {'Industrial': [8, 6, 5, 5, 5, 1, 2],
         'Engineering': [6, 5, 3, 4, 2, 2, 2],
         'Patriotic': [5, 8, 4, 4, 4, 3, 3],
         'Mechanical': [6, 6, 4, 3, 4, 1, 1],
         'Agricultural': [5, 4, 4, 3, 2, 2, 3],
         'Militant': [7, 7, 5, 3, 4, 4, 3],
         'Innovative': [7, 7, 6, 5, 6, 4, 4]}

# default penalty and ban levels
dpen = 7
dban = 8
dfull = 0
vfact, vmat, vpen, vban, vfull, vjoin = {}, {}, {}, {}, {}, {}

thanks_notation = ['thanks', 'Thanks', 'thanx', 'Thanx', 'Thx', 'thx', 'thanq', ',Thanq', 'dank', 'Dank']
thanks_responses = ['You\'re welcome!', 'No problem!', 'Alsjeblieft', 'Graag gedaan', 'Your wish is my command',
                    'Het is dat je het zo lief vroeg', 'Heel fijn om eens bedankt te worden :)', 'Nee, jij bedankt!',
                    'Veel plezier!', 'Succes met gamen!', 'Zet \'m op!']
thanks_responded = {}

response_notation = ['lol', 'haha', 'damn', 'oh shit', 'wtf']
response_responses = ['Het is gewoon heel normaal om bedankt te worden.', 'Ik vind het fijn om bedankt te worden.',
                      'Wat had je dan verwacht?', 'Ik heb ook gevoelens ja',
                      '01101100 01100001 01100001 01110100 00100000 01101101 01100101 00100000 01101101 01100101 '
                      '01110100 00100000 01110010 01110101 01110011 01110100']


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
        rank.append(rank_names[rank_index[i] - 1])
        penalty_list.append(g_penalty * rank_index[i])
    penalty_offset = [pen - min(penalty_list) for pen in penalty_list]
    if (max(rank_index) >= banned_rank):
        message = await generate(g_players, g_penalty, banned_rank, g_full)
        return message
    for i in range(len(g_players)):
        message[i] = ('{}: {} {}; rank {} ({}); penalty {} points'.format(g_players[i], factions[i], mats[i], rank[i],
                                                                          rank_index[i], penalty_offset[i]))
    return message


async def levdist(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y
    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x, y] = min(matrix[x - 1, y] + 1, matrix[x - 1, y - 1], matrix[x, y - 1] + 1)
            else:
                matrix[x, y] = min(matrix[x - 1, y] + 1, matrix[x - 1, y - 1] + 1, matrix[x, y - 1] + 1)
    return (matrix[size_x - 1, size_y - 1])


@bot.command(name='join',
             help='Join the player list for the next game round. As is to add own name or pass (multiple) arguments for each player name.')
async def join(ctx, *args):
    global vjoin
    if (ctx.guild.id not in vjoin):
        vjoin[ctx.guild.id] = []
    if not args:
        vjoin[ctx.guild.id].append(ctx.author.name)
    elif (args[0] == '$c'):
        # voice_channel = discord.utils.get(ctx.guild.voice_channels, name="General")
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


@bot.command(name='list', help='Show current list of players joined.')
async def list(ctx):
    await ctx.send(vjoin[ctx.guild.id])
    return


@bot.command(name='start', help='Start generating based on the list of joined players')
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


@bot.command(name='js', help='Join+Start [optional options] [list of names]')
async def js(ctx, *args):
    userlist = []
    l_pen = vpen[ctx.guild.id] if ctx.guild.id in vpen else dpen
    l_ban = vban[ctx.guild.id] if ctx.guild.id in vban else dban
    l_full = vfull[ctx.guild.id] if ctx.guild.id in vfull else dfull
    if (not args) or (args[0] == '$c' and len(args) == 1):
        if ctx.author.voice and ctx.author.voice.channel:
            userlist = [user.name for user in ctx.author.voice.channel.members]
            if (len(userlist) >= 1):
                response = await generate(userlist, l_pen, l_ban, l_full)
            else:
                await ctx.send('No players found in voice chat')
                return
    elif (args[0] == '$c') and (len(args) > 1):
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
            if min(levdistlist) < 4:
                voice_channel = discord.utils.get(ctx.guild.voice_channels,
                                                  name=voice_list[levdistlist.index(min(levdistlist))])
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


@bot.command(name='jsf',
             help='Join+Start+Full [list of names]. Generate random faction/mat combo\'s based on base game and expansion')
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


@bot.command(name='jsa',
             help='Join+Start+Add-on Only [list of names]. Generate random faction/mat combo\'s based on base game and expansion')
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


@bot.command(name='pen', help='Set the penalty multiplier.')
async def pen(ctx, set_penalty: int):
    vpen[ctx.guild.id] = set_penalty
    await ctx.send('Penalty multiplier set to {}'.format(set_penalty))
    return


@bot.command(name='ban', help='Set the banned level')
async def ban(ctx, set_ban: int):
    vban[ctx.guild.id] = set_ban
    await ctx.send('Ban level set to {}'.format(set_ban))
    return


@bot.command(name='full', help='Set which factions/mats to use: 0=original, 1=full, 2=addon only')
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
    message = {'Factions': dfact_full, 'Mats': dmats_full, 'Ranks (ordered)': drank, 'Penalty': l_pen,
               'Banned level': l_ban, 'Full': l_full}
    await ctx.send(message)


@bot.command(name='reset', help='Resets servers specific saved parameters')
async def reset(ctx):
    del vpen[ctx.guild.id]
    del vban[ctx.guild.id]
    del vfull[ctx.guild.id]
    del vjoin[ctx.guild.id]
    return


@bot.command(name='spm', help='Test to send PM')
async def spm(ctx):
    await ctx.author.send('You send me a request for a PM')
    return


@bot.command(name='valheim', help='Retrieve Valheim IP address/port from dynamic DNS')
async def valheim(ctx):
    server = socket.gethostbyname(VALHEIM_HOST)
    await ctx.send(f'{server}:{VALHEIM_PORT}')
    return


@bot.command(name='proverb')
async def proverb(ctx):
    if not loop_proverb.get(ctx.guild.id, False):
        # if loop_proverb is false or non-existent, set to True
        loop_proverb[ctx.guild.id] = True

        # handle multiple instances by assigning individual ids
        if loop_proverb_id.get(ctx.guild.id, None) == None:
            loop_proverb_id[ctx.guild.id] = {}
        loop_id = len(loop_proverb_id[ctx.guild.id])  # id is the length of the instances
        loop_proverb_id[ctx.guild.id][loop_id] = True
        await ctx.send(f'Starting proverb loop_id {loop_id}')

        # actual loop
        while loop_proverb[ctx.guild.id] and loop_proverb_id[ctx.guild.id][loop_id]:
            if datetime.now().time() > datetime.strptime('08:00:00', '%H:%M:%S').time():
                if datetime.now().time() < datetime.strptime('09:30:00', '%H:%M:%S').time():
                    if (loop_proverb[ctx.guild.id]) & (loop_proverb_id[ctx.guild.id][loop_id]):
                        # send answer
                        _proverb, _meaning = use_proverb()
                        await ctx.send(_proverb)
                        await sleep(5 * 60 * 60)

                        if (loop_proverb[ctx.guild.id]) & (loop_proverb_id[ctx.guild.id][loop_id]):
                            await ctx.send(_meaning)
                            await sleep(19 * 60 * 60)
                else:
                    # same day but after time, postpone until next day:
                    await sleep((datetime(datetime.now().year, datetime.now().month, datetime.now().day + 1, 8, 0, 0) - datetime.now()).seconds)
            else:
                # same day but too early:
                await sleep(
                    (datetime(datetime.now().year, datetime.now().month, datetime.now().day, 8, 0,
                              0) - datetime.now()).seconds)
    return


@bot.command(name='stop.proverb')
async def stop_proverb(ctx, loop_id: int = None):
    # stopping one loop, will stop all loops, can be rewritten to only check for the individual loop
    if loop_proverb.get(ctx.guild.id, False):
        loop_proverb[ctx.guild.id] = False

        # if no loop_id is given, get loop_ids and find the first True value
        if loop_id is None:
            loop_ids = loop_proverb_id.get(ctx.guild.id, None)
            if loop_ids is not None:
                loop_the_ids = True
                while loop_the_ids:
                    for key, value in loop_ids.items():
                        if value:
                            loop_id = key
                            loop_the_ids = False
        if loop_proverb_id[ctx.guild.id].get(loop_id):
            loop_proverb_id[ctx.guild.id][loop_id] = False
            await ctx.send('Een gegeven paard moet je niet in de bek kijken')
        else:
            await ctx.send('Kon geen passende loop vinden om te stoppen')

    return

@bot.command(name='next.proverb')
async def next_proverb(ctx, wait_time: int = 300):
    proverb, meaning = use_proverb()
    await ctx.send(proverb)
    await sleep(wait_time)
    await ctx.send(meaning)
    return

@bot.command(name='hist.proverb')
async def proverb_history(ctx, num: int = 7):
    message = get_proverb_history(num)
    await ctx.send(message)
    return

@bot.command(name='num.proverb')
async def proverb_num(ctx):
    used, remaining, total = get_proverb_numericals()
    message = f"Proverbs: {used}/{total} ({round(used/total*100, 1)})% used. {remaining} remaining."
    await ctx.send(message)
    return

bot.run(TOKEN)
