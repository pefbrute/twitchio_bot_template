import logging
import random
import asyncio
import re
from twitchio.ext import commands
from commands import BotCommand
from utils.word_filter import word_filter
from utils.username_filter import username_filter
from utils.safe_content import safe_content
from utils.cooldown_manager import with_cooldown as cooldown
from .reputation_manager import ReputationManager
from api_commands.twitch_api import TwitchAPI

logger = logging.getLogger('twitch_bot')

class PispisCommand(BotCommand):
    def __init__(self, bot):
        # Track recent chatters for random selection
        self.recent_chatters = set()
        self.chatters_lock = asyncio.Lock()
        
        # Responses when someone tries to pispis on the bot
        self.bot_defense_responses = [
            "сделал жёсткий пис пис на тебя, сиди и нюхай!",
            "облил тебя тонной жёлтой, вытирайся, неудачник!",
            "затопил тебя пис писом, плыви, если сможешь!",
            "плеснул на тебя пис писом, сиди в луже!",
            "засадил тебе жёлтой волной, смойся с глаз!",
            "залил тебя пис писом, теперь ты мой шедевр!"
        ]
        
        # Random pispis phrases to use instead of fixed message
        self.pispis_phrases = [
            "сделал пис пис на",
            "облил тонной жёлтенькой",
            "затопил пис писом",
            "плеснул жёлтой водичкой на",
            "полил струёй пис писа",
            "оросил жёлтеньким",
            "сбрызнул пис писом",
            "окатил свежим пис писом",
            "оставил жёлтую лужицу на",
            "пустил струю пис писа на"
        ]
        
        # Add reputation manager
        self.reputation_manager = ReputationManager()
        
        # Add base failure chance (5%)
        self.base_failure_chance = 0.05
        
        # Add reputation penalty multiplier
        self.rep_penalty_multiplier = 0.001  # 0.1% per negative reputation point
        
        # Add TwitchAPI
        self.twitch_api = TwitchAPI(bot)
        
        # Call parent constructor to register commands
        super().__init__(bot)
        
    def register_commands(self):
        """Register pispis and pray commands with the bot"""
        
        # Instead of registering a new event handler, we'll just set up a message listener
        # that will be called by the bot's main event_message handler
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        # If this is the first command module to register, patch the bot's event_message method
        if not hasattr(self.bot, '_original_event_message'):
            # Store the original event_message method
            self.bot._original_event_message = self.bot.event_message
            
            # Create a new event_message method that calls all listeners
            async def new_event_message(message):
                # Call the original event_message first
                if self.bot._original_event_message:
                    await self.bot._original_event_message(message)
                
                # Then call all registered message listeners
                if hasattr(self.bot, 'message_listeners'):
                    for listener in self.bot.message_listeners:
                        try:
                            await listener(message)
                        except Exception as e:
                            logger.error(f"Error in message listener: {str(e)}")
            
            # Replace the bot's event_message with our new one
            self.bot.event_message = new_event_message
        
        @self.bot.command(name="молиться")
        @cooldown(user_cooldown=120)  # 2 minute cooldown
        async def pray_command(ctx: commands.Context):
            """Command to pray and improve reputation for self or another user"""
            message_parts = ctx.message.content.split()
            user = ctx.author.name.lower()
            
            # Determine target - if specified, otherwise self
            target = user
            if len(message_parts) > 1:
                target = message_parts[1].strip('@').lower()
                
                # Check if target username is safe
                is_safe, reason = username_filter.is_safe(target)
                if not is_safe:
                    await ctx.send(f"@{user}, бот не может молиться за этого пользователя.")
                    logger.info(f"Skipping pray for unsafe username: {target} (Reason: {reason})")
                    return
            
            # Improve reputation
            self.reputation_manager.modify_reputation(target, 1)
            new_rep = self.reputation_manager.get_reputation(target)
            status = self.reputation_manager.get_status(new_rep)
            
            # Different messages for self-pray and praying for others
            if target == user:
                await ctx.send(f"@{user} помолился и очистил свою карму! Репутация: {new_rep} ({status})")
            else:
                await ctx.send(f"@{user} помолился за @{target}! Репутация {target}: {new_rep} ({status})")
            
            logger.info(f"User {user} prayed for {target}, reputation improved to {new_rep}")

        @self.bot.command(name="репутация")
        async def reputation_command(ctx: commands.Context):
            """Command to check reputation"""
            message_parts = ctx.message.content.split()
            
            # Check if checking someone else's reputation
            if len(message_parts) > 1:
                target = message_parts[1].lower().strip('@')
            else:
                target = ctx.author.name.lower()
            
            rep = self.reputation_manager.get_reputation(target)
            status = self.reputation_manager.get_status(rep)
            
            await ctx.send(f"@{target} имеет репутацию {rep} ({status})")

        @self.bot.command(name="мион")
        @cooldown(user_cooldown=120)  # 2 minute cooldown
        @safe_content
        async def pispis_command(ctx):
            """Command to make pis pis on a user"""
            try:
                # Parse the message to find the target
                message_parts = ctx.message.content.split()
                user = ctx.author.name.lower()
                
                # Calculate failure chance based on user's reputation
                user_rep = self.reputation_manager.get_reputation(user)
                failure_chance = self.calculate_failure_chance(user_rep)
                
                # Roll for failure
                if random.random() < failure_chance:
                    # Failed - hit self instead
                    self.reputation_manager.modify_reputation(user, -1)
                    new_rep = self.reputation_manager.get_reputation(user)
                    status = self.reputation_manager.get_status(new_rep)
                    await self.twitch_api.reply_to_message(
                        channel_name=ctx.channel.name,
                        message=f"ты промахнулся и облил себя! Репутация: {new_rep} {status}",
                        reply_to_msg_id=ctx.message.id
                    )
                    return
                
                # Default behavior: if no target specified, pick a random user
                if len(message_parts) <= 1:
                    # Get a random user from recent chatters
                    async with self.chatters_lock:
                        if not self.recent_chatters or len(self.recent_chatters) <= 1:
                            # No recent chatters to pick from
                            await ctx.send(f"@{user}, в чате недостаточно людей для случайного выбора.")
                            return
                            
                            # Filter out the command user and the bot
                            potential_targets = [
                                chatter for chatter in self.recent_chatters 
                                if chatter.lower() != user.lower() and chatter.lower() != self.bot.nick.lower()
                            ]
                            
                            if not potential_targets:
                                await ctx.send(f"@{user}, в чате недостаточно людей для случайного выбора.")
                                return
                                
                            target = random.choice(list(potential_targets))
                else:
                    # Get specified target
                    target = message_parts[1].strip('@')
                
                # Check if the target is the bot itself
                if target.lower() == self.bot.nick.lower():
                    random_response = random.choice(self.bot_defense_responses)
                    await self.twitch_api.reply_to_message(
                        channel_name=ctx.channel.name,
                        message=random_response,
                        reply_to_msg_id=ctx.message.id
                    )
                    logger.info(f"User {user} tried to pispis on the bot")
                    return
                
                # Check if the target username is safe
                is_safe, reason = username_filter.is_safe(target)
                if not is_safe:
                    await ctx.send(f"{user}, бот не может делать пис пис на этого пользователя.")
                    logger.info(f"Skipping pispis on unsafe username: {target} (Reason: {reason})")
                    return
                    
                # Choose a random phrase
                random_phrase = random.choice(self.pispis_phrases)
                
                # Create the message with the random phrase and fixed "mion" emote
                # Remove the username prefix from the message
                message = f"{random_phrase} {target} mion"
                
                # Before sending the message, decrease target's reputation
                self.reputation_manager.modify_reputation(target.lower(), -1)
                new_rep = self.reputation_manager.get_reputation(target.lower())
                status = self.reputation_manager.get_status(new_rep)
                
                # Check if the message contains banned phrases
                is_safe, filtered_message = word_filter.filter_message(message)
                
                if is_safe:
                    # Message is safe to send
                    await self.twitch_api.reply_to_message(
                        channel_name=ctx.channel.name,
                        message=message,
                        reply_to_msg_id=ctx.message.id
                    )
                    logger.info(f"User {user} did pispis on {target} with phrase '{random_phrase}'")
                else:
                    # Message contains banned phrases - use a safer phrase
                    safer_phrases = [
                        "полил водичкой",
                        "намочил слегка",
                        "окатил жидкостью",
                        "увлажнил немного"
                    ]
                    safer_phrase = random.choice(safer_phrases)
                    safe_message = f"{safer_phrase} {target} mion"
                    
                    # Double-check the safer message
                    if word_filter.filter_message(safe_message)[0]:
                        await self.twitch_api.reply_to_message(
                            channel_name=ctx.channel.name,
                            message=safe_message,
                            reply_to_msg_id=ctx.message.id
                        )
                        logger.info(f"Used safe alternative phrase due to banned phrase in original message")
                    else:
                        logger.warning(f"Could not send pispis message due to banned phrases: {message}")
                        await self.twitch_api.reply_to_message(
                            channel_name=ctx.channel.name,
                            message="твоё сообщение не может быть отправлено из-за запрещённых фраз.",
                            reply_to_msg_id=ctx.message.id
                        )

            except Exception as e:
                logger.error(f"Error in pispis command: {str(e)}")
                await self.twitch_api.reply_to_message(
                    channel_name=ctx.channel.name,
                    message="произошла ошибка при выполнении команды.",
                    reply_to_msg_id=ctx.message.id
                )

        @self.bot.command(name="репутацияпоставить")
        async def set_reputation_command(ctx: commands.Context):
            """Command to set reputation (mod and VIP)"""
            # Parse command arguments
            args = ctx.message.content.split()
            if len(args) != 3:
                # Silently ignore incorrect format
                return
                
            # Get target username and remove @ if present
            target = args[1].lower().strip('@')
            
            # Parse reputation value
            try:
                new_rep = int(args[2])
            except ValueError:
                # Silently ignore non-numeric values
                return

            # Check permissions
            is_mod = ctx.author.is_mod
            is_vip = ctx.author.is_vip
            user = ctx.author.name.lower()

            # VIPs can only change their own reputation
            if is_vip and not is_mod:  # VIP but not mod
                if target != user:  # Trying to change someone else's reputation
                    await ctx.send(f"@{user}, VIP-гости могут менять только свою репутацию!")
                    return
            # Non-VIP, non-mod users can't use this command
            elif not (is_vip or is_mod):
                # Silently ignore
                return
                
            # At this point, either:
            # 1. User is a mod (can change anyone's rep)
            # 2. User is VIP and is changing their own rep
            
            # Set the new reputation
            old_rep = self.reputation_manager.get_reputation(target)
            self.reputation_manager.reputation_data["reputations"][target] = new_rep
            self.reputation_manager._save_data()
            
            # Get status for new reputation
            status = self.reputation_manager.get_status(new_rep)
            
            # Send confirmation message
            await ctx.send(f"@{ctx.author.name} изменил репутацию пользователя {target} с {old_rep} на {new_rep} ({status})")
            logger.info(f"{ctx.author.name} set reputation for {target} from {old_rep} to {new_rep}")

    def is_phone_number_like(self, username):
        """
        Check if a username looks like a phone number to avoid getting muted
        """
        # Remove common username prefixes if present
        username = re.sub(r'^@', '', username)
        
        # Count digits in the username
        digit_count = sum(c.isdigit() for c in username)
        
        # Check if username has 7+ digits which would suggest it might be a phone number
        if digit_count >= 7:
            return True
            
        # Check for common phone number patterns with separators
        phone_patterns = [
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}',  # Various international formats
            r'\+?\d{1,3}[-.\s]?\d{3,}',  # +1-234567890
        ]
        
        for pattern in phone_patterns:
            if re.search(pattern, username):
                return True
                
        return False
    
    async def on_message(self, message):
        """Process messages to track chatters for the pispis command"""
        if message.author is not None:
            username = message.author.name
            async with self.chatters_lock:
                self.recent_chatters.add(username)

    async def _get_random_target(self, ctx):
        """Get a random user from recent chatters"""
        user = ctx.author.name.lower()
        
        async with self.chatters_lock:
            if not self.recent_chatters or len(self.recent_chatters) <= 1:
                # No recent chatters to pick from
                return "ансабов"  # Fallback to default target
            
            # Filter out the command user and the bot
            potential_targets = [
                chatter for chatter in self.recent_chatters 
                if chatter.lower() != user.lower() and chatter.lower() != self.bot.nick.lower()
            ]
            
            if not potential_targets:
                return "ансабов"  # Fallback to default target
            
            return random.choice(list(potential_targets))

    def calculate_success_chance(self, reputation):
        """Calculate chance of successful pis pis based on reputation"""
        # Base chance is 90% for positive reputation
        if reputation >= 0:
            return 0.9
        
        # For negative reputation, chance decreases
        # At -100 rep: ~40% chance
        # At -500 rep: ~10% chance
        # At -1000 rep: ~5% chance
        return max(0.05, 0.9 * (1 / (1 + abs(reputation/100))))

    def calculate_failure_chance(self, reputation: int) -> float:
        """Calculate chance of failing pispis based on reputation"""
        if reputation >= 0:
            return self.base_failure_chance
        
        # Increase failure chance based on negative reputation
        # At -1000 rep: ~15% chance
        # At -10000 rep: ~25% chance
        penalty = abs(reputation) * self.rep_penalty_multiplier
        return min(0.95, self.base_failure_chance + penalty)

    async def handle_pispis(self, ctx, target_username=None):
        user = ctx.author.name.lower()
        
        # Get user's current reputation
        user_rep = await self.reputation_manager.get_reputation(user)
        
        # Calculate success chance
        success_chance = self.calculate_success_chance(user_rep)
        
        # Roll for success
        if random.random() > success_chance:
            # Failed roll - hit self instead
            await self.reputation_manager.decrease_reputation(user)
            current_rep = await self.reputation_manager.get_reputation(user)
            status = await self.reputation_manager.get_status_for_reputation(current_rep)
            
            return f"@{user} промахнулся и облил себя! Репутация: {current_rep} ({status})"
        
        # Original pis pis logic continues here...