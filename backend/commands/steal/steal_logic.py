import random
from commands.balance.balance_manager import balance_manager
from .steal_chance_manager import steal_chance_manager

def try_steal(thief, victim, is_privileged=False, force_starter_chance=False):
    """
    Attempt to steal money from another user
    
    Args:
        thief (str): Username of the thief
        victim (str): Username of the victim
        is_privileged (bool): Whether the thief is a privileged user
        force_starter_chance (bool): Whether to force starter chance (20%) for zero balance users
    """
    # Get current balances
    thief_balance = balance_manager.get_balance(thief)
    victim_balance = balance_manager.get_balance(victim)
    
    # If victim has no money
    if victim_balance == 0:
        return {
            'success': False,
            'reason': 'no_money',
            'thief_balance': thief_balance,
            'victim_balance': victim_balance
        }
    
    # For users with 0 balance, use 20% chance if force_starter_chance is True
    if force_starter_chance:
        steal_chance = 0.2  # 20% chance for new/broke users
    else:
        # Get final steal chance from steal_chance_manager
        steal_chance = steal_chance_manager.get_final_steal_chance(thief, victim)
    
    # Privileged users get +20% chance
    if is_privileged:
        steal_chance = min(1.0, steal_chance + 0.2)
    
    # Roll for success
    if random.random() < steal_chance:
        # Success - calculate steal amount
        if force_starter_chance:
            # For zero balance users, steal 1 ruble on success
            steal_amount = 1
        else:
            # Normal steal calculation
            max_steal = int(victim_balance * 0.3)  # Can steal up to 30%
            steal_amount = random.randint(1, max_steal)
        
        # Transfer the money
        balance_manager.adjust_balance(victim, -steal_amount)
        new_thief_balance = balance_manager.adjust_balance(thief, steal_amount)
        new_victim_balance = balance_manager.get_balance(victim)
        
        return {
            'success': True,
            'amount': steal_amount,
            'thief_balance': new_thief_balance,
            'victim_balance': new_victim_balance
        }
    
    # Failed attempt
    # Penalty: lose some rubles (if the thief has any)
    penalty = 0
    
    if thief_balance > 0:
        # Calculate maximum penalty (30% of thief's balance)
        max_penalty = int(thief_balance * 0.3)
        
        # Calculate random penalty between 1 and max_penalty
        penalty = random.randint(1, max_penalty) if max_penalty > 0 else 1
        
        # Remove penalty from thief
        balance_manager.adjust_balance(thief, -penalty)
        # Give penalty to victim
        balance_manager.adjust_balance(victim, penalty)
    
    return {
        'success': False,
        'reason': 'failed',
        'penalty': penalty,
        'thief_balance': balance_manager.get_balance(thief),
        'victim_balance': balance_manager.get_balance(victim)
    } 