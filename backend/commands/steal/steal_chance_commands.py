import logging
from twitchio.ext import commands
from .steal_chance_manager import steal_chance_manager
from utils.permission_manager import mod_only

logger = logging.getLogger('twitch_bot')

class StealChanceCommands:
    def __init__(self, bot):
        self.bot = bot
        self.steal_chance_manager = steal_chance_manager
        
        # Регистрация команд
        self.register_commands()
        
    def register_commands(self):
        @self.bot.command(name="шанс-кражи")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_steal_chance(ctx: commands.Context):
            message_parts = ctx.message.content.split()
            
            # Проверка наличия username
            if len(message_parts) < 2:
                await ctx.send(f"@{ctx.author.name}, использование: !шанс-кражи @username [шанс]")
                return
                
            # Парсинг имени пользователя
            username = message_parts[1].strip('@').lower()
            
            # Если передан только username - показываем текущий шанс
            if len(message_parts) == 2:
                chance = self.steal_chance_manager.get_custom_steal_chance(username)
                if chance is not None:
                    chance_percent = chance * 100
                    await ctx.send(f"@{ctx.author.name}, шанс кражи для @{username}: {chance_percent}%")
                else:
                    await ctx.send(f"@{ctx.author.name}, для @{username} не установлен пользовательский шанс кражи (используется стандартный 40%)")
                return
            
            # Если передан шанс - устанавливаем новое значение
            try:
                chance_percent = float(message_parts[2])
                if not 0 <= chance_percent <= 100:
                    raise ValueError
                chance = chance_percent / 100.0  # Конвертация в десятичную дробь
            except ValueError:
                await ctx.send(f"@{ctx.author.name}, шанс должен быть числом от 0 до 100")
                return
                
            # Установка пользовательского шанса
            result = self.steal_chance_manager.set_custom_steal_chance(username, chance)
            
            if result:
                await ctx.send(f"@{ctx.author.name}, установлен шанс кражи {chance_percent}% для пользователя @{username}")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось установить шанс кражи для @{username}")
        
        @self.bot.command(name="шанс-жертвы")
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def set_victim_chance(ctx: commands.Context):
            message_parts = ctx.message.content.split()
            
            # Проверка наличия username
            if len(message_parts) < 2:
                await ctx.send(f"@{ctx.author.name}, использование: !шанс-жертвы @username [шанс]")
                return
                
            # Парсинг имени пользователя
            username = message_parts[1].strip('@').lower()
            
            # Если передан только username - показываем текущий шанс
            if len(message_parts) == 2:
                chance = self.steal_chance_manager.get_custom_victim_chance(username)
                if chance is not None:
                    chance_percent = chance * 100
                    await ctx.send(f"@{ctx.author.name}, шанс быть обкраденным для @{username}: {chance_percent}%")
                else:
                    await ctx.send(f"@{ctx.author.name}, для @{username} не установлен пользовательский шанс быть обкраденным (используется шанс вора или стандартный 40%)")
                return
            
            # Если передан шанс - устанавливаем новое значение
            try:
                chance_percent = float(message_parts[2])
                if not 0 <= chance_percent <= 100:
                    raise ValueError
                chance = chance_percent / 100.0  # Конвертация в десятичную дробь
            except ValueError:
                await ctx.send(f"@{ctx.author.name}, шанс должен быть числом от 0 до 100")
                return
                
            # Установка пользовательского шанса
            result = self.steal_chance_manager.set_custom_victim_chance(username, chance)
            
            if result:
                await ctx.send(f"@{ctx.author.name}, установлен шанс быть обкраденным {chance_percent}% для пользователя @{username}")
            else:
                await ctx.send(f"@{ctx.author.name}, не удалось установить шанс быть обкраденным для @{username}")