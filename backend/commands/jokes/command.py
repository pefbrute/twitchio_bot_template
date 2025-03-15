import logging
import random
from commands import BotCommand
from utils.cooldown_manager import cooldown
from api_commands.twitch_api import TwitchAPI

logger = logging.getLogger('twitch_bot')

class JokesCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.twitch_api = TwitchAPI(bot)  # Initialize TwitchAPI
        # Список анекдотов (можно расширить)
        self.jokes = [
            "— Дочь, ты пила? — Нет, мама, я топор!",
            "Маленькую Лизу, глухую на одно ухо, мама ласково называла Моно Лиза.",
            "Смотрел недавно открытие Параолимпиады. Всё хорошо, но, глядя на спортсменов, не отпускала мысль: Чего-то не хватает...",
            "Однажды к Соломону привели двух женщин, которые спорили, кому принадлежит мужчина. Соломон предложил разрубить мужика, в гта рп. Обе женщины согласились. Дело было в Питере.",
            "У нас есть шутка про одного жителя Санкт-Петербурга, но она состоит из нескольких частей...",
            "Мало кто знает, но сиамские близнецы бьются яйцами не только на пасху.",
            "— Почему в Африке так много болезней? — Потому что таблетки нужно запивать водой."

        ]

    def register_commands(self):
        #@self.bot.command(name="анекдот")
        async def joke_command(ctx):
            """Команда !анекдот - рассказывает случайный анекдот"""
            joke = random.choice(self.jokes)
            
            await self.twitch_api.reply_to_message(
                channel_name=ctx.channel.name,
                message=joke,
                reply_to_msg_id=ctx.message.id
            )
            logger.info(f"User {ctx.author.name} requested a joke") 