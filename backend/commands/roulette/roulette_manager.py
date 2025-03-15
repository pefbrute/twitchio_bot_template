import json
import os
import random
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger('twitch_bot')

class RouletteManager:
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), 'roulette_data.json')
        self.load_data()
        self.reward_range = (50, 200)  # Range for reward amount

    def load_data(self):
        """Load roulette data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load roulette data: {e}")
                self.data = {}
        else:
            self.data = {}

    def save_data(self):
        """Save roulette data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save roulette data: {e}")

    def initialize_cylinder(self, user_id: str) -> Dict:
        """Initialize or reset cylinder for user"""
        # Get existing stats if they exist
        existing_data = self.data.get(user_id, {})
        stats = {
            'total_games': existing_data.get('total_games', 0) + 1,  # New game starts
            'deaths': existing_data.get('deaths', 0),
            'wins': existing_data.get('wins', 0)  # Preserve win count
        }
        
        # Create new cylinder data while preserving stats
        cylinder_data = {
            'bullet_position': random.randint(0, 5),  # Random position 0-5
            'current_position': 0,
            'shots_fired': 0,  # Reset shots for new game
            'total_games': stats['total_games'],
            'deaths': stats['deaths'],
            'wins': stats['wins'],  # Add wins to cylinder data
            'timeout_duration': random.randint(1, 70)  # Предопределяем время мута
        }
        self.data[user_id] = cylinder_data
        self.save_data()
        return cylinder_data

    def get_user_data(self, user_id: str) -> Dict:
        """Get user's cylinder data, initialize if doesn't exist"""
        if user_id not in self.data:
            return self.initialize_cylinder(user_id)
        
        # Ensure wins field exists for older data
        if 'wins' not in self.data[user_id]:
            self.data[user_id]['wins'] = 0
            self.save_data()
            
        return self.data[user_id]

    def pull_trigger(self, user_id: str) -> Tuple[bool, int]:
        """
        Pull the trigger for user
        Returns: (is_shot: bool, timeout_duration: int)
        """
        user_data = self.get_user_data(user_id)
        
        # Check if bullet is in current position
        is_shot = user_data['current_position'] == user_data['bullet_position']
        
        # Get predetermined timeout duration
        timeout_duration = user_data['timeout_duration'] if is_shot else 0
        
        # Update shots counter
        user_data['shots_fired'] += 1
        
        if is_shot:
            user_data['deaths'] += 1
            # Save stats before resetting cylinder
            self.data[user_id] = user_data
            self.save_data()
            # Reset cylinder after shot
            self.initialize_cylinder(user_id)
        else:
            # Rotate cylinder
            user_data['current_position'] = (user_data['current_position'] + 1) % 6
            self.data[user_id] = user_data
            self.save_data()
        
        return is_shot, timeout_duration

    def get_stats(self, user_id: str) -> Dict:
        """Get user's roulette statistics"""
        user_data = self.get_user_data(user_id)
        return {
            'total_games': user_data['total_games'],
            'deaths': user_data['deaths'],
            'shots_fired': user_data['shots_fired'],
            'wins': user_data.get('wins', 0)  # Include wins in stats
        }

    def get_remaining_shots(self, user_id: str) -> int:
        """Get number of remaining shots in cylinder (6 - shots_fired)"""
        user_data = self.get_user_data(user_id)
        total_chambers = 6
        shots_fired = user_data['shots_fired']
        return total_chambers - shots_fired

    def stop_game(self, user_id: str) -> Tuple[bool, int, int, int]:
        """
        Stop the current game and check if user wins
        Returns: (is_win: bool, reward: int, remaining_shots: int, shots_until_death: int)
        """
        user_data = self.get_user_data(user_id)
        
        # Check if bullet is in current position (not next position)
        is_win = user_data['current_position'] == user_data['bullet_position']
        
        # Calculate shots until death
        shots_until_death = 0
        if not is_win:
            # Calculate how many shots until the bullet position
            if user_data['bullet_position'] > user_data['current_position']:
                shots_until_death = user_data['bullet_position'] - user_data['current_position']
            else:
                # Bullet is behind current position, need to go around
                shots_until_death = (6 - user_data['current_position']) + user_data['bullet_position']
        
        reward = 0
        if is_win:
            # Generate random reward amount
            reward = random.randint(self.reward_range[0], self.reward_range[1])
            # Increment win counter
            user_data['wins'] = user_data.get('wins', 0) + 1
            self.data[user_id] = user_data
            self.save_data()
        
        remaining_shots = self.get_remaining_shots(user_id)
        
        # Reset cylinder after stopping
        self.initialize_cylinder(user_id)
        
        return is_win, reward, remaining_shots, shots_until_death 