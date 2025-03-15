# Balance System Documentation

## Overview
The balance system allows users to manage virtual currency (rubles) in Twitch chat. Users can check balances, steal from others, gift money, and participate in various currency-related activities.

## Integration with Other Modules

### Importing and Using BalanceManager

To integrate the balance system into your module, use the singleton `balance_manager` instance:

```python
# Correct way to import
from commands.balance.balance_manager import balance_manager

# Example usage in command class
class YourCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.balance_manager = balance_manager
```

⚠️ **IMPORTANT**: Never create a new `BalanceManager` instance! Always use the existing singleton `balance_manager`.

### Core Balance Operations

#### Getting User Balance
```python
# Get current user balance
balance = balance_manager.get_balance(username)
```

#### Modifying Balance
```python
# Add funds (positive value)
new_balance = balance_manager.adjust_balance(username, amount)

# Subtract funds (negative value)
new_balance = balance_manager.adjust_balance(username, -amount)
```

#### Transferring Between Users
```python
# Transfer funds between users
success, sender_balance, recipient_balance = balance_manager.transfer(from_user, to_user, amount)
```

#### Formatting Balance for Display
```python
# Format number with thousand separators
formatted_balance = balance_manager.format_balance(amount)
# Example: 1000000 -> "1,000,000"
```

## Core Components

### BalanceManager
Central component handling all balance-related operations. Located in `balance_manager.py`.

Key features:
- Manages user balances in JSON storage
- Handles transactions between users
- Manages steal chances and cooldowns
- Provides leaderboard functionality
- Supports custom steal and protection chances

### Commands

#### Basic Commands
1. **!баланс** [username]
   - Shows balance for self or specified user
   - New users receive 100 rubles starting balance
   - Supports checking balance via message reply
   - Usage: `!баланс` or `!баланс @username`

2. **!подарить-рубли** @username amount
   - Gifts specified amount to another user
   - Supports gifting via message reply
   - Usage: `!подарить-рубли @username 100`

3. **!лидеры**
   - Shows top 3 users by balance
   - Cooldown: 20s per user, 5s globally
   - Usage: `!лидеры`

4. **!раздать** num_users total_amount
   - Distributes money among random active chat participants
   - Automatically adapts to available recipients
   - Uses list of active users from chat
   - Usage: `!раздать 5 1000`

#### Moderator Commands
1. **!забрать** @username amount
   - Removes money from user
   - Moderator only
   - Usage: `!забрать @username 100`

2. **!начислить** @username amount
   - Adds money to user
   - Moderator only
   - Usage: `!начислить @username 100`

## Integration Examples

### Casino Command Example
```python
@self.bot.command(name="казино")
@cooldown(user_cd=30, global_cd=5)
async def casino_command(ctx):
    username = ctx.author.name.lower()
    current_balance = balance_manager.get_balance(username)
    
    # Calculate bet (e.g., 50% of balance)
    bet_amount = int(current_balance * 0.5)
    
    # Determine result (e.g., 10% win chance)
    if random.random() < 0.1:  # Win
        new_balance = balance_manager.adjust_balance(username, bet_amount)
        await ctx.send(f"You won {bet_amount} rubles! New balance: {new_balance}")
    else:  # Loss
        new_balance = balance_manager.adjust_balance(username, -bet_amount)
        await ctx.send(f"You lost {bet_amount} rubles. New balance: {new_balance}")
```

### Activity Reward Example
```python
async def reward_active_users():
    for username in active_users:
        # Add 10 rubles for activity
        new_balance = balance_manager.adjust_balance(username, 10)
        logger.info(f"Rewarded {username} with 10 rubles. New balance: {new_balance}")
```

## Data Storage

### Files
- `balances.json`: Stores user balances and related data

### User Data Structure
```json
{
  "username": {
    "balance": 1000,
    "got_starter": true,
    "last_steal_attempt": 1234567890.123
  }
}
```

## Security Features
- Username validation before transactions
- Balance never goes below 0
- Safe username filtering through username_filter
- Transaction logging
- Error handling for all operations
- Permission checks for moderator commands

## Best Practices

1. **Always use the singleton instance**:
   ```python
   from commands.balance.balance_manager import balance_manager
   ```

2. **Use correct methods for balance modification**:
   - To add: `balance_manager.adjust_balance(username, positive_amount)`
   - To subtract: `balance_manager.adjust_balance(username, -negative_amount)`
   - For transfers: `balance_manager.transfer(from_user, to_user, amount)`

3. **Format amounts for display**:
   ```python
   formatted = balance_manager.format_balance(amount)
   ```

4. **Check sufficient funds before operations**:
   ```python
   if balance_manager.get_balance(username) >= amount:
       # Perform operation
   ```

5. **Use try-except for error handling**:
   ```python
   try:
       new_balance = balance_manager.adjust_balance(username, amount)
   except Exception as e:
       logger.error(f"Error adjusting balance: {str(e)}")
   ```

This documentation covers the main features and functionality of the balance system. For specific implementation details, refer to the individual source files.