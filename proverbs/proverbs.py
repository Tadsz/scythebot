from datetime import datetime, time
import pandas as pd


def use_proverb(USE_GENERATED: bool = False):
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

def get_proverb_history(num:int=7):
    data = pd.read_csv('sayings.csv')
    selection = data.loc[data['used'].notna()].sort_values('used', ascending=False)[['proverb', 'meaning']].head(num+1)
    if time(8,0) <= datetime.now().time() <= time(13,0):
        selection = selection[1:]
    else:
        selection = selection[:-1]
    message = ''
    for proverb, meaning in zip(selection['proverb'], selection['meaning']):
        message += f"{proverb} || {meaning} ||\n"
    return message

def get_proverb_numericals():
    data = pd.read_csv('sayings.csv')
    used = data['used'].notna().sum()
    total = len(data)
    remaining = total - used
    return used, remaining, total

def get_last_proverb():
    data = pd.read_csv('sayings.csv')
    selection = data.sort_values('used', ascending=False).head()
    proverb = selection['proverb'].iloc[0]
    meaning = selection['meaning'].iloc[0]
    return proverb, meaning
