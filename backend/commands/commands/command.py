import logging
from twitchio.ext import commands
from commands import BotCommand
from utils.word_filter import word_filter

logger = logging.getLogger('twitch_bot')

class CommandsListCommand(BotCommand):
    def register_commands(self):
        """Register commands list command with the bot"""
        
        @self.bot.command(name="к")
        async def commands_list(ctx: commands.Context):
            """Command to list all available commands"""
            # Create a list of available commands, getting names from the commands dict
            command_list = list(self.bot._commands.keys())
            command_list.sort()  # Sort alphabetically
            
            # Format commands with the bot's prefix
            formatted_commands = [f"!{cmd}" for cmd in command_list]
            
            # Prepare the message without mentioning the user
            message = f"Доступные команды: {', '.join(formatted_commands)}"
            
            # Get the parent message ID from the context if this is a reply
            reply_to_msg_id = ctx.message.tags.get('reply-parent-msg-id')
            
            if reply_to_msg_id:
                # Use the reply_to_message method if we have a parent message ID
                await self.bot.api.reply_to_message(ctx.channel.name, message, reply_to_msg_id)
            else:
                # Fall back to regular send if no parent message ID is available
                await self.send_safe(ctx, message)
                
            logger.info(f"User {ctx.author.name} requested command list") 