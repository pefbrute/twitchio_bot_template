import logging
from twitchio.ext import commands

logger = logging.getLogger('twitch_bot')

class BotCommand:
    """Base class for all bot commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.register_commands()
        
    def register_commands(self):
        """Register all commands with the bot. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement register_commands()")