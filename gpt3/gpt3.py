# openai.py
"""
Python module for the discord ScytheBot to host the Proverbs cog / module
"""

import os
import json
import datetime
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
import openai
import gpt3.gpt_config

load_dotenv()
dev_mode = True if os.getenv('SCYTHEBOT_DEBUG_MODE', False) == 'True' else False
ADMINS = json.loads(os.getenv('ADMIN_DICT'))


class OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_history = []
        self.bot_emoji = "🤖"
        self.db = sqlite3.connect("chat_history.db")
        self.cursor = self.db.cursor()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.create_tables()

        self.engine = "text-davinci-003"
        self.max_tokens = 16
        self.temperature = 0.7
        self.frequency_penalty = 1
        self.presence_penalty = 0

    def create_tables(self):
        for table in gpt3.gpt_config.CREATE_TABLES:
            self.cursor.execute(table)

    # Function to process prompts from chat messages
    def process_prompt(self, prompt, user, user_id):

        last_hour = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        last_day = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        recent_activity = self.cursor.execute(
            f"""
            WITH hourly AS (SELECT row_number() over(order by cr.id) rn, SUM(input_tokens) + SUM(output_tokens) as tokens_hour
                FROM chat_requests cr
                WHERE cr.user_id = '{user_id}'
                  AND cr.created_at > '{last_day}'
            ), daily AS (
                SELECT row_number() over(order by cr.id) rn, SUM(input_tokens) + SUM(output_tokens) as tokens_day
                FROM chat_requests cr
                WHERE cr.user_id = '{user_id}'
                AND cr.created_at > '{last_hour}'
            ) SELECT h.tokens_hour, d.tokens_day
              FROM hourly h
              LEFT JOIN daily d on h.rn = d.rn
            """
        ).fetchone()

        if recent_activity:
            if recent_activity[0]:
                if recent_activity[0] > 10_000:
                    return f"You have used over {recent_activity[0]} in an hour. Slow down and try again later."
            if recent_activity[1]:
                if recent_activity[1] > 100_000:
                    return f"You have used over {recent_activity[1]} in one day. Slow down and try again later."

        # build a new prompt with the chat_history context:
        if len(self.chat_history) > 0:
            full_message = "Given the following chat history context:\n\n"
            for _msg, _user in self.chat_history:
                full_message += f"{_user}: {_msg}\n\n"

            full_message += f"Process the following prompt:\n\n{prompt}"
        else:
            full_message = prompt

        expected_prompt_tokens = int(len(full_message.split()) * 1.25)
        if self.max_tokens - expected_prompt_tokens < 16:
            return "Input too large for any possible and/or meaningful output. Reduce the input or clear history using the !clear_history command."
        try:
            # Use the OpenAI API to generate a response to the prompt
            response = openai.Completion.create(engine=self.engine,
                                                prompt=full_message,
                                                max_tokens=self.max_tokens - expected_prompt_tokens,
                                                temperature=self.temperature,
                                                # top_p=1,
                                                frequency_penalty=self.frequency_penalty,
                                                presence_penalty=self.presence_penalty,
                                                best_of=1,
                                                )
        except:
            print(response)

        # Add the prompt and user to the chat history
        self.chat_history.append((prompt, user))
        self.chat_history.append((response.choices[0].text, 'ChatGPT'))
        self.add_to_db(user, user_id, prompt, full_message, self.max_tokens, response)

        # Return the generated response
        return response.choices[0].text

    def add_to_db(self, user_name, user_id, prompt, full_message, max_tokens, response):

        input_tokens = response.usage['prompt_tokens']
        output_tokens = response.usage['completion_tokens']

        # check if user in users table, and add if not exists
        user_row = self.cursor.execute(
            f"""
            SELECT * FROM users
            WHERE users.id = {user_id}
            """
        ).fetchone()
        if not user_row:
            # add to database
            self.cursor.execute(
                """
                INSERT INTO users
                VALUES (?, ?)
                """, (user_id, user_name)
            )

        # add record to chat history
        self.cursor.execute(
            """
            INSERT INTO chat_requests
            (user_id, created_at, prompt, prompt_history, prompt_response, input_tokens, output_tokens, max_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, datetime.datetime.utcnow(), prompt, full_message, response.choices[0].text,
                  input_tokens, output_tokens, max_tokens)
        )
        self.db.commit()
        return

    @commands.command(name="text", help='Generate a textual response')
    async def get_response(self, ctx):
        await ctx.message.add_reaction(self.bot_emoji)
        response = self.process_prompt(prompt=ctx.message.content[6:],
                                             user=ctx.author.display_name,
                                             user_id=ctx.author.id,
                                             )
        await ctx.reply(response)

    async def kwargs_parser(self, kwargs_as_list_of_strings):
        kwargs = dict()
        for arg in kwargs_as_list_of_strings:
            kw, val = arg.split('=')
            try:
                val_f = float(val)
                val_i = int(val)
                if val_f == val_i:
                    kwargs[kw] = val_i
                else:
                    kwargs[kw] = val_f
            except ValueError:
                if val.lower() == 'true':
                    kwargs[kw] = True
                elif val.lower() == 'false':
                    kwargs[kw] = False
                else:
                    kwargs[kw] = val
        return kwargs

    @commands.command(name='textset', help='Set settings for generating a textual response')
    async def set_text_settings(self, ctx, *kwargs):
        await ctx.message.add_reaction(self.bot_emoji)
        kwargs = await self.kwargs_parser(kwargs)

        self.engine = kwargs.get('engine', self.engine)
        self.max_tokens = kwargs.get('max_tokens', self.max_tokens)
        self.temperature = kwargs.get('temperature', self.temperature)
        self.frequency_penalty = kwargs.get('frequency_penalty', self.frequency_penalty)
        self.presence_penalty = kwargs.get('presence_penalty', self.presence_penalty)

        await ctx.reply(kwargs)

    @commands.command(name='clear_history', help='Clear the context passed')
    async def clear_history(self, ctx):
        self.chat_history = []
        await ctx.message.add_reaction(self.bot_emoji)
