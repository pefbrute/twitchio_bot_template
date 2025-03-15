import logging
import random
import asyncio
from twitchio.ext import commands
from commands import BotCommand
from utils.username_filter import username_filter

logger = logging.getLogger('twitch_bot')

class TrustCommand(BotCommand):
    def __init__(self, bot):
        # Track recent chatters for random selection
        self.recent_chatters = set()
        self.chatters_lock = asyncio.Lock()
        
        # Bot defense responses when someone tries to target the bot
        self.bot_defense_responses = [
            "ты просишь меня о доверии? Я бот, я никому не доверяю!",
            "доверие к ботам не приводит ни к чему хорошему, поверь мне!",
            "между нами не может быть доверия, только байты и алгоритмы!",
            "доверие - это для людей, а я - просто набор кода!"
        ]
        
        # Call parent constructor to register commands
        super().__init__(bot)
        
    def register_commands(self):
        """Register trust command with the bot"""
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        #@self.bot.command(name="трастни")
        async def trust_command(ctx: commands.Context):
            """Command to ask someone to trust you in a brotherly way"""
            user = ctx.author.name
            message_content = ctx.message.content
            
            # Check if the requesting user's name is safe
            is_user_safe, user_reason = username_filter.is_safe(user)
            if not is_user_safe:
                logger.warning(f"Blocked trust command from user with unsafe name: {user} ({user_reason})")
                return
            
            # Initialize target
            target_user = None
            
            # Check for reply first
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            
            if reply_to_user:
                # Check if replied-to username is safe
                is_target_safe, target_reason = username_filter.is_safe(reply_to_user)
                if not is_target_safe:
                    logger.warning(f"Blocked trust command targeting unsafe username in reply: {reply_to_user} ({target_reason})")
                    return
                target_user = reply_to_user
                logger.info(f"Reply detected: {user} is asking {target_user} to trust them")
            else:
                # Not a reply - parse the command for target
                parts = message_content.split()
                
                if len(parts) > 1:
                    # Check if a target user was specified
                    target_mention = parts[1]
                    
                    # Remove @ symbol if present
                    if target_mention.startswith('@'):
                        target_mention = target_mention[1:]
                        
                    # Check if specified target username is safe
                    is_target_safe, target_reason = username_filter.is_safe(target_mention)
                    if not is_target_safe:
                        logger.warning(f"Blocked trust command targeting unsafe username: {target_mention} ({target_reason})")
                        return
                        
                    target_user = target_mention
                    logger.info(f"Direct target: {user} is asking {target_user} to trust them")
                
                # If we still don't have a target, pick a random one
                if not target_user:
                    async with self.chatters_lock:
                        # Filter out unsafe usernames from potential targets
                        potential_targets = [
                            name for name in self.recent_chatters 
                            if name.lower() != user.lower() and 
                               name.lower() != self.bot.bot_username.lower() and
                               username_filter.is_safe(name)[0]  # Only include safe usernames
                        ]
                    
                    if potential_targets:
                        target_user = random.choice(potential_targets)
                    else:
                        default_targets = ["телезрителя", "стримера", "модератора", "случайного прохожего"]
                        target_user = random.choice(default_targets)
                    
                    logger.info(f"Random target: {user} is asking {target_user} to trust them")
            
            # Check if the target is the bot itself
            if target_user.lower() == self.bot.bot_username.lower():
                random_response = random.choice(self.bot_defense_responses)
                await ctx.send(f"@{user}, {random_response}")
                logger.info(f"User {user} tried to ask the bot to trust them")
                return
            
            # Send the trust message
            await ctx.send(f"@{target_user} трастни @{user} по-братски, пж")
            logger.info(f"User {user} asked {target_user} to trust them")
    
    async def on_message(self, message):
        """Process messages to track chatters for the trust command"""
        if message.author is not None:
            username = message.author.name
            async with self.chatters_lock:
                self.recent_chatters.add(username) 