import logging
from commands import BotCommand
from twitchio.ext import commands
from utils.cooldown_manager import cooldown
from utils.safe_content import safe_content
from api_commands.twitch_api import TwitchAPI

logger = logging.getLogger('twitch_bot')

class LickCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.api = TwitchAPI(bot)
        
    def register_commands(self):
        """Регистрация команды лизать"""
        
        @self.bot.command(name="лизать")
        @cooldown(user_cd=10, global_cd=2)  # Устанавливаем кулдаун для предотвращения спама
        @safe_content  # Проверка безопасности контента
        async def lick_command(ctx):
            """Команда !лизать [объект]"""
            try:
                # Получаем текст сообщения и разделяем на части
                message_parts = ctx.message.content.split(maxsplit=1)
                
                # Если после команды есть объект
                if len(message_parts) > 1:
                    object_to_lick = message_parts[1].strip()
                    response = f"ты полизал {object_to_lick}"
                    
                    # Отправляем ответ как реплай на сообщение пользователя
                    await self.api.reply_to_message(
                        channel_name=ctx.channel.name,
                        message=response,
                        reply_to_msg_id=ctx.message.id
                    )
                    
                    logger.info(f"User {ctx.author.name} licked {object_to_lick}")
                else:
                    # Если объект не указан
                    await ctx.send(f"@{ctx.author.name}, укажи что именно ты хочешь полизать!")
                    
            except Exception as e:
                logger.error(f"Error in lick command: {str(e)}")
                await ctx.send(f"@{ctx.author.name}, произошла ошибка при выполнении команды.") 