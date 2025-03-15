import logging
import random
from twitchio.ext import commands
from commands import BotCommand
from api_commands.twitch_api import TwitchAPI
from .roulette_manager import RouletteManager
from commands.balance.balance_manager import balance_manager

logger = logging.getLogger('twitch_bot')

class RouletteCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.twitch_api = TwitchAPI(bot)
        self.roulette_manager = RouletteManager()
        
        # Сообщения при проигрыше (timeout)
        self.lose_messages = [
            "ВЫСТРЕЛ В УПОР — {time} в могиле, неудачник DIESOFCRINGE",
            "БАХ! Мозги на стенке, {time} в отключке DIESOFCRINGE",
            "ПРЯМО В ЛОБ! {time} гнить в больнице DIESOFCRINGE",
            "Промахнулся и сдох — {time} таймаута, лузер DIESOFCRINGE",
            "Добро пожаловать в гроб, {time} отдыха DIESOFCRINGE"
        ]
        
        # Сообщения при выигрыше (выживании)
        self.win_messages = [
            "*щелчок* — не сдох, мразь! Осталось {shots}/6 патронов PogChamp",
            "Пронесло, крыса! Ещё {shots}/6 попыток осталось monkaS",
            "Выжил, ублюдок! {shots}/6 патронов в барабане EZ",
            "*клик* — пусто! {shots}/6 выстрелов осталось PauseChamp",
            "Повезло, тварь! Осталось всего {shots}/6 патронов Kappa"
        ]

        # Add messages for stopping game
        self.stop_win_messages = [
            "Остановился прямо перед смертью! Награда: {reward} рублей PogChamp",
            "Чуйка не подвела! Получай {reward} рублей за интуицию POGGERS",
            "Вовремя соскочил! Забирай {reward} рублей EZ",
            "Профессиональный игрок! {reward} рублей твои PogU",
            "Мастер интуиции! Награда: {reward} рублей PETTHEPEEPO"
        ]
        
        self.stop_fail_messages = [
            "Слился, когда до смерти было далеко! Патрон был через {death_shots} выстрелов KEKW",
            "Не дотерпел! А ведь смерть ждала через {death_shots} выстрелов Jebaited",
            "Рано сдался! Патрон был в {death_shots} выстрелах от тебя 4Head",
            "Слабак! Бросил игру, когда до смерти оставалось {death_shots} выстрелов NotLikeThis",
            "Трус! А ведь смерть была в {death_shots} выстрелах от тебя KEKL"
        ]

    def register_commands(self):
        """Register roulette command with the bot"""
        
        @self.bot.command(name="рулетка")
        async def roulette_command(ctx: commands.Context):
            """Command that has a chance to timeout the user who uses it"""
            try:
                message_parts = ctx.message.content.split()
                is_mod = ctx.author.is_mod or ctx.author.name.lower() == ctx.channel.name.lower()
                
                # Get message ID for reply
                reply_to_msg_id = ctx.message.tags.get('id')
                
                if len(message_parts) > 1 and message_parts[1].startswith('@'):
                    if not is_mod:
                        await self.twitch_api.reply_to_message(
                            ctx.channel.name,
                            "только модераторы могут играть в рулетку с другими! NotLikeThis",
                            reply_to_msg_id
                        )
                        return
                    target_user = message_parts[1][1:]  # Remove @ symbol
                else:
                    target_user = ctx.author.name

                # Get target user ID
                if target_user != ctx.author.name:
                    target_user_id = await self.twitch_api.get_user_id(target_user)
                    if not target_user_id:
                        await self.twitch_api.reply_to_message(
                            ctx.channel.name,
                            f"не удалось найти пользователя {target_user} NotLikeThis",
                            reply_to_msg_id
                        )
                        return
                else:
                    target_user_id = ctx.message.tags['user-id']

                # Pull the trigger
                is_shot, timeout_duration = self.roulette_manager.pull_trigger(target_user_id)
                
                if is_shot:
                    # User lost the roulette
                    broadcaster_id = ctx.message.tags['room-id']
                    
                    # Timeout the user using TwitchAPI
                    success = await self.twitch_api.timeout_user(
                        broadcaster_id=broadcaster_id,
                        target_user_id=target_user_id,
                        duration=timeout_duration,
                        reason='Проиграл в русскую рулетку'
                    )
                    
                    if success:
                        minutes = timeout_duration // 60
                        seconds = timeout_duration % 60
                        time_text = f"{minutes}м {seconds}с" if minutes > 0 else f"{seconds}с"
                        
                        message = random.choice(self.lose_messages).format(time=time_text)
                        # Use regular message for timeout case
                        await ctx.send(f"@{target_user} {message}")
                        logger.info(f"User {target_user} lost roulette and got {timeout_duration}s timeout")
                    else:
                        logger.error(f"Failed to timeout user {target_user}")
                        await self.twitch_api.reply_to_message(
                            ctx.channel.name,
                            "Технические неполадки, везучий... пока что MrDestructoid",
                            reply_to_msg_id
                        )
                else:
                    # Get remaining shots info
                    remaining_shots = self.roulette_manager.get_remaining_shots(target_user_id)
                    message = random.choice(self.win_messages).format(shots=remaining_shots)
                    # Use reply for survival case
                    await self.twitch_api.reply_to_message(ctx.channel.name, message, reply_to_msg_id)
                    logger.info(f"User {target_user} survived roulette, {remaining_shots} shots remaining")
                
            except Exception as e:
                logger.error(f"Failed to process roulette for user {ctx.author.name}: {str(e)}")
                await self.twitch_api.reply_to_message(
                    ctx.channel.name,
                    "Что-то пошло не так с рулеткой BibleThump",
                    reply_to_msg_id
                )

        @self.bot.command(name="рулстат")
        async def roulette_stats(ctx: commands.Context):
            """Show user's roulette statistics"""
            try:
                user_id = ctx.message.tags['user-id']
                stats = self.roulette_manager.get_stats(user_id)
                reply_to_msg_id = ctx.message.tags.get('id')
                
                await self.twitch_api.reply_to_message(
                    ctx.channel.name,
                    f"статистика: Игр: {stats['total_games']}, "
                    f"Смертей: {stats['deaths']}, "
                    f"Побед: {stats['wins']}, "
                    f"Выстрелов: {stats['shots_fired']}",
                    reply_to_msg_id
                )
            except Exception as e:
                logger.error(f"Failed to get stats for user {ctx.author.name}: {str(e)}")
                await self.twitch_api.reply_to_message(
                    ctx.channel.name,
                    "Не удалось получить статистику BibleThump",
                    reply_to_msg_id
                )

        @self.bot.command(name="рулстоп")
        async def stop_roulette(ctx: commands.Context):
            """Command to stop current roulette game"""
            try:
                user_id = ctx.message.tags['user-id']
                reply_to_msg_id = ctx.message.tags.get('id')
                
                # Try to stop the game
                is_win, reward, remaining_shots, shots_until_death = self.roulette_manager.stop_game(user_id)
                
                if is_win:
                    # Add reward to user's balance
                    balance_manager.adjust_balance(ctx.author.name, reward)
                    
                    message = random.choice(self.stop_win_messages).format(reward=reward)
                    await self.twitch_api.reply_to_message(
                        ctx.channel.name,
                        message,
                        reply_to_msg_id
                    )
                    logger.info(f"User {ctx.author.name} won roulette stop with {reward} reward")
                else:
                    # Customize message based on how close they were to death
                    if shots_until_death <= 2:
                        message = random.choice([
                            f"Вовремя остановился! Смерть была всего в {shots_until_death} выстрелах от тебя monkaS",
                            f"Чуть не умер! Патрон был через {shots_until_death} выстрела(ов) monkaW",
                            f"Повезло! Смерть ждала тебя через {shots_until_death} выстрела(ов) PauseChamp"
                        ])
                    else:
                        message = random.choice(self.stop_fail_messages).format(
                            death_shots=shots_until_death
                        )
                    
                    await self.twitch_api.reply_to_message(
                        ctx.channel.name,
                        message,
                        reply_to_msg_id
                    )
                    logger.info(f"User {ctx.author.name} stopped roulette with {remaining_shots} shots remaining, {shots_until_death} until death")
                    
            except Exception as e:
                logger.error(f"Failed to process roulette stop for user {ctx.author.name}: {str(e)}")
                await self.twitch_api.reply_to_message(
                    ctx.channel.name,
                    "Что-то пошло не так при остановке рулетки BibleThump",
                    reply_to_msg_id
                )