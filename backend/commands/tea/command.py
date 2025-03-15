import logging
import random
import asyncio
import time
from twitchio.ext import commands
from commands import BotCommand
from utils.username_filter import username_filter

logger = logging.getLogger('twitch_bot')

class TeaCommand(BotCommand):
    def __init__(self, bot):
        # Track recent chatters for random selection
        self.recent_chatters = set()
        self.chatters_lock = asyncio.Lock()
        # Add cooldown tracking
        self.last_use = 0
        self.cooldown = 10  # seconds
        
        # Call parent constructor to register commands
        super().__init__(bot)
        
    def register_commands(self):
        """Register tea command with the bot"""
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        @self.bot.command(name="чай")
        async def tea_command(ctx: commands.Context):
            """Command to invite someone for tea"""
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_use < self.cooldown:
                return
            
            # Update last use time
            self.last_use = current_time
            
            user = ctx.author.name
            message_content = ctx.message.content
            
            # Check if this is a reply (starts with @username)
            is_reply = False
            target_user = None
            
            # Get reply information from tags
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            
            if reply_to_user:
                is_reply = True
                target_user = reply_to_user
                
                # Check if the reply is to the bot itself
                if target_user.lower() == self.bot.bot_username.lower():
                    await ctx.send(f"@{user}, спасибо за приглашение, но я предпочитаю электричество!")
                    logger.info(f"User {user} tried to invite the bot for tea")
                    return
                
                # Check if the target username is safe
                is_safe, reason = username_filter.is_safe(target_user)
                if not is_safe:
                    await ctx.send(f"{user}, бот не может пригласить этого пользователя на чай.")
                    logger.info(f"Skipping tea invite for unsafe username: {target_user} (Reason: {reason})")
                    return
                
                logger.info(f"Reply detected: {user} is inviting {target_user} for tea")
            
            # Not a reply, check for direct username specification
            elif len(message_content.split()) > 1:
                # Get the username from the command arguments
                target_user = message_content.split(None, 1)[1]
                
                # Remove @ symbol if present
                if target_user.startswith('@'):
                    target_user = target_user[1:]
                
                # Check if the target is the bot itself
                if target_user.lower() == self.bot.bot_username.lower():
                    await ctx.send(f"@{user}, спасибо за приглашение, но я предпочитаю электричество!")
                    logger.info(f"User {user} tried to invite the bot for tea")
                    return
                
                # Check if the target username is safe
                is_safe, reason = username_filter.is_safe(target_user)
                if not is_safe:
                    await ctx.send(f"{user}, пососи GAGAGA")
                    logger.info(f"Skipping tea invite for unsafe username: {target_user} (Reason: {reason})")
                    return
                
                logger.info(f"Direct target: {user} is inviting {target_user} for tea")
            
            # No specific target - choose a random user
            else:
                async with self.chatters_lock:
                    # Create a list of chatters excluding the command user and the bot
                    potential_targets = [
                        name for name in self.recent_chatters 
                        if name.lower() != user.lower() and 
                           name.lower() != self.bot.bot_username.lower()
                    ]
                
                if potential_targets:
                    # Filter out unsafe usernames
                    safe_targets = [
                        name for name in potential_targets 
                        if username_filter.is_safe(name)[0]
                    ]
                    
                    if safe_targets:
                        target_user = random.choice(safe_targets)
                        logger.info(f"Random target: {user} is inviting {target_user} for tea")
                    else:
                        # If no safe targets available, use default names
                        default_targets = ["телезрителя", "стримера", "модератора", "случайного прохожего"]
                        target_user = random.choice(default_targets)
                        logger.info(f"No safe targets available, using default: {target_user}")
                else:
                    # If no other users have chatted, use default names
                    default_targets = ["телезрителя", "стримера", "модератора", "случайного прохожего"]
                    target_user = random.choice(default_targets)
                    logger.info(f"Default target: {user} is inviting {target_user} for tea")
            
            # Send the tea invitation message
            await ctx.send(f"@{user} пригласил тебя @{target_user} на чай Chai")
            logger.info(f"User {user} invited {target_user} for tea")
    
    async def on_message(self, message):
        """Process messages to track chatters for the tea command"""
        if message.author is not None:
            username = message.author.name
            async with self.chatters_lock:
                self.recent_chatters.add(username) 