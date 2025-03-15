# PispisCommand Documentation

## Overview

The `PispisCommand` module implements a playful interaction system for Twitch chat where users can "make pis pis" (a humorous action) on other users. The system includes a reputation tracking mechanism, allowing users to damage others' reputation with the action and to repair their own reputation by "praying".

## Command Structure

The module consists of several files:

- `__init__.py`: Package initialization
- `command.py`: Main command implementation
- `reputation_manager.py`: Handles reputation tracking and cooldowns
- `reputation_data.json`: Stores user reputation data and cooldowns

## Available Commands

### !мион (Pis Pis Command)

Makes a "pis pis" action on a specified user.

**Usage:**
- `!мион @username` - Makes pis pis on the specified user
- `!мион username` - Makes pis pis on the specified user (without @ symbol)
- `!мион` - Makes pis pis on a random user from recent chatters

**Effects:**
- Decreases the target's reputation by 1
- Sets a cooldown for the user (120 seconds by default)
- Shows the target's updated reputation status

**Examples:**
```
User: !мион @friend
Bot: user сделал пис пис на friend mion [Репутация friend: -1 (Мокрый бинт 💦)]
```

### !молиться (Pray Command)

Allows users to improve their own reputation or pray for another user.

**Usage:**
- `!молиться` - Increases the user's own reputation by 1
- `!молиться @username` - Increases the specified user's reputation by 1

**Effects:**
- Increases the target's reputation by 1
- Sets a cooldown for the praying user (120 seconds by default)
- Shows the target's updated reputation status

**Examples:**
```
User: !молиться
Bot: @user помолился и очистил свою карму! Репутация: 1 (Норм чел 👍)
```

### !репутация (Reputation Command)

Checks a user's reputation.

**Usage:**
- `!репутация` - Checks your own reputation
- `!репутация @username` - Checks the specified user's reputation

**Example:**
```
User: !репутация
Bot: @user имеет репутацию 5 (Норм чел 👍)
```

### !репутацияпоставить (Set Reputation Command)

Allows moderators to set a user's reputation. VIPs can only modify their own reputation.

**Usage:**
- `!репутацияпоставить username value` - Sets the specified user's reputation to the given value

**Permissions:**
- Moderators: Can set anyone's reputation
- VIPs: Can only set their own reputation
- Regular users: Cannot use this command

**Example:**
```
Mod: !репутацияпоставить user 10
Bot: @mod изменил репутацию пользователя user с 5 на 10 (Хороший человек 😊)
```

## Reputation System

### Reputation Levels

The system assigns status labels based on reputation points:

| Reputation Range | Status |
|------------------|--------|
| ≥ 200 | Божество 🌠 |
| ≥ 150 | Мифическая фигура 🦄 |
| ≥ 100 | Легенда 🌟 |
| ... | ... |
| ≥ 0 | Норм чел 👍 |
| ≥ -10 | Мокрый бинт 💦 |
| ... | ... |
| < -1500 | Абсолютный ноль существования ❄️💀 |

### Reputation Management

- Each `!мион` command decreases a target's reputation by 1
- Each `!молиться` command increases the user's reputation by 1
- Reputation is stored persistently in `reputation_data.json`

## Cooldown System

The module implements individual and global cooldowns:

### Individual Cooldowns
- Each user has separate cooldowns for pis pis and pray commands
- Default cooldown: 120 seconds

### Global Cooldowns
- Prevents command spam across all users
- Default global cooldown: 10 seconds per command type

## Special Features

### Random Targets
Users can make pis pis on a random chatter using the `!мион р` command.

### Bot Defense
If a user tries to make pis pis on the bot itself, the bot will respond with a defensive message.

### Safety Filters
- Username filter prevents actions on potentially unsafe usernames
- Word filter ensures generated messages don't contain inappropriate content
- Special handling for phone-number-like usernames to avoid ToS violations

### Varied Phrases
The bot uses a variety of phrases for the pis pis action to keep interactions fresh and entertaining.

## Technical Implementation

### Event Handling
The module registers a message listener with the bot to process commands.

### Data Storage
User reputation and cooldown data is stored in a JSON file:
- `reputations`: Maps usernames to reputation values
- `cooldowns`: Tracks cooldowns for different command types per user

### Concurrency
Uses asyncio locks to safely handle concurrent updates to shared data structures.

### Logging
All significant actions are logged for troubleshooting and monitoring.

## Example Implementation

To use the module in a bot:

```python
from commands.pispis.command import PispisCommand

# In your bot initialization
pispis_command = PispisCommand(bot)
```

This will register all necessary commands with your bot instance.