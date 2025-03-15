import logging
import random
import asyncio
import time
from twitchio.ext import commands
from commands import BotCommand
from utils.word_filter import word_filter

logger = logging.getLogger('twitch_bot')

class GiftCommand(BotCommand):
    def __init__(self, bot):
        # Track recent chatters for random selection
        self.recent_chatters = set()
        self.chatters_lock = asyncio.Lock()
        
        # List of possible gifts
        self.gifts = [
            "герпес",
            "подписку на спам",
            "чашку с дыркой",
            "тренболон",
            "билет на вчерашний концерт",
            "ВИЧ",
            "чай с печеньем",
            "молоко с печеньем",
            "шоколад с молоком",
            "шоколад с чаем"
        ]
        
        # 7TV emotes to use instead of emoji
        self.emotes = [
            "BESPLATNO",
            "PapichSng",
            "sng",
            "sDR"
        ]
        
        # Bot responses when someone tries to gift the bot
        self.bot_responses = [
            "спасибо за подарок, но я бот и не могу его принять! Может, подаришь его кому-то другому?",
            "это очень мило, но у меня нет физического тела, чтобы принять это!",
            "ценю твою щедрость, но я живу в мире кода и алгоритмов!",
            "благодарю, но лучше сделай подарок живому человеку!"
        ]
        
        # Add global cooldown tracking
        self.last_global_gift = 0
        self.global_gift_cooldown = 10  # 10 seconds global cooldown
        
        # Call parent constructor to register commands
        super().__init__(bot)
        
    def register_commands(self):
        """Register gift command with the bot"""
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        @self.bot.command(name="подарить")
        async def gift_command(ctx: commands.Context):
            """Command to 'gift' someone with a random item"""
            # Check global cooldown first
            current_time = time.time()
            if current_time - self.last_global_gift < self.global_gift_cooldown:
                return
            
            user = ctx.author.name
            message_content = ctx.message.content
            
            # Check for reply first
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            
            # Initialize target and gift
            target_user = None
            gift = None
            
            if reply_to_user:
                # Reply format - check for custom gift
                target_user = reply_to_user
                message_parts = message_content.split('!подарить', 1)
                if len(message_parts) > 1 and message_parts[1].strip():
                    # Use the text after !подарить as the gift
                    gift = message_parts[1].strip()
                else:
                    # No custom gift specified, use random
                    gift = random.choice(self.gifts)
                logger.info(f"Reply detected: {user} is gifting {target_user} with {gift}")
            else:
                # Not a reply - parse the command for custom gift and target
                if len(message_content.split()) > 1:
                    # Find if there's an @ mentioned to determine username
                    message_after_command = message_content.split('!подарить', 1)[1].strip()
                    
                    # Try to find a username (with @ symbol)
                    at_position = message_after_command.rfind('@')
                    
                    if at_position != -1:
                        # We found a username with @ - extract it and the gift
                        username_part = message_after_command[at_position+1:].strip().split()[0]
                        gift_part = message_after_command[:at_position].strip()
                        
                        target_user = username_part
                        if gift_part:
                            gift = gift_part
                        else:
                            gift = random.choice(self.gifts)
                        
                        logger.info(f"Found format with @: gift='{gift}', target='{target_user}'")
                    else:
                        # No @ found - check if the last word could be a username
                        words = message_after_command.split()
                        if len(words) > 1:
                            # Assume last word is username, rest is gift
                            target_user = words[-1]
                            gift = ' '.join(words[:-1])
                            logger.info(f"Parsed as last word username: gift='{gift}', target='{target_user}'")
                        else:
                            # Just one word - assume it's the username
                            target_user = words[0]
                            gift = random.choice(self.gifts)
                            logger.info(f"Single word command: random gift, target='{target_user}'")
                
                # If we still don't have a target, pick a random one
                if not target_user:
                    async with self.chatters_lock:
                        potential_targets = [
                            name for name in self.recent_chatters 
                            if name.lower() != user.lower() and 
                               name.lower() != self.bot.bot_username.lower()
                        ]
                    
                    if potential_targets:
                        target_user = random.choice(potential_targets)
                    else:
                        default_targets = ["телезрителю", "стримеру", "модератору", "случайному прохожему"]
                        target_user = random.choice(default_targets)
                    
                    gift = random.choice(self.gifts) if not gift else gift
                    logger.info(f"Random target: {user} is gifting {target_user} with {gift}")
            
            # Check if the target is the bot itself (in any format)
            if target_user.lower() == self.bot.bot_username.lower():
                random_response = random.choice(self.bot_responses)
                await ctx.send(f"@{user}, {random_response}")
                logger.info(f"User {user} tried to gift the bot")
                return
            
            # Select a random 7TV emote
            random_emote = random.choice(self.emotes)
            
            # Create the message first
            message = f"@{user} подарил @{target_user} {gift} {random_emote}"
            
            # Check if it's safe to send
            is_safe, filtered_message = word_filter.filter_message(message)
            
            if is_safe:
                await ctx.send(message)
                logger.info(f"User {user} gifted {target_user} with {gift} using emote {random_emote}")
            else:
                # Try with a different gift if the current one has issues
                safe_gifts = ["подарок", "сюрприз", "презент"]
                safe_gift = random.choice(safe_gifts)
                safe_message = f"@{user} подарил @{target_user} {safe_gift} {random_emote}"
                
                # Check again to be extra safe
                if word_filter.filter_message(safe_message)[0]:
                    await ctx.send(safe_message)
                    logger.info(f"Used safe gift alternative due to banned phrase in original gift")
                else:
                    logger.warning(f"Could not send gift message due to banned phrases: {message}")
            
            # Update global cooldown timestamp after successful gift
            self.last_global_gift = time.time()
    
    async def on_message(self, message):
        """Process messages to track chatters for the gift command"""
        if message.author is not None:
            username = message.author.name
            async with self.chatters_lock:
                self.recent_chatters.add(username) 