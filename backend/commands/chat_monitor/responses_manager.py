import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger('twitch_bot')

class ResponsesManager:
    """Manages the names of games, anime, etc. for chat responses"""
    
    def __init__(self):
        self.responses_file = os.path.join(os.path.dirname(__file__), 'responses.json')
        self.default_names = {
            "anime": "моб психо 100",
            "game": "The Last of Us Часть 1",
            "difficulty": "реализм",
            "anime_voice": "Анкорд"  # Добавляем озвучку аниме
        }
        
        # Шаблоны ответов (не изменяются через команды)
        self.response_templates = {
            "anime": "ну, чел, ты чо в глаза долбишься, {name}",
            "game": "как обычно, в любимый {name}",
            "difficulty": "{name}, как всегда",
            "anime_voice": "озвучка от {name}, самая лучшая"
        }
        
        self.names = self.load_names()
        
        # Удаляем ненужные поля, если они есть
        self._cleanup_unused_fields()
    
    def load_names(self) -> Dict[str, str]:
        """Load names from the JSON file or create default if not exists"""
        try:
            if os.path.exists(self.responses_file):
                with open(self.responses_file, 'r', encoding='utf-8') as f:
                    names = json.load(f)
                    logger.info(f"Loaded {len(names)} names from file")
                    return names
            else:
                logger.info("Names file not found, creating with defaults")
                self.save_names(self.default_names)
                return self.default_names
        except Exception as e:
            logger.error(f"Error loading names: {str(e)}")
            return self.default_names
    
    def save_names(self, names: Dict[str, str]) -> bool:
        """Save names to the JSON file"""
        try:
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(names, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved {len(names)} names to file")
            return True
        except Exception as e:
            logger.error(f"Error saving names: {str(e)}")
            return False
    
    def get_response(self, response_type: str) -> str:
        """Get a formatted response by its type"""
        name = self.names.get(response_type, self.default_names.get(response_type, "неизвестно"))
        template = self.response_templates.get(response_type, "{name}")
        return template.format(name=name)
    
    def set_name(self, name_type: str, name: str) -> bool:
        """Set a name and save to file"""
        if name_type not in self.default_names:
            logger.warning(f"Attempted to set unknown name type: {name_type}")
            return False
        
        self.names[name_type] = name
        return self.save_names(self.names)
    
    def get_all_names(self) -> Dict[str, str]:
        """Get all names"""
        return self.names 
    
    def _cleanup_unused_fields(self):
        """Удаляет ненужные поля из данных"""
        unused_fields = ["game_type"]
        changed = False
        
        for field in unused_fields:
            if field in self.names:
                del self.names[field]
                changed = True
        
        # Добавляем новые поля, если их нет
        if "anime_voice" not in self.names:
            self.names["anime_voice"] = self.default_names["anime_voice"]
            changed = True
        
        if changed:
            self.save_names(self.names)
            logger.info("Обновлена структура данных в файле responses.json") 