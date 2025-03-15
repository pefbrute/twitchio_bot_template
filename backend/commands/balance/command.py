import logging
import sys
import os
from commands import BotCommand

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

logger = logging.getLogger('twitch_bot')

class BalanceCommand(BotCommand):
    def __init__(self, bot):
        # Initialize attributes before calling parent constructor
        self.base_commands = None
        
        # Call parent constructor
        super().__init__(bot)
        
        # Store bot reference
        self.bot = bot
        
        try:
            # Now initialize the command groups
            from .commands.base_commands import BaseBalanceCommands
            
            self.base_commands = BaseBalanceCommands(bot)
            
            # Initialize username filter if it doesn't exist
            if not hasattr(bot, 'username_filter'):
                from utils.username_filter import username_filter
                bot.username_filter = username_filter
            
            # Manually register the commands
            self.register_commands()
            
        except Exception as e:
            logger.error(f"Error initializing BalanceCommand: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def register_commands(self):
        """Register all balance-related commands"""
        try:
            # Only register commands if they've been initialized
            if self.base_commands:
                self.base_commands.register()
                logger.info("Base balance commands registered")
            
            # Log all registered commands
            command_names = list(self.bot.commands.keys())
            logger.info(f"All registered commands: {command_names}")
            
            logger.info("Registered all balance-related commands")
        except Exception as e:
            logger.error(f"Error registering commands: {str(e)}")
            import traceback
            logger.error(traceback.format_exc()) 