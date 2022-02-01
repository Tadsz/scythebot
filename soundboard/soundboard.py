# soundboard.py
"""
Python module for the discord ScytheBot to host the Soundboard cog / module
"""

import os
import glob
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord import FFmpegPCMAudio, PCMVolumeTransformer

class SoundBoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        load_dotenv()

        self.dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
        self.ADMINS = json.loads(os.getenv('ADMIN_DICT'))
        self.SUPER_ADMIN = os.getenv('SUPER_ADMIN')

        # load default datasets
        sb_files = glob.glob('./soundboard/data/d1mp3/*.mp3')
        self.audio_dict = {i: f for i, f in enumerate(sb_files)}

        return

    @commands.command(name='sbp')
    async def play(self, ctx, audio_fragment: int):

        voice_channel = ctx.message.author.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None:
            voice_client = await voice_channel.connect()
        else:
            await voice_client.move_to(voice_channel)

        source = FFmpegPCMAudio(self.audio_dict.get(audio_fragment, './soundboard/data/d1mp3/aah.mp3'))

        voice_client.play(source)

        return

    @commands.command(name='sbl')
    async def leave_voice(self, ctx):
        discord.utils.get(self.bot.voice_clients, guild=ctx.guild).disconnect()
        return

    @commands.command(name='sbh')
    async def show_audio_dict(self, ctx, low: int, high: int):
        msg = {i: f.split('\\')[-1] for i, f in self.audio_dict.items() if i in range(low, high)}
        await ctx.author.send(msg)
        return
