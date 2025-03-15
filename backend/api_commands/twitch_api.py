import logging
import requests
import os
from typing import Optional
from functools import wraps

logger = logging.getLogger('twitch_bot')

def handle_api_errors(func):
    """Декоратор для обработки ошибок API"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except requests.RequestException as e:
            logger.error(f"API request failed in {func.__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.exception("Full traceback:")
            return None
    return wrapper

class TwitchAPI:
    def __init__(self, bot):
        self.bot = bot
        self.headers = {
            'Authorization': f'Bearer {self.bot._access_token}',
            'Client-Id': self.bot.client_id,
            'Content-Type': 'application/json'
        }

    @handle_api_errors
    async def timeout_user(self, 
                          broadcaster_id: str, 
                          target_user_id: str, 
                          duration: int, 
                          reason: Optional[str] = None) -> bool:
        """
        Timeout (mute) a user in the channel
        
        Args:
            broadcaster_id (str): ID of the channel broadcaster
            target_user_id (str): ID of the user to timeout
            duration (int): Timeout duration in seconds
            reason (str, optional): Reason for the timeout
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"https://api.twitch.tv/helix/moderation/bans"
        params = {
            'broadcaster_id': broadcaster_id,
            'moderator_id': self.bot.user_id
        }
        
        json_data = {
            'data': {
                'user_id': target_user_id,
                'duration': duration,
                'reason': reason or 'No reason provided'
            }
        }
        
        response = requests.post(
            url, 
            headers=self.headers, 
            params=params,
            json=json_data
        )
        
        success = response.status_code == 200
        if success:
            logger.info(f"Successfully timed out user {target_user_id} for {duration} seconds")
        return success

    @handle_api_errors
    async def get_user_id(self, username: str) -> Optional[str]:
        """
        Get user ID from username
        
        Args:
            username (str): Twitch username
            
        Returns:
            Optional[str]: User ID if found, None otherwise
        """
        url = f"https://api.twitch.tv/helix/users"
        response = requests.get(
            url, 
            headers=self.headers, 
            params={'login': username.lower()}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]['id']
        return None

    @handle_api_errors
    async def get_username(self, user_id: str) -> Optional[str]:
        """
        Get username from user ID
        
        Args:
            user_id (str): Twitch user ID
            
        Returns:
            Optional[str]: Username if found, None otherwise
        """
        url = f"https://api.twitch.tv/helix/users"
        response = requests.get(
            url, 
            headers=self.headers, 
            params={'id': user_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]['login']
        return None

    async def reply_to_message(self, channel_name: str, message: str, reply_to_msg_id: Optional[str] = None) -> bool:
        """
        Send a message or reply to a specific message in the channel
        
        Args:
            channel_name (str): Name of the channel to send message to
            message (str): Message content to send
            reply_to_msg_id (Optional[str]): ID of the message to reply to
            
        Returns:
            bool: True if successful, False otherwise
        """
        channel = channel_name.lstrip('#')
        
        try:
            if reply_to_msg_id and hasattr(self.bot, '_connection') and self.bot._connection:
                irc_command = f"@reply-parent-msg-id={reply_to_msg_id} PRIVMSG #{channel} :{message}"
                await self.bot._connection.send(irc_command)
                logger.info(f"Sent reply to message {reply_to_msg_id} in channel {channel}")
                return True
            
            # Отправка обычного сообщения
            for ch in self.bot.connected_channels:
                if ch.name.lower() == channel.lower():
                    await ch.send(message)
                    logger.info(f"Sent message to channel {channel}")
                    return True
            
            logger.error(f"Channel {channel} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False 