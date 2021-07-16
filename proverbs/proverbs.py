# proverbs.py
"""
Python module for the discord ScytheBot to host the Proverbs cog / module
"""

import os
import glob
import json
import pickle as pkl
import random
import discord
import numpy as np
from discord.ext import commands
from dotenv import load_dotenv
from asyncio import sleep
from datetime import datetime, timedelta, time
import pandas as pd

# PROVERB SETTINGS
load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
ADMINS = json.loads(os.getenv('ADMIN_DICT'))
EMOJIS = json.loads(os.getenv('EMOJIS'))


proverb_scores = {}
proverb_counts = {}
proverb_real = {}
proverb_fake = {}


# load proverb_scores:
for guild in glob.glob('./proverbs/proverb_scores_*.pkl'):
    guild_id = int(guild.split('proverb_scores_')[-1].split('.pkl')[0])
    proverb_scores[guild_id] = pkl.load(open(f'./proverbs/proverb_scores_{guild_id}.pkl', 'rb'))
for guild in glob.glob('./proverbs/proverb_counts_*.pkl'):
    guild_id = int(guild.split('proverb_counts_')[-1].split('.pkl')[0])
    proverb_counts[guild_id] = pkl.load(open(f'./proverbs/proverb_counts_{guild_id}.pkl', 'rb'))


proverb_prov_start = {} # prov_start is desired start time
proverb_prov_start['default'] = '08:00:00'
proverb_prov_end = {} # prov_end is the latest allowed to directly start
proverb_prov_end['default' ] = '13:00:00'
proverb_mean_start = {} # prov_mean is the time point to release the answer
proverb_mean_start['default'] = '13:00:00'


loop_proverb = {}
loop_proverb_id = {}


bot_emoji = "🤖"
emoji_real = EMOJIS.get('real', "🧑‍🏫")
emoji_fake = EMOJIS.get('fake', "🤖")
if dev_mode:
    emoji_real = "🧑‍🏫"
    emoji_fake = "🤖"


class Proverbs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def read_proverb(self, USE_GENERATED: bool = False):
        if USE_GENERATED:
            proverb_file = './proverbs/generated_proverbs.csv'
        else:
            proverb_file = './proverbs/sayings.csv'
        data = pd.read_csv(proverb_file)
        index = data.loc[data['used'].isna()]['index'].iloc[0]
        mask = data['index'] == index
        proverb = data.loc[mask]['proverb'].iloc[0]
        if USE_GENERATED:
            meaning = 'This was a generated proverb'
        else:
            meaning = data.loc[mask]['meaning'].iloc[0]
        data.loc[data['index'] == index, 'used'] = datetime.now()
        data.to_csv(proverb_file, index=False)
        return proverb, meaning

    async def get_proverb_history(self, num: int = 7):
        data = pd.read_csv('sayings.csv')
        selection = data.loc[data['used'].notna()].sort_values('used', ascending=False)[['proverb', 'meaning']].head(
            num + 1)
        if time(8, 0) <= datetime.now().time() <= time(13, 0):
            selection = selection[1:]
        else:
            selection = selection[:-1]
        message = ''
        for proverb, meaning in zip(selection['proverb'], selection['meaning']):
            message += f"{proverb} || {meaning} ||\n"
        return message

    async def get_proverb_numericals(self):
        data = pd.read_csv('sayings.csv')
        used = data['used'].notna().sum()
        total = len(data)
        remaining = total - used
        return used, remaining, total

    async def get_last_proverb(self):
        data = pd.read_csv('sayings.csv')
        selection = data.sort_values('used', ascending=False).head()
        proverb = selection['proverb'].iloc[0]
        meaning = selection['meaning'].iloc[0]
        return proverb, meaning

    @commands.command(name='prov.start')
    async def proverb(self, ctx, cont_prov: bool = False) -> None:
        """
        Start the daily proverb loop
        :param ctx: context
        :param cont_prov: boolean for continuation of previous proverb
        :return: None
        """
        _admin = self.bot.get_user(ADMINS.get('Tadsz'))
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
                                _proverb, _meaning = self.read_proverb(USE_GENERATED=_use_generated)
                            else:
                                # only works on the last real proverb;
                                # TODO: add last proverb to persistent variable instead of re-reading
                                _proverb, _meaning = self.get_last_proverb()
                                cont_prov = False

                            # send proverb
                            posted_message = await ctx.send(_proverb)
                            await self.add_vote_buttons(posted_message)

                            # wait until 13:00 server time to continue with the answer
                            sleep_time = (datetime(datetime.now().year, datetime.now().month, datetime.now().day, 13, 0,
                                                   0) - datetime.now()).seconds

                            sleep_time = (datetime.combine(datetime.now().date(),
                                                           datetime.strptime(proverb_mean_start.get(ctx.guild.id,
                                                                                                    proverb_mean_start[
                                                                                                        'default']),
                                                                             '%H:%M:%S').time()) - datetime.now()).seconds
                            await _admin.send(f'Proverb sent {datetime.now()} | {sleep_time} seconds')
                            if dev_mode:
                                print('proverb sent, sleeping for meaning')
                                print(sleep_time)
                                sleep_time = 5
                            await sleep(sleep_time)

                            # check if loop has not been canceled, then send the meaning
                            if (loop_proverb[ctx.guild.id]) & (loop_proverb_id[ctx.guild.id][loop_id]):
                                await self.get_votes_from_buttons(ctx, posted_message)
                                await posted_message.reply(_meaning, mention_author=False)

                                if proverb_scores.get(ctx.guild.id, False) == False:
                                    # create score list
                                    print('Creating score and count dicts')
                                    proverb_scores[ctx.guild.id] = {}
                                    proverb_counts[ctx.guild.id] = {}

                                await self.process_scores(ctx, _use_generated)

                                # wait until 08:00 server time the next day to continue with the next iteration
                                sleep_time = (datetime.combine(datetime.now().date() + timedelta(days=1),
                                                               datetime.strptime(proverb_prov_start.get(ctx.guild.id,
                                                                                                        proverb_prov_start[
                                                                                                            'default']),
                                                                                 '%H:%M:%S').time()) - datetime.now()).seconds

                                await _admin.send(
                                    f'Meaning sent {datetime.now()}, waiting for next day | {sleep_time} seconds')
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
                        await _admin.send(
                            f'Loop started after end time {datetime.now()}; waiting next day | {sleep_time} seconds')
                        if dev_mode:
                            print('loop started after end time')
                            print(sleep_time)
                            sleep_time = 10
                        await sleep(sleep_time)
                else:
                    # same day but too early:
                    sleep_time = (datetime.combine(datetime.now().date(),
                                                   datetime.strptime(proverb_prov_start.get(ctx.guild.id,
                                                                                            proverb_prov_start[
                                                                                                'default']),
                                                                     '%H:%M:%S').time()) - datetime.now()).seconds
                    await _admin.send(f'Same day but too early: {datetime.now()} | sleeping {sleep_time} seconds')
                    if dev_mode:
                        print('same day too early')
                        print(sleep_time)
                        sleep_time = 10
                    await sleep(sleep_time)
        return

    @commands.command(name='prov.stop')
    async def stop_proverb(self, ctx, loop_id: int = None) -> None:
        """
        Stop the proverb loop
        :param ctx: context
        :param loop_id: specific loop id to stop in case of multiple loops
        :return: None
        """
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

    @commands.command(name='prov.next')
    async def next_proverb(self, ctx, wait_time: int = 300) -> None:
        """
        Manually get one real proverb in 300 seconds or specify seconds
        :param ctx: context
        :param wait_time: integer of the number of seconds to wait before sending the meaning
        :return: None
        """
        proverb, meaning = self.read_proverb(USE_GENERATED=False)
        _posted_message = await ctx.send(proverb)
        await sleep(wait_time)
        await _posted_message.reply(meaning)
        return

    @commands.command(name='prov.next.gen')
    async def next_gen_proverb(self, ctx, wait_time: int = 300) -> None:
        """
        Manually get a generated proverb in the specified number of seconds (default: 300)
        :param ctx: context
        :param wait_time: integer of number of seconds to wait before releasing the meaning
        :return:
        """
        proverb, meaning = self.read_proverb(USE_GENERATED=True)
        await ctx.send(proverb)
        await sleep(wait_time)
        await ctx.send(meaning)
        return

    @commands.command(name='prov.next.random', aliases=['nrp', 'pnr'])
    async def next_random_proverb(self, ctx, p: float = 0.50, wait_time: int = 300) -> None:
        """
        Manually get next proverb, randomized for real or generated, with probability p (default: 0.50) and
        time until result in seconds (default: 300)
        :param ctx: context
        :param p: probability of generated proverb
        :param wait_time: number of seconds to wait until result
        :return:
        """
        if p < 0:
            p = 0.50
        if p > 1:
            p = 0.50

        _use_generated = np.random.rand() > p

        proverb, meaning = self.read_proverb(USE_GENERATED=_use_generated)

        _posted_message = await ctx.send(proverb)
        await self.add_vote_buttons(_posted_message)

        await sleep(wait_time)

        await _posted_message.reply(meaning)

        await self.process_scores(ctx, _use_generated)

        return

    async def process_scores(self, ctx, _use_generated) -> None:
        """
        Processes the scores based on the member ids registered for each vote, adds and saves
        :param ctx: context
        :param _use_generated: boolean for which vote gets points awarded
        :return: None
        """
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
            await self.show_proverb_scores(ctx, 'avg')
            await self.save_proverb_scores(ctx)
        return

    async def save_proverb_scores(self, ctx) -> None:
        """
        Saves the persistent variables to survive reboots
        :param ctx: context
        :return:
        """
        pkl.dump(proverb_scores[ctx.guild.id],
                 open(f'./proverbs/proverb_scores_{ctx.guild.id}.pkl', 'wb'))
        pkl.dump(proverb_counts[ctx.guild.id],
                 open(f'./proverbs/proverb_counts_{ctx.guild.id}.pkl', 'wb'))
        return

    async def save_variable(self, ctx, variable, file_prefix: str = 'proverb') -> None:
        """
        Saves the passed variable to the passed file_prefix in such a way that it can be reloaded with the load_variable
        function
        :param ctx: context for keeping track of guilds
        :param variable: global variable to pass
        :param file_prefix: file name prefix to save to
        :return: None
        """
        pkl.dump(variable[ctx.guild.id],
                 open(f'./proverbs/{file_prefix}_{ctx.guild.id}.pkl', 'wb'))
        return

    async def load_variable(self, file_prefix) -> object:
        """
        Loads variables from disk for each guild that was once active
        :param file_prefix: file name prefix to load from
        :return: loaded object
        """
        variables_to_load = glob.glob(f'./proverbs/{file_prefix}_*.pkl')
        loaded_variables = {}
        for current_variable in variables_to_load:
            guild_id = current_variable.split(f'{file_prefix}_')[-1].split('.pkl')[0]
            loaded_variables[guild_id] = pkl.load(open(current_variable, 'rb'))
        return loaded_variables

    @commands.command(name='prov.history', aliases=['hist.proverb'])
    async def proverb_history(self, ctx, num: int = 7) -> None:
        """
        Show the last x used real proverbs with meanings censored
        :param ctx: context
        :param num: number of proverbs to show
        :return: None
        """
        message = self.get_proverb_history(num)
        await ctx.send(message)
        return

    @commands.command(name='prov.num', aliases=['num.proverb'])
    async def proverb_num(self, ctx) -> None:
        """
        Show the number of used and remaining real proverbs
        :param ctx:
        :return:
        """
        used, remaining, total = self.get_proverb_numericals()
        message = f"Proverbs: {used}/{total} ({round(used / total * 100, 1)})% used. {remaining} remaining."
        await ctx.send(message)
        return

    @commands.command(name='prov.cont', aliases=['cont.proverb'])
    async def proverb_continue(self, ctx) -> None:
        """
        Continues from the last used proverb - identical to prov.start True
        :param ctx: context
        :return:
        """
        await self.proverb(ctx, cont_prov=True)
        return

    @commands.command(name='prov.scores', aliases=['scores.proverb'])
    async def show_proverb_scores(self, ctx, metric: str = 'sum') -> None:
        """
        Show current leaderbord (default: sum)
        :param ctx: context
        :param metric: (sum|avg)
        :return: None
        """
        if proverb_scores.get(ctx.guild.id, False) == False:
            proverb_scores[ctx.guild.id] = {}

        # return a list of scores
        _message = 'Score list: \n'
        if metric == 'sum':
            for _id, score in proverb_scores[ctx.guild.id].items():
                _message += f'{self.bot.get_user(_id).name}: {score}\n'
        elif (metric == 'avg') or (metric == 'mean'):
            for _id, score in proverb_scores[ctx.guild.id].items():
                _message += f'{self.bot.get_user(_id).name}: {score}/{proverb_counts[ctx.guild.id][_id]} ({round(score / proverb_counts[ctx.guild.id][_id] * 100, 1)}%)\n'
        await ctx.send(_message)
        return

    async def add_vote_buttons(self, posted_message) -> None:
        """
        Adds vote buttons to the passed message using the global emoji_real and emoji_fake variables
        :param posted_message: Discord message object
        :return: None
        """
        await posted_message.add_reaction(emoji_real)
        await posted_message.add_reaction(emoji_fake)
        return

    async def get_votes_from_buttons(self, ctx, posted_message) -> None:
        """
        Get votes from the reactions to the passed message
        :param ctx: context
        :param posted_message: message to read posted message from
        :return: None
        """
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
                if user.id != self.bot.user.id:
                    proverb_fake[ctx.guild.id].append(user.id)

        proverb_real[ctx.guild.id] = []
        if users_real is not None:
            for user in users_real:
                if user.id != self.bot.user.id:
                    proverb_real[ctx.guild.id].append(user.id)

        # remove id from both lists if they are duplicates to prevent double votes
        _fake_voters = proverb_fake[ctx.guild.id].copy()
        _real_voters = proverb_real[ctx.guild.id].copy()

        proverb_fake[ctx.guild.id] = [userid for userid in proverb_fake[ctx.guild.id] if userid not in _real_voters]
        proverb_real[ctx.guild.id] = [userid for userid in proverb_real[ctx.guild.id] if userid not in _fake_voters]
        return

    @commands.command(name='prov.alter.scores', aliases=['alter.scores'])
    async def alter_scores(self, ctx, user: discord.User, score) -> None:
        """
        Admin-only: alter scores in memory of the passed string discord names (as shown in score list)
        :param ctx: context
        :param user: discord username (not user object, id or mention!)
        :param score: int for new score or str for desired operation (add/sub/div/mult)
        :return: None
        """
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

        await self.save_proverb_scores(ctx)
        await self.show_proverb_scores(ctx)
        return

    @commands.command(name='prov.alter.counts', aliases=['alter.counts'])
    async def alter_counts(self, ctx, user: discord.User, count) -> None:
        """
        Admin-only: alter counts in memory of the passed string discord names (as shown in score list)
        :param ctx: context
        :param user: discord username (not user object, id or mention!)
        :param count: int for new score or str for desired operation (add/sub/div/mult)
        :return: None
        """
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

        await self.save_proverb_scores(ctx)
        await self.show_proverb_scores(ctx)

        return