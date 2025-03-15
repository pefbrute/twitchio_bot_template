import logging
import re
import os
from commands import BotCommand
from twitchio.ext import commands
from .responses_manager import ResponsesManager
import spacy
from functools import lru_cache
import pymorphy2
from utils.permission_manager import mod_only

logger = logging.getLogger('twitch_bot')

class ChatMonitorCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        
        # Set debug level for logger
        logger.setLevel(logging.DEBUG)
        
        # Register message listener
        self.bot.message_listeners.append(self.monitor_chat)
        
        # Initialize processed messages set
        self.processed_messages = set()
        
        # Initialize pymorphy2
        self.morph = pymorphy2.MorphAnalyzer()
        
        try:
            # Используем маленькую модель вместо большой
            self.nlp = spacy.load("ru_core_news_sm")
            logger.info("Successfully loaded spaCy model")
        except IOError:
            logger.warning("Could not load spaCy model, falling back to regex patterns")
            self.nlp = None
        
        # Initialize responses manager
        self.responses_manager = ResponsesManager()
        
        # Keywords for voice acting questions
        self.voice_keywords = [
            # Существительные
            "озвучка", "озвучивание", "войс", "голос", "дабберы",
            "дубляж", "перевод", "переводчик", "студия",
            # Глаголы
            "озвучивать", "озвучить", "дублировать", "переводить",
            # Сленг
            "озвучкер", "войсер", "даббер"
        ]
        
        # Добавим список вопросительных слов
        self.question_words = {
            "что", "как", "какой", "где", "когда", "почему", "зачем", "чей", 
            "кто", "куда", "откуда", "чо", "че", "шо", "какая", "какое", "какие"
        }
        
        # Define reusable pattern parts
        self.pattern_parts = {
            'question_start': r'(?:какой|какая|какое|что за|чо за|че за|как|кто)',
            'time_context': r'(?:сейчас )?',
            'endings': r'(?:\s|\?|$)',
            'playing_verbs': r'(?:играе(?:шь|те|м)|рубите|гоняете)',
        }

        # Define specific keywords for each type
        self.type_keywords = {
            'anime': {
                'main': r'(?:аниме|анимэ)',
                'verbs': r'(?:смотр)',
            },
            'game': {
                'main': r'(?:игра|игрушка)',
                'prefixes': r'(?:в |во )?',
                'extra': r'(?:во что|чем)',
            },
            'difficulty': {
                'main': r'(?:сложность|сложности|difficulty)',
                'extra': r'(?:уровень|уровне)',
                'prefixes': r'(?:на |в )?',
            },
            'anime_voice': {
                'main': r'(?:озвучка|озвучивание|войс|голос|дабберы|дубляж|перевод)',
                'verbs': r'(?:озвучил|дублировал|переводил)',
            }
        }

        # Build patterns dynamically
        self.patterns = {}
        
        for type_name, keywords in self.type_keywords.items():
            patterns_for_type = []
            
            # Basic question pattern
            patterns_for_type.append(
                f"{self.pattern_parts['question_start']} "
                f"{self.pattern_parts['time_context']}"
                f"{keywords['main']}"
                f"{self.pattern_parts['endings']}"
            )
            
            # Simple form pattern (e.g. "сложность?")
            patterns_for_type.append(
                f"^{keywords['main']}\??$"
            )
            
            # Add type-specific patterns
            if 'prefixes' in keywords:
                patterns_for_type.append(
                    f"{keywords['prefixes']}{self.pattern_parts['question_start']} "
                    f"{keywords['main']}"
                    f"{self.pattern_parts['endings']}"
                )
            
            if 'verbs' in keywords:
                patterns_for_type.append(
                    f"{self.pattern_parts['question_start']} "
                    f"{self.pattern_parts['time_context']}"
                    f"{keywords['verbs']}"
                    f"{self.pattern_parts['endings']}"
                )
            
            if 'extra' in keywords:
                patterns_for_type.append(
                    f"{keywords['extra']} "
                    f"{self.pattern_parts['time_context']}"
                    f"{self.pattern_parts['playing_verbs']}"
                    f"{self.pattern_parts['endings']}"
                )

            # Add special "чо по" pattern
            patterns_for_type.append(
                f"(?:чо|че|что) (?:по|за) "
                f"{keywords['main']}"
                f"{self.pattern_parts['endings']}"
            )

            # Combine all patterns for this type with OR operator
            self.patterns[type_name] = '|'.join(f"(?:{p})" for p in patterns_for_type)

        self._voice_question_cache = {}
        
    def register_commands(self):
        """Register commands for managing responses"""
        
        @self.bot.command(name="указатьаниме")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_anime(ctx):
            # Extract the new name from the message
            args = ctx.message.content.split(' ', 1)
            if len(args) < 2:
                await ctx.send(f"@{ctx.author.name}, укажите название аниме!")
                return
                
            new_name = args[1].strip()
            if self.responses_manager.set_name("anime", new_name):
                await ctx.send(f"@{ctx.author.name}, название аниме обновлено на '{new_name}'!")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось обновить название!")
        
        @self.bot.command(name="указатьигру")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_game(ctx):
            args = ctx.message.content.split(' ', 1)
            if len(args) < 2:
                await ctx.send(f"@{ctx.author.name}, укажите название игры!")
                return
                
            new_name = args[1].strip()
            if self.responses_manager.set_name("game", new_name):
                await ctx.send(f"@{ctx.author.name}, название игры обновлено на '{new_name}'!")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось обновить название!")
        
        @self.bot.command(name="указатьсложность")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_difficulty(ctx):
            args = ctx.message.content.split(' ', 1)
            if len(args) < 2:
                await ctx.send(f"@{ctx.author.name}, укажите сложность!")
                return
                
            new_name = args[1].strip()
            if self.responses_manager.set_name("difficulty", new_name):
                await ctx.send(f"@{ctx.author.name}, сложность обновлена на '{new_name}'!")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось обновить сложность!")
                
        @self.bot.command(name="показатьназвания")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def show_names(ctx):       
            names = self.responses_manager.get_all_names()
            response_text = "Текущие названия: "
            for name_type, name in names.items():
                display_type = {
                    "anime": "Аниме", 
                    "game": "Игра", 
                    "difficulty": "Сложность", 
                    "game_type": "Тип игры"
                }.get(name_type, name_type)
                response_text += f"{display_type}: '{name}', "
            
            await ctx.send(response_text[:-2])
            
        @self.bot.command(name="указатьозвучку")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_anime_voice(ctx):  
            args = ctx.message.content.split(' ', 1)
            if len(args) < 2:
                await ctx.send(f"@{ctx.author.name}, укажите озвучку аниме!")
                return
                
            new_name = args[1].strip()
            if self.responses_manager.set_name("anime_voice", new_name):
                await ctx.send(f"@{ctx.author.name}, озвучка аниме обновлена на '{new_name}'!")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось обновить озвучку!")

    @lru_cache(maxsize=1000)
    def _is_voice_question_cached(self, text):
        """Кэшированная версия проверки вопроса"""
        doc = self.nlp(text)
        return self._is_voice_question(doc)

    async def monitor_chat(self, message):
        """Monitor chat messages and respond to questions"""
        try:
            # Skip if message has no author or is from bot
            if not message.author:
                logger.debug("Skipping message without author")
                return
            
            if message.author.name.lower() == self.bot.nick.lower():
                logger.debug("Skipping bot's own message")
                return

            # Skip if message starts with "!"
            if message.content.startswith('!'):
                logger.debug("Skipping command message starting with '!'")
                return
                
            # Skip messages with less than 6 characters or more than 60 characters
            content_length = len(message.content.strip())
            if content_length < 6 or content_length > 60:
                logger.debug(f"Skipping message with length {content_length} (outside 6-60 range)")
                return
                
            # Skip single-word messages
            if len(message.content.strip().split()) <= 1:
                logger.debug("Skipping single-word message")
                return
                
            # Get message content and ID
            content = message.content.lower()
            msg_id = message.tags.get('id')
            
            # Skip if we've already processed this message
            if msg_id and msg_id in self.processed_messages:
                return
                
            logger.debug(f"Processing message: {content}")
            
            # Check for future/past context before pattern matching
            future_words = ["будет", "станет", "собирается", "планирует", "планируется"]
            past_words = ["делали", "была", "делалась", "делалось", "играли"]
            
            has_future = any(word in content for word in future_words)
            has_past = any(word in content for word in past_words)
            
            if has_future or has_past:
                logger.debug("Skipping due to non-current time context")
                return
            
            # Try spaCy first if available
            if self.nlp is not None:
                logger.debug("Using spaCy for processing")
                doc = self.nlp(content)
                
                # Log token information
                logger.debug("Token analysis:")
                for token in doc:
                    logger.debug(f"Token: {token.text}, POS: {token.pos_}, DEP: {token.dep_}")
                
                if self._is_voice_question_cached(content):
                    logger.debug("Detected voice question via spaCy")
                    response = self.responses_manager.get_response("anime_voice")
                    await self._send_response(message, response)
                    if msg_id:
                        self.processed_messages.add(msg_id)
                    return
                else:
                    logger.debug("Not detected as voice question via spaCy")
            
            # Fall back to regex patterns
            logger.debug("Falling back to regex patterns")
            matched = False
            for response_type, pattern in self.patterns.items():
                try:
                    if re.search(pattern, content, re.IGNORECASE):
                        logger.debug(f"Matched pattern for type: {response_type}")
                        matched = True
                        response = self.responses_manager.get_response(response_type)
                        await self._send_response(message, response)
                        if msg_id:
                            self.processed_messages.add(msg_id)
                        break
                except re.error as e:
                    logger.error(f"Invalid regex pattern for {response_type}: {str(e)}")
            
            if not matched:
                logger.debug("No patterns matched")
            
            # Clean up old message IDs occasionally
            if len(self.processed_messages) > 1000:
                self.processed_messages.clear()
                
        except Exception as e:
            logger.error(f"Error in chat monitor: {str(e)}")
            logger.exception("Full traceback:")

    def _get_lemma(self, word):
        """Get lemma (normal form) of a word using pymorphy2"""
        return self.morph.parse(word)[0].normal_form

    def _is_voice_question(self, doc):
        """Check if message is asking about voice acting using NLP"""
        # Check for voice keywords using lemmas and word roots
        voice_words = []
        for token in doc:
            lemma = self._get_lemma(token.text)
            # Проверяем и слово, и его лемму, и начало слова
            if (lemma in self.voice_keywords or 
                token.text in self.voice_keywords or
                any(lemma.startswith(keyword) for keyword in ["озвуч", "дубл", "перевод"]) or
                any(token.text.startswith(keyword) for keyword in ["озвуч", "дубл", "перевод"])):
                voice_words.append(token.text)
        
        has_voice_word = bool(voice_words)
        
        # Check for question words using lemmas
        question_words = [
            token.text for token in doc 
            if self._get_lemma(token.text) in self.question_words
        ]
        
        has_question = bool(question_words)
        
        # Check for special patterns
        has_cho_po = "чо по" in doc.text.lower()
        
        # Check for context indicators
        context_words = ["эта", "это", "этот", "текущ", "данн", "сейчас"]
        has_current_context = any(word in doc.text.lower() for word in context_words)
        
        # Check for past tense indicators
        past_words = ["делали", "была", "делалась", "делалось"]
        has_past_context = any(word in doc.text.lower() for word in past_words)
        
        # Check for future tense indicators
        future_words = ["будет", "станет", "собирается", "планирует", "планируется"]
        has_future_context = any(word in doc.text.lower() for word in future_words)
        
        # Check for anime-related words using lemmas
        anime_words = [
            token.text for token in doc 
            if self._get_lemma(token.text) in ["аниме", "анимэ", "анимешка"]
        ]
        has_anime = bool(anime_words)
        
        # Detailed logging
        logger.debug(f"Message: '{doc.text}'")
        logger.debug(f"Token lemmas: {[self._get_lemma(token.text) for token in doc]}")
        logger.debug(f"Voice words found: {voice_words}")
        logger.debug(f"Question words found: {question_words}")
        logger.debug(f"Has current context: {has_current_context}")
        logger.debug(f"Has past context: {has_past_context}")
        logger.debug(f"Has future context: {has_future_context}")
        logger.debug(f"Has cho po: {has_cho_po}")
        logger.debug(f"Anime words found: {anime_words}")
        
        # Если есть "чо по" и слово связанное с озвучкой - это точно вопрос про текущую озвучку
        if has_cho_po and has_voice_word:
            logger.debug("Matched by 'чо по' + voice word")
            return True
            
        # Если есть вопросительное слово и слово про озвучку
        if has_question and has_voice_word:
            # Проверяем контекст
            if has_current_context:
                logger.debug("Matched by question word + voice word (explicit current context)")
                return True
            if has_future_context or has_past_context:
                logger.debug("Skipped due to non-current time context")
                return False
            # Если нет явных временных маркеров, считаем что вопрос о текущем
            logger.debug("Matched by question word + voice word (implicit current context)")
            return True
            
        # Check if message ends with question mark
        ends_with_question = doc.text.strip().endswith('?')
        
        # Иначе проверяем стандартные условия
        result = has_voice_word and (has_question or (has_anime and ends_with_question))
        if result and (has_past_context or has_future_context) and not has_current_context:
            result = False
            logger.debug("Skipped due to non-current time context")
            
        logger.debug(f"Final result: {result}")
        return result

    async def _send_response(self, message, response):
        """Send a response to the chat"""
        await self.bot.api.reply_to_message(
            message.channel.name,
            response,
            message.tags.get('id')
        ) 