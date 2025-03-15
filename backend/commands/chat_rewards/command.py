import logging
import random
import time
import json
import os
from pathlib import Path
from commands import BotCommand
from commands.balance.balance_manager import balance_manager
from .chat_stats_manager import chat_stats_manager
from utils.permission_manager import mod_only
from utils.cooldown_manager import cooldown

logger = logging.getLogger('twitch_bot')

class ChatRewardsCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        
        # Register message listener
        self.bot.message_listeners.append(self.monitor_chat)
        
        # Reward settings
        self.reward_chance = 0  # Changed from 1 to 0 to disable rewards
        self.min_reward = 1000  # Minimum reward if user has no balance
        
        # Global cooldown settings
        self.cooldown_file = Path(os.path.dirname(__file__)) / 'cooldowns.json'
        self.cooldown_data = self._load_cooldown_data()
        self.cooldown_time = 600  # 10 minutes cooldown
        
        # Message length requirements
        self.min_message_length = 5  # Minimum characters
        
        # Track processed message IDs to avoid duplicates
        self.processed_message_ids = set()
        
        logger.info("Chat rewards system initialized")

    def _load_cooldown_data(self):
        """Load cooldown data from JSON file or create new if not exists"""
        try:
            if self.cooldown_file.exists():
                with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"last_reward_time": 0, "last_rewarded_user": ""}
        except Exception as e:
            logger.error(f"Error loading cooldown data: {str(e)}")
            return {"last_reward_time": 0, "last_rewarded_user": ""}
            
    def _save_cooldown_data(self):
        """Save cooldown data to JSON file"""
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.cooldown_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving cooldown data: {str(e)}")
            return False

    def register_commands(self):
        """Register stats-related commands"""
        @self.bot.command(name="активстат")
        @cooldown(user_cd=120, global_cd=3)
        async def show_stats(ctx):
            username = ctx.author.name.lower()
            stats = chat_stats_manager.get_user_stats(username)
            level_name = chat_stats_manager._get_level_name(stats['level'])
            next_level_xp = chat_stats_manager._get_xp_for_next_level(stats['level'])
            
            if next_level_xp:
                xp_progress = f"{stats['xp']}/{next_level_xp}"
            else:
                xp_progress = str(stats['xp'])
            
            await ctx.send(
                f"@{username}, твоя статистика: "
                f"Уровень: {stats['level']} ({level_name}), "
                f"Опыт: {xp_progress}, "
                f"Всего сообщений: {stats['messages']}"
            )

        @self.bot.command(name="лвлап")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def show_levelup(ctx):
            username = ctx.author.name.lower()
            stats = chat_stats_manager.get_user_stats(username)
            level_name = chat_stats_manager._get_level_name(stats['level'])
            next_level_xp = chat_stats_manager._get_xp_for_next_level(stats['level'])
            
            if next_level_xp:
                remaining_xp = next_level_xp - stats['xp']
                await ctx.send(
                    f"@{username}, до следующего уровня осталось {remaining_xp} опыта"
                )
            else:
                await ctx.send(
                    f"@{username}, поздравляем! Вы достигли максимального уровня: {level_name}"
                )

    async def monitor_chat(self, message):
        """Monitor chat messages and give random rewards"""
        try:
            # Skip if message is from the bot itself
            if message.author is None or message.author.name.lower() == self.bot.nick.lower():
                return
                
            # Skip if message has already been processed
            if hasattr(message, 'id') and message.id in self.processed_message_ids:
                logger.debug(f"Skipping already processed message: {message.content}")
                return
                
            # Mark message as processed
            if hasattr(message, 'id'):
                self.processed_message_ids.add(message.id)
                # Limit size of set to avoid memory issues
                if len(self.processed_message_ids) > 1000:
                    self.processed_message_ids = set(list(self.processed_message_ids)[-500:])
                
            # Skip if message starts with "!" (commands)
            if message.content.startswith('!'):
                return
                
            # Get username
            username = message.author.name.lower()
            
            # Skip if message is too short
            if len(message.content) < self.min_message_length:
                return
                
            # Process message for XP and leveling
            level_up = chat_stats_manager.add_message(username)
            
            # If user leveled up, announce it
            if level_up:
                await message.channel.send(
                    f"🎉 @{username} достиг {level_up['new_level']} уровня ({level_up['new_level_name']})! "
                    f"Всего сообщений: {level_up['total_messages']}"
                )
                
            # Check global cooldown for rewards
            current_time = time.time()
            last_reward_time = float(self.cooldown_data.get("last_reward_time", 0))
            
            if current_time - last_reward_time < self.cooldown_time:
                return
                    
            # Random chance to get reward
            if random.random() < self.reward_chance:
                # Get current balance
                current_balance = balance_manager.get_balance(username)
                
                # Calculate reward as 1% of current balance
                if current_balance > 0:
                    reward = max(int(current_balance * 0.01), self.min_reward)
                else:
                    reward = self.min_reward
                
                # Add reward to user's balance
                new_balance = balance_manager.adjust_balance(username, reward)
                
                # Update global cooldown
                self.cooldown_data["last_reward_time"] = current_time
                self.cooldown_data["last_rewarded_user"] = username
                self._save_cooldown_data()
                
                # Send message about reward
                await message.channel.send(
                    f"@{username} получает {reward} {self.get_currency_name(reward)} "
                    f"за активность в чате! Баланс: {balance_manager.format_balance(new_balance)} "
                    f"{self.get_currency_name(new_balance)}"
                )
                
                logger.info(f"Gave {reward} currency to {username}")
                
        except Exception as e:
            logger.error(f"Error in chat rewards: {str(e)}")
            logger.exception("Full traceback:")

    def get_currency_name(self, amount):
        """Get the correct currency name form based on amount"""
        if amount % 10 == 1 and amount % 100 != 11:
            return "рубль"
        elif amount % 10 in [2, 3, 4] and amount % 100 not in [12, 13, 14]:
            return "рубля"
        else:
            return "рублей" 