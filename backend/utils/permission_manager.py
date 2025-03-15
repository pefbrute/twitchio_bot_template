import logging
import functools
from typing import List, Callable, Set

logger = logging.getLogger('twitch_bot')

class PermissionManager:
    """Simplified permission manager for commands"""
    
    def __init__(self):
        # Dictionary mapping command names to sets of specific users
        self.command_specific_users: dict = {}
        
        # Dictionary mapping command names to mod-only status
        self.mod_only_commands: Set[str] = set()
        
    def add_specific_user(self, command_name: str, username: str):
        """Add a specific user who can use a command"""
        if command_name not in self.command_specific_users:
            self.command_specific_users[command_name] = set()
            
        self.command_specific_users[command_name].add(username.lower())
        logger.info(f"Added {username} to allowed users for command {command_name}")
        
    def remove_specific_user(self, command_name: str, username: str):
        """Remove a specific user from being able to use a command"""
        if command_name in self.command_specific_users and username.lower() in self.command_specific_users[command_name]:
            self.command_specific_users[command_name].remove(username.lower())
            logger.info(f"Removed {username} from allowed users for command {command_name}")
    
    def set_mod_only(self, command_name: str, is_mod_only: bool = True):
        """Set whether a command is mod-only"""
        if is_mod_only:
            self.mod_only_commands.add(command_name)
            logger.info(f"Set command {command_name} to mod-only")
        elif command_name in self.mod_only_commands:
            self.mod_only_commands.remove(command_name)
            logger.info(f"Removed mod-only restriction from command {command_name}")
            
    def check_permission(self, command_name: str, username: str, is_mod: bool = False, is_broadcaster: bool = False) -> bool:
        """
        Check if a user has permission to use a command
        
        Args:
            command_name: Name of the command
            username: Username of the user
            is_mod: Whether the user is a moderator
            is_broadcaster: Whether the user is the broadcaster
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        username = username.lower()
        
        # Broadcaster always has permission
        if is_broadcaster:
            return True
            
        # Check if user is in specific users list
        if command_name in self.command_specific_users and username in self.command_specific_users[command_name]:
            return True
            
        # Check if command is mod-only
        if command_name in self.mod_only_commands:
            return is_mod
            
        # If not mod-only and not in specific users, everyone can use it
        return True

# Create a singleton instance
permission_manager = PermissionManager()

def mod_only(func=None, specific_users=None):
    """
    Decorator to make a command mod-only with optional specific users
    
    Can be used as @mod_only or @mod_only(specific_users=["user1", "user2"])
    """
    if func is None:
        # Called with arguments: @mod_only(specific_users=...)
        return lambda f: mod_only(f, specific_users=specific_users)
    
    # Called without arguments: @mod_only
    @functools.wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        command_name = ctx.command.name
        username = ctx.author.name.lower()
        
        # Check if user is mod or broadcaster
        is_mod = ctx.author.is_mod if hasattr(ctx.author, 'is_mod') else False
        is_broadcaster = username == ctx.channel.name.lower()
        
        # Set command as mod-only
        permission_manager.set_mod_only(command_name)
        
        # Add specific users if provided
        if specific_users:
            for user in specific_users:
                permission_manager.add_specific_user(command_name, user)
                
        # Check permission
        has_permission = permission_manager.check_permission(
            command_name, username, is_mod, is_broadcaster
        )
        
        if not has_permission:
            logger.info(f"User {username} tried to use {command_name} but doesn't have permission")
            # Optionally send a message to the user
            # await ctx.send(f"@{username}, you don't have permission to use this command")
            return
            
        # User has permission, execute the command
        return await func(ctx, *args, **kwargs)
            
    return wrapper 