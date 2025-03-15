import os
import logging
import importlib
import pkgutil
from dotenv import load_dotenv
import commands
from bot import SpoilerBot
from twitch_auth import validate_token_sync, get_auth_credentials
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_bot')

def load_credentials():
    """Load authentication credentials from environment variables"""
    load_dotenv()
    
    return {
        'bot_username': os.getenv('BOT_USERNAME'),
        'channel_name': os.getenv('CHANNEL_NAME'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'access_token': os.getenv('ACCESS_TOKEN'),
        'refresh_token': os.getenv('REFRESH_TOKEN')
    }

def load_commands(bot):
    """Dynamically load all command modules"""
    logger.info("Loading command modules...")
    commands_dir = os.path.join(os.path.dirname(__file__), 'commands')
    
    # Iterate through all command directories
    for item in os.listdir(commands_dir):
        command_dir = os.path.join(commands_dir, item)
        if os.path.isdir(command_dir) and not item.startswith('__'):
            # Look for command.py in each directory
            command_file = os.path.join(command_dir, 'command.py')
            if os.path.exists(command_file):
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(
                        f"commands.{item}.command", command_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find the command class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, commands.BotCommand) and 
                            attr != commands.BotCommand):
                            # Instantiate the command handler
                            attr(bot)
                            logger.info(f"Loaded command module: {item}")
                            break
                except Exception as e:
                    logger.error(f"Failed to load command module {item}: {str(e)}")

def main():
    # Validate and refresh token before starting the bot
    logger.info("Validating Twitch OAuth token...")
    if validate_token_sync():
        logger.info("Token is valid or has been refreshed successfully")
        # Get the updated credentials after potential refresh
        auth_creds = get_auth_credentials()
    else:
        logger.error("Failed to validate or refresh token. Please run twitch_oauth_setup.py to get new tokens.")
        return
    
    # Initialize the bot with the validated credentials
    bot = SpoilerBot(auth_creds)
    
    # Load command modules
    load_commands(bot)
    
    # Start the bot
    logger.info("Starting bot...")
    bot.run()

if __name__ == "__main__":
    main()
