# Utility Modules Documentation

This directory contains various utility modules used throughout the bot. Below is documentation for each module.

## Table of Contents
- [Cooldown Manager](#cooldown-manager)
- [Permission Manager](#permission-manager)
- [Safe Content System](#safe-content-system)

## Cooldown Manager
**Location**: `utils/cooldown_manager.py`

Manages command cooldowns across the bot to prevent spam and abuse.

### Key Features:
- User-specific cooldowns
- Global cooldowns
- Privileged user bypass
- Cooldown message management
- Enable/disable cooldown system

### Usage Example:
```python
from utils.cooldown_manager import with_cooldown

@with_cooldown(user_cooldown=10, global_cooldown=5)
async def my_command(ctx):
    # Command implementation
```

## Permission Manager
**Location**: `utils/permission_manager.py`

Handles command permissions and access control.

### Key Features:
- Mod-only commands
- User-specific permissions
- Broadcaster override
- Permission checking

### Usage Example:
```python
from utils.permission_manager import mod_only

@mod_only
async def admin_command(ctx):
    # Command implementation

@mod_only(specific_users=["user1", "user2"])
async def special_command(ctx):
    # Command implementation
```

## Safe Content System
**Location**: `utils/safe_content/`

A comprehensive content filtering system to ensure safe message content.

### Components:

#### 1. Content Filter
**Location**: `utils/safe_content/content_filter.py`

Main content filtering system that checks for:
- Banned phrases
- Phone numbers
- Discriminatory language
- Harmful content

#### 2. Username Filter
**Location**: `utils/safe_content/username_filter.py`

Specialized filter for usernames:
- Checks for inappropriate content
- Prevents phone numbers in usernames
- Filters banned words

#### 3. Word Filter
**Location**: `utils/safe_content/word_filter.py`

Basic word filtering system:
- Exact and partial phrase matching
- Configurable banned phrases
- Message safety validation

### Usage Example:
```python
from utils.safe_content import safe_content

@safe_content
async def my_command(ctx):
    # Command implementation
```

## Best Practices

1. **Cooldowns**:
   - Use `with_cooldown` decorator for commands that could be spammed
   - Set appropriate cooldown times based on command impact
   - Consider using global cooldowns for resource-intensive commands

2. **Permissions**:
   - Use `mod_only` for moderation commands
   - Combine with cooldowns for better control
   - Always specify specific users when needed

3. **Content Safety**:
   - Apply `safe_content` decorator to commands that process user input
   - Use content_filter for manual message checking
   - Keep banned phrase lists updated

## Error Handling

All utility modules include built-in error handling and logging. Make sure to configure your logging system appropriately:

```python
import logging
logger = logging.getLogger('twitch_bot')
```

## Configuration

Most utility modules use singleton instances for consistent state:

- `cooldown_manager`
- `permission_manager`
- `content_filter`
- `word_filter`
- `username_filter`

These instances are automatically created when importing the modules.

## Dependencies

- Python 3.7+
- logging module
- re (for regex operations)
- functools (for decorators)
```