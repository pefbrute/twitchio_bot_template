import logging
import random
import asyncio
import time
from twitchio.ext import commands
from commands import BotCommand
from utils.word_filter import word_filter
from utils.username_filter import username_filter

logger = logging.getLogger('twitch_bot')

class InfectCommand(BotCommand):
    def __init__(self, bot):
        # Track recent chatters for random selection
        self.recent_chatters = set()
        self.chatters_lock = asyncio.Lock()
        
        # List of possible diseases
        self.diseases = [
            "чумой",
            "гриппом",
            "насморком",
            "лихорадкой",
            "ковидом",
            "простудой",
            "вирусом",
            "аллергией",
            "мигренью",
            "бессонницей",
            "ленью",
            "депрессией",
            "кринжем",
            "мемами",
            "зависимостью от твича",
            "любовью к аниме",
            "синдромом донатера"
        ]
        
        # List of emojis to use at the end of messages
        self.emojis = ["xdd", "XDD"]
        
        # Bot defense responses when someone tries to infect the bot
        self.bot_defense_responses = [
            "пхаха, получи заряд мощного вича и гриппа, чел",
            "чел, ты ща глупость сделал"
        ]
        
        # Add global cooldown tracking
        self.last_global_infect = 0
        self.global_infect_cooldown = 10  # 10 seconds global cooldown
        
        # Call parent constructor to register commands
        super().__init__(bot)
        
    def register_commands(self):
        """Register infect command with the bot"""
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        @self.bot.command(name="заразить")
        async def infect_command(ctx: commands.Context):
            """Command to 'infect' someone with a random disease"""
            # Check global cooldown first
            current_time = time.time()
            if current_time - self.last_global_infect < self.global_infect_cooldown:
                return
            
            user = ctx.author.name
            message_content = ctx.message.content
            
            # Check for reply first
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            
            # Initialize target and disease
            target_user = None
            disease = None
            
            if reply_to_user:
                # Reply format - check for custom disease
                target_user = reply_to_user
                message_after_command = message_content.split('!заразить', 1)[1].strip()
                
                if message_after_command:
                    # Use custom disease if provided
                    disease = message_after_command
                else:
                    # Use random disease if no custom disease
                    disease = random.choice(self.diseases)
                
                # Check if the reply is to the bot itself
                if target_user.lower() == self.bot.bot_username.lower():
                    random_response = random.choice(self.bot_defense_responses)
                    await ctx.send(f"@{user}, {random_response}")
                    logger.info(f"User {user} tried to infect the bot")
                    return
                
                # Check if the target username is safe
                is_safe, reason = username_filter.is_safe(target_user)
                if not is_safe:
                    await ctx.send(f"{user}, пососи GAGAGA")
                    logger.info(f"Skipping infect on unsafe username: {target_user} (Reason: {reason})")
                    return
                
                logger.info(f"Reply detected: {user} is infecting {target_user} with {disease}")
            else:
                # Not a reply - parse the command for custom disease and target
                if len(message_content.split()) > 1:
                    # Find if there's an @ mentioned to determine username
                    message_after_command = message_content.split('!заразить', 1)[1].strip()
                    
                    # Try to find a username (with @ symbol)
                    at_position = message_after_command.rfind('@')
                    
                    if at_position != -1:
                        # We found a username with @ - extract it and the disease
                        username_part = message_after_command[at_position+1:].strip().split()[0]
                        disease_part = message_after_command[:at_position].strip()
                        
                        target_user = username_part
                        if disease_part:
                            disease = disease_part
                        else:
                            disease = random.choice(self.diseases)
                            
                        # Check if the target is the bot itself
                        if target_user.lower() == self.bot.bot_username.lower():
                            random_response = random.choice(self.bot_defense_responses)
                            await ctx.send(f"@{user}, {random_response}")
                            logger.info(f"User {user} tried to infect the bot")
                            return
                            
                        # Check if the target username is safe
                        is_safe, reason = username_filter.is_safe(target_user)
                        if not is_safe:
                            await ctx.send(f"{user}, пососи GAGAGA")
                            logger.info(f"Skipping infect on unsafe username: {target_user} (Reason: {reason})")
                            return
                        
                        logger.info(f"Found format with @: disease='{disease}', target='{target_user}'")
                    else:
                        # No @ found - check if the last word could be a username
                        words = message_after_command.split()
                        if len(words) > 1:
                            # Assume last word is username, rest is disease
                            target_user = words[-1]
                            disease = ' '.join(words[:-1])
                            
                            # Check if the target is the bot itself
                            if target_user.lower() == self.bot.bot_username.lower():
                                random_response = random.choice(self.bot_defense_responses)
                                await ctx.send(f"@{user}, {random_response}")
                                logger.info(f"User {user} tried to infect the bot")
                                return
                                
                            # Check if the target username is safe
                            is_safe, reason = username_filter.is_safe(target_user)
                            if not is_safe:
                                await ctx.send(f"{user}, пососи GAGAGA")
                                logger.info(f"Skipping infect on unsafe username: {target_user} (Reason: {reason})")
                                return
                            
                            logger.info(f"Parsed as last word username: disease='{disease}', target='{target_user}'")
                        else:
                            # Just one word - assume it's the username
                            target_user = words[0]
                            disease = random.choice(self.diseases)
                            
                            # Check if the target is the bot itself
                            if target_user.lower() == self.bot.bot_username.lower():
                                random_response = random.choice(self.bot_defense_responses)
                                await ctx.send(f"@{user}, {random_response}")
                                logger.info(f"User {user} tried to infect the bot")
                                return
                                
                            # Check if the target username is safe
                            is_safe, reason = username_filter.is_safe(target_user)
                            if not is_safe:
                                await ctx.send(f"{user}, пососи GAGAGA")
                                logger.info(f"Skipping infect on unsafe username: {target_user} (Reason: {reason})")
                                return
                            
                            logger.info(f"Single word command: random disease, target='{target_user}'")
                
                # If we still don't have a target, pick a random one
                if not target_user:
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
                            disease = random.choice(self.diseases) if not disease else disease
                            logger.info(f"Random target: {user} is infecting {target_user} with {disease}")
                        else:
                            # If no safe targets available, use default names
                            default_targets = ["телезрителя", "стримера", "модератора", "случайного прохожего"]
                            target_user = random.choice(default_targets)
                            disease = random.choice(self.diseases) if not disease else disease
                            logger.info(f"No safe targets available, using default: {target_user}")
                    else:
                        # If no other users have chatted, use default names
                        default_targets = ["телезрителя", "стримера", "модератора", "случайного прохожего"]
                        target_user = random.choice(default_targets)
                        disease = random.choice(self.diseases) if not disease else disease
                        logger.info(f"Default target: {user} is infecting {target_user} with {disease}")
            
            # Choose a random emoji from the list
            random_emoji = random.choice(self.emojis)
            
            # Create the infection message with random emoji at the end
            message = f"@{user} заразил @{target_user} {disease} {random_emoji}"
            
            # Use the safe send method
            await self.send_safe(ctx, message)
            logger.info(f"User {user} infected {target_user} with {disease}, using emoji {random_emoji}")
            
            # Update global cooldown timestamp after successful infection
            self.last_global_infect = time.time()
    
    async def on_message(self, message):
        """Process messages to track chatters for the infect command"""
        if message.author is not None:
            username = message.author.name
            async with self.chatters_lock:
                self.recent_chatters.add(username) 