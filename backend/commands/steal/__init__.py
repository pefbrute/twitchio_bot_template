from .steal_chance_commands import StealChanceCommands
from .steal_chance_manager import steal_chance_manager
from .command import StealCommand
from .steal_logic import try_steal

__all__ = ['StealChanceCommands', 'steal_chance_manager', 'StealCommand', 'try_steal']

# Удаляем функцию setup, так как она не нужна
# Динамическая загрузка из main.py справится с инициализацией 