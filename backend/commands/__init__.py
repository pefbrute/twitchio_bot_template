import logging
from twitchio.ext import commands
from utils.word_filter import word_filter

logger = logging.getLogger('twitch_bot')

class BotCommand:
    """Base class for all bot commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.register_commands()
        
    def register_commands(self):
        """Register all commands with the bot. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement register_commands()")
        
    async def send_safe(self, ctx, message):
        """Send a message after checking it against the word filter"""
        is_safe, filtered_message = word_filter.filter_message(message)
        
        if is_safe:
            # Message is safe to send
            await ctx.send(message)
            return True
        else:
            # Message contains banned phrases - log it but don't send
            logger.warning(f"Prevented sending message with banned phrase: {message}")
            return False 