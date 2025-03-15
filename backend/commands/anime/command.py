import logging
from twitchio.ext import commands
from commands import BotCommand

logger = logging.getLogger('twitch_bot')

class AnimeCommand(BotCommand):
    def register_commands(self):
        """Register anime-related commands with the bot"""
        
        @self.bot.command(name="аниме")
        async def anime_command(ctx: commands.Context):
            """Command to respond with anime information"""
            message = "аниме будет после аука, аук после 17 марта"
            
            try:
                # Сначала пробуем использовать встроенный метод reply
                await ctx.reply(message)
            except Exception as e:
                logger.error(f"Failed to send reply: {str(e)}")
                # Если не получилось, отправляем обычное сообщение
                await ctx.send(message)
                
            logger.info(f"User {ctx.author.name} used the anime command")
        
        @self.bot.command(name="аниме-озвучка")
        async def anime_voice_command(ctx: commands.Context):
            """Command to respond with anime voice actor information"""
            message = "аниме будет после аука, аук после 17 марта"
            
            try:
                await ctx.reply(message)
            except Exception as e:
                logger.error(f"Failed to send reply: {str(e)}")
                await ctx.send(message)
                
            logger.info(f"User {ctx.author.name} used the anime-voice command")