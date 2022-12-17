# bot.py
import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import socket
from proverbs.proverbs import Proverbs
from scythe.scythe import Scythe
from soundboard.soundboard import SoundBoard
from utils.utils import Utils
from gpt3.gpt3 import OpenAI
import datetime as dt
from datetime import datetime


load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
ADMINS = json.loads(os.getenv('ADMIN_DICT'))
TOKEN = os.getenv('DISCORD_TOKEN')
VALHEIM_HOST = os.getenv('VALHEIM_HOST')
VALHEIM_PORT = os.getenv('VALHEIM_PORT')
sourcelink = 'https://github.com/tadsz/scythebot/'
botversion = '0.0.3'


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

### MEME SETTINGS
response_meme = {}
last_schijtbot = datetime.now() - dt.timedelta(hours=2)
emojis_list = ['😊', '😁', '😛', '🤓', '👻', '🤖', '💩', '🦾', '🕵️', '🦄']
print(f'last_schijtbot: {last_schijtbot}')

### DISCORD SETTINGS
intents = discord.Intents.default()
intents.members = True
discord.Permissions.add_reactions = True
intents.messages = True

if dev_mode:
    bot = commands.Bot(command_prefix='.', intents=intents)
else:
    bot = commands.Bot(command_prefix='!', intents=intents)

bot.add_cog(Scythe(bot))
bot.add_cog(Proverbs(bot))
bot.add_cog(Utils(bot))
bot.add_cog(OpenAI(bot))

@bot.event
async def on_ready():
    print('Logged in as ScytheBot')
    print(f'ScytheBot {botversion} - {bot.user} - {bot.user.id}')
    print(f'dev_mode={dev_mode}')
    print('----------')
    return


@bot.event
async def on_message(message):
    global last_schijtbot
    if message.author.bot:  # len(message.content) > 100 or message.author.bot:
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

    if any(x in message.content for x in ['scythebot', 'Scythebot', 'ScytheBot']):
        ctx = await bot.get_context(message)
        await ctx.message.add_reaction(random.choice(emojis_list))


    if any(x in message.content for x in ['schijtbot']):
        ctx = await bot.get_context(message)
        await ctx.message.add_reaction('😇')
        last_schijtbot = datetime.now()
        print(f'last_schijtbot: {last_schijtbot}')

    if any(x in message.content for x in [x[0] for y in response_meme.values() for x in y]):
        if (datetime.now() - last_schijtbot) < dt.timedelta(hours=1):
            return
        ctx = await bot.get_context(message)
        if ctx.author.id in response_meme.keys():
            if any(x in message.content for x in [x[0] for y in response_meme[ctx.author.id] for x in y]):
                return_message = message.content
                for replacement in response_meme[ctx.author.id]:
                    return_message = return_message.replace(replacement[0], replacement[1])
                return_message = "_More like:_\n" + return_message

                await ctx.message.reply(return_message)
    await bot.process_commands(message)
    return

@bot.command(name='sb', help='Start the soundbard')
async def start_soundboard(ctx, command_type: str = None):
    if command_type == 'reload':
        try:
            bot.remove_cog('SoundBoard')
            bot.add_cog(SoundBoard(bot))
        except:
            pass
    else:
        bot.add_cog(SoundBoard(bot))
    return

@bot.command(name='v', help='Get current version')
async def version(ctx):
    await ctx.send('Current version {}. Source code available at {}'.format(botversion, sourcelink))
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

@commands.command(name='replace', help='Replaces user text')
async def set_replacement(ctx, userid, source, target):
    try:
        userid = int(userid)
    except:
        return

    if response_meme.get(userid, None) == None:
        response_meme[userid] = []
    if tuple([source, target]) not in response_meme[userid]:
        response_meme[userid] += [tuple([source, target])]

    print(response_meme)
    return

@commands.command(name='replace.clear', help='Replaces user text')
async def clear_replacement(ctx, userid, source=None, target=None):
    try:
        userid = int(userid)
    except:
        return
    if response_meme.get(userid, None) == None:
        response_meme[userid] = []
    if source == None:
        response_meme[userid] = []
    return

bot.run(TOKEN)
