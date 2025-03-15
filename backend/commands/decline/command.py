import logging
from commands import BotCommand
from twitchio.ext import commands
from utils.cooldown_manager import cooldown
from utils.safe_content import safe_content
from api_commands.twitch_api import TwitchAPI

logger = logging.getLogger('twitch_bot')

class DeclineCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.api = TwitchAPI(bot)
        
    def register_commands(self):
        """Регистрация команды отклонения"""
        
        @self.bot.command(name="отклонить")
        @safe_content  # Проверка безопасности упоминаний
        async def decline_command(ctx):
            """Команда !отклонить для отклонения предложения на чай"""
            try:
                message_parts = ctx.message.content.split()
                
                # Проверяем формат команды
                if len(message_parts) < 4 or "предложение на чай" not in ctx.message.content:
                    await ctx.send(f"@{ctx.author.name}, используйте формат: !отклонить предложение на чай @username")
                    return
                    
                # Извлекаем имя пользователя
                username = None
                for part in message_parts:
                    if part.startswith('@'):
                        username = part.strip('@')
                        break
                        
                if not username:
                    await ctx.send(f"@{ctx.author.name}, укажите пользователя через @")
                    return
                
                # Отправляем ответ с использованием reply
                response_message = f"ты отклонил предложение на чай от @{username} blyat"
                
                # Пробуем использовать API для реплая если есть message_id
                message_id = getattr(ctx.message, 'id', None)
                if message_id:
                    success = await self.api.reply_to_message(
                        channel_name=ctx.channel.name,
                        message=response_message,
                        reply_to_msg_id=message_id
                    )
                    if success:
                        logger.info(f"User {ctx.author.name} declined tea offer from {username}")
                        return
                
                # Если реплай не сработал, отправляем обычное сообщение
                await ctx.send(f"@{ctx.author.name}, {response_message}")
                logger.info(f"User {ctx.author.name} declined tea offer from {username}")
                
            except Exception as e:
                logger.error(f"Error in decline command: {str(e)}")
                await ctx.send(f"@{ctx.author.name}, произошла ошибка при выполнении команды.") 