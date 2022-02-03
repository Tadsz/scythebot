# ScytheBot
ScytheBot grew to be a discord companion of some sorts. It started out as a randomizer for the Scythe game, but soon found it's way to share profound knowledge. After many fortnights though not too many, ScytheBot spoke up for the voiceless. 

## Cogs
[Discord.py](https://discordpy.readthedocs.io/en/stable/) uses cogs to separate code into manageable chunks. Cogs are modular and can be added and removed while the bot is running. ScytheBot currently consists of the following chunks of code:
- main
   - general methods to boot the bot and load other cogs as well as some basic functions
- scythe
    - Scythe specific functions, for which the bot was initially created. Assigns random teams based on [shibrady/scythe-stats](https://github.com/shibrady/scythe-stats) tier list. 
- proverbs
    - A proverb cog containing methods to post proverbs, gather votes and keep track of votes. These proverbs are collected through scraping websites using the sayings.py file. These real proverbs are then used to generate new proverbs.
 - soundboard
    - A soundboard cog containing methods to join voice channels and play mp3 audio fragments uploaded in the `./soundboard/data/d1mp3` folder

## Set-up
### Discord
Create a bot (application) over at the [discord developers website](https://discord.com/developers/applications). After successful creation, copy your application's discord token to an environment file. You can find your bot's token under Application > Settings (left) > Bot > Token > Click to Reveal Token

```
File: .env
--------------
DISCORD_TOKEN='AA.nA.nas313'
ADMIN_DICT='{"Name": discord.user.id}'
SUPER_ADMIN='Name'
SCYTHEBOT_DEBUG_MODE='False'
LIBOPUS=/absolute/path/to/libopus/so/if/needed
```   

### Host
Clone this repo, install the `requirements.txt`, create `.env` file in root of the ScytheBot folder and run `scythebot.py`

### Develop
See Host, but set `SCYTHEBOT_DEBUG_MODE` to `'True'` It is recommended to host a separate developers application to test your changes and prevent your production server from crashing or spamming constantly
