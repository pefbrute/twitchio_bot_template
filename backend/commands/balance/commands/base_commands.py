import logging
from twitchio.ext import commands
from ..balance_manager import balance_manager
from utils.cooldown_manager import cooldown
from utils.permission_manager import mod_only
import time

logger = logging.getLogger('twitch_bot')

class BaseBalanceCommands:
    def __init__(self, bot):
        self.bot = bot
        # Starter balance for new users
        self.starter_balance = 100
        # Remove privileged users list from here - rely on permission_manager instead
        self.privileged_users = []  # This should be empty, use permission_manager instead
        
    def register(self):
        """Register basic balance commands"""
        
        @self.bot.command(name="баланс")
        @cooldown(user_cd=5, global_cd=2)
        async def balance_command(ctx: commands.Context):
            """Show user's balance or another user's balance"""
            user = ctx.author.name.lower()
            message_parts = ctx.message.content.split()
            
            # Default to checking own balance
            target_user = user
            
            # Check if a user is specified
            if len(message_parts) > 1:
                specified_user = ''.join(c for c in message_parts[1] if c.isprintable()).strip()
                
                if specified_user.startswith('@'):
                    specified_user = specified_user[1:]  # Remove @ symbol
                
                if specified_user:  # If after cleaning it's not empty
                    target_user = specified_user.lower()
            
            # Check for reply context
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            if reply_to_user:
                target_user = reply_to_user.lower()
            
            # Get balance
            balance = balance_manager.get_balance(target_user)
            formatted_balance = balance_manager.format_balance(balance)
            
            # If checking own balance and haven't received starter
            if target_user == user and not balance_manager.has_received_starter(user):
                balance_manager.give_starter_balance(user, 100)
                await ctx.send(f"@{user}, добро пожаловать! Ты получаешь 100 рублей. Можешь использовать !украсть или !подарить-рубли")
                return
            
            # Format response based on whether checking own or other's balance
            if target_user == user:
                if balance == 0:
                    await ctx.send(f"@{user}, у тебя пусто в кармане! Попробуй что-нибудь украсть...")
                else:
                    await ctx.send(f"@{user}, на твоём счету {formatted_balance} рублей")
            else:
                if balance == 0:
                    await ctx.send(f"@{user}, у {target_user} пусто в кармане!")
                else:
                    await ctx.send(f"@{user}, на счету @{target_user} {formatted_balance} рублей")
            
            logger.info(f"User {user} checked balance for {target_user}: {formatted_balance} rubles")
            
        @self.bot.command(name="подарить-рубли")
        @cooldown(user_cd=30, global_cd=5)
        async def gift_command(ctx: commands.Context):
            """Command to gift rubles to another user"""
            sender = ctx.author.name.lower()
            message_content = ctx.message.content
            
            # Default values
            recipient = None
            amount = None
            
            # Parse the command and extract recipient and amount
            message_parts = message_content.split()
            
            # Check reply first
            reply_to_user = ctx.message.tags.get('reply-parent-user-login')
            if reply_to_user:
                recipient = reply_to_user.lower()
                # Parse amount from message
                if len(message_parts) > 1:
                    try:
                        # Try to parse amount from first part after command
                        amount = int(message_parts[1])
                    except ValueError:
                        pass
            elif len(message_parts) > 1:
                # No reply - check for @mention and amount
                for part in message_parts[1:]:
                    if part.startswith('@'):
                        recipient = part[1:].lower()  # Remove @ symbol
                    else:
                        try:
                            amount = int(part)
                        except ValueError:
                            pass
            
            # Validate recipient and amount
            if not recipient:
                await ctx.send(f"@{sender}, укажите получателя! Например: !подарить-рубли @username 100")
                return
            
            # Check if recipient is valid
            if hasattr(self.bot, 'username_filter'):
                is_safe, _ = self.bot.username_filter.is_safe(recipient)
                if not is_safe:
                    await ctx.send(f"@{sender}, этот пользователь не может получать подарки")
                    return
                    
            # Check for self-gifting
            if recipient == sender:
                await ctx.send(f"@{sender}, нельзя подарить рубли самому себе!")
                return
            
            # Check if amount is valid
            if not amount or amount <= 0:
                await ctx.send(f"@{sender}, укажите положительную сумму для подарка! Например: !подарить-рубли @{recipient} 100")
                return
            
            # Check sender's balance
            sender_balance = balance_manager.get_balance(sender)
            
            # Give starter balance if new user
            if sender_balance == 0:
                sender_balance = self.starter_balance
                balance_manager.adjust_balance(sender, self.starter_balance)
                await ctx.send(f"@{sender}, добро пожаловать! Ты получаешь {self.starter_balance} рублей.")
            
            # Check if sender has enough funds
            if sender_balance < amount:
                await ctx.send(f"@{sender}, у тебя недостаточно средств! На твоём счету только {sender_balance} рублей")
                return
            
            # Transfer the amount
            success, new_sender_balance, new_recipient_balance = balance_manager.transfer(sender, recipient, amount)
            
            if success:
                await ctx.send(f"@{sender} подарил {amount} рублей @{recipient}! Баланс отправителя: {new_sender_balance}, баланс получателя: {new_recipient_balance}")
                logger.info(f"User {sender} gifted {amount} rubles to {recipient}")
            else:
                await ctx.send(f"@{sender}, не удалось отправить подарок. Проверьте свой баланс.")
                
        @self.bot.command(name="лидеры")
        @cooldown(user_cd=20, global_cd=5)
        async def leaderboard_command(ctx: commands.Context):
            """Command to show the top 3 users by balance"""
            top_users = balance_manager.get_leaderboard(3)
            
            if not top_users:
                await ctx.send("Еще никто не накопил рублей! Будь первым с помощью !баланс")
                return
            
            # Format the leaderboard
            leaderboard_text = "Топ богачей: "
            for i, (username, data) in enumerate(top_users, 1):
                formatted_balance = balance_manager.format_balance(data['balance'])
                leaderboard_text += f"{i}. {username}: {formatted_balance} руб. "
            
            await ctx.send(leaderboard_text.strip())
            logger.info("Leaderboard requested by user")

        @self.bot.command(name="забрать")
        @cooldown(user_cd=5, global_cd=2)
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def take_money(ctx):
            """Command for mods/privileged users to take money from users"""
            # Parse command arguments
            parts = ctx.message.content.split()
            if len(parts) < 3:
                await ctx.send(f"@{ctx.author.name}, использование: !забрать @username сумма")
                return

            # Get target user and amount
            target = parts[1].strip('@').lower()
            try:
                amount = int(parts[2])
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await ctx.send(f"@{ctx.author.name}, сумма должна быть положительным числом")
                return

            # Get target's current balance
            current_balance = balance_manager.get_balance(target)
            if current_balance < amount:
                amount = current_balance  # Take all available money

            # Remove money from target
            if amount > 0:
                new_balance = balance_manager.adjust_balance(target, -amount)
                await ctx.send(f"@{ctx.author.name} забрал {amount:,}₽ у @{target}. Новый баланс: {new_balance:,}₽")
                logger.info(f"Mod {ctx.author.name} took {amount} rubles from {target}")

        @self.bot.command(name="начислить")
        @cooldown(user_cd=5, global_cd=2)
        @mod_only(specific_users=["fedor_jogaboga82"])
        async def give_money(ctx):
            """Command for mods/privileged users to give money to users"""
            # Parse command arguments
            parts = ctx.message.content.split()
            if len(parts) < 3:
                await ctx.send(f"@{ctx.author.name}, использование: !начислить @username сумма")
                return

            # Get target user and amount
            target = parts[1].strip('@').lower()
            try:
                amount = int(parts[2])
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await ctx.send(f"@{ctx.author.name}, сумма должна быть положительным числом")
                return

            # Add money to target
            new_balance = balance_manager.adjust_balance(target, amount)
            await ctx.send(f"@{ctx.author.name} начислил {amount:,}₽ пользователю @{target}. Новый баланс: {new_balance:,}₽")
            logger.info(f"Mod {ctx.author.name} gave {amount} rubles to {target}")

        @self.bot.command(name="раздать")
        @cooldown(user_cd=30, global_cd=10)
        async def distribute_command(ctx: commands.Context):
            """Distribute money to random users"""
            sender = ctx.author.name.lower()
            message_parts = ctx.message.content.split()
            
            # Check command format
            if len(message_parts) != 3:
                await ctx.send(f"@{sender}, использование: !раздать <количество_людей> <общая_сумма>")
                return
            
            try:
                num_recipients = int(message_parts[1])
                total_amount = int(message_parts[2])  # Это общая сумма для раздачи
            except ValueError:
                await ctx.send(f"@{sender}, укажите числа для количества людей и суммы")
                return
            
            # Validate numbers
            if num_recipients <= 0 or total_amount <= 0:
                await ctx.send(f"@{sender}, укажите положительные числа")
                return
            
            # Calculate amount per person
            amount_per_person = total_amount // num_recipients
            if amount_per_person <= 0:
                await ctx.send(f"@{sender}, сумма слишком мала для раздачи {num_recipients} людям")
                return
            
            logger.info(f"Initial values: num_recipients={num_recipients}, total_amount={total_amount}, amount_per_person={amount_per_person}")
            
            # Check sender's balance
            sender_balance = balance_manager.get_balance(sender)
            if sender_balance < total_amount:
                await ctx.send(f"@{sender}, недостаточно средств! Нужно: {total_amount:,} руб.")
                return
            
            # Get potential recipients from recent chatters and channel users
            potential_recipients = []
            
            # Try getting chatters from channel users first
            if ctx.channel:
                try:
                    # Get current chatters in the channel
                    chatters = [user.name.lower() for user in ctx.channel.chatters]
                    potential_recipients.extend([
                        name for name in chatters
                        if name != sender and 
                           name != self.bot.bot_username.lower()
                    ])
                    logger.info(f"Got {len(potential_recipients)} potential recipients from channel chatters")
                except Exception as e:
                    logger.error(f"Error getting channel chatters: {str(e)}")
            
            # Add recent chatters if they're not already in the list
            if hasattr(self.bot, 'recent_chatters') and self.bot.recent_chatters:
                for name in self.bot.recent_chatters:
                    name = name.lower()
                    if (name != sender and 
                        name != self.bot.bot_username.lower() and 
                        name not in potential_recipients):
                        potential_recipients.append(name)
            
            # Log potential recipients for debugging
            logger.info(f"Total potential recipients: {potential_recipients}")
            
            if not potential_recipients:
                await ctx.send(f"@{sender}, нет активных пользователей для раздачи")
                return
            
            # If we have fewer recipients than requested, adjust the numbers
            if len(potential_recipients) < num_recipients:
                total_recipients = len(potential_recipients)
                old_amount = amount_per_person
                # Recalculate amount per person by dividing total amount by actual number of recipients
                amount_per_person = total_amount // total_recipients
                logger.info(f"Recalculated: total_recipients={total_recipients}, old_amount={old_amount}, new_amount={amount_per_person}")
                num_recipients = total_recipients
                await ctx.send(f"@{sender}, найдено только {total_recipients} пользователей. Сумма на человека: {amount_per_person:,} руб.")
            
            # Randomly select recipients
            import random
            recipients = random.sample(potential_recipients, num_recipients)
            
            # Distribute money
            successful_transfers = []
            for recipient in recipients:
                # Check if recipient username is safe
                if hasattr(self.bot, 'username_filter'):
                    is_safe, _ = self.bot.username_filter.is_safe(recipient)
                    if not is_safe:
                        continue
                
                # Transfer money
                success, _, _ = balance_manager.transfer(sender, recipient, amount_per_person)
                if success:
                    successful_transfers.append(recipient)
            
            # Report results
            if successful_transfers:
                # Calculate how many @mentions we can fit
                # Estimate max chars: "@user1, @user2, " = ~10 chars per user
                # Leave room for the rest of the message (~100 chars)
                max_mentions = (500 - 100) // 10
                
                # Get the displayable recipients and total count
                display_recipients = successful_transfers[:max_mentions]
                total_recipients = len(successful_transfers)
                
                # Format the message
                recipients_str = ", ".join(f"@{r}" for r in display_recipients)
                actual_total = len(successful_transfers) * amount_per_person
                
                # Add indication of hidden recipients if needed
                if len(successful_transfers) > max_mentions:
                    hidden_count = total_recipients - len(display_recipients)
                    message = (f"@{sender} раздал по {amount_per_person:,} руб. пользователям: {recipients_str} "
                              f"и еще {hidden_count} другим! Всего: {actual_total:,} руб.")
                else:
                    message = f"@{sender} раздал по {amount_per_person:,} руб. следующим пользователям: {recipients_str}! Всего: {actual_total:,} руб."
                
                await ctx.send(message)
                logger.info(f"User {sender} distributed {actual_total} rubles to {len(successful_transfers)} users")
            else:
                await ctx.send(f"@{sender}, не удалось раздать деньги")