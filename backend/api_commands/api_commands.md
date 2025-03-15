# Twitch API Documentation

This module provides a wrapper for Twitch API operations commonly used by the bot.

## TwitchAPI Class

### Initialization

```python
from api_commands.twitch_api import TwitchAPI

# The bot instance is required for initialization
twitch_api = TwitchAPI(bot)
```

### Methods

#### timeout_user
Timeout (temporarily ban) a user in a channel.

```python
success = await twitch_api.timeout_user(
    broadcaster_id="123456789",  # Channel owner's ID
    target_user_id="987654321",  # User to timeout
    duration=300,                 # Duration in seconds
    reason="Spam"                # Optional reason
)
```

#### get_user_id
Get Twitch user ID from username.

```python
user_id = await twitch_api.get_user_id("username")
if user_id:
    print(f"User ID: {user_id}")
```

#### get_username
Get Twitch username from user ID.

```python
username = await twitch_api.get_username("123456789")
if username:
    print(f"Username: {username}")
```

#### reply_to_message
Send a message or reply to a specific message in a channel.

```python
# Simple message
success = await twitch_api.reply_to_message(
    channel_name="channel",
    message="Hello!"
)

# Reply to specific message
success = await twitch_api.reply_to_message(
    channel_name="channel",
    message="Hello!",
    reply_to_msg_id="123-456-789"
)
```

## Error Handling

All methods are decorated with `@handle_api_errors` which:
- Catches and logs API request errors
- Catches and logs unexpected errors
- Returns `None` or `False` on failure

## Usage Example

```python
async def moderate_channel(bot):
    api = TwitchAPI(bot)
    
    # Get user ID
    user_id = await api.get_user_id("problematic_user")
    if user_id:
        # Timeout user for 10 minutes
        success = await api.timeout_user(
            broadcaster_id="channel_id",
            target_user_id=user_id,
            duration=600,
            reason="Inappropriate behavior"
        )
        
        if success:
            await api.reply_to_message(
                channel_name="channel",
                message="User has been timed out for 10 minutes."
            )
```

## Message Reply System

### Quick Start

To use the reply system in your command:

```python
from api_commands.twitch_api import TwitchAPI

class YourCommand(BotCommand):
    def __init__(self, bot):
        # Initialize TwitchAPI in your command class
        self.twitch_api = TwitchAPI(bot)
        super().__init__(bot)

    def register_commands(self):
        @self.bot.command(name="yourcommand")
        async def your_command(ctx):
            # Reply to the original message
            await self.twitch_api.reply_to_message(
                channel_name=ctx.channel.name,
                message="Your reply message here",
                reply_to_msg_id=ctx.message.id
            )
```

### Detailed Reply Usage

#### Method Signature
```python
async def reply_to_message(
    self, 
    channel_name: str,
    message: str, 
    reply_to_msg_id: Optional[str] = None
) -> bool
```

#### Parameters
- `channel_name`: The channel where the message should be sent
- `message`: The content of your reply
- `reply_to_msg_id`: The ID of the message you're replying to (from ctx.message.id)

#### Example Usage Scenarios

1. Basic Reply:
```python
await self.twitch_api.reply_to_message(
    channel_name=ctx.channel.name,
    message="Simple reply",
    reply_to_msg_id=ctx.message.id
)
```

2. Reply with Status:
```python
await self.twitch_api.reply_to_message(
    channel_name=ctx.channel.name,
    message=f"Action completed! Status: {status}",
    reply_to_msg_id=ctx.message.id
)
```

3. Error Handling:
```python
try:
    result = await some_operation()
    await self.twitch_api.reply_to_message(
        channel_name=ctx.channel.name,
        message=f"Operation successful: {result}",
        reply_to_msg_id=ctx.message.id
    )
except Exception as e:
    await self.twitch_api.reply_to_message(
        channel_name=ctx.channel.name,
        message="An error occurred!",
        reply_to_msg_id=ctx.message.id
    )
```

### Important Notes

1. Always initialize TwitchAPI in your command class:
```python
def __init__(self, bot):
    self.twitch_api = TwitchAPI(bot)
    super().__init__(bot)
```

2. Don't use ctx.send() if you want to reply - use reply_to_message instead:
```python
# Instead of:
await ctx.send(f"@{user}, your message")

# Use:
await self.twitch_api.reply_to_message(
    channel_name=ctx.channel.name,
    message="your message",
    reply_to_msg_id=ctx.message.id
)
```

3. The reply will automatically be linked to the original message - no need to add username mentions

### Common Patterns

#### Command Response
```python
@self.bot.command(name="command")
async def command(ctx):
    await self.twitch_api.reply_to_message(
        channel_name=ctx.channel.name,
        message="Command executed!",
        reply_to_msg_id=ctx.message.id
    )
```

#### Status Updates
```python
@self.bot.command(name="status")
async def status(ctx):
    status = await get_status()
    await self.twitch_api.reply_to_message(
        channel_name=ctx.channel.name,
        message=f"Current status: {status}",
        reply_to_msg_id=ctx.message.id
    )
```

#### Error Messages
```python
try:
    # Your code here
    raise ValueError("Something went wrong")
except Exception as e:
    await self.twitch_api.reply_to_message(
        channel_name=ctx.channel.name,
        message="Error occurred during operation",
        reply_to_msg_id=ctx.message.id
    )
```

### Troubleshooting

1. If replies aren't working:
   - Check that TwitchAPI is properly initialized
   - Verify ctx.message.id exists
   - Ensure channel_name is correct

2. Common errors:
   - `AttributeError: 'Bot' object has no attribute 'reply_to_message'`
     - Solution: Make sure you're using self.twitch_api.reply_to_message, not self.bot.reply_to_message
   
   - `TypeError: reply_to_message() missing required argument`
     - Solution: Check that you're providing all required arguments (channel_name, message, reply_to_msg_id)

### Best Practices

1. Always use reply_to_message for direct responses to commands
2. Keep messages concise and clear
3. Include proper error handling
4. Use consistent message formatting
5. Don't include @ mentions in reply messages - they're redundant in replies

### Migration from ctx.send()

If you're updating old code:

```python
# Old code
await ctx.send(f"@{user}, your message")

# New code
await self.twitch_api.reply_to_message(
    channel_name=ctx.channel.name,
    message="your message",
    reply_to_msg_id=ctx.message.id
)
```

Remember to remove @ mentions when migrating to replies, as they're handled automatically by the reply system.
```