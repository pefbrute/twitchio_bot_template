import os
import logging
import requests
from openai import OpenAI
from twitchio.ext import commands
from dotenv import set_key, load_dotenv
from utils.word_filter import word_filter
from api_commands.twitch_api import TwitchAPI
from utils.cooldown_manager import cooldown_manager
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_bot')

load_dotenv()

# Load OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class SpoilerBot(commands.Bot):
    def __init__(self, auth_creds):
        # Get auth credentials
        self.bot_username = auth_creds['bot_username']
        self.channel_name = auth_creds['channel_name']
        self.client_id = auth_creds['client_id']
        self.client_secret = auth_creds['client_secret']
        self._access_token = auth_creds['access_token']
        self._refresh_token = auth_creds['refresh_token']
        
        # Initialize our Bot with our access token, prefix and a list of channels to join on boot
        logger.info(f"Initializing bot with username: {self.bot_username}")
        logger.info(f"Connecting to channel: {self.channel_name}")
        
        # Initialize message listeners list
        self.message_listeners = []
        
        # Add whisper capability
        self.can_send_whispers = True
        
        # Set up cooldown manager privileged users
        cooldown_manager.privileged_users.extend(["Lisiy_tapocheck"])  # Only include specific users who should bypass cooldowns
        
        # Initialize token refresh task
        self.token_check_task = None
        
        # Call the parent constructor to initialize the bot
        super().__init__(
            token=self._access_token,
            prefix='!',
            initial_channels=[self.channel_name]
        )
        
        # Initialize API commands after parent class initialization
        self.api = TwitchAPI(self)
        
        # Start token refresh task
        self.token_check_task = self.loop.create_task(self.token_check_loop())
        
    async def token_check_loop(self):
        """Periodically check and refresh token if needed"""
        while True:
            try:
                await self.validate_token()
                # Check every 30 minutes
                await asyncio.sleep(1800)
            except Exception as e:
                logger.error(f"Error in token check loop: {str(e)}")
                # If there's an error, wait 5 minutes before retrying
                await asyncio.sleep(300)

    async def validate_token(self):
        """Validate the current token and refresh if needed"""
        try:
            headers = {
                'Authorization': f'Bearer {self._access_token}',
                'Client-Id': self.client_id
            }
            response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Token validated successfully. User: {data.get('login')}, expires in: {data.get('expires_in')} seconds")
                # If token expires in less than 1 hour, refresh it
                if data.get('expires_in', 0) < 3600:
                    logger.info("Token is close to expiry, refreshing...")
                    success = await self.refresh_oauth_token()
                    if success:
                        # Update the token in the bot's connection
                        self._connection.token = self._access_token
            else:
                logger.warning(f"Token validation failed: {response.status_code}")
                success = await self.refresh_oauth_token()
                if success:
                    # Update the token in the bot's connection
                    self._connection.token = self._access_token
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            await self.refresh_oauth_token()

    async def event_ready(self):
        """Called once when the bot goes online."""
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")
        
        # Validate token on startup
        await self.validate_token()

    async def event_message(self, message):
        """Called once when the bot goes online."""
        # Add debug logging
        logger.info(f"Received message: {message.content}")
        logger.info(f"Message author: {message.author.name if message.author else 'None'}")
        logger.info(f"Message tags: {message.tags}")
        
        # Ignore messages from the bot itself
        if message.author is None or message.author.name.lower() == self.bot_username.lower():
            return
            
        # Process commands - check if message contains command anywhere
        if '!' in message.content:
            try:
                # Extract command name
                parts = message.content.split('!')
                if len(parts) > 1:
                    command_name = parts[1].strip().split()[0]  # Get first word after !
                    logger.info(f"Found command: {command_name}")
                    
                    # Get command from commands dict if it exists
                    command = self.commands.get(command_name.lower())
                    if command:
                        logger.info(f"Executing command: {command_name}")
                        ctx = await self.get_context(message)
                        await command(ctx)
                    else:
                        logger.info(f"Command not found: {command_name}")
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                logger.exception("Full traceback:")
        
        # Call all registered message listeners
        for listener in self.message_listeners:
            try:
                await listener(message)
            except Exception as e:
                logger.error(f"Error in message listener: {str(e)}")

    async def refresh_oauth_token(self):
        """Refresh the OAuth token using the refresh token"""
        try:
            refresh_url = "https://id.twitch.tv/oauth2/token"
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self._refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(refresh_url, data=payload)
            response.raise_for_status()
            token_data = response.json()
            
            # Update the tokens
            self._access_token = token_data['access_token']
            self._refresh_token = token_data['refresh_token']
            
            # Update the .env file
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            set_key(dotenv_path, 'ACCESS_TOKEN', self._access_token)
            set_key(dotenv_path, 'REFRESH_TOKEN', self._refresh_token)
            
            # Update the token in the bot
            self._connection.token = self._access_token
            
            logger.info("OAuth token refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {str(e)}")
            return False 

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
            # Optionally send a notification to the channel owner through DM or other means
            return False 

    async def send_whisper(self, user, message):
        """Send a whisper (private message) to a user"""
        try:
            url = f'https://api.twitch.tv/helix/whispers'
            
            # Добавляем параметры from_user_id и to_user_id в URL
            params = {
                'from_user_id': self.user_id,
                'to_user_id': user.id
            }
            
            headers = {
                'Authorization': f'Bearer {self._access_token}',
                'Client-Id': self.client_id,
                'Content-Type': 'application/json'
            }
            
            # Отправляем сообщение в теле запроса как JSON
            data = {
                'message': message
            }
            
            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=data
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully sent whisper to {user.name}")
                return True
            else:
                logger.error(f"Failed to send whisper: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending whisper: {str(e)}")
            return False 