import logging
import random
import os
import sys
from commands import BotCommand
from utils.cooldown_manager import cooldown
from utils.permission_manager import mod_only

# Добавляем текущую директорию в путь для корректной работы импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

logger = logging.getLogger('twitch_bot')

class CasinoCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        
        # Импортируем менеджер баланса из модуля balance
        try:
            # Используем singleton экземпляр balance_manager вместо создания нового
            from commands.balance.balance_manager import balance_manager
            self.balance_manager = balance_manager
            logger.info("Casino module initialized with balance manager")
        except ImportError as e:
            logger.error(f"Failed to import balance_manager: {str(e)}")
            self.balance_manager = None
    
    def register_commands(self):
        """Регистрация команд казино"""
        
        @self.bot.command(name="казик")
        @cooldown(user_cd=30, global_cd=5)  # Кулдаун 30 секунд для пользователя, 5 секунд глобально
        async def casino_command(ctx):
            """Команда !казик [процент]"""
            try:
                if not self.balance_manager:
                    await ctx.send(f"@{ctx.author.name}, система баланса недоступна. Попробуйте позже.")
                    return
                
                # Разбираем сообщение
                message_parts = ctx.message.content.split()
                
                # Проверяем, указан ли процент
                if len(message_parts) < 2:
                    await ctx.send(f"@{ctx.author.name}, укажите процент от вашего баланса для ставки (1-100). Пример: !казино 50")
                    return
                
                # Получаем и проверяем процент
                try:
                    percentage = int(message_parts[1])
                    if percentage < 1 or percentage > 100:
                        await ctx.send(f"@{ctx.author.name}, процент должен быть от 1 до 100.")
                        return
                except ValueError:
                    await ctx.send(f"@{ctx.author.name}, укажите корректный процент от 1 до 100.")
                    return
                
                # Получаем текущий баланс пользователя
                username = ctx.author.name.lower()
                current_balance = self.balance_manager.get_balance(username)
                
                # Проверяем, есть ли у пользователя деньги
                if current_balance <= 0:
                    await ctx.send(f"@{ctx.author.name}, у вас нет денег для игры в казино.")
                    return
                
                # Рассчитываем ставку
                bet_amount = int(current_balance * percentage / 100)
                if bet_amount < 1:
                    bet_amount = 1  # Минимальная ставка - 1 рубль
                
                # Определяем результат (10% шанс на победу)
                win = random.random() < 0.1
                
                if win:
                    # Выигрыш - добавляем ставку к балансу
                    new_balance = self.balance_manager.adjust_balance(username, bet_amount)
                    formatted_bet = self.balance_manager.format_balance(bet_amount)
                    formatted_balance = self.balance_manager.format_balance(new_balance)
                    
                    await ctx.send(f"🎰 @{ctx.author.name} ВЫИГРАЛ в казино! Ставка: {formatted_bet} руб. ({percentage}%). "
                                  f"Новый баланс: {formatted_balance} руб. (+{formatted_bet} руб.)")
                    logger.info(f"User {username} won {bet_amount} rubles in casino. New balance: {new_balance}")
                else:
                    # Проигрыш - вычитаем ставку из баланса
                    new_balance = self.balance_manager.adjust_balance(username, -bet_amount)
                    formatted_bet = self.balance_manager.format_balance(bet_amount)
                    formatted_balance = self.balance_manager.format_balance(new_balance)
                    
                    await ctx.send(f"🎰 @{ctx.author.name} проиграл в казино. Ставка: {formatted_bet} руб. ({percentage}%). "
                                  f"Новый баланс: {formatted_balance} руб. (-{formatted_bet} руб.)")
                    logger.info(f"User {username} lost {bet_amount} rubles in casino. New balance: {new_balance}")
                
            except Exception as e:
                logger.error(f"Error in casino command: {str(e)}")
                await ctx.send(f"@{ctx.author.name}, произошла ошибка при выполнении команды казино.")
        
        # Команда для модераторов для изменения шанса выигрыша (временно)
        @self.bot.command(name="казик-шанс")
        @mod_only()
        async def casino_chance_command(ctx):
            """Команда !казик-шанс [процент] - только для модераторов"""
            try:
                message_parts = ctx.message.content.split()
                
                if len(message_parts) < 2:
                    await ctx.send(f"@{ctx.author.name}, укажите процент шанса выигрыша (1-100). Пример: !казино-шанс 10")
                    return
                
                try:
                    chance = int(message_parts[1])
                    if chance < 1 or chance > 100:
                        await ctx.send(f"@{ctx.author.name}, процент должен быть от 1 до 100.")
                        return
                    
                    # Обновляем шанс выигрыша в декораторе команды
                    # Это временное решение, в будущем лучше использовать конфигурационный файл
                    casino_command.__globals__['random'].random = lambda: random.random()  # Сбрасываем на случай, если была подмена
                    await ctx.send(f"@{ctx.author.name}, шанс выигрыша в казино установлен на {chance}%.")
                    logger.info(f"Casino win chance set to {chance}% by {ctx.author.name}")
                    
                except ValueError:
                    await ctx.send(f"@{ctx.author.name}, укажите корректный процент от 1 до 100.")
                    
            except Exception as e:
                logger.error(f"Error in casino chance command: {str(e)}")
                await ctx.send(f"@{ctx.author.name}, произошла ошибка при изменении шанса выигрыша.") 