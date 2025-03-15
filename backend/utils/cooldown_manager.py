import time
import logging
from typing import Dict, Tuple, Optional, Callable, Set
import functools

logger = logging.getLogger('twitch_bot')

class CooldownManager:
    """Manages cooldowns for commands across the bot"""
    
    def __init__(self):
        # Add debug logging for initialization
        logger.debug("Initializing new CooldownManager instance")
        # Structure: {command_name: {user_id: last_used_timestamp}}
        self.cooldowns: Dict[str, Dict[str, float]] = {}
        # Global cooldowns: {command_name: last_used_timestamp}
        self.global_cooldowns: Dict[str, float] = {}
        # Default cooldown duration in seconds
        self.default_cooldown = 3
        # Default global cooldown duration in seconds
        self.default_global_cooldown = 1
        # Users who can bypass cooldowns
        self.privileged_users = []  # Only include specific users you want to bypass cooldowns
        
        # Track recent command responses to prevent chat spam
        # For global cooldown responses
        self.global_responses: Dict[str, float] = {}
        # For user-specific cooldown responses
        self.user_responses: Dict[str, Dict[str, float]] = {}
        
        # How long to wait before allowing another response (in seconds)
        self.global_response_cooldown = 30  # Longer cooldown for global messages (affects everyone)
        self.user_response_cooldown = 20    # Shorter cooldown for user-specific messages
        
        # Set to track users who have been notified about a command being on cooldown
        self.notified_users: Dict[str, Set[str]] = {}
        
        # Flag to enable/disable cooldowns globally
        self.cooldowns_enabled = True
    
    def check_cooldown(self, command_name: str, user_id: str, 
                      user_cooldown: Optional[int] = None,
                      global_cooldown: Optional[int] = None,
                      ctx=None) -> Tuple[bool, Optional[int], str]:
        """
        Check if a command is on cooldown for a user
        
        Args:
            command_name: Name of the command
            user_id: User ID or username
            user_cooldown: Command-specific cooldown in seconds (overrides default)
            global_cooldown: Command-specific global cooldown in seconds (overrides default)
            ctx: Command context (optional)
            
        Returns:
            Tuple of (is_on_cooldown, seconds_remaining, cooldown_type)
            cooldown_type is either 'user' or 'global'
        """
        # Add debug logging
        logger.debug(f"Checking cooldown in CooldownManager instance {id(self)}")
        logger.debug(f"Checking cooldown for command {command_name}, cooldowns_enabled: {self.cooldowns_enabled}")
        
        # If cooldowns are disabled globally, skip all checks
        if not self.cooldowns_enabled:
            logger.debug("Cooldowns are disabled globally, skipping checks")
            return False, None, ''
            
        # Get current time
        current_time = time.time()
        
        # Check if user is privileged (in the list or is a moderator)
        is_privileged = user_id.lower() in self.privileged_users
        
        # If context is provided, check if user is a moderator
        if ctx and hasattr(ctx.author, 'is_mod') and ctx.author.is_mod:
            is_privileged = True
        
        if is_privileged:
            return False, None, ''
        
        # Use provided cooldown values or defaults
        user_cd = user_cooldown if user_cooldown is not None else self.default_cooldown
        global_cd = global_cooldown if global_cooldown is not None else self.default_global_cooldown
        
        # Check global cooldown first
        if command_name in self.global_cooldowns:
            time_since_last = current_time - self.global_cooldowns[command_name]
            if time_since_last < global_cd:
                return True, round(global_cd - time_since_last), 'global'
        
        # Initialize command entry if not exists
        if command_name not in self.cooldowns:
            self.cooldowns[command_name] = {}
        
        # Check user-specific cooldown
        if user_id in self.cooldowns[command_name]:
            time_since_last = current_time - self.cooldowns[command_name][user_id]
            if time_since_last < user_cd:
                return True, round(user_cd - time_since_last), 'user'
        
        return False, None, ''
    
    def update_cooldown(self, command_name: str, user_id: str):
        """Update cooldown timestamps for a command and user"""
        # If cooldowns are disabled, don't update anything
        if not self.cooldowns_enabled:
            return
            
        current_time = time.time()
        
        # Skip updating for privileged users
        if user_id.lower() in self.privileged_users:
            return
            
        # Update global cooldown
        self.global_cooldowns[command_name] = current_time
        
        # Initialize command entry if not exists
        if command_name not in self.cooldowns:
            self.cooldowns[command_name] = {}
            
        # Update user-specific cooldown
        self.cooldowns[command_name][user_id] = current_time
    
    def enable_cooldowns(self):
        """Enable the cooldown system"""
        self.cooldowns_enabled = True
        return "Система кулдаунов включена"
    
    def disable_cooldowns(self):
        """Disable the cooldown system"""
        logger.debug(f"Disabling cooldowns in CooldownManager instance {id(self)}")
        self.cooldowns_enabled = False
        return "Система кулдаунов отключена"
    
    def toggle_cooldowns(self):
        """Toggle the cooldown system on/off"""
        self.cooldowns_enabled = not self.cooldowns_enabled
        status = "включена" if self.cooldowns_enabled else "отключена"
        return f"Система кулдаунов {status}"
    
    def get_cooldown_status(self):
        """Get the current status of the cooldown system"""
        status = "включена" if self.cooldowns_enabled else "отключена"
        return f"Система кулдаунов {status}"
    
    def should_send_cooldown_message(self, command_name: str, user_id: str, cooldown_type: str) -> bool:
        """
        Check if we should send a cooldown message to this user
        
        This prevents spamming the chat with cooldown messages when
        multiple users try to use the same command in a short time
        
        Args:
            command_name: Name of the command
            user_id: User ID or username
            cooldown_type: Type of cooldown ('global' or 'user')
            
        Returns:
            bool: True if we should send a message, False otherwise
        """
        current_time = time.time()
        
        # Initialize tracking structures if they don't exist
        if command_name not in self.notified_users:
            self.notified_users[command_name] = set()
            
        if command_name not in self.user_responses:
            self.user_responses[command_name] = {}
        
        # Handle global cooldown responses
        if cooldown_type == 'global':
            response_key = f"{command_name}_global"
            
            # Check if we've recently sent a global response for this command
            if response_key in self.global_responses:
                time_since_last = current_time - self.global_responses[response_key]
                
                # If we've recently sent a global response, don't send again
                if time_since_last < self.global_response_cooldown:
                    # Add user to notified set so they get a personal message next time
                    self.notified_users[command_name].add(user_id)
                    return False
            
            # Update the global response time
            self.global_responses[response_key] = current_time
            return True
            
        # Handle user-specific cooldown responses
        else:  # cooldown_type == 'user'
            # Check if this specific user has been notified recently
            if user_id in self.user_responses[command_name]:
                time_since_last = current_time - self.user_responses[command_name][user_id]
                
                # If we've recently sent a user-specific response to this user, don't send again
                if time_since_last < self.user_response_cooldown:
                    return False
            
            # Update the user response time
            self.user_responses[command_name][user_id] = current_time
            
            # Clean up user responses periodically
            if len(self.user_responses[command_name]) > 100:
                # Keep only the most recent entries
                self.user_responses[command_name] = {
                    k: v for k, v in sorted(
                        self.user_responses[command_name].items(), 
                        key=lambda item: item[1], 
                        reverse=True
                    )[:50]
                }
            
            return True
    
    def add_privileged_user(self, user_id: str):
        """Add a user to the privileged list"""
        self.privileged_users.append(user_id.lower())
        
    def remove_privileged_user(self, user_id: str):
        """Remove a user from the privileged list"""
        if user_id.lower() in self.privileged_users:
            self.privileged_users.remove(user_id.lower())

# Create a singleton instance
cooldown_manager = CooldownManager()

def with_cooldown(user_cooldown=None, global_cooldown=None, cooldown_message=None):
    """
    Decorator to add cooldown to a command
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # Get command name from the function or context
            command_name = func.__name__
            if hasattr(ctx, 'command') and hasattr(ctx.command, 'name'):
                command_name = ctx.command.name
            
            # Add debug logging
            logger.debug(f"Entering with_cooldown decorator for command {command_name}")
            
            # Get user ID from context
            user_id = ctx.author.name.lower()
            
            # Check if cooldowns are disabled globally
            logger.debug(f"Checking cooldowns_enabled in decorator: {cooldown_manager.cooldowns_enabled}")
            if not cooldown_manager.cooldowns_enabled:
                logger.debug(f"Cooldowns are disabled, executing command {command_name} directly")
                # Skip cooldown check and execute the command
                return await func(ctx, *args, **kwargs)
                
            # Check if command is on cooldown
            is_on_cooldown, seconds_remaining, cooldown_type = cooldown_manager.check_cooldown(
                command_name, user_id, user_cooldown, global_cooldown, ctx
            )
            
            if is_on_cooldown:
                # Format the cooldown message
                if cooldown_message:
                    message = cooldown_message
                else:
                    if cooldown_type == 'global':
                        message = f"эта команда будет доступна через {seconds_remaining} секунд!"
                    else:
                        message = f"подожди еще {seconds_remaining} секунд перед тем, как снова использовать эту команду!"
                
                # Check if we should send a cooldown message
                if cooldown_manager.should_send_cooldown_message(command_name, user_id, cooldown_type):
                    # Get the parent message ID from the context if this is a reply
                    reply_to_msg_id = ctx.message.tags.get('reply-parent-msg-id')
                    
                    if reply_to_msg_id and hasattr(ctx.channel, 'name'):
                        try:
                            # Use the reply_to_message method if we have a parent message ID
                            await ctx.bot.api.reply_to_message(ctx.channel.name, f"@{user_id}, {message}", reply_to_msg_id)
                        except Exception as e:
                            logger.error(f"Failed to send reply: {str(e)}")
                            # Fallback to regular message if reply not possible
                            await ctx.send(f"@{user_id}, {message}")
                    else:
                        # Fallback to regular message if reply not possible
                        await ctx.send(f"@{user_id}, {message}")
                return
            
            # Update cooldown and execute the command
            cooldown_manager.update_cooldown(command_name, user_id)
            return await func(ctx, *args, **kwargs)
        
        return wrapper
    return decorator 

# Алиас для обратной совместимости с переименованием аргументов
def cooldown(user_cd=None, global_cd=None, cooldown_message=None):
    """
    Алиас для with_cooldown с поддержкой старых имен аргументов
    """
    return with_cooldown(
        user_cooldown=user_cd,
        global_cooldown=global_cd,
        cooldown_message=cooldown_message
    ) 