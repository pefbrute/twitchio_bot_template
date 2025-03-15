import json
import os
import logging

logger = logging.getLogger('twitch_bot')

class StealChanceManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StealChanceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, data_dir=None):
        if self._initialized:
            return
            
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))
        self.steal_chances_file = os.path.join(self.data_dir, 'steal_chances.json')
        self.victim_chances_file = os.path.join(self.data_dir, 'victim_chances.json')
        
        # Загрузка данных
        self.steal_chances = self._load_json(self.steal_chances_file)
        self.victim_chances = self._load_json(self.victim_chances_file)
        
        logger.info(f"Loaded {len(self.steal_chances)} custom steal chances")
        logger.info(f"Loaded {len(self.victim_chances)} custom victim chances")
        
        self._initialized = True
    
    def _load_json(self, file_path):
        """Загружает данные из JSON-файла"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding {file_path}, creating new one")
                return {}
        else:
            logger.info(f"File {file_path} not found, creating new one")
            return {}
    
    def _save_json(self, data, file_path):
        """Сохраняет данные в JSON-файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {str(e)}")
            return False
    
    def set_custom_steal_chance(self, username, chance):
        """Устанавливает пользовательский шанс кражи"""
        if not 0 <= chance <= 1:
            return False
        
        username = username.lower()
        self.steal_chances[username] = chance
        logger.info(f"Set custom steal chance for {username} to {chance*100}%")
        
        return self._save_json(self.steal_chances, self.steal_chances_file)
    
    def get_custom_steal_chance(self, username):
        """Возвращает пользовательский шанс кражи или None"""
        username = username.lower()
        return self.steal_chances.get(username)
    
    def set_custom_victim_chance(self, username, chance):
        """Устанавливает пользовательский шанс быть обкраденным"""
        if not 0 <= chance <= 1:
            return False
        
        username = username.lower()
        self.victim_chances[username] = chance
        logger.info(f"Set custom victim chance for {username} to {chance*100}%")
        
        return self._save_json(self.victim_chances, self.victim_chances_file)
    
    def get_custom_victim_chance(self, username):
        """Возвращает пользовательский шанс быть обкраденным или None"""
        username = username.lower()
        return self.victim_chances.get(username)
    
    def get_final_steal_chance(self, thief, victim):
        """Определяет итоговый шанс кражи с учетом всех факторов"""
        # Приоритет: шанс жертвы > шанс вора > базовый шанс
        victim_chance = self.get_custom_victim_chance(victim)
        thief_chance = self.get_custom_steal_chance(thief)
        
        # Базовый шанс 40%
        base_chance = 0.4
        
        # Если у жертвы шанс 0%, кража невозможна
        if victim_chance == 0.0:
            return 0.0
        
        # Если у вора 100% шанс, он всегда успешно крадёт
        if thief_chance == 1.0:
            return 1.0
        
        # В остальных случаях приоритет у шанса жертвы
        if victim_chance is not None:
            return victim_chance
        elif thief_chance is not None:
            return thief_chance
        else:
            return base_chance


# Создаем синглтон-экземпляр менеджера
steal_chance_manager = StealChanceManager() 