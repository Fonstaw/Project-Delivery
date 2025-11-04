from supabase import create_client, Client
import config
from typing import Optional, Dict, List

class Database:
    def __init__(self):
        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    def is_user_authorized(self, user_id: int) -> bool:
        """Check if user is authorized (either in database or is admin)"""
        # Check if user is admin first
        if user_id in config.ADMIN_IDS:
            return True
        
        # Otherwise check if user exists in database
        try:
            response = self.client.table('users').select('*').eq('telegram_id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking user authorization: {e}")
            return False
    
    def get_user_balance(self, user_id: int) -> float:
        """Get user balance"""
        try:
            response = self.client.table('users').select('balance').eq('telegram_id', user_id).execute()
            if response.data:
                return response.data[0]['balance']
            return 0.0
        except Exception as e:
            print(f"Error getting user balance: {e}")
            return 0.0
    
    def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Update user balance"""
        try:
            response = self.client.table('users').update({'balance': amount}).eq('telegram_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user balance: {e}")
            return False
    
    def add_user(self, telegram_id: int, name: str, initial_balance: float = 0.0) -> tuple[bool, str]:
        """Add new user - returns (success, error_message)"""
        try:
            data = {
                'telegram_id': telegram_id,
                'name': name,
                'balance': initial_balance
            }
            response = self.client.table('users').insert(data).execute()
            return True, ""
        except Exception as e:
            error_msg = str(e)
            print(f"Error adding user: {error_msg}")
            return False, error_msg
    
    def create_order(self, order_data: Dict) -> bool:
        """Create new order"""
        try:
            response = self.client.table('orders').insert(order_data).execute()
            return True
        except Exception as e:
            print(f"Error creating order: {e}")
            return False
    
    def get_next_order_number(self) -> int:
        """Get next order number"""
        try:
            response = self.client.table('orders').select('order_number').order('created_at', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]['order_number'] + 1
            return 1000
        except Exception as e:
            print(f"Error getting next order number: {e}")
            return 1000
