import logging
import random
from twitchio.ext import commands
from commands import BotCommand
from utils.word_filter import word_filter
from collections import deque
import time

logger = logging.getLogger('twitch_bot')

class FunnyCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        # Store last 100 messages with their IDs
        self.message_history = deque(maxlen=100)
        
        # Add global cooldown tracking
        self.last_global_funny = 0
        self.global_funny_cooldown = 10  # 10 seconds global cooldown

    def register_commands(self):
        """Register funny command with the bot"""
        
        # Responses when someone tries to use funny command on the bot
        self.bot_defense_responses = [
            "ты пытался меня выставить клоуном, но нет, ты сам клоун!",
            "хотел выставить меня дураком? Ты уже родился таким, гений!",
            "Пытался сделать из меня посмешище? Ты сам посмешище, утырок!",
            "хотел унизить меня? Я унижу тебя так, что мама не узнает!"
        ]
        
        # Register a message listener with the bot if it doesn't exist yet
        if not hasattr(self.bot, 'message_listeners'):
            self.bot.message_listeners = []
        
        # Add our listener function to the bot's list of listeners
        self.bot.message_listeners.append(self.on_message)
        
        # If this is the first command module to register, patch the bot's event_message method
        if not hasattr(self.bot, '_original_event_message'):
            # Store the original event_message method
            self.bot._original_event_message = self.bot.event_message
            
            # Create a new event_message method that calls all listeners
            async def new_event_message(message):
                # Call the original event_message first
                if self.bot._original_event_message:
                    await self.bot._original_event_message(message)
                
                # Then call all registered message listeners
                if hasattr(self.bot, 'message_listeners'):
                    for listener in self.bot.message_listeners:
                        try:
                            await listener(message)
                        except Exception as e:
                            logger.error(f"Error in message listener: {str(e)}")
            
            # Replace the bot's event_message with our new one
            self.bot.event_message = new_event_message
        
        @self.bot.command(name="смешно")
        async def funny_command(ctx: commands.Context):
            """Command to react to a funny message"""
            # Check global cooldown first
            current_time = time.time()
            if current_time - self.last_global_funny < self.global_funny_cooldown:
                return
            
            try:
                logger.info("====== FUNNY COMMAND TRIGGERED ======")
                logger.info(f"Author: {ctx.author.name}")
                logger.info(f"Message content: {ctx.message.content}")
                logger.info(f"Message tags: {ctx.message.tags}")
                
                # List of possible funny reactions
                funny_reactions = [
                    "очень смешно, иди нахуй imba",
                    "пхаха, так смешно, аж в бан тебя отправить захотелось",
                    "о, великий юморист, как же я не умер от смеха",
                    "пхах, это было так 'смешно', что я чуть не блеванул",
                    "о да, я прям в экстазе от твоей тупой херни",
                    "пхах, это твой юмор? Серьёзно, вызови врача",
                    "пхах, это твой юмор? Ну ты и конч, поздравляю",
                    "о, гений с шуткой уровня мусорки",
                    "браво, ты изобрёл новый жанр — унылый пиздец",
                    "о, великий шутник, твой высер — шедевр кринжа",
                    "ржу, но только потому, что ты такой нелепый",
                    "пиздец, ты реально считаешь это смешным, да?"
                ]
                
                # Choose a random reaction
                reaction = random.choice(funny_reactions)
                
                # Get reply information from tags
                reply_to_user = ctx.message.tags.get('reply-parent-user-login')
                reply_to_msg_id = ctx.message.tags.get('reply-parent-msg-id')
                
                logger.info(f"Reply to user: {reply_to_user}")
                logger.info(f"Reply to message ID: {reply_to_msg_id}")
                
                if reply_to_user and reply_to_msg_id:
                    # Check if the reply is to the bot itself
                    if reply_to_user.lower() == self.bot.bot_username.lower():
                        random_response = random.choice(self.bot_defense_responses)
                        message = f"@{ctx.author.name}, {random_response}"
                        await self.send_safe(ctx, message)
                        logger.info(f"User {ctx.author.name} tried to use funny command on the bot")
                        return
                    
                    # Check if the reaction contains banned phrases
                    is_safe, _ = word_filter.filter_message(reaction)
                    if not is_safe:
                        # Choose a safer reaction if the original contains banned phrases
                        safer_reactions = [
                            "ну и юморок у тебя",
                            "это что за шутка такая?",
                            "ты серьезно считаешь это смешным?",
                            "я вежливо промолчу о качестве юмора"
                        ]
                        reaction = random.choice(safer_reactions)
                    
                    # Send reply using raw IRC command
                    await ctx.channel._ws.send(f"@reply-parent-msg-id={reply_to_msg_id} PRIVMSG #{ctx.channel.name} :{reaction}")
                    logger.info(f"User {ctx.author.name} used the funny command in reply to {reply_to_user}")
                else:
                    # No reply context found
                    message = "Используйте эту команду в ответ на сообщение, которое вы считаете смешным!"
                    await self.send_safe(ctx, message)
                    logger.info(f"User {ctx.author.name} used the funny command without replying to a message")
                
                # Update global cooldown timestamp after successful funny
                self.last_global_funny = time.time()
            except Exception as e:
                logger.error(f"Error in funny command: {str(e)}")
                logger.exception("Full traceback:")
    
    async def on_message(self, message):
        """Store messages for reply tracking"""
        # Add message to history
        self.message_history.append(message)