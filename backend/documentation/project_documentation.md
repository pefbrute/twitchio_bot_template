# Документация по добавлению новых команд в Twitch бота

Эта документация описывает процесс добавления новых команд в Twitch бота. Бот построен на основе библиотеки TwitchIO и использует модульную архитектуру для организации команд.

## Структура проекта

Команды организованы в модули, каждый из которых находится в отдельной директории внутри `backend/commands/`. Каждый модуль команд содержит:

1. Файл `__init__.py` для экспорта классов
2. Файл `command.py` с основной логикой команд
3. Дополнительные файлы для хранения данных или вспомогательных функций (опционально)

## Важно: Автоматическая загрузка команд

**Вам НЕ нужно модифицировать файлы `main.py` или `bot.py` для добавления новых команд!**

Система автоматически обнаруживает и загружает все модули команд при запуске бота. Функция `load_commands()` в `main.py` сканирует директорию `commands/`, находит все подпапки с файлом `command.py` и автоматически инициализирует классы команд.

Просто создайте новую директорию с правильной структурой в папке `commands/`, и ваши команды будут автоматически загружены при следующем запуске бота.

## Базовый класс команд

Все модули команд наследуются от базового класса `BotCommand`, который находится в `backend/commands/__init__.py`. Этот класс предоставляет общие методы и требует реализации метода `register_commands()`.
```python
from commands import BotCommand

class MyNewCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        # Инициализация дополнительных атрибутов
        
    def register_commands(self):
        """Регистрация команд для бота"""
        
        @self.bot.command(name="моя-команда")
        async def my_command(ctx):
            """Обработчик команды !моя-команда"""
            await ctx.send(f"Привет, @{ctx.author.name}!")
```

## Пошаговое руководство по добавлению новой команды

### 1. Создание структуры модуля

Создайте новую директорию в `backend/commands/` для вашего модуля команд:

```
backend/commands/my_module/
├── __init__.py
└── command.py
```

### 2. Настройка файла `__init__.py`

Экспортируйте ваш класс команд в `__init__.py`:

```python
from .command import MyNewCommand

__all__ = ['MyNewCommand']
```

### 3. Создание класса команд

В файле `command.py` создайте класс, наследующийся от `BotCommand`:

```python
import logging
from commands import BotCommand
from twitchio.ext import commands
from utils.cooldown_manager import cooldown

logger = logging.getLogger('twitch_bot')

class MyNewCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        # Инициализация атрибутов
        
    def register_commands(self):
        """Регистрация команд для бота"""
        
        @self.bot.command(name="привет")
        @cooldown(user_cd=10, global_cd=2)  # Опционально: добавление кулдауна
        async def hello_command(ctx):
            """Команда !привет"""
            await ctx.send(f"Привет, @{ctx.author.name}!")
            logger.info(f"User {ctx.author.name} used hello command")
        
        @self.bot.command(name="пока")
        async def goodbye_command(ctx):
            """Команда !пока"""
            await ctx.send(f"До свидания, @{ctx.author.name}!")
            logger.info(f"User {ctx.author.name} used goodbye command")
```

### 4. Готово!

После создания этих файлов с правильной структурой, ваши команды будут автоматически загружены при следующем запуске бота. Никаких дополнительных действий не требуется!

## Как работает автоматическая загрузка команд

Когда бот запускается:

1. Функция `load_commands()` в `main.py` сканирует директорию `commands/`
2. Для каждой поддиректории она ищет файл `command.py`
3. Если файл найден, он импортируется и система ищет класс, наследующийся от `BotCommand`
4. Найденный класс инициализируется с экземпляром бота в качестве аргумента
5. Конструктор класса вызывает `register_commands()`, который регистрирует все команды

Это означает, что вам нужно только создать правильную структуру файлов, и система сделает все остальное.

## Добавление обработчика сообщений (опционально)

Если ваш модуль должен реагировать на все сообщения в чате, а не только на команды, добавьте обработчик сообщений:

```python
def __init__(self, bot):
    super().__init__(bot)
    # Регистрация обработчика сообщений
    self.bot.message_listeners.append(self.monitor_chat)

async def monitor_chat(self, message):
    """Обработка всех сообщений в чате"""
    try:
        # Пропускаем сообщения от бота
        if message.author is None or message.author.name.lower() == self.bot.nick.lower():
            return
            
        # Ваша логика обработки сообщений
        content = message.content.lower()
        if "ключевое слово" in content:
            await message.channel.send(f"@{message.author.name}, я заметил ключевое слово!")
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике сообщений: {str(e)}")
```

## Использование утилит и вспомогательных функций

Бот предоставляет несколько полезных утилит:

### Проверка безопасности контента

```python
from utils.safe_content import safe_content

@self.bot.command(name="команда")
@safe_content  # Проверяет безопасность сообщений и упоминаний
async def my_command(ctx):
    # Ваш код
```

Декоратор `@safe_content` автоматически:
- Проверяет текст сообщения на наличие запрещенного контента
- Проверяет безопасность упоминаний пользователей (@username)
- Блокирует выполнение команды, если обнаружен небезопасный контент
- Отправляет уведомление пользователю о причине блокировки

### Управление кулдаунами

```python
from utils.cooldown_manager import cooldown

@self.bot.command(name="команда")
@cooldown(user_cd=30, global_cd=5)  # Кулдаун 30 секунд для пользователя, 5 секунд глобально
async def my_command(ctx):
    # Ваш код
```

### Проверка прав доступа

```python
from utils.permission_manager import mod_only

@self.bot.command(name="мод-команда")
@mod_only()  # Только для модераторов
async def mod_command(ctx):
    # Ваш код

@self.bot.command(name="спец-команда")
@mod_only(specific_users=["username1", "username2"])  # Для модераторов и указанных пользователей
async def special_command(ctx):
    # Ваш код
```

### Безопасная отправка сообщений

```python
# Использование встроенного метода бота для безопасной отправки сообщений
await self.bot.send_safe(ctx, "Текст сообщения")
```

## Пример полного модуля команд с проверкой безопасности

### Файл `__init__.py`

```python
# backend/commands/greetings/__init__.py
from .command import GreetingsCommand

__all__ = ['GreetingsCommand']
```

### Файл `command.py`

```python
# backend/commands/greetings/command.py
import logging
import random
from commands import BotCommand
from twitchio.ext import commands
from utils.cooldown_manager import cooldown
from utils.safe_content import safe_content

logger = logging.getLogger('twitch_bot')

class GreetingsCommand(BotCommand):
    def __init__(self, bot):
        super().__init__(bot)
        
        self.greetings = [
            "Привет, {}!",
            "Здравствуй, {}!",
            "Приветствую, {}!",
            "Хай, {}!"
        ]
        
    def register_commands(self):
        """Регистрация команд приветствия"""
        
        @self.bot.command(name="привет")
        @cooldown(user_cd=10, global_cd=2)
        async def hello_command(ctx):
            """Команда !привет"""
            greeting = random.choice(self.greetings).format(ctx.author.name)
            await ctx.send(greeting)
            logger.info(f"User {ctx.author.name} used hello command")
        
        @self.bot.command(name="поздороваться")
        @cooldown(user_cd=30, global_cd=5)
        @safe_content  # Проверяем безопасность упоминаний
        async def greet_command(ctx):
            """Команда !поздороваться с другим пользователем"""
            message_parts = ctx.message.content.split()
            
            if len(message_parts) > 1:
                target = message_parts[1].strip('@')
                greeting = random.choice(self.greetings).format(target)
                await ctx.send(f"{ctx.author.name} говорит: {greeting}")
                logger.info(f"User {ctx.author.name} greeted {target}")
            else:
                await ctx.send(f"@{ctx.author.name}, укажите пользователя для приветствия!")
```

## Отладка и тестирование

1. **Логирование**: Используйте `logger` для отслеживания работы ваших команд:
   ```python
   logger.info(f"Command executed by {ctx.author.name}")
   logger.error(f"Error in command: {str(e)}")
   ```

2. **Тестирование команд**: После запуска бота, проверьте работу ваших команд в чате Twitch, введя команду с префиксом `!`.

3. **Проверка загрузки**: При запуске бота в логах должно появиться сообщение о загрузке вашего модуля:
   ```
   INFO - Loaded command module: my_module
   ```

## Советы и рекомендации

1. **Безопасность**: Используйте декоратор `@safe_content` для команд, где пользователи могут упоминать других пользователей или вводить произвольный текст
2. **Логирование**: Всегда используйте логгер для отслеживания действий и ошибок
3. **Обработка ошибок**: Оборачивайте код в блоки try-except для предотвращения падения бота
4. **Кулдауны**: Используйте кулдауны для предотвращения спама командами
5. **Модульность**: Разделяйте функциональность на логические модули
6. **Документация**: Добавляйте docstrings к функциям и классам
7. **Конфигурация**: Храните настройки в отдельных JSON-файлах для легкого изменения
8. **Именование**: Используйте понятные имена для директорий модулей и классов команд

## Заключение

Следуя этой документации, вы можете легко добавлять новые команды и функциональность в бота. Система предоставляет встроенные механизмы для:
- Автоматической загрузки команд
- Управления правами доступа
- Контроля кулдаунов
- Проверки безопасности контента
- Логирования действий

Главное преимущество этой системы - вам не нужно модифицировать основные файлы бота (`main.py` и `bot.py`), чтобы добавить новые команды. Просто создайте новый модуль с правильной структурой, и он будет автоматически загружен при запуске бота.

## Предотвращение конфликтов команд

При разработке новых модулей команд важно избегать конфликтов при регистрации команд. Есть несколько ситуаций, которые могут привести к ошибке "command with that name already exists":

### 1. Проверка существования команды

Всегда проверяйте существование команды перед регистрацией:

```python
def register_commands(self):
    """Регистрация команд для бота"""
    
    # Проверяем существование команды перед регистрацией
    if 'команда' not in self.bot.commands:
        @self.bot.command(name="команда")
        async def my_command(ctx):
            await ctx.send(f"Привет, @{ctx.author.name}!")
```

### 2. Избегание двойной регистрации

Распространенная ошибка - регистрация команд и в `__init__.py`, и в `command.py`. Используйте только один способ:

❌ Неправильно:
```python
# __init__.py
def setup(bot):
    return MyCommand(bot)  # Не используйте setup() для инициализации

# command.py
def register_commands(self):
    # Регистрация здесь
```

✅ Правильно:
```python
# __init__.py
from .command import MyCommand
__all__ = ['MyCommand']

# command.py
def register_commands(self):
    # Регистрация только здесь
```

### 3. Решение конфликтов команд

Если вы столкнулись с ошибкой "command already exists":

1. **Проверьте все модули** на наличие команды с тем же именем
2. **Используйте отладочное логирование** для отслеживания регистрации:
```python
def register_commands(self):
    logger.debug(f"Registering commands for {self.__class__.__name__}")
    if 'команда' not in self.bot.commands:
        logger.debug("Command 'команда' not registered yet, registering...")
        @self.bot.command(name="команда")
        async def my_command(ctx):
            # ...
    else:
        logger.warning(f"Command 'команда' already exists, skipping registration")
```

3. **Временное решение**: Если нужно быстро исправить ситуацию, можно переименовать конфликтующую команду:
```python
def register_commands(self):
    command_name = "команда"
    if command_name in self.bot.commands:
        command_name = "команда2"  # Временное решение
        logger.warning(f"Command conflict, using alternative name: {command_name}")
    
    @self.bot.command(name=command_name)
    async def my_command(ctx):
        # ...
```

### 4. Безопасная регистрация команд

Создайте вспомогательный метод для безопасной регистрации:

```python
class BotCommand:
    def safe_register_command(self, name, **kwargs):
        """Безопасная регистрация команды с проверкой существования"""
        if name in self.bot.commands:
            logger.warning(f"Command '{name}' already exists, skipping registration")
            return None
            
        def decorator(func):
            logger.debug(f"Registering command '{name}'")
            return self.bot.command(name=name, **kwargs)(func)
        return decorator

class MyCommand(BotCommand):
    def register_commands(self):
        @self.safe_register_command(name="команда")
        async def my_command(ctx):
            # ...
```

### 5. Отладка загрузки команд

Если проблема сохраняется:

1. Включите отладочное логирование:
```python
logging.getLogger('twitch_bot').setLevel(logging.DEBUG)
```

2. Добавьте вывод списка загруженных команд:
```python
def load_commands(bot):
    logger.debug("Currently registered commands:")
    for cmd_name in bot.commands:
        logger.debug(f"  - {cmd_name}")
        
    # ... загрузка новых команд ...
    
    logger.debug("Commands after loading:")
    for cmd_name in bot.commands:
        logger.debug(f"  - {cmd_name}")
```

### 6. Проверка перед запуском

Добавьте проверку дубликатов команд перед запуском бота:

```python
def check_command_duplicates(bot):
    """Проверка дубликатов команд перед запуском"""
    command_sources = {}
    for cmd_name, cmd in bot.commands.items():
        source = cmd.__module__
        if cmd_name in command_sources:
            logger.error(f"Command '{cmd_name}' registered multiple times:")
            logger.error(f"  - First in: {command_sources[cmd_name]}")
            logger.error(f"  - Then in: {source}")
            raise ValueError(f"Duplicate command: {cmd_name}")
        command_sources[cmd_name] = source

def main():
    # ... инициализация бота ...
    load_commands(bot)
    check_command_duplicates(bot)  # Проверка перед запуском
    bot.run()
```
