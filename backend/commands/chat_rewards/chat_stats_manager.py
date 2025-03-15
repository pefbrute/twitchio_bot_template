import json
import os
import logging
from pathlib import Path

logger = logging.getLogger('twitch_bot')

class ChatStatsManager:
    def __init__(self):
        self.data_dir = Path(os.path.dirname(__file__))
        self.stats_file = self.data_dir / 'chat_stats.json'
        self.settings_file = self.data_dir / 'level_settings.json'
        
        # Load settings and stats
        self.settings = self._load_settings()
        self.stats = self._load_stats()
        
    def _load_settings(self):
        """Load level settings from JSON file or create default"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default settings
                default_settings = {
                    "xp_per_message": 10,
                    "levels": {
                        "0": {"name": "Новичок", "xp_required": 0},
                        "1": {"name": "Болтун", "xp_required": 100}
                    }
                }
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, ensure_ascii=False, indent=2)
                return default_settings
        except Exception as e:
            logger.error(f"Error loading level settings: {str(e)}")
            return {"xp_per_message": 10, "levels": {"0": {"name": "Новичок", "xp_required": 0}}}
            
    def _save_settings(self):
        """Save level settings to JSON file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving level settings: {str(e)}")
            return False
            
    def _load_stats(self):
        """Load stats from JSON file or create new if not exists"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading chat stats: {str(e)}")
            return {}
            
    def _save_stats(self):
        """Save stats to JSON file"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving chat stats: {str(e)}")
            return False
            
    def _calculate_level(self, xp):
        """Calculate level based on XP"""
        levels = self.settings["levels"]
        current_level = "0"
        
        # Convert xp to float for comparison
        xp = float(xp)
        
        # Find highest level where user has enough XP
        for level, data in sorted(levels.items(), key=lambda x: int(x[0])):
            if xp >= float(data["xp_required"]):
                current_level = level
            else:
                break
                
        return current_level
        
    def _get_level_name(self, level):
        """Get name for the given level"""
        return self.settings["levels"].get(str(level), {}).get("name", "Неизвестный")
        
    def _get_xp_for_next_level(self, current_level):
        """Calculate XP needed for next level"""
        levels = self.settings["levels"]
        current_level = str(current_level)
        
        # Get list of levels sorted by number
        sorted_levels = sorted(levels.items(), key=lambda x: int(x[0]))
        
        # Find next level
        for i, (level, data) in enumerate(sorted_levels):
            if level == current_level and i + 1 < len(sorted_levels):
                return sorted_levels[i + 1][1]["xp_required"]
                
        # If no next level, return None
        return None
        
    def get_user_stats(self, username):
        """Get user stats, creating if not exists"""
        username = username.lower()
        if username not in self.stats:
            self.stats[username] = {
                'messages': 0,
                'xp': 0.0,  # Initialize as float
                'level': "0"
            }
            self._save_stats()
        else:
            # Convert existing xp to float if it's not already
            self.stats[username]['xp'] = float(self.stats[username]['xp'])
        return self.stats[username]
        
    def add_message(self, username):
        """Process a new message from user, returns level up info if applicable"""
        username = username.lower()
        stats = self.get_user_stats(username)
        
        # Update message count
        stats['messages'] += 1
        
        # Add XP (convert to float and round to 1 decimal place)
        old_level = stats['level']
        old_xp = float(stats['xp'])
        xp_to_add = float(self.settings["xp_per_message"])
        
        stats['xp'] = round(old_xp + xp_to_add, 1)
        
        logger.debug(f"Adding XP for {username}: {old_xp} + {xp_to_add} = {stats['xp']}")
        
        # Calculate new level
        new_level = self._calculate_level(stats['xp'])
        stats['level'] = new_level
        
        # Save changes
        self._save_stats()
        
        # Return level up info if level changed
        if new_level != old_level:
            next_level_xp = self._get_xp_for_next_level(new_level)
            return {
                'old_level': old_level,
                'old_level_name': self._get_level_name(old_level),
                'new_level': new_level,
                'new_level_name': self._get_level_name(new_level),
                'total_messages': stats['messages'],
                'total_xp': stats['xp'],
                'next_level_xp': next_level_xp
            }
        return None
        
    def update_level_settings(self, new_settings):
        """Update level settings"""
        try:
            # Validate new settings
            if not isinstance(new_settings, dict):
                return False, "Настройки должны быть словарем"
            if "xp_per_message" not in new_settings:
                return False, "Отсутствует xp_per_message"
            if "levels" not in new_settings:
                return False, "Отсутствуют настройки уровней"
                
            # Update settings
            self.settings = new_settings
            self._save_settings()
            
            # Recalculate all user levels
            for username in self.stats:
                self.stats[username]['level'] = self._calculate_level(self.stats[username]['xp'])
            self._save_stats()
            
            return True, "Настройки уровней обновлены"
        except Exception as e:
            logger.error(f"Error updating level settings: {str(e)}")
            return False, f"Ошибка обновления настроек: {str(e)}"

# Create singleton instance
chat_stats_manager = ChatStatsManager() 