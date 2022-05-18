# utils.py
"""
Python module for the discord ScytheBot to host the Proverbs cog / module
"""

import os
import json
import random
import numpy as np
from datetime import datetime
import pandas as pd

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
ADMINS = json.loads(os.getenv('ADMIN_DICT'))


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='gpm')
    async def send_guild_message(self, ctx, channel_id, *args):
        if ctx.author.id not in ADMINS.values():
            return

        if isinstance(int(channel_id), int):
            channel_id = int(channel_id)
            channel = self.bot.get_channel(channel_id)
            message = ''
            for word in args:
                message += word + ' '
            message = message[:-1]
            await channel.send(message)
        return

    @commands.command(name='rtm')
    async def react_to_message(self, ctx, channel_id, message_id, emoji):
        if ctx.author.id not in ADMINS.values():
            return

        channel_id = int(channel_id)
        message_id = int(message_id)
        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        await message.add_reaction(emoji)
        return

    @commands.command(name='qtm')
    async def quote_to_message(self, ctx, channel_id, message_id, *args):
        if ctx.author.id not in ADMINS.values():
            return

        channel_id = int(channel_id)
        message_id = int(message_id)
        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        text_to_send = ''
        for word in args:
            text_to_send += word + ' '
        text_to_send = text_to_send[:-1]
        await message.reply(text_to_send)
        return


    @commands.command(name='remove.message', aliases=['rmbi'], help='Remove message by channel id and message id')
    async def remove_message_by_id(self, ctx, channel_id, message_id):
        if ctx.author.id not in ADMINS.values():
            return
        try:
            channel_id = int(channel_id)
            message_id = int(message_id)
        except:
            ctx.send('Error in converting channel and/or message ids')
            return

        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.delete()

        await ctx.send('Message deleted', delete_after=5)
        return

    @commands.command(name='name')
    async def name(self, ctx, option):
        if option == 'username':
            await ctx.message.reply(ctx.author.name)
        elif option == 'nickname':
            await ctx.message.reply(ctx.author.display_name)
        return
