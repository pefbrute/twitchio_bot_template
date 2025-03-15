import os
import json
import logging
import random
import time
from pathlib import Path

logger = logging.getLogger('twitch_bot')

class BalanceManager:
    """Manager for user balance operations and storage"""
    
    def __init__(self):
        # Store balances.json in the balance command directory
        self.data_dir = Path(os.path.dirname(__file__))
        
        # Path to balances file
        self.balances_file = self.data_dir / 'balances.json'
        
        # Load existing balances or create new file
        self.balances = self._load_balances()
        # Конвертируем старый формат в новый если нужно
        self._migrate_old_format()
        
        # Cache for last steal attempts to implement cooldowns
        self.last_steal_attempts = {}
        self.steal_cooldown = 60  # Changed from 60 to 5 seconds for testing
        
        # Add global steal cooldown tracking
        self.last_global_steal = 0
        self.global_steal_cooldown = 10  # 10 seconds global cooldown
        
        # Add privileged users who can bypass cooldowns
        self.privileged_users = []
        
        logger.info(f"Balance manager initialized, tracking {len(self.balances)} users")
    
    def _load_balances(self):
        """Load balances from the JSON file or create a new one"""
        if self.balances_file.exists():
            try:
                with open(self.balances_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding balances file, creating new one")
                return {}
        else:
            logger.info(f"Balances file not found, creating new one")
            return {}
    
    def _save_balances(self):
        """Save balances to the JSON file"""
        try:
            with open(self.balances_file, 'w', encoding='utf-8') as f:
                json.dump(self.balances, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving balances: {str(e)}")
            return False
    
    def _migrate_old_format(self):
        """Convert old format to new format with required fields"""
        need_save = False
        required_fields = {
            'balance': 0,
            'got_starter': False,
            'last_steal_attempt': 0
        }
        
        for username, value in list(self.balances.items()):
            if isinstance(value, dict):
                updated = False
                for field, default_value in required_fields.items():
                    if field not in value:
                        value[field] = default_value
                        updated = True
                if updated:
                    self.balances[username] = value
                    need_save = True
        
        if need_save:
            logger.info("Migrating old data format to include all required fields")
            self._save_balances()
    
    def get_balance(self, username):
        """Get the balance for a user"""
        username = username.lower()
        user_data = self.balances.get(username, {'balance': 0, 'got_starter': False, 'last_steal_attempt': 0})
        return user_data['balance']
    
    def has_received_starter(self, username):
        """Check if user has already received starter balance"""
        username = username.lower()
        user_data = self.balances.get(username, {'balance': 0, 'got_starter': False, 'last_steal_attempt': 0})
        return user_data['got_starter']
    
    def adjust_balance(self, username, amount):
        """Adjust a user's balance by the given amount (positive or negative)"""
        username = username.lower()
        
        # Get or create user data
        user_data = self.balances.get(username, {'balance': 0, 'got_starter': False, 'last_steal_attempt': 0})
        
        # Calculate new balance (ensure it never goes below 0)
        new_balance = max(0, user_data['balance'] + amount)
        
        # Update balance while preserving other fields
        self.balances[username] = {
            'balance': new_balance,
            'got_starter': user_data['got_starter'],
            'last_steal_attempt': user_data.get('last_steal_attempt', 0)  # Preserve cooldown
        }
        
        # Save after each transaction
        self._save_balances()
        
        return new_balance
    
    def give_starter_balance(self, username, amount):
        """Give starter balance to user and mark them as having received it"""
        username = username.lower()
        if not self.has_received_starter(username):
            # Get current balance if any
            current_balance = self.get_balance(username)
            
            # Add starter amount to current balance
            self.balances[username] = {
                'balance': current_balance + amount,  # Add to existing balance
                'got_starter': True,
                'last_steal_attempt': self.balances.get(username, {}).get('last_steal_attempt', 0)
            }
            self._save_balances()
            return True
        return False
    
    def transfer(self, from_user, to_user, amount):
        """Transfer an amount from one user to another"""
        from_user = from_user.lower()
        to_user = to_user.lower()
        
        # Get current balances
        from_balance = self.get_balance(from_user)
        
        # Check if sender has enough funds
        if from_balance < amount:
            return False, from_balance, self.get_balance(to_user)
        
        # Get full user data
        from_data = self.balances.get(from_user, {'balance': from_balance, 'got_starter': True, 'last_steal_attempt': 0})
        to_data = self.balances.get(to_user, {'balance': 0, 'got_starter': False, 'last_steal_attempt': 0})
        
        # Update balances
        self.balances[from_user] = {
            'balance': max(0, from_data['balance'] - amount),
            'got_starter': from_data['got_starter'],
            'last_steal_attempt': from_data.get('last_steal_attempt', 0)
        }
        
        self.balances[to_user] = {
            'balance': to_data['balance'] + amount,
            'got_starter': to_data['got_starter'],
            'last_steal_attempt': to_data.get('last_steal_attempt', 0)
        }
        
        self._save_balances()
        
        return True, self.get_balance(from_user), self.get_balance(to_user)
    
    def get_leaderboard(self, limit=5):
        """Get the top users by balance"""
        sorted_users = sorted(self.balances.items(), key=lambda x: x[1]['balance'], reverse=True)
        return sorted_users[:limit]

    def format_balance(self, amount):
        """Format balance with commas for thousands"""
        return f"{amount:,}".replace(",", ",")

# Create a singleton instance
balance_manager = BalanceManager()