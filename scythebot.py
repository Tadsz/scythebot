# bot.py
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import socket
from proverbs.proverbs import Proverbs
from scythe.scythe import Scythe

load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
TOKEN = os.getenv('DISCORD_TOKEN')
VALHEIM_HOST = os.getenv('VALHEIM_HOST')
VALHEIM_PORT = os.getenv('VALHEIM_PORT')
sourcelink = 'https://github.com/tadsz/scythebot/'
botversion = 'alpha011a'


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

bot.add_cog(Scythe(bot))
bot.add_cog(Proverbs(bot))

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


@commands.command(name='v', help='Get current version')
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


bot.run(TOKEN)
