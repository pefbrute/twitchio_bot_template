import re
import logging

logger = logging.getLogger('twitch_bot')

class ContentFilter:
    def __init__(self):
        # Единый список запрещенных фраз
        self.banned_phrases = [
            # Расистские/этнические оскорбления
            "ниггер", "ниггеры", "нигер", "нигеры", "негр", "чурка", "хач", "жид", 
            "хохол", "черножопый", "белокурый дьявол", "узкоглазый",
            
            # ЛГБТК+-фобия
            "пидорасы", "пидорас", "пидоры", "пидор", "педик", "гомик", "гейчик",
            "лесбиянка", "трансгендер", "трансвестит", "содомит", "педераст",
            
            # Мизогинные выражения
            "шлюха", "проститутка", "сука", "стерва", "баба дура", "курица", 
            "женское дело", "кухня", "швабра", "место на кухне",
            
            # Инвалидизирующие выражения
            "даун", "дебил", "кретин", "имбецил", "аутист", "псих", "урод",
            "калека", "больной на голову", "шизик",
            
            # Эйджизм
            "старый пердун", "старая перечница", "сопляк", "малолетка",
            "отработанный материал", "древний",
            
            # Социальная дискриминация
            "нищеброд", "бомж", "алкаш", "наркоман", "уголовник", "зек",
            "деревенщина", "колхозник",
            
            # Опасные призывы
            "сдохни", "умри", "убей себя", "порежься", "повесься", "сожги себя",
            "выпей яду", "бросься под поезд",
            
            # Исходный список
            "zv", "передай привет", "поиграй в", "сыграешь в", "го на", "+ в чат",
            "сломай барьер", "сдох", "пишите +", "ставьте +", "что мут"
        ]
        
        # Компилируем регулярные выражения для быстрого поиска
        self.patterns = [re.compile(re.escape(phrase), re.IGNORECASE) 
                         for phrase in self.banned_phrases]
    
    def is_phone_number_like(self, text):
        """
        Проверяет, похож ли текст на номер телефона
        """
        matches = list(re.finditer(r'\d+', text))
        if not matches:
            return False
        consecutive_digits = max(len(match[0]) for match in matches)
        return consecutive_digits >= 7

    def contains_banned_phrases(self, text):
        """
        Проверяет, содержит ли текст запрещенные фразы
        """
        if not text:
            return False
        
        # Проверяем каждый паттерн
        for pattern in self.patterns:
            if pattern.search(text):
                return True
                
        return False

    def is_safe_username(self, username):
        """
        Проверяет безопасность имени пользователя
        Возвращает (bool, str) кортеж: (безопасно, причина_если_небезопасно)
        """
        if not username:
            return False, "Username is empty"

        # Удаляем символ @ если присутствует
        clean_username = re.sub(r'^@', '', username)
        
        # Проверяем на номера телефонов
        if self.is_phone_number_like(clean_username):
            return False, "Username contains phone number pattern"
            
        # Проверяем на запрещенные слова
        if self.contains_banned_phrases(clean_username):
            return False, "Username contains banned words"
            
        return True, None
    
    def filter_message(self, text):
        """
        Проверяет, содержит ли сообщение запрещенные фразы или номера телефонов
        Возвращает кортеж: (безопасно, отфильтрованный_текст)
        - безопасно: bool - True если сообщение безопасно
        - отфильтрованный_текст: str - Исходный текст или безопасно измененная версия
        """
        if not text:
            return True, text
            
        # Проверяем на номера телефонов
        if self.is_phone_number_like(text):
            logger.warning(f"Message contains phone number pattern, would be filtered: {text}")
            return False, "⚠️ Сообщение содержит номер телефона и не может быть отправлено"
            
        # Проверяем на запрещенные фразы
        if self.contains_banned_phrases(text):
            logger.warning(f"Message contains banned phrase, would be filtered: {text}")
            return False, "⚠️ Сообщение содержит запрещенную фразу и не может быть отправлено"
            
        return True, text

# Создаем экземпляр-синглтон
content_filter = ContentFilter() 