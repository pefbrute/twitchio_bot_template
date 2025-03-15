import logging
import random
import asyncio
import time
import json
import os
from twitchio.ext import commands
from commands import BotCommand
from utils.username_filter import username_filter

logger = logging.getLogger('twitch_bot')

class VirusCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.infected_users = {}  # user_id -> infection timestamp
        self.recent_chatters = set()  # Set of recent chatters
        self.chatters_lock = asyncio.Lock()
        self.infection_lock = asyncio.Lock()
        self.infection_duration = 300  # 5 minutes
        self.message_history = {}  # msg_id -> message object
        
        # Path to JSON file for storing infected users
        self.data_file = os.path.join(os.path.dirname(__file__), 'infected_users.json')
        
        # Load infected users from JSON file
        self.load_infected_users()
        
        # Add cache for subscriber status
        self.subscriber_cache = {}
        self.subscriber_cache_duration = 300  # 5 minutes
        
        self.bot_defense_responses = [
            "у меня антивирус!",
            "я защищен от вирусов!",
            "не могу заразиться!",
            "я неуязвим для вирусов!"
        ]
        
        # Start cleanup task in a proper way
        self.bot.loop.create_task(self.cleanup_chatters())
        
        self.processed_messages = set()  # Add this line to track processed messages
        
    def load_infected_users(self):
        """Load infected users from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.infected_users = json.load(f)
                # Convert string timestamps back to float
                self.infected_users = {k: float(v) for k, v in self.infected_users.items()}
        except Exception as e:
            logger.error(f"Error loading infected users: {str(e)}")
            self.infected_users = {}

    def save_infected_users(self):
        """Save infected users to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.infected_users, f)
        except Exception as e:
            logger.error(f"Error saving infected users: {str(e)}")

    def register_commands(self):
        """Register virus command and message listener with the bot"""
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Check if our listener is already registered
        if self.on_message not in self.bot.message_listeners:
            # Add our listener function to the bot's list of listeners
            self.bot.message_listeners.append(self.on_message)
        
        #@self.bot.command(name="вирус")
        async def virus_command(ctx: commands.Context):
            """Command to infect a specific user or random user with a virus"""
            user = ctx.author.name
            
            # Check if user has permission to use this command
            if not (ctx.author.is_mod or user.lower() == "fedor_jogaboga82"):
                await ctx.send(f"@{user}, только модераторы и @fedor_jogaboga82 могут использовать эту команду!")
                return
            
            # Check if a target was specified
            message_parts = ctx.message.content.split()
            target_specified = len(message_parts) > 1 and message_parts[1].startswith('@')
            
            if target_specified:
                # Get the specified target (remove @ symbol)
                target_user = message_parts[1][1:].lower()
                
                # Check if target is the bot
                if target_user == self.bot.bot_username.lower():
                    random_response = random.choice(self.bot_defense_responses)
                    await ctx.send(f"@{user}, {random_response}")
                    logger.info(f"User {user} tried to infect the bot")
                    return
                    
                # Check if target is already infected
                target_id = await self.bot.api.get_user_id(target_user)
                if str(target_id) in self.infected_users:
                    await ctx.send(f"Пользователь @{target_user} уже заражен!")
                    return
                    
                # Check if username is safe
                if not username_filter.is_safe(target_user)[0]:
                    await ctx.send(f"Невозможно заразить этого пользователя!")
                    return
            else:
                # Get a random user from recent chatters
                async with self.chatters_lock:
                    # Debug logging
                    logger.info(f"Recent chatters: {self.recent_chatters}")
                    logger.info(f"Current user: {user}")
                    
                    # Filter out already infected users, current user, bot, and unsafe usernames
                    potential_targets = [
                        name for name in self.recent_chatters 
                        if name.lower() != user.lower() and 
                           name.lower() != self.bot.bot_username.lower() and
                           name.lower() not in self.infected_users and
                           username_filter.is_safe(name)[0]
                    ]
                    
                    # Debug logging
                    logger.info(f"Potential targets: {potential_targets}")
                
                if not potential_targets:
                    await ctx.send(f"@{user}, в чате нет подходящих целей для заражения! Все уже заражены monkaS")
                    return
                
                target_user = random.choice(potential_targets)
            
            logger.info(f"Selected target: {target_user}")
            
            # Infect the target user
            async with self.infection_lock:
                target_id = await self.bot.api.get_user_id(target_user)
                self.infected_users[str(target_id)] = time.time()
                self.save_infected_users()
            
            # Send infection message
            await ctx.send(f"@{target_user} подцепил опасный вирус monkaS. Теперь можешь заразить других через реплаи!")
            logger.info(f"User {user} infected {target_user} with virus")
        
        @self.bot.command(name="ядерка")
        async def nuclear_command(ctx: commands.Context):
            """Command to timeout all infected users"""
            # Check if user has permission to use this command
            user = ctx.author.name
            if not (ctx.author.is_mod or user.lower() == "fedor_jogaboga82"):
                return
                
            async with self.infection_lock:
                infected_count = len(self.infected_users)
                if infected_count == 0:
                    await ctx.send("Нет зараженных пользователей для помещения в карантин!")
                    return
                
                # Get list of infected users before clearing
                infected_list = list(self.infected_users.keys())
                
                # Clear infected users
                self.infected_users.clear()
                self.save_infected_users()  # Save after clearing
                
                # Get broadcaster ID from context tags
                broadcaster_id = ctx.message.tags.get('room-id')
                if not broadcaster_id:
                    logger.error("Could not get broadcaster ID from context")
                    await ctx.send("Произошла ошибка при попытке карантина!")
                    return
                
                # Timeout all infected users
                timeout_failures = 0
                successful_timeouts = 0
                try:
                    for uid in infected_list:
                        try:
                            # Use the API to timeout the user
                            success = await self.bot.api.timeout_user(
                                broadcaster_id=broadcaster_id,
                                target_user_id=uid,
                                duration=20,
                                reason="Ядерная дезинфекция"
                            )
                            if success:
                                successful_timeouts += 1
                            else:
                                timeout_failures += 1
                        except Exception as e:
                            timeout_failures += 1
                            logger.error(f"Failed to timeout {uid}: {str(e)}")
                            
                    # Only show successfully timed out users
                    status_msg = f"была активирована ядерная дезинфекция! {successful_timeouts} пользователей помещены в карантин на 20 секунд monkaS"
                    
                    await ctx.send(status_msg)
                    logger.info(f"Nuclear command used by {ctx.author.name}, {successful_timeouts} users timed out, {timeout_failures} failures")
                except Exception as e:
                    logger.error(f"Error during nuclear timeout: {str(e)}")
                    await ctx.send("Произошла ошибка при попытке карантина!")

        #@self.bot.command(name="вирускол")
        async def virus_multi_command(ctx: commands.Context):
            """Command to infect multiple random users with a virus"""
            user = ctx.author.name
            
            # Check if user has permission to use this command
            if not (ctx.author.is_mod or user.lower() == "fedor_jogaboga82"):
                return
            
            # Get the number of users to infect
            message_parts = ctx.message.content.split()
            if len(message_parts) < 2:
                await ctx.send(f"@{user}, укажите количество пользователей для заражения!")
                return
            
            try:
                count = int(message_parts[1])
                if count <= 0:
                    await ctx.send(f"@{user}, количество должно быть положительным числом!")
                    return
            except ValueError:
                await ctx.send(f"@{user}, укажите корректное число!")
                return
            
            # Get all potential targets
            async with self.chatters_lock:
                # Filter out already infected users, current user, bot, and unsafe usernames
                potential_targets = [
                    name for name in self.recent_chatters 
                    if name.lower() != user.lower() and 
                       name.lower() != self.bot.bot_username.lower() and
                       str(name) not in self.infected_users and
                       username_filter.is_safe(name)[0]
                ]
                
                logger.info(f"Potential targets for mass infection: {potential_targets}")
            
            if not potential_targets:
                await ctx.send(f"@{user}, в чате нет подходящих целей для заражения! Все уже заражены monkaS")
                return
            
            # Determine how many users we can actually infect
            count = min(count, len(potential_targets))
            targets = random.sample(potential_targets, count)
            
            # Infect all selected targets
            async with self.infection_lock:
                current_time = time.time()
                for target in targets:
                    target_id = await self.bot.api.get_user_id(target)
                    self.infected_users[str(target_id)] = current_time
                self.save_infected_users()  # Save after infecting all users
            
            # Send infection message
            if count == 1:
                await ctx.send(f"@{targets[0]} подцепил опасный вирус от @{user} monkaS теперь может заразить других через ответы на сообщения!")
            else:
                targets_list = ', '.join([f"@{target}" for target in targets])
                await ctx.send(f"@{user} заразил сразу {count} пользователей: {targets_list} monkaS")
            
            logger.info(f"User {user} infected {count} users with virus: {targets}")

        #@self.bot.command(name="виркол")
        async def virus_count_command(ctx: commands.Context):
            """Command to show current number of infected users"""
            async with self.infection_lock:
                # Clean up expired infections first
                current_time = time.time()
                expired = [uid for uid, timestamp in self.infected_users.items() 
                          if current_time - timestamp > self.infection_duration]
                if expired:
                    for uid in expired:
                        del self.infected_users[uid]
                    self.save_infected_users()

                infected_count = len(self.infected_users)
                if infected_count == 0:
                    await ctx.send("В чате нет зараженных пользователей PogChamp")
                elif infected_count <= 3:
                    # Get usernames for the infected user IDs
                    infected_usernames = []
                    for uid in self.infected_users.keys():
                        try:
                            username = await self.bot.api.get_username(uid)
                            infected_usernames.append(f"@{username}")
                        except Exception as e:
                            logger.error(f"Error getting username for {uid}: {str(e)}")
                            infected_usernames.append(f"ID:{uid}")
                    
                    infected_list = ", ".join(infected_usernames)
                    await ctx.send(f"Зараженных пользователей: {infected_count} monkaS [{infected_list}]")
                else:
                    await ctx.send(f"Зараженных пользователей: {infected_count} monkaS")

    async def is_subscriber(self, username):
        """Check if user is protected using message history and Twitch API"""
        try:
            # Skip checks for default target
            if username == "случайного ансаба":
                return False
                
            # Check cache first
            current_time = time.time()
            if username in self.subscriber_cache:
                cache_time, is_sub = self.subscriber_cache[username]
                if current_time - cache_time < self.subscriber_cache_duration:
                    return is_sub

            # First try to get from message history
            for msg in self.message_history.values():
                if (hasattr(msg, 'author') and 
                    msg.author and 
                    msg.author.name.lower() == username.lower()):
                    
                    # First check badges from message tags
                    if hasattr(msg, 'tags') and 'badges' in msg.tags:
                        badges = msg.tags['badges'].split(',') if msg.tags['badges'] else []
                        is_protected = any(badge.startswith(('subscriber', 'moderator', 'vip', 'broadcaster')) 
                                         for badge in badges)
                        if is_protected:
                            self.subscriber_cache[username] = (current_time, True)
                            return True
                    
                    # Fallback to chatter properties
                    chatter = msg.author
                    is_protected = (
                        chatter.is_subscriber or
                        chatter.is_mod or
                        chatter.is_vip or
                        chatter.is_broadcaster
                    )
                    self.subscriber_cache[username] = (current_time, is_protected)
                    return is_protected

            # If not found in messages, try to get from channel's chatters
            try:
                channel = self.bot.connected_channels[0]
                if channel:
                    try:
                        for chatter in channel.chatters:
                            if chatter.name.lower() == username.lower():
                                # Handle PartialChatter case
                                if not hasattr(chatter, 'is_subscriber'):
                                    if hasattr(chatter, 'badges'):
                                        is_protected = any(badge.startswith(('subscriber', 'moderator', 'vip', 'broadcaster'))
                                                         for badge in chatter.badges)
                                        self.subscriber_cache[username] = (current_time, is_protected)
                                        return is_protected
                                    continue

                                is_protected = (
                                    chatter.is_subscriber or
                                    chatter.is_mod or
                                    chatter.is_vip or
                                    chatter.is_broadcaster
                                )
                                self.subscriber_cache[username] = (current_time, is_protected)
                                return is_protected
                    except Exception as e:
                        logger.error(f"Error accessing chatters: {str(e)}")
                else:
                    logger.error("Could not get channel")
            except Exception as e:
                logger.error(f"Error accessing channel: {str(e)}")

            # If we haven't found the user anywhere
            logger.info(f"User {username} not found in messages or channel, assuming not protected")
            self.subscriber_cache[username] = (current_time, False)
            return False

        except Exception as e:
            logger.error(f"Error checking subscriber status for {username}: {str(e)}")
            return False

    async def on_message(self, message):
        """Process messages to track chatters and handle virus spread"""
        # Skip bot's own messages and already processed messages
        if (message.author is None or 
            message.author.name.lower() == self.bot.bot_username.lower() or
            (hasattr(message, 'tags') and message.tags.get('id') in self.processed_messages)):
            return
            
        # Mark message as processed
        if hasattr(message, 'tags') and 'id' in message.tags:
            self.processed_messages.add(message.tags['id'])
            # Keep set size reasonable
            if len(self.processed_messages) > 1000:
                self.processed_messages.clear()
            
        username = message.author.name.lower()
        
        # Store message in history (keep only last 1000 messages)
        if hasattr(message, 'tags') and 'id' in message.tags:
            self.message_history[message.tags['id']] = message
            if len(self.message_history) > 1000:
                # Remove oldest messages
                oldest_keys = sorted(self.message_history.keys())[:100]
                for key in oldest_keys:
                    del self.message_history[key]
        
        # Add user to recent chatters
        async with self.chatters_lock:
            self.recent_chatters.add(username)
        
        # Update subscriber cache if we have badge information
        if hasattr(message, 'tags'):
            tags = message.tags
            is_protected = (
                tags.get('subscriber') == '1' or 
                tags.get('mod') == '1' or 
                tags.get('vip') == '1' or 
                'broadcaster' in tags.get('badges', '')
            )
            if is_protected:
                self.subscriber_cache[username] = (time.time(), True)
        
        # Handle virus spread through replies
        if hasattr(message, 'tags') and 'reply-parent-user-login' in message.tags:
            await self.handle_virus_spread(message)

    async def handle_protected_user(self, attacker, target, channel):
        """Handle attempt to infect a protected user"""
        logger.info(f"Skipping protected user {target}")
        await channel.send(f"@{attacker} попытался заразить @{target}, но у него есть щит от вируса! PunOko")

    async def handle_virus_spread(self, message):
        """Handle virus spread logic"""
        user_id = message.author.id
        
        async with self.infection_lock:
            # Clean up expired infections
            current_time = time.time()
            expired = [uid for uid, timestamp in self.infected_users.items() 
                      if current_time - timestamp > self.infection_duration]
            if expired:
                for uid in expired:
                    del self.infected_users[uid]
                self.save_infected_users()
            
            # Check if the replying user is infected
            if str(user_id) in self.infected_users:
                target_id = message.tags.get('reply-parent-user-id')
                target_name = message.tags.get('reply-parent-user-login')
                
                # Skip if target is the bot or already infected
                if (target_name.lower() == self.bot.bot_username.lower() or 
                    str(target_id) in self.infected_users):
                    return
                
                # Always infect the user (100% chance)
                self.infected_users[str(target_id)] = current_time
                self.save_infected_users()
                await message.channel.send(f"@{target_name} заразился вирусом от @{message.author.name} monkaS")
                logger.info(f"User {target_name} got infected by {message.author.name}")

    async def cleanup_chatters(self):
        """Periodically clean up the list of chatters to prevent memory issues"""
        try:
            while True:
                await asyncio.sleep(3600)  # Clean up every hour
                async with self.chatters_lock:
                    if len(self.recent_chatters) > 1000:  # Arbitrary limit
                        logger.info(f"Cleaning up chatter list, current size: {len(self.recent_chatters)}")
                        # Keep only the most recent 100 chatters
                        self.recent_chatters = set(list(self.recent_chatters)[-100:])
        except asyncio.CancelledError:
            logger.info("Cleanup task for chatters list was cancelled")
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")