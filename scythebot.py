# bot.py
import os
import glob
import json
import pickle as pkl
import random
import discord
import numpy as np
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from asyncio import sleep
from datetime import datetime, timedelta
import socket
from proverbs.proverbs import use_proverb, get_proverb_history, get_proverb_numericals, get_last_proverb

load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
TOKEN = os.getenv('DISCORD_TOKEN')
VALHEIM_HOST = os.getenv('VALHEIM_HOST')
VALHEIM_PORT = os.getenv('VALHEIM_PORT')
ADMINS = json.loads(os.getenv('ADMIN_DICT'))
EMOJIS = json.loads(os.getenv('EMOJIS'))
sourcelink = 'https://github.com/tadsz/scythebot/'
botversion = 'alpha010a'

### PROVERB SETTINGS
proverb_scores = {}
proverb_counts = {}
proverb_real = {}
proverb_fake = {}


proverb_prov_start = {} # prov_start is desired start time
proverb_prov_start['default'] = '08:00:00'
proverb_prov_end = {} # prov_end is the latest allowed to directly start
proverb_prov_end['default' ] = '13:00:00'
proverb_mean_start = {} # prov_mean is the timepoint to release the answer
proverb_mean_start['default'] = '13:00:00'


# load proverb_scores:
for guild in glob.glob('./proverbs/proverb_scores_*.pkl'):
    guild_id = int(guild.split('proverb_scores_')[-1].split('.pkl')[0])
    proverb_scores[guild_id] = pkl.load(open(f'./proverbs/proverb_scores_{guild_id}.pkl', 'rb'))
for guild in glob.glob('./proverbs/proverb_counts_*.pkl'):
    guild_id = int(guild.split('proverb_counts_')[-1].split('.pkl')[0])
    proverb_counts[guild_id] = pkl.load(open(f'./proverbs/proverb_counts_{guild_id}.pkl', 'rb'))

loop_proverb = {}
loop_proverb_id = {}
bot_emoji = "🤖"
emoji_real = EMOJIS.get('real', "🧑‍🏫")
emoji_fake = EMOJIS.get('fake', "🤖")

if dev_mode:
    emoji_real = "🧑‍🏫"
    emoji_fake = "🤖"

### SCYTHE SETTINGS
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

### VALHEIM
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

### DISCORD SETTINGS
intents = discord.Intents.default()
intents.members = True
discord.Permissions.add_reactions = True

if dev_mode:
    bot = commands.Bot(command_prefix='.', intents=intents)
else:
    bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Logged in as ScytheBot')
    print(f'ScytheBot {botversion} - {bot.user} - {bot.user.id}')
    print(f'dev_mode={dev_mode}')
    print('----------')
    return

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
async def proverb(ctx, cont_prov: bool = False):
    _admin = bot.get_user(ADMINS.get('Tadsz'))
    await _admin.send(f'Proverb command started by {ctx.author}')
    if dev_mode:
        print(f'Proverb command ran by {ctx.author}')
    if not loop_proverb.get(ctx.guild.id, False):
        # if loop_proverb is false or non-existent, set to True
        loop_proverb[ctx.guild.id] = True

        _use_generated = None

        # handle multiple instances by assigning individual ids
        if loop_proverb_id.get(ctx.guild.id, None) == None:
            loop_proverb_id[ctx.guild.id] = {}
        loop_id = len(loop_proverb_id[ctx.guild.id])  # id is the length of the instances
        loop_proverb_id[ctx.guild.id][loop_id] = True

        # acknowledge message
        await ctx.message.add_reaction(bot_emoji)

        # actual loop
        loop_counter = 0
        while loop_proverb[ctx.guild.id] and loop_proverb_id[ctx.guild.id][loop_id]:
            loop_counter += 1
            print(f'Running loop: {loop_counter}')
            await _admin.send(f'Running loop: {loop_counter}')
            _prov_start = proverb_prov_start.get(ctx.guild.id, proverb_prov_start['default'])
            if datetime.now().time() > datetime.strptime(_prov_start, '%H:%M:%S').time():
                print(f'Datetime after 08:00:00: {datetime.now()}')
                await _admin.send(f'Datetime after 08:00:00: {datetime.now()}')
                _prov_end = proverb_prov_end.get(ctx.guild.id, proverb_prov_end['default'])
                if datetime.now().time() < datetime.strptime(_prov_end, '%H:%M:%S').time():
                    print(f'Datetime before 13:00:00')
                    await _admin.send(f'Datetime before 13:00:00')
                    if (loop_proverb[ctx.guild.id]) & (loop_proverb_id[ctx.guild.id][loop_id]):

                        # check and initialize voting lists
                        if proverb_fake.get(ctx.guild.id, False) == False:
                            proverb_fake[ctx.guild.id] = []
                        if proverb_real.get(ctx.guild.id, False) == False:
                            proverb_real[ctx.guild.id] = []

                        if not cont_prov:
                            _use_generated = bool(random.getrandbits(1))
                            _proverb, _meaning = use_proverb(USE_GENERATED=_use_generated)
                        else:
                            _proverb, _meaning = get_last_proverb()
                            cont_prov = False

                        # send proverb
                        posted_message = await ctx.send(_proverb)
                        await add_vote_buttons(posted_message)

                        # wait until 13:00 server time to continue with the answer
                        sleep_time = (datetime(datetime.now().year, datetime.now().month, datetime.now().day, 13, 0, 0) - datetime.now()).seconds

                        sleep_time = (datetime.combine(datetime.now().date(),
                                                       datetime.strptime(proverb_mean_start.get(ctx.guild.id,
                                                                                                proverb_mean_start['default']),
                                                                         '%H:%M:%S').time()) - datetime.now()).seconds
                        await _admin.send(f'Proverb sent {datetime.now()} | {sleep_time} seconds')
                        if dev_mode:
                            print('proverb sent, sleeping for meaning')
                            print(sleep_time)
                            sleep_time = 5
                        await sleep(sleep_time)

                        # check if loop has not been canceled, then send the meaning
                        if (loop_proverb[ctx.guild.id]) & (loop_proverb_id[ctx.guild.id][loop_id]):
                            await get_votes_from_buttons(ctx, posted_message)
                            await posted_message.reply(_meaning, mention_author=False)

                            if proverb_scores.get(ctx.guild.id, False) == False:
                                # create score list
                                print('Creating score and count dicts')
                                proverb_scores[ctx.guild.id] = {}
                                proverb_counts[ctx.guild.id] = {}

                            await process_scores(ctx, _use_generated)

                            # wait until 08:00 server time the next day to continue with the next iteration
                            sleep_time = (datetime.combine(datetime.now().date() + timedelta(days=1),
                                                           datetime.strptime(proverb_prov_start.get(ctx.guild.id,
                                                                                                    proverb_prov_start['default']),
                                                                             '%H:%M:%S').time()) - datetime.now()).seconds

                            await _admin.send(f'Meaning sent {datetime.now()}, waiting for next day | {sleep_time} seconds')
                            if dev_mode:
                                print('meaning sent, now sleeping for next loop')
                                print(sleep_time)
                                sleep_time = 10
                            await sleep(sleep_time)
                            print('meaning sleep time ended')
                else:
                    # same day but after time, postpone until next day:
                    print('loop started too late; waiting until next day')
                    sleep_time = (datetime.combine(datetime.now().date() + timedelta(days=1),
                                                   datetime.strptime(proverb_prov_start.get(ctx.guild.id,
                                                                                            proverb_prov_start[
                                                                                                'default']),
                                                                     '%H:%M:%S').time()) - datetime.now()).seconds
                    await _admin.send(f'Loop started after end time {datetime.now()}; waiting next day | {sleep_time} seconds')
                    if dev_mode:
                        print('loop started after end time')
                        print(sleep_time)
                        sleep_time = 10
                    await sleep(sleep_time)
            else:
                # same day but too early:
                sleep_time = (datetime.combine(datetime.now().date(),
                                               datetime.strptime(proverb_prov_start.get(ctx.guild.id,
                                                                                        proverb_prov_start['default']),
                                                                 '%H:%M:%S').time()) - datetime.now()).seconds
                await _admin.send(f'Same day but too early: {datetime.now()} | sleeping {sleep_time} seconds')
                if dev_mode:
                    print('same day too early')
                    print(sleep_time)
                    sleep_time = 10
                await sleep(sleep_time)
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
    proverb, meaning = use_proverb(USE_GENERATED=False)
    await ctx.send(proverb)
    await sleep(wait_time)
    await ctx.send(meaning)
    return

@bot.command(name='next.generated.proverb')
async def next_gen_proverb(ctx, wait_time: int = 300):
    proverb, meaning = use_proverb(USE_GENERATED=True)
    await ctx.send(proverb)
    await sleep(wait_time)
    await ctx.send(meaning)
    return

@bot.command(name='next.random.proverb', aliases=['nrp'])
async def next_random_proverb(ctx, p: float = 0.50, wait_time: int = 300):
    if p < 0:
        p = 0.50
    if p > 1:
        p = 0.50

    _use_generated = np.random.rand() > p

    proverb, meaning = use_proverb(USE_GENERATED=_use_generated)

    await ctx.send(proverb)

    await sleep(wait_time)

    await ctx.send(meaning)

    await process_scores(ctx, _use_generated)

    return

async def process_scores(ctx, _use_generated):
    print('processing scores')
    if proverb_scores.get(ctx.guild.id, False) == False:
        print('creating scores and counts dicts')
        proverb_scores[ctx.guild.id] = {}
        proverb_counts[ctx.guild.id] = {}

    if _use_generated is not None:
        # verify if all users who voted are in the score list
        users_to_add = [userid for userid in proverb_fake[ctx.guild.id] + proverb_real[ctx.guild.id] if
                        userid not in proverb_scores[ctx.guild.id].keys()]
        for userid in users_to_add:
            proverb_scores[ctx.guild.id][userid] = 0
            proverb_counts[ctx.guild.id][userid] = 0

        # process votes
        if _use_generated:
            # add points to bot voters
            for userid in proverb_fake[ctx.guild.id]:
                proverb_scores[ctx.guild.id][userid] += 1
                proverb_counts[ctx.guild.id][userid] += 1
            for userid in proverb_real[ctx.guild.id]:
                proverb_counts[ctx.guild.id][userid] += 1

        elif not _use_generated:
            # add points to real voters
            users_to_add = [userid for userid in proverb_real[ctx.guild.id] if
                            userid not in proverb_scores[ctx.guild.id].keys()]
            for userid in users_to_add:
                proverb_scores[ctx.guild.id][userid] = 0
                proverb_counts[ctx.guild.id][userid] = 0
            # add points to real voters
            for userid in proverb_real[ctx.guild.id]:
                proverb_scores[ctx.guild.id][userid] += 1
                proverb_counts[ctx.guild.id][userid] += 1
            for userid in proverb_fake[ctx.guild.id]:
                proverb_counts[ctx.guild.id][userid] += 1

        # empty list of current votes
        proverb_real[ctx.guild.id] = []
        proverb_fake[ctx.guild.id] = []

        # return a list of scores
        await show_proverb_scores(ctx, 'avg')
        await save_proverb_scores(ctx)
    return


async def save_proverb_scores(ctx):
    pkl.dump(proverb_scores[ctx.guild.id],
             open(f'./proverbs/proverb_scores_{ctx.guild.id}.pkl', 'wb'))
    pkl.dump(proverb_counts[ctx.guild.id],
             open(f'./proverbs/proverb_counts_{ctx.guild.id}.pkl', 'wb'))
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

@bot.command(name='cont.proverb')
async def proverb_continue(ctx):
    await proverb(ctx, cont_prov=True)
    return


@bot.command(name='scores.proverb')
async def show_proverb_scores(ctx, metric: str = 'sum'):
    if proverb_scores.get(ctx.guild.id, False) == False:
        proverb_scores[ctx.guild.id] = {}

    # return a list of scores
    _message = 'Score list: \n'
    if metric == 'sum':
        for _id, score in proverb_scores[ctx.guild.id].items():
            _message += f'{bot.get_user(_id).name}: {score}\n'
    elif (metric == 'avg') or (metric == 'mean'):
        for _id, score in proverb_scores[ctx.guild.id].items():
            _message += f'{bot.get_user(_id).name}: {score}/{proverb_counts[ctx.guild.id][_id]} ({round(score / proverb_counts[ctx.guild.id][_id] * 100, 1)}%)'
    await ctx.send(_message)
    return


async def add_vote_buttons(posted_message):
    await posted_message.add_reaction(emoji_real)
    await posted_message.add_reaction(emoji_fake)
    return

async def get_votes_from_buttons(ctx, posted_message):
    posted_message = await ctx.channel.fetch_message(posted_message.id)
    users_real = None
    users_fake = None

    for reaction in posted_message.reactions:
        if str(reaction.emoji) == emoji_fake:
            users_fake = await reaction.users().flatten()
        elif str(reaction.emoji) == emoji_real:
            users_real = await reaction.users().flatten()

    proverb_fake[ctx.guild.id] = []
    if users_fake is not None:
        for user in users_fake:
            if user.id != bot.user.id:
                proverb_fake[ctx.guild.id].append(user.id)

    proverb_real[ctx.guild.id] = []
    if users_real is not None:
        for user in users_real:
            if user.id != bot.user.id:
                proverb_real[ctx.guild.id].append(user.id)

    # remove id from both lists if they are duplicates to prevent double votes
    _fake_voters = proverb_fake[ctx.guild.id].copy()
    _real_voters = proverb_real[ctx.guild.id].copy()

    proverb_fake[ctx.guild.id] = [userid for userid in proverb_fake[ctx.guild.id] if userid not in _real_voters]
    proverb_real[ctx.guild.id] = [userid for userid in proverb_real[ctx.guild.id] if userid not in _fake_voters]
    return

@bot.command(name='alter.scores')
async def alter_scores(ctx, user: discord.User, score):
    if ctx.author.id not in ADMINS.values():
        return

    if proverb_scores.get(ctx.guild.id, False) == False:
        proverb_scores[ctx.guild.id] = {}
        proverb_counts[ctx.guild.id] = {}

    if proverb_scores[ctx.guild.id].get(user.id, False) == False:
        proverb_scores[ctx.guild.id][user.id] = 0
        proverb_counts[ctx.guild.id][user.id] = 0

    if isinstance(score, int):
        proverb_scores[ctx.guild.id][user.id] = score
    elif isinstance(score, str):
        if score[0] == '+':
            try:
                add_score = int(score[1:])
                proverb_scores[ctx.guild.id][user.id] += add_score
            except:
                await ctx.send('Score not understood')
                return
        elif score[0] == '-':
            try:
                subtract_score = int(score[1:])
                proverb_scores[ctx.guild.id][user.id] -= subtract_score
            except:
                await ctx.send('Score not understood')
                return
        elif (score[0] == 'x') or (score[0] == '*'):
            try:
                mult_score = int(score[1:])
                proverb_scores[ctx.guild.id][user.id] *= mult_score
            except:
                await ctx.send('Score not understood')
                return
        elif (score[0] == '/') or (score[0] == ':'):
            try:
                div_score = int(score[1:])
                proverb_scores[ctx.guild.id][user.id] /= div_score
            except:
                await ctx.send('Score not understood')
                return

    await save_proverb_scores(ctx)
    await show_proverb_scores(ctx)
    return

@bot.command(name='alter.counts')
async def alter_counts(ctx, user: discord.User, count):
    if ctx.author.id not in ADMINS.values():
        return

    if proverb_scores.get(ctx.guild.id, False) == False:
        proverb_scores[ctx.guild.id] = {}
        proverb_counts[ctx.guild.id] = {}

    if proverb_scores[ctx.guild.id].get(user.id, False) == False:
        proverb_scores[ctx.guild.id][user.id] = 0
        proverb_counts[ctx.guild.id][user.id] = 0

    if isinstance(count, int):
        proverb_counts[ctx.guild.id][user.id] = count
    elif isinstance(count, str):
        if count[0] == '+':
            try:
                add_score = int(count[1:])
                proverb_counts[ctx.guild.id][user.id] += add_score
            except:
                await ctx.send('Score not understood')
                return
        elif count[0] == '-':
            try:
                subtract_score = int(count[1:])
                proverb_counts[ctx.guild.id][user.id] -= subtract_score
            except:
                await ctx.send('Score not understood')
                return
        elif (count[0] == 'x') or (count[0] == '*'):
            try:
                mult_score = int(count[1:])
                proverb_counts[ctx.guild.id][user.id] *= mult_score
            except:
                await ctx.send('Score not understood')
                return
        elif (count[0] == '/') or (count[0] == ':'):
            try:
                div_score = int(count[1:])
                proverb_counts[ctx.guild.id][user.id] /= div_score
            except:
                await ctx.send('Score not understood')
                return

    await save_proverb_scores(ctx)
    await show_proverb_scores(ctx)

    return

bot.run(TOKEN)
