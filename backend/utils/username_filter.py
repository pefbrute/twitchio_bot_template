import logging
import re
from utils.word_filter import word_filter

logger = logging.getLogger('twitch_bot')

class UsernameFilter:
    @staticmethod
    def is_phone_number_like(username):
        """
        Check if a username looks like a phone number to avoid getting muted
        """
        matches = list(re.finditer(r'\d+', username))
        if not matches:
            return False
        consecutive_digits = max(len(match[0]) for match in matches)
        return consecutive_digits >= 7

    @staticmethod
    def contains_banned_words(username):
        """
        Check if username contains any banned words from the word filter
        """
        # Remove @ symbol if present
        username = re.sub(r'^@', '', username)
        
        # Check username against word filter
        is_safe, _ = word_filter.filter_message(username)
        return not is_safe

    @staticmethod
    def is_safe(username):
        """
        Check if a username is safe to use in bot responses
        Returns (bool, str) tuple: (is_safe, reason_if_unsafe)
        """
        if not username:
            return False, "Username is empty"

        # Remove @ symbol if present for checking
        clean_username = re.sub(r'^@', '', username)
        
        # Check for phone numbers
        if UsernameFilter.is_phone_number_like(clean_username):
            return False, "Username contains phone number pattern"
            
        # Check for banned words
        if UsernameFilter.contains_banned_words(clean_username):
            return False, "Username contains banned words"
            
        return True, None

username_filter = UsernameFilter() 