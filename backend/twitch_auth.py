import os
import logging
import requests
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_auth')

# Load environment variables from .env file
load_dotenv()

# Auth settings
BOT_USERNAME = os.getenv('BOT_USERNAME')
CHANNEL_NAME = os.getenv('CHANNEL_NAME')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

def refresh_oauth_token_sync():
    """Synchronous version of refresh_oauth_token to use before bot initialization"""
    global ACCESS_TOKEN, REFRESH_TOKEN
    logger.info("Attempting to refresh OAuth token synchronously...")
    
    try:
        # Prepare the request to refresh the token
        refresh_url = "https://id.twitch.tv/oauth2/token"
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
        
        # Make the request
        response = requests.post(refresh_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        
        # Update the tokens
        ACCESS_TOKEN = token_data['access_token']
        REFRESH_TOKEN = token_data['refresh_token']
        
        # Update the .env file
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(dotenv_path, 'ACCESS_TOKEN', ACCESS_TOKEN)
        set_key(dotenv_path, 'REFRESH_TOKEN', REFRESH_TOKEN)
        
        logger.info("OAuth token refreshed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to refresh OAuth token: {str(e)}")
        return False

def validate_token_sync():
    """Synchronous version of validate_token to use before bot initialization"""
    global ACCESS_TOKEN
    try:
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Client-Id': CLIENT_ID
        }
        response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Token validated successfully. User: {data.get('login')}, expires in: {data.get('expires_in')} seconds")
            # If token is close to expiry (less than 1 hour), refresh it
            if data.get('expires_in', 0) < 3600:
                logger.info("Token is close to expiry, refreshing...")
                refresh_oauth_token_sync()
            return True
        else:
            logger.warning(f"Token validation failed: {response.status_code}")
            return refresh_oauth_token_sync()
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return refresh_oauth_token_sync()

def get_auth_credentials():
    """Return the current auth credentials to be used by the bot"""
    return {
        'bot_username': BOT_USERNAME,
        'channel_name': CHANNEL_NAME,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'access_token': ACCESS_TOKEN,
        'refresh_token': REFRESH_TOKEN
    } 