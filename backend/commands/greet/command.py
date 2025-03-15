from commands import BotCommand
import logging

logger = logging.getLogger('twitch_bot')

class GreetCommand(BotCommand):
    """A simple command that greets users"""
    
    def register_commands(self):
        """Register the greet command"""
        
        @self.bot.command(name="greet")
        async def greet(ctx):
            """Send a friendly greeting message"""
            await ctx.send("Hello! Welcome to the stream! 👋") 