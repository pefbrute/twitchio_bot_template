import logging
import random
from twitchio.ext import commands
from commands.balance.balance_manager import balance_manager
from utils.cooldown_manager import cooldown_manager, with_cooldown
from commands import BotCommand
from .steal_chance_commands import StealChanceCommands
from .steal_logic import try_steal

logger = logging.getLogger('twitch_bot')

class StealCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        # Use the same privileged users list from cooldown_manager
        self.privileged_users = cooldown_manager.privileged_users
        # Starter balance for new users
        self.starter_balance = 100
        
        # Инициализация команд управления шансами кражи
        self.steal_chance_commands = StealChanceCommands(bot)
        
        # Load messages
        self.steal_success_messages = [
            "украл {amount:,}₽ у {victim}! EZ",
            "спёр {amount:,}₽ у {victim}! LUL",
            "забрал {amount:,}₽ у {victim}! CashTime",
            "снял {amount:,}₽ с {victim}! TriHard"
        ]
        
        self.steal_failure_messages = [
            "поймали при краже у {victim}! Штраф {penalty:,}₽ shook",
            "провалил кражу у {victim}! Потерял {penalty:,}₽ shook",
            "не смог украсть у {victim}! Штраф {penalty:,}₽ shook",
            "засветился с {victim}! Отдал {penalty:,}₽ shook"
        ]
        
        self.steal_no_money_messages = [
            "у {victim} пусто! PunOko",
            "нечего воровать у {victim}! Sadge",
            "{victim} без денег! BibleThump",
            "{victim} - нищий! LUL"
        ]
        
        self.steal_no_money_thief_messages = [
            "пойман при краже у {victim}! shook",
            "промах с кражей у {victim}! shook",
            "не смог обокрасть {victim}! shook",
            "позорная кража у {victim}! shook"
        ]
        
        # Вместо регистрации в конструкторе, создадим метод для регистрации
        self.register_steal_command()
        
    def register_steal_command(self):
        """Register steal command if it doesn't exist"""
        if 'украсть' not in self.bot.commands:
            @self.bot.command(name="украсть")
            @with_cooldown(user_cooldown=60, global_cooldown=10)
            async def steal_command(ctx: commands.Context):
                """Command to attempt stealing rubles from another user"""
                thief = ctx.author.name.lower()
                message_content = ctx.message.content
                
                # Parse to find the victim
                victim = None
                
                # Check for reply first
                reply_to_user = ctx.message.tags.get('reply-parent-user-login')
                if reply_to_user:
                    victim = reply_to_user.lower()
                else:
                    # Try to find @mention in the message
                    message_parts = message_content.split()
                    if len(message_parts) > 1:
                        for part in message_parts[1:]:
                            if part.startswith('@'):
                                victim = part[1:].lower()  # Remove @ symbol
                                break
                
                # If no victim specified, choose random user
                if not victim:
                    # Get a random user from recent chatters
                    if hasattr(self.bot, 'recent_chatters') and self.bot.recent_chatters:
                        potential_victims = [
                            name.lower() for name in self.bot.recent_chatters 
                            if name.lower() != thief and 
                               name.lower() != self.bot.bot_username.lower()
                        ]
                        if potential_victims:
                            victim = random.choice(potential_victims)
                    
                    # If still no victim, use default names
                    if not victim:
                        default_victims = ["случайного_зрителя", "телезрителя", "прохожего"]
                        victim = random.choice(default_victims)
                
                # Check if thief is trying to steal from themselves
                if victim == thief:
                    await ctx.send(f"@{thief}, нельзя украсть у самого себя!")
                    return
                
                # Check if victim username is safe
                if victim not in ["случайного_зрителя", "телезрителя", "прохожего"]:
                    if hasattr(self.bot, 'username_filter'):
                        is_safe, _ = self.bot.username_filter.is_safe(victim)
                        if not is_safe:
                            await ctx.send(f"@{thief}, у этого пользователя нельзя красть.")
                            return
                
                # Check thief's balance - give starter amount if new user
                thief_balance = balance_manager.get_balance(thief)
                
                # Give starter balance only if they haven't received it before
                if thief_balance == 0 and not balance_manager.has_received_starter(thief):
                    thief_balance = self.starter_balance
                    balance_manager.give_starter_balance(thief, self.starter_balance)
                    await ctx.send(f"@{thief}, добро пожаловать! Ты получаешь {self.starter_balance} рублей перед тем, как начать свою преступную карьеру.")
                
                # Check if victim is the bot
                if victim == self.bot.bot_username.lower():
                    # Get thief's current balance
                    if thief_balance > 0:
                        # Set thief's balance to 0
                        balance_manager.adjust_balance(thief, -thief_balance)
                        
                        # Add their balance to bot's balance
                        balance_manager.adjust_balance(self.bot.bot_username.lower(), thief_balance)
                        
                        await ctx.send(f"@{thief}, по непонятным причинам, твой баланс ({thief_balance:,} руб.) обнулился и все твои деньги оказались на счету бота!")
                        logger.info(f"User {thief} tried to steal from bot and lost {thief_balance} rubles")
                    else:
                        await ctx.send(f"@{thief}, у бота нельзя украсть! Бот всегда начеку.")
                    return
                
                # Check if user is mod or privileged user
                is_privileged = (
                    thief in self.privileged_users or 
                    ctx.author.is_mod
                )
                
                # Use the new try_steal function
                result = try_steal(thief, victim, is_privileged, force_starter_chance=(thief_balance == 0))
                
                # Handle response based on result
                if result is None:
                    # Global cooldown result
                    return
                
                # Handle successful theft
                if result['success']:
                    message = random.choice(self.steal_success_messages).format(
                        amount=result['amount'],
                        victim=victim,
                        thief_balance=result['thief_balance'],
                        victim_balance=result['victim_balance']
                    )
                    await ctx.send(f"@{thief} {message}")
                    logger.info(f"User {thief} stole {result['amount']} rubles from {victim}")
                    return
                
                # Handle failure due to empty pockets
                if result['reason'] == 'no_money':
                    message = random.choice(self.steal_no_money_messages).format(
                        victim=victim
                    )
                    await ctx.send(f"@{thief} {message}")
                    logger.info(f"User {thief} tried to steal from {victim} but they have no money")
                    return
                
                # Handle failed theft with penalty
                if result['reason'] == 'failed':
                    message = random.choice(self.steal_failure_messages).format(
                        victim=victim,
                        penalty=result['penalty'],
                        thief_balance=result['thief_balance'],
                        victim_balance=result['victim_balance']
                    )
                    await ctx.send(f"@{thief} {message}")
                    logger.info(f"User {thief} failed to steal from {victim}, lost {result['penalty']} rubles")
                    return
                
                # Handle failure when thief has no money
                if result['reason'] == 'no_money_thief':
                    message = random.choice(self.steal_no_money_thief_messages).format(
                        victim=victim
                    )
                    await ctx.send(f"@{thief} {message}")
                    logger.info(f"User {thief} failed to steal from {victim} (no money to pay penalty)")
                    return
                
                # Handle cooldown response
                if result['reason'] == 'cooldown':
                    await ctx.send(f"@{thief}, подожди еще {result['remaining']} секунд перед тем, как снова воровать!")
                    return

    def register_commands(self):
        """This method is called by BotCommand parent class"""
        # Оставляем пустым, так как регистрация происходит в register_steal_command
        pass