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


class Proverbs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        load_dotenv()
        self.dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
        self.ADMINS = json.loads(os.getenv('ADMIN_DICT'))
        self.EMOJIS = json.loads(os.getenv('EMOJIS'))
        self.bot_emoji = "🤖"
        self.emoji_real = self.EMOJIS.get('real', "🧑‍🏫")
        self.emoji_fake = self.EMOJIS.get('fake', "🤖")
        if self.dev_mode:
            self.emoji_real = "🧑‍🏫"
            self.emoji_fake = "🤖"

        self.proverb_prov_start = {'default': '08:00:00'}  # prov_start is desired start time
        self.proverb_prov_end = {'default': '13:00:00'}  # prov_end is the latest allowed to directly start
        self.proverb_mean_start = {'default': '13:00:00'}  # prov_mean is the time point to release the answer

        self.proverb_real = {}
        self.proverb_fake = {}

        self.loop_proverb = {}
        self.loop_proverb_id = {}

        # TODO: place scores/variables in self
        self.proverb_score = {}

        if len(glob.glob('./proverbs/proverb_scores_*.pkl')) > 0:
            # old datafiles detected; load and convert dataset
            old_scores_files = glob.glob('./proverbs/proverb_scores_*.pkl')
            old_counts_files = glob.glob('./proverbs/proverb_counts_*.pkl')
            for guild in old_scores_files:
                guild_id = int(guild.split('proverb_scores_')[-1].split('.pkl')[0])
                self.proverb_score[guild_id] = {}
                old_scores = pkl.load(open(f'./proverbs/proverb_scores_{guild_id}.pkl', 'rb'))
                for _id, score in old_scores.items():
                    self.proverb_score[guild_id][_id] = {}
                    self.proverb_score[guild_id][_id]['score'] = score
            for guild in old_counts_files:
                guild_id = int(guild.split('proverb_counts_')[-1].split('.pkl')[0])
                old_counts = pkl.load(open(f'./proverbs/proverb_counts_{guild_id}.pkl', 'rb'))
                for _id, count in old_counts.items():
                    self.proverb_score[guild_id][_id]['count'] = count
                pkl.dump(self.proverb_score[guild_id], open(f'./proverbs/proverb_score_{guild_id}.pkl', 'wb'))
            for old_file in old_scores_files + old_counts_files:
                os.remove(old_file)
            print('Imported old scores succesfully')
            print(self.proverb_score)

        # load datasets
        score_files = glob.glob('./proverbs/proverb_score_*.pkl')
        for guild in score_files:
            guild_id = int(guild.split('proverb_score_')[-1].split('.pkl')[0])
            if self.proverb_score.get(guild_id, False) == False:
                self.proverb_score[guild_id] = {}
            self.proverb_score[guild_id].update(pkl.load(open(guild, 'rb')))
        print('Imported proverb score database')
        print(self.proverb_score)

        # TODO: version check on saved variables to convert databases

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
        return proverb, meaning, index

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
        index = selection['index'].iloc[0]
        return proverb, meaning, index

    @commands.command(name='prov.start')
    async def proverb(self, ctx, cont_prov: bool = False) -> None:
        """
        Start the daily proverb loop
        :param ctx: context
        :param cont_prov: boolean for continuation of previous proverb
        :return: None
        """
        _admin = self.bot.get_user(self.ADMINS.get('Tadsz'))
        await _admin.send(f'Proverb command started by {ctx.author}')
        if self.dev_mode:
            print(f'Proverb command ran by {ctx.author}')
        if not self.loop_proverb.get(ctx.guild.id, False):
            # if loop_proverb is false or non-existent, set to True
            self.loop_proverb[ctx.guild.id] = True

            _use_generated = None

            # handle multiple instances by assigning individual ids
            if self.loop_proverb_id.get(ctx.guild.id, None) == None:
                self.loop_proverb_id[ctx.guild.id] = {}
            loop_id = len(self.loop_proverb_id[ctx.guild.id])  # id is the length of the instances
            self.loop_proverb_id[ctx.guild.id][loop_id] = True

            # acknowledge message
            await ctx.message.add_reaction(self.bot_emoji)

            # actual loop
            loop_counter = 0
            while self.loop_proverb[ctx.guild.id] and self.loop_proverb_id[ctx.guild.id][loop_id]:
                loop_counter += 1
                print(f'Running loop: {loop_counter}')
                await _admin.send(f'Running loop: {loop_counter}')
                _prov_start = self.proverb_prov_start.get(ctx.guild.id, self.proverb_prov_start['default'])
                if datetime.now().time() > datetime.strptime(_prov_start, '%H:%M:%S').time():
                    print(f'Datetime after 08:00:00: {datetime.now()}')
                    await _admin.send(f'Datetime after 08:00:00: {datetime.now()}')
                    _prov_end = self.proverb_prov_end.get(ctx.guild.id, self.proverb_prov_end['default'])
                    if datetime.now().time() < datetime.strptime(_prov_end, '%H:%M:%S').time():
                        print(f'Datetime before 13:00:00')
                        await _admin.send(f'Datetime before 13:00:00')
                        if (self.loop_proverb[ctx.guild.id]) & (self.loop_proverb_id[ctx.guild.id][loop_id]):

                            # check and initialize voting lists
                            if self.proverb_fake.get(ctx.guild.id, False) == False:
                                self.proverb_fake[ctx.guild.id] = []
                            if self.proverb_real.get(ctx.guild.id, False) == False:
                                self.proverb_real[ctx.guild.id] = []

                            if not cont_prov:
                                _use_generated = bool(random.getrandbits(1))
                                _proverb, _meaning, _index = await self.read_proverb(USE_GENERATED=_use_generated)
                            else:
                                # only works on the last real proverb;
                                # TODO: add last proverb to persistent variable instead of re-reading
                                _proverb, _meaning, _index = await self.get_last_proverb()
                                cont_prov = False

                            # send proverb
                            posted_message = await ctx.send(_proverb)
                            await self.add_vote_buttons(posted_message)

                            # wait until 13:00 server time to continue with the answer
                            sleep_time = (datetime(datetime.now().year, datetime.now().month, datetime.now().day, 13, 0,
                                                   0) - datetime.now()).seconds

                            sleep_time = (datetime.combine(datetime.now().date(),
                                                           datetime.strptime(self.proverb_mean_start.get(ctx.guild.id,
                                                                                                         self.proverb_mean_start[
                                                                                                             'default']),
                                                                             '%H:%M:%S').time()) - datetime.now()).seconds
                            await _admin.send(f'Proverb sent {datetime.now()} | {sleep_time} seconds')
                            if self.dev_mode:
                                print('proverb sent, sleeping for meaning')
                                print(sleep_time)
                                sleep_time = 5
                            await sleep(sleep_time)

                            # check if loop has not been canceled, then send the meaning
                            if (self.loop_proverb[ctx.guild.id]) & (self.loop_proverb_id[ctx.guild.id][loop_id]):
                                await self.get_votes_from_buttons(ctx, posted_message)
                                await posted_message.reply(_meaning, mention_author=False)

                                if self.proverb_score.get(ctx.guild.id, False) == False:
                                    # create score list
                                    print('Creating score and count dicts')
                                    self.proverb_score[ctx.guild.id] = {}

                                await self.process_scores(ctx, _use_generated, _index, posted_message)

                                # wait until 08:00 server time the next day to continue with the next iteration
                                sleep_time = (datetime.combine(datetime.now().date() + timedelta(days=1),
                                                               datetime.strptime(
                                                                   self.proverb_prov_start.get(ctx.guild.id,
                                                                                               self.proverb_prov_start[
                                                                                                   'default']),
                                                                   '%H:%M:%S').time()) - datetime.now()).seconds

                                await _admin.send(
                                    f'Meaning sent {datetime.now()}, waiting for next day | {sleep_time} seconds')
                                if self.dev_mode:
                                    print('meaning sent, now sleeping for next loop')
                                    print(sleep_time)
                                    sleep_time = 10
                                await sleep(sleep_time)
                                print('meaning sleep time ended')
                    else:
                        # same day but after time, postpone until next day:
                        print('loop started too late; waiting until next day')
                        sleep_time = (datetime.combine(datetime.now().date() + timedelta(days=1),
                                                       datetime.strptime(self.proverb_prov_start.get(ctx.guild.id,
                                                                                                     self.proverb_prov_start[
                                                                                                         'default']),
                                                                         '%H:%M:%S').time()) - datetime.now()).seconds
                        await _admin.send(
                            f'Loop started after end time {datetime.now()}; waiting next day | {sleep_time} seconds')
                        if self.dev_mode:
                            print('loop started after end time')
                            print(sleep_time)
                            sleep_time = 10
                        await sleep(sleep_time)
                else:
                    # same day but too early:
                    sleep_time = (datetime.combine(datetime.now().date(),
                                                   datetime.strptime(self.proverb_prov_start.get(ctx.guild.id,
                                                                                                 self.proverb_prov_start[
                                                                                                     'default']),
                                                                     '%H:%M:%S').time()) - datetime.now()).seconds
                    await _admin.send(f'Same day but too early: {datetime.now()} | sleeping {sleep_time} seconds')
                    if self.dev_mode:
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
        if self.loop_proverb.get(ctx.guild.id, False):
            self.loop_proverb[ctx.guild.id] = False

            # if no loop_id is given, get loop_ids and find the first True value
            if loop_id is None:
                loop_ids = self.loop_proverb_id.get(ctx.guild.id, None)
                if loop_ids is not None:
                    loop_the_ids = True
                    while loop_the_ids:
                        for key, value in loop_ids.items():
                            if value:
                                loop_id = key
                                loop_the_ids = False
            if self.loop_proverb_id[ctx.guild.id].get(loop_id):
                self.loop_proverb_id[ctx.guild.id][loop_id] = False
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

        proverb, meaning, _index = self.read_proverb(USE_GENERATED=_use_generated)

        _posted_message = await ctx.send(proverb)
        await self.add_vote_buttons(_posted_message)

        await sleep(wait_time)

        await _posted_message.reply(meaning)

        await self.process_scores(ctx, _use_generated, _index, _posted_message)

        return

    async def process_scores(self, ctx, _use_generated, _index, _posted_message) -> None:
        """
        Processes the scores based on the member ids registered for each vote, adds and saves
        :param ctx: context
        :param _use_generated: boolean for which vote gets points awarded
        :param _index: index from respective source file
        :param _posted_message: message object
        :return: None
        """
        if self.proverb_score.get(ctx.guild.id, False) == False:
            self.proverb_score[ctx.guild.id] = {}

        if _use_generated is not None:
            print(self.proverb_score[ctx.guild.id])
            # convert old scores where datetime was missing
            for userid in self.proverb_score[ctx.guild.id].keys():
                if self.proverb_score[ctx.guild.id][userid].get('last_vote_datetime', False) == False:
                    self.proverb_score[ctx.guild.id][userid]['last_vote_datetime'] = datetime.now().date()

            print(self.proverb_score[ctx.guild.id])

            # verify if all users who voted are in the score list
            users_to_add = [userid for userid in self.proverb_fake[ctx.guild.id] + self.proverb_real[ctx.guild.id] if
                            userid not in self.proverb_score[ctx.guild.id].keys()]
            for userid in users_to_add:
                self.proverb_score[ctx.guild.id][userid] = {'score': 0, 'count': 0,
                                                            'last_vote_datetime': datetime.now().date()}

            # process votes
            if _use_generated:
                # add points to bot voters
                for userid in self.proverb_fake[ctx.guild.id]:
                    self.proverb_score[ctx.guild.id][userid]['score'] += 1
                    self.proverb_score[ctx.guild.id][userid]['count'] += 1
                    self.proverb_score[ctx.guild.id][userid]['last_vote_datetime'] = datetime.now().date()
                for userid in self.proverb_real[ctx.guild.id]:
                    self.proverb_score[ctx.guild.id][userid]['count'] += 1
                    self.proverb_score[ctx.guild.id][userid]['last_vote_datetime'] = datetime.now().date()

            elif not _use_generated:
                # add points to real voters
                for userid in self.proverb_real[ctx.guild.id]:
                    self.proverb_score[ctx.guild.id][userid]['score'] += 1
                    self.proverb_score[ctx.guild.id][userid]['count'] += 1
                    self.proverb_score[ctx.guild.id][userid]['last_vote_datetime'] = datetime.now().date()
                for userid in self.proverb_fake[ctx.guild.id]:
                    self.proverb_score[ctx.guild.id][userid]['count'] += 1
                    self.proverb_score[ctx.guild.id][userid]['last_vote_datetime'] = datetime.now().date()

            # return a list of scores
            await self.show_proverb_scores(ctx, 'time')
            await self.save_proverb_scores(ctx)

            # initialize tracking record

            track_columns = ['discord_channel_id',
                             'discord_start_series_id',
                             'discord_prompt_id',
                             'proverb_id',
                             'datetime',
                             'generated',
                             'voted_real',
                             'voted_false']

            _df_vote_tracker = pd.DataFrame([[ctx.guild.id,
                                              ctx.message.id,
                                              _posted_message.id,
                                              _index,
                                              datetime.now(),
                                              _use_generated,
                                              self.proverb_real[ctx.guild.id],
                                              self.proverb_fake[ctx.guild.id]]],
                                            columns=track_columns)

            track_file = f'./proverbs/proverb_vote_history_{ctx.guild.id}.csv'
            if not os.path.exists(track_file):
                pd.DataFrame([], columns=track_columns).to_csv(track_file, index=False)

            vote_track_concat = pd.concat([pd.read_csv(track_file), _df_vote_tracker])
            vote_track_concat.to_csv(track_file, index=False)

            # empty list of current votes
            self.proverb_real[ctx.guild.id] = []
            self.proverb_fake[ctx.guild.id] = []

        return

    async def save_proverb_scores(self, ctx) -> None:
        """
        Saves the persistent variables to survive reboots
        :param ctx: context
        :return:
        """
        pkl.dump(self.proverb_score[ctx.guild.id],
                 open(f'./proverbs/proverb_score_{ctx.guild.id}.pkl', 'wb'))
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
    async def show_proverb_scores(self, ctx, metric: str = 'time') -> None:
        """
        Show current leaderbord (default: sum)
        :param ctx: context
        :param metric: (sum|avg|time)
        :return: None
        """

        mmr_days = 31

        if self.proverb_score.get(ctx.guild.id, False) == False:
            self.proverb_score[ctx.guild.id] = {}

        # return a list of scores
        _message = 'Score list: \n'
        if metric == 'sum':
            for _id, values in sorted(self.proverb_score[ctx.guild.id].items(), key=lambda x: x[1]['score']):
                _message += f'{self.bot.get_user(_id).name}: {values["score"]}\n'
        elif (metric == 'avg') or (metric == 'mean'):
            for _id, values in sorted(self.proverb_score[ctx.guild.id].items(),
                                      key=lambda x: x[1]['score'] / x[1]['count'], reverse=True):
                _message += f'{self.bot.get_user(_id).name}: {values["score"]}/{values["count"]} ({round(values["score"] / values["count"] * 100, 1)}%)\n'
        elif (metric == 'time'):
            df_scores = pd.DataFrame.from_dict(self.proverb_score[ctx.guild.id]).transpose()
            print(df_scores.info())

            _a = (pd.Timedelta(mmr_days, 'd') - (datetime.now().date() - df_scores['last_vote_datetime'])) / pd.Timedelta(mmr_days, 'd')
            # prevent negative scores
            _a[_a<0] = 0
            df_scores['mmr'] = df_scores['score'] / df_scores['count'] * _a

            df_scores = df_scores.sort_values(['mmr', 'last_vote_datetime', 'score'], ascending=False).copy()
            for _id, _score, _count, _mmr in zip(df_scores.index, df_scores['score'], df_scores['count'], df_scores['mmr']):
                if _mmr > 0:
                    _message += f'{self.bot.get_user(_id).name}: {_score}/{_count} ({int(round(_mmr, 3) * 1000)})\n'
        await ctx.send(_message)
        return

    async def add_vote_buttons(self, posted_message) -> None:
        """
        Adds vote buttons to the passed message using the global emoji_real and emoji_fake variables
        :param posted_message: Discord message object
        :return: None
        """
        await posted_message.add_reaction(self.emoji_real)
        await posted_message.add_reaction(self.emoji_fake)
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
            if str(reaction.emoji) == self.emoji_fake:
                users_fake = await reaction.users().flatten()
            elif str(reaction.emoji) == self.emoji_real:
                users_real = await reaction.users().flatten()

        self.proverb_fake[ctx.guild.id] = []
        if users_fake is not None:
            for user in users_fake:
                if user.id != self.bot.user.id:
                    self.proverb_fake[ctx.guild.id].append(user.id)

        self.proverb_real[ctx.guild.id] = []
        if users_real is not None:
            for user in users_real:
                if user.id != self.bot.user.id:
                    self.proverb_real[ctx.guild.id].append(user.id)

        # remove id from both lists if they are duplicates to prevent double votes
        _fake_voters = self.proverb_fake[ctx.guild.id].copy()
        _real_voters = self.proverb_real[ctx.guild.id].copy()

        self.proverb_fake[ctx.guild.id] = [userid for userid in self.proverb_fake[ctx.guild.id] if
                                           userid not in _real_voters]
        self.proverb_real[ctx.guild.id] = [userid for userid in self.proverb_real[ctx.guild.id] if
                                           userid not in _fake_voters]
        return

    @commands.command(name='prov.alter', aliases=['alter.scores', 'alter'])
    async def alter_scores(self, ctx, item: str, user: discord.User, score: str = None) -> None:
        """
        Admin-only: alter scores in memory of the passed string discord names (as shown in score list)
        :param ctx: context
        :param item: (score|count|clear) to alter score or count, or remove user from score list
        :param user: discord username (not user object, id or mention!)
        :param score: int for new score or str for desired operation (add/sub/div/mult)
        :return: None
        """
        if ctx.author.id not in self.ADMINS.values():
            print('admin not found')
            return

        if item not in ('score', 'count', 'clear'):
            return

        if self.proverb_score.get(ctx.guild.id, False) == False:
            print('ctx not in proverb score')
            self.proverb_score[ctx.guild.id] = {}

        if self.proverb_score[ctx.guild.id].get(user.id, False) == False:
            print('user not in score')
            self.proverb_score[ctx.guild.id][user.id] = {'score': 0, 'count': 0}

        if item == 'clear':
            self.proverb_score[ctx.guild.id].pop(user.id, None)
            await self.save_proverb_scores(ctx)
            await self.show_proverb_scores(ctx)
            return
        else:
            if score is None:
                await ctx.send('No value submitted.')
                return

        try:
            score = int(score)
        except:
            pass

        if isinstance(score, int):
            self.proverb_score[ctx.guild.id][user.id][item] = score
        elif isinstance(score, str):
            if score[0] == '+':
                try:
                    add_score = int(score[1:])
                    self.proverb_score[ctx.guild.id][user.id][item] += add_score
                except:
                    await ctx.send('Score not understood')
                    return
            elif score[0] == '-':
                try:
                    subtract_score = int(score[1:])
                    self.proverb_score[ctx.guild.id][user.id][item] -= subtract_score
                except:
                    await ctx.send('Score not understood')
                    return
            elif (score[0] == 'x') or (score[0] == '*'):
                try:
                    mult_score = int(score[1:])
                    self.proverb_score[ctx.guild.id][user.id][item] *= mult_score
                except:
                    await ctx.send('Score not understood')
                    return
            elif (score[0] == '/') or (score[0] == ':'):
                try:
                    div_score = int(score[1:])
                    self.proverb_score[ctx.guild.id][user.id][item] /= div_score
                except:
                    await ctx.send('Score not understood')
                    return
        await self.save_proverb_scores(ctx)
        await self.show_proverb_scores(ctx)
        return
