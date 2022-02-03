# soundboard.py
"""
Python module for the discord ScytheBot to host the Soundboard cog / module
Through fate, luck and a dash of entropy, the SoundBoard module is often named SoundBard
"""

import os
import glob
import json
import discord
import pprint
from asyncio import sleep
from discord.ext import commands
from dotenv import load_dotenv
from discord import FFmpegPCMAudio, PCMVolumeTransformer


class SoundBoard(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the SoundBoard cog, loads environment variables
        :param bot: discord bot object, passed from the main file being executed
        """
        self.bot = bot

        load_dotenv()

        self.dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
        self.ADMINS = json.loads(os.getenv('ADMIN_DICT'))
        self.SUPER_ADMIN = os.getenv('SUPER_ADMIN')

        # load opus library manually for linux systems in which opus is not loaded by default or library needs to be
        # manually specified in the .env file
        self.LIBOPUS = os.getenv('LIBOPUS')
        if not discord.opus.is_loaded():
            if self.LIBOPUS:
                discord.opus.load_opus(self.LIBOPUS)
            else:
                discord.opus.load_opus()

        # load default datasets
        sb_files = sorted(glob.glob('./soundboard/data/d1mp3/*.mp3'))
        self.audio_dict = {i: f for i, f in enumerate(sb_files)}
        self.still_talking = False
        return

    @commands.command(name='sbp')
    async def play(self, ctx, *audio_fragment):
        """
        Play audio fragment by specifying the index of the audio file. Pass multiple integers to queue multiple fragments
        :param ctx: discord context
        :param audio_fragment: list of arguments passed in discord [str, ...] which will be converted to [int, ...]
        :return:
        """

        try:
            audio_fragment = [int(i) for i in audio_fragment]
        except:
            # non-integer values passed which we can't deal with so return without attempting anything
            return

        voice_channel = ctx.message.author.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None:
            voice_client = await voice_channel.connect()
        else:
            await voice_client.move_to(voice_channel)

        for frag in audio_fragment:
            source = FFmpegPCMAudio(self.audio_dict.get(frag, './soundboard/data/d1mp3/aah.mp3'))

            while self.still_talking:
                # prevent playing the next fragment until the toggle is switched
                await sleep(0.1)

            self.still_talking = True
            voice_client.play(source, after=self.talk_toggle)

        return

    def talk_toggle(self, unknown_var):
        """
        Toggles the flag to let ScytheBot that the next fragment can start playing
        :param unknown_var:
        :return:
        """
        self.still_talking = not self.still_talking
        return


    @commands.command(name='sbl')
    async def leave_voice(self, ctx):
        """
        Disconnect from voice channel
        :param ctx: discord context
        :return:
        """
        await discord.utils.get(self.bot.voice_clients, guild=ctx.guild).disconnect()
        return

    @commands.command(name='sbh')
    async def show_audio_dict(self, ctx, low: int, high: int):
        """
        Sends a private message to the sender with the current dictionary of index: audio filenames.
        Parts can be specified through upper and lower bound integers. If dictionary exceeds the characterlimit
        it will be split across multiple messages. Works both in guild and direct messages to ScytheBot.
        :param ctx: discord context
        :param low: lower bound of index
        :param high: upper bound of index
        :return:
        """
        msg = {i: os.path.split(f)[-1] for i, f in self.audio_dict.items() if i in range(low, high)}

        msg = pprint.pformat(msg, indent=4, width=50)
        if len(msg) > 2000:
            chunks = int((len(msg) / 2000) + 1)
            for i in range(chunks):
                await ctx.author.send(msg[i*2000:i*2000+2000])
        else:
            await ctx.author.send(msg)
        return
