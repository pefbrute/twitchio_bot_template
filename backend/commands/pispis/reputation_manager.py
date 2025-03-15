import json
import os
import logging
from typing import Dict

logger = logging.getLogger('twitch_bot')

class ReputationManager:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), 'reputation_data.json')
        self.reputation_data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load reputation data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {"reputations": data.get("reputations", {})}
            except Exception as e:
                logger.error(f"Error loading reputation data: {e}")
                return {"reputations": {}}
        return {"reputations": {}}
    
    def _save_data(self):
        """Save reputation data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.reputation_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving reputation data: {e}")

    def get_reputation(self, username: str) -> int:
        """Get user's reputation"""
        return self.reputation_data["reputations"].get(username.lower(), 0)

    def modify_reputation(self, username: str, change: int):
        """Modify user's reputation"""
        username = username.lower()
        current = self.get_reputation(username)
        self.reputation_data["reputations"][username] = current + change
        self._save_data()

    def get_status(self, reputation: int) -> str:
        """Get status based on reputation range"""
        if reputation >= 200:
            return "Божество 🌠"
        elif reputation >= 150:
            return "Мифическая фигура 🦄"
        elif reputation >= 100:
            return "Легенда 🌟"
        elif reputation >= 75:
            return "Герой 🦸‍♂️"
        elif reputation >= 50:
            return "Святой 😇"
        elif reputation >= 30:
            return "Праведник 🙏"
        elif reputation >= 10:
            return "Хороший человек 😊"
        elif reputation >= 0:
            return "Норм чел 👍"
        elif reputation >= -10:
            return "Мокрый бинт 💦"
        elif reputation >= -20:
            return "Гнилой зуб 🦷"
        elif reputation >= -30:
            return "Плесень вселенной 🍄"
        elif reputation >= -50:
            return "Проказа чата 🦠"
        elif reputation >= -75:
            return "Токсичный осадок ☢️"
        elif reputation >= -100:
            return "Аварийный выброс 💨"
        elif reputation >= -125:
            return "Биоопасность ☣️"
        elif reputation >= -150:
            return "Чумной бубон 🐭"
        elif reputation >= -175:
            return "Радиоактивный шлак ☢️💀"
        elif reputation >= -200:
            return "Инфернальная гниль 🔥"
        elif reputation >= -225:
            return "Апокалиптический мусор 🌌🗑️"
        elif reputation >= -275:
            return "Чернодырная слизь 🕳️"
        elif reputation >= -300:
            return "Вечнострадающий труп ☠️"
        elif reputation >= -350:
            return "Галактическая инфекция 🌌☣️"
        elif reputation >= -400:
            return "Квантовая пыль небытия ⚛️💨"
        elif reputation >= -550:
            return "Гнилостный отброс в вакууме 🦠🚮"
        elif reputation >= -600:
            return "Конечная стадия деградации 🧠💀"
        elif reputation >= -650:
            return "Живой труп без надежды ⚰️💔"
        elif reputation >= -700:
            return "Психический мусор континента 🧠🗑️"
        elif reputation >= -750:
            return "Антиматерия позора ⚛️🤢"
        elif reputation >= -800:
            return "Космическая рвота вселенной 🌌🤮"
        elif reputation >= -850:
            return "Нуклеарный позор ☢️👎"
        elif reputation >= -900:
            return "Био-мешок с отходами 🧬🗑️"
        elif reputation >= -950:
            return "Червоточина безнадёги 🕳️😭"
        elif reputation >= -1000:
            return "Плазменный выброс стыда 🔥😳"
        elif reputation >= -1050:
            return "Крипто-дерьмо блокчейна 💩🔗"
        elif reputation >= -1100:
            return "Генетический брак эволюции 🧬❌"
        elif reputation >= -1150:
            return "Нейтронная помойка времени ⏳🗑️"
        elif reputation >= -1200:
            return "Квантовый мусор бытия ⚛️🚮"
        elif reputation >= -1250:
            return "Термоядерный позор реактора ☢️🤦"
        elif reputation >= -1300:
            return "Галактическая мусорная ДНК 🌌🧬"
        elif reputation >= -1350:
            return "Чернодырное дно реальности 🕳️⬇️"
        elif reputation >= -1400:
            return "Астральный шлак мироздания 🌠🗑️"
        elif reputation >= -1450:
            return "Хронос-помойка временной петли ⏳🌀"
        elif reputation >= -1500:
            return "Финальный аккорд апокалипсиса 🎵💥"
        else:
            return "Абсолютный ноль существования ❄️💀"