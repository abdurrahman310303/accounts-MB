from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.database import DatabaseManager
from app.models import Account, AccountCreate, Team
import logging

logger = logging.getLogger(__name__)

class AccountService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create_account(self, account_data: AccountCreate) -> Account:
        """Create a new account"""
        query = """
        INSERT INTO accounts (name, account_type, default_currency, opening_balance, current_balance)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, name, account_type, default_currency, opening_balance, current_balance, 
                  is_active, created_at, updated_at
        """
        
        opening_balance = account_data.opening_balance or Decimal('0.00')
        
        result = await self.db.fetch_one(
            query, 
            account_data.name, 
            account_data.account_type, 
            account_data.default_currency,
            opening_balance,
            opening_balance
        )
        
        return Account(**result)
    
    async def get_account(self, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        query = """
        SELECT id, name, account_type, default_currency, opening_balance, current_balance, 
               is_active, created_at, updated_at
        FROM accounts WHERE id = $1 AND is_active = TRUE
        """
        
        result = await self.db.fetch_one(query, account_id)
        if result:
            return Account(**result)
        return None
    
    async def get_accounts(self, team_id: Optional[int] = None, account_type: Optional[str] = None) -> List[Account]:
        """Get all accounts with optional filtering"""
        conditions = ["is_active = TRUE"]
        params = []
        param_count = 1
        
        if account_type:
            conditions.append(f"account_type = ${param_count}")
            params.append(account_type)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
        SELECT id, name, account_type, default_currency, opening_balance, current_balance, 
               is_active, created_at, updated_at
        FROM accounts {where_clause}
        ORDER BY name
        """
        
        results = await self.db.fetch_all(query, *params)
        return [Account(**result) for result in results]
    
    async def update_account(self, account_id: int, account_data: dict) -> Optional[Account]:
        """Update account information"""
        set_clauses = []
        params = []
        param_count = 1
        
        # Handle opening balance change - if opening balance changes, we need to recalculate current balance
        if 'opening_balance' in account_data:
            # Get current account to check if opening balance is changing
            current_account = await self.get_account(account_id)
            if current_account:
                old_opening_balance = current_account.opening_balance
                new_opening_balance = Decimal(str(account_data['opening_balance']))
                
                # Calculate the difference and adjust current balance accordingly
                balance_difference = new_opening_balance - old_opening_balance
                
                # Get total transactions amount for this account
                tx_query = "SELECT COALESCE(SUM(amount_pkr), 0) as total_tx FROM transactions WHERE account_id = $1"
                tx_result = await self.db.fetch_one(tx_query, account_id)
                total_transactions = tx_result['total_tx'] if tx_result else Decimal('0')
                
                # New current balance = new opening balance + total transactions
                new_current_balance = new_opening_balance + total_transactions
                
                # Add current_balance to the update as well
                account_data['current_balance'] = new_current_balance
        
        allowed_fields = ['name', 'account_type', 'default_currency', 'opening_balance', 'current_balance']
        for field in allowed_fields:
            if field in account_data:
                set_clauses.append(f"{field} = ${param_count}")
                params.append(account_data[field])
                param_count += 1
        
        if not set_clauses:
            return await self.get_account(account_id)
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(account_id)
        
        query = f"""
        UPDATE accounts 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_count}
        RETURNING id, name, account_type, default_currency, opening_balance, current_balance, 
                  is_active, created_at, updated_at
        """
        
        result = await self.db.fetch_one(query, *params)
        if result:
            return Account(**result)
        return None
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete an account (only if no transactions exist)"""
        # Check if account has transactions
        check_query = "SELECT COUNT(*) as count FROM transactions WHERE account_id = $1"
        result = await self.db.fetch_one(check_query, account_id)
        
        if result['count'] > 0:
            raise ValueError("Cannot delete account with existing transactions")
        
        delete_query = "DELETE FROM accounts WHERE id = $1"
        await self.db.execute(delete_query, account_id)
        return True
    
    async def get_account_summary(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account summary with transactions and balance"""
        # Simplified query without views
        query = """
        SELECT id, name, account_type, default_currency, opening_balance, current_balance, 
               is_active, created_at, updated_at
        FROM accounts 
        WHERE id = $1 AND is_active = TRUE
        """
        
        result = await self.db.fetch_one(query, account_id)
        return dict(result) if result else None
    
    async def get_accounts_summary(self, team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get summary for all accounts"""
        # Simplified query without views
        query = """
        SELECT id, name, account_type, default_currency, opening_balance, current_balance, 
               is_active, created_at, updated_at
        FROM accounts
        WHERE is_active = TRUE
        ORDER BY name
        """
        
        results = await self.db.fetch_all(query)
        return [dict(row) for row in results]
