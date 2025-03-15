import logging
import re
from commands import BotCommand
from utils.safe_content import safe_content
from utils.cooldown_manager import cooldown

logger = logging.getLogger('twitch_bot')

class AcceptInvitationCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        
    def register_commands(self):
        """Регистрация команды принятия предложений"""
        
        @self.bot.command(name="принять")
        @cooldown(user_cd=10, global_cd=3)
        @safe_content
        async def accept_command(ctx):
            """Команда !принять для принятия предложений от других пользователей"""
            try:
                # Получаем текст сообщения
                message_content = ctx.message.content
                
                # Ищем упоминание пользователя в формате @username
                username_match = re.search(r'@(\w+)', message_content)
                
                if username_match:
                    # Извлекаем имя пользователя
                    username = username_match.group(1)
                    
                    # Определяем тип предложения (по умолчанию "предложение")
                    invitation_type = "предложение на чай"
                    
                    # Проверяем, есть ли в сообщении указание на тип предложения
                    invitation_match = re.search(r'принять\s+(.+?)\s+@', message_content)
                    if invitation_match:
                        invitation_type = invitation_match.group(1)
                    
                    # Формируем ответное сообщение
                    response = f"ты принял {invitation_type} от @{username}"
                    
                    # Отправляем сообщение как ответ на исходное
                    await ctx.reply(response)
                    
                    logger.info(f"User {ctx.author.name} accepted invitation from {username}")
                else:
                    # Если пользователь не указан, отправляем подсказку
                    await ctx.reply(f"@{ctx.author.name}, укажите пользователя в формате: !принять предложение на чай @username")
            
            except Exception as e:
                logger.error(f"Error in accept command: {str(e)}")
                await ctx.reply(f"@{ctx.author.name}, произошла ошибка при обработке команды.") 