import logging
from twitchio.ext import commands
from utils.permission_manager import mod_only
from commands import BotCommand
from utils.cooldown_manager import cooldown_manager

logger = logging.getLogger('twitch_bot')

class CooldownCommands(BotCommand):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot)
    
    def register_commands(self):
        """Register cooldown commands with the bot"""
        
        @self.bot.command(name="кд")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def cooldown_command(ctx, action=None):
            """
            Команда для управления системой кулдаунов
            Использование:
            !кд статус - показать текущий статус кулдаунов
            !кд стоп - отключить кулдауны
            !кд старт - включить кулдауны
            !кд переключить - переключить состояние кулдаунов
            """
            user_id = ctx.author.name
            
            if not action:
                # Show current status
                status = "включена" if cooldown_manager.cooldowns_enabled else "отключена"
                await ctx.send(f"@{user_id}, Система кулдаунов {status}")
                return
            
            if action.lower() == "стоп":
                # Add debug logging
                logger.debug("Disabling cooldowns")
                cooldown_manager.cooldowns_enabled = False
                message = cooldown_manager.disable_cooldowns()
                await ctx.send(f"@{user_id}, {message}")
                logger.info(f"Cooldowns disabled by {user_id}")
                # Add debug logging
                logger.debug(f"Cooldowns enabled status: {cooldown_manager.cooldowns_enabled}")
                return
                
            if action.lower() == "старт":
                message = cooldown_manager.enable_cooldowns()
                await ctx.send(f"@{user_id}, {message}")
                logger.info(f"Cooldowns enabled by {user_id}")
                return
                
            if action.lower() == "переключить":
                message = cooldown_manager.toggle_cooldowns()
                await ctx.send(f"@{user_id}, {message}")
                logger.info(f"Cooldowns toggled by {user_id}: {cooldown_manager.cooldowns_enabled}")
                return
                
            # Если команда не распознана
            await ctx.send(f"@{user_id}, неизвестное действие. Используйте: !кд статус/стоп/старт/переключить")

def prepare(bot):
    # Не нужно использовать add_cog, так как BotCommand сам регистрирует команды
    CooldownCommands(bot) 