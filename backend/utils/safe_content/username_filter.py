import logging
import re

logger = logging.getLogger('twitch_bot')

class UsernameFilter:
    def __init__(self):
        # Список запрещенных слов в именах пользователей
        self.banned_words = [
            "zv",
            "сдох",
            "умри",
        ]
        
        # Компилируем регулярные выражения для быстрого поиска
        self.patterns = [re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE) 
                         for word in self.banned_words]
    
    def is_phone_number_like(self, username):
        """
        Check if a username looks like a phone number to avoid getting muted
        """
        matches = list(re.finditer(r'\d+', username))
        if not matches:
            return False
        consecutive_digits = max(len(match[0]) for match in matches)
        return consecutive_digits >= 7

    def contains_banned_words(self, username):
        """
        Check if username contains any banned words
        """
        # Remove @ symbol if present
        username = re.sub(r'^@', '', username)
        
        # Check against each pattern
        for pattern in self.patterns:
            if pattern.search(username):
                return True
                
        return False

    def is_safe(self, username):
        """
        Check if a username is safe to use in bot responses
        Returns (bool, str) tuple: (is_safe, reason_if_unsafe)
        """
        if not username:
            return False, "Username is empty"

        # Remove @ symbol if present for checking
        clean_username = re.sub(r'^@', '', username)
        
        # Check for phone numbers
        if self.is_phone_number_like(clean_username):
            return False, "Username contains phone number pattern"
            
        # Check for banned words
        if self.contains_banned_words(clean_username):
            return False, "Username contains banned words"
            
        return True, None

# Create a singleton instance
username_filter = UsernameFilter() 