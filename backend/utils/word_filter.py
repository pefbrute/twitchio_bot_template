import re
import logging

logger = logging.getLogger('twitch_bot')

class WordFilter:
    def __init__(self):
        # List of banned phrases - each entry is a tuple of (phrase, is_exact_match)
        # is_exact_match=True requires exact word match
        # is_exact_match=False will match partial phrases
        self.banned_phrases = [
            ("zv", False),  # exact word match only
            ("передай привет", False),
            ("поиграй в", False),
            ("сыграешь в", False),
            ("го на", False),
            ("+ в чат", False),
            ("сломай барьер", False),
            ("сдох", False),
            ("пишите +", False),
            ("ставьте +", False),
            ("что мут", False),
            ("умри", False),
        ]
        
        # Compile regex patterns for faster matching
        self.compile_patterns()
        
    def compile_patterns(self):
        """Compile regex patterns for the banned phrases"""
        self.patterns = []
        
        for phrase, is_exact_match in self.banned_phrases:
            if is_exact_match:
                # For exact matches, use word boundaries
                pattern = r'\b' + re.escape(phrase) + r'\b'
            else:
                # For partial matches, just escape the phrase
                pattern = re.escape(phrase)
            
            self.patterns.append(re.compile(pattern, re.IGNORECASE))
    
    def contains_banned_phrase(self, text):
        """Check if the text contains any banned phrases"""
        if not text:
            return False
            
        # Check each pattern
        for pattern in self.patterns:
            if pattern.search(text):
                return True
                
        return False
    
    def filter_message(self, text):
        """
        Check if message contains banned phrases
        Returns a tuple: (is_safe, filtered_text)
        - is_safe: bool - True if message doesn't contain banned phrases
        - filtered_text: str - The original text or a safely modified version
        """
        if not self.contains_banned_phrase(text):
            return True, text
            
        # Message contains banned phrases
        logger.warning(f"Message contains banned phrase, would be filtered: {text}")
        return False, "⚠️ Сообщение содержит запрещенную фразу и не может быть отправлено"

# Create a singleton instance
word_filter = WordFilter() 