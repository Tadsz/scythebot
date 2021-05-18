from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np

# %%
URL = 'https://www.woorden.org/inc/10spreekwoorden.php'

proverbs = []
meanings = []
for i in range(500):
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')

    sayings = soup.find_all('li')

    for saying in sayings:
        txt = saying.text
        proverb, meaning = txt.split(' (=')
        meaning = meaning[:-1]
        proverbs.append(proverb)
        meanings.append(meaning)

data = pd.DataFrame({'proverb': proverbs,
                     'meaning': meanings})

data['used'] = np.nan

print(data.info())
print(data.head())

# merge with existing data
old = pd.read_csv('sayings.csv')

data = pd.concat([old, data])

# drop duplicates

data = data.drop_duplicates()

data.to_csv('sayings.csv', index=False)

data.shape

