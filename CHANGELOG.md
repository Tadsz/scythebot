# CHANGELOG

## [0.0.1] - Hidden motive - 2022/01/02
### Added
- Proverbs: hide votes if message management permissions are set
- Proverbs: show user nick/display name/username/discriminator in score list

### Fixed:
- Proper changelog etiquette
- Proverbs: emoji response now also works with custom emoji

### TODO:
- Scythebot/Proverb: move emoji reaction to Scythebot but keep voting in Proverb
- Proverb: refactor voting lists from two dictionaries with guild_id keys (proverb_fake[ctx.guild.id]) to one dictionary: proverb_votes[ctx.guild.id][prompt_id][true/false]
- Proverb: add last proverb to persistent variable instead of re-reading
- Proverb: limit voting scores to the past month while keeping a running total (output a score over the past 30 days)

## [a011a] - Long Time No See - 2021/10/26
### Added
- Scythebot: react to message through text, quotes or emojis
- Scythebot/proverbs: persist scores from voting
- Scythebot/proverbs: functions for voting using reactions
- Scythebot/proverbs: keep track of votes by prompt and userid
- Scythebot meme settings: quote and replace characters for specific users in specific guilds
- Limit Scythebot response to messages if 'schijtbot' was used in recent history
- Scythebot/proverbs will react with emoji if >2 users reacted with this emoji

### Changed
- Moved emojis to environment variable

### Fixed
- Split Scythebot into cogs (modules) for better management
- User id was parsed as str instead of int when passed in command to scythebot

### Removed
- Old voting system

## [a007] - Channeling - 2020/12/16
### Added
- Added options to indicate which channel to use
- Added levenshtein distance to determine channels with minor spelling mistakes

### Fixed
- Minor bugfixes due to new features

## [a006] - Random errors - 2020/12/14
### Fixed
- Fixed issue where shuffling resulted in shuffled base list (multiple variables refer to same list object, not to separate lists)

## [a005] - Server Specific Settings - 2020/12/12
### Added
- Server specific settings; introduced dictionaries with ctx.guild.id as keys
### Known bugs
- reroll upon banned combination

## [a005] - Rewrite-Reduce-Repeat - 2020/12/12 
### Fixed
- Code cleanup to remove repetitive code

## [a004] - Minor improvements - 09/12/2020
### Fixed
- Minor bugfixes/improvements

## [a003] - Added full function - 07/12/2020
### Added
- Extra player mats, removed unused functions

## [a002] - Using a changelog for a change - 06/12/2020
### Added
- Discord bot up and running, can still use major improvements
