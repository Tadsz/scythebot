from datetime import datetime
import pandas as pd


def use_proverb():
    data = pd.read_csv('sayings.csv')
    index = data.loc[data['used'].isna()]['index'].iloc[0]
    mask = data['index'] == index
    proverb = data.loc[mask]['proverb'].iloc[0]
    meaning = data.loc[mask]['meaning'].iloc[0]
    data.loc[data['index'] == index, 'used'] = datetime.now()
    data.to_csv('sayings.csv', index=False)
    return proverb, meaning
