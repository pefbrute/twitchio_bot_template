import logging
import functools
import re
from .content_filter import content_filter

logger = logging.getLogger('twitch_bot')

def safe_content(func):
    """
    Декоратор для проверки безопасности содержимого сообщений в командах.
    
    Проверяет:
    1. Безопасность упоминаний пользователей (@username)
    2. Безопасность текста сообщения на наличие запрещенных слов/фраз
    
    Использование:
        @safe_content
        async def my_command(ctx):
            # Ваш код
    """
    @functools.wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        try:
            # Получаем текст сообщения
            message_content = ctx.message.content
            
            # 1. Проверяем безопасность текста сообщения
            is_safe_message, _ = content_filter.filter_message(message_content)
            if not is_safe_message:
                msg = f"@{ctx.author.name}, ваше сообщение содержит запрещенный контент."
                logger.warning(f"Unsafe message content from {ctx.author.name}: {message_content}")
                await ctx.send(msg)
                return
            
            # 2. Ищем все упоминания пользователей в формате @username
            username_matches = re.findall(r'@(\w+)', message_content)
            
            # Проверяем каждое найденное имя пользователя
            for username in username_matches:
                is_safe_username, reason = content_filter.is_safe_username(username)
                if not is_safe_username:
                    msg = f"@{ctx.author.name}, упомянутое имя пользователя содержит запрещенный контент."
                    logger.warning(f"Unsafe username detected: {username}, reason: {reason}")
                    await ctx.send(msg)
                    return
            
            # Если все проверки пройдены, выполняем команду
            return await func(ctx, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in safe_content decorator: {str(e)}")
            # В случае ошибки выполняем команду без проверки
            return await func(ctx, *args, **kwargs)
    
    return wrapper 