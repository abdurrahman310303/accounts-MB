from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.database import DatabaseManager
from app.models import Transaction, TransactionCreate, TransactionUpdate
import logging

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction with balance validation and inter-account transfers"""
        # All amounts are in PKR - no currency conversion needed
        amount_pkr = transaction_data.amount
        
        # Get sender account details
        sender_query = "SELECT current_balance, name FROM accounts WHERE id = $1"
        sender_result = await self.db.fetch_one(sender_query, transaction_data.account_id)
        
        if not sender_result:
            raise ValueError(f"Account with ID {transaction_data.account_id} not found")
        
        sender_current_balance = sender_result['current_balance']
        sender_name = sender_result['name']
        
        # Check if this is an inter-account transfer
        is_inter_account_transfer = False
        receiver_account = None
        
        if transaction_data.counterparty and transaction_data.counterparty != 'External':
            # Check if counterparty is an internal account
            counterparty_query = "SELECT id, current_balance, name FROM accounts WHERE name = $1"
            receiver_result = await self.db.fetch_one(counterparty_query, transaction_data.counterparty)
            
            if receiver_result:
                is_inter_account_transfer = True
                receiver_account = receiver_result
                
                # For inter-account transfers, ensure sender transaction is negative (outgoing)
                if transaction_data.amount > 0:
                    transaction_data.amount = -abs(transaction_data.amount)
                    amount_pkr = transaction_data.amount
        
        # Determine if this is an outgoing transaction (expense or transfer)
        is_outgoing_transaction = False
        
        # Check if this is an expense transaction (negative amount or category indicates expense)
        if transaction_data.amount < 0:
            is_outgoing_transaction = True
        elif is_inter_account_transfer:
            is_outgoing_transaction = True  # Already converted to negative above
        else:
            # Check if category indicates this is an expense or transfer
            if transaction_data.category_id:
                category_query = "SELECT name, category_type FROM categories WHERE id = $1"
                category_result = await self.db.fetch_one(category_query, transaction_data.category_id)
                
                # Validate counterparty for transfer transactions
                if category_result and category_result['category_type'] == 'transfer':
                    if not transaction_data.counterparty or transaction_data.counterparty.strip() == '':
                        raise ValueError("Counterparty is required for transfer transactions")
                
                if category_result and category_result['category_type'] == 'expense':
                    # Convert positive amount to negative for expense
                    transaction_data.amount = -abs(transaction_data.amount)
                    amount_pkr = transaction_data.amount
                    is_outgoing_transaction = True
        
        # For outgoing transactions, check if sender has sufficient balance
        if is_outgoing_transaction:
            required_balance = abs(amount_pkr)
            if sender_current_balance < required_balance:
                raise ValueError(
                    f"Insufficient balance in account '{sender_name}'. "
                    f"Available: Rs.{sender_current_balance:.2f}, Required: Rs.{required_balance:.2f}"
                )
        
        # Start transaction block for atomicity
        async with self.db.pool.connection() as conn:
            async with conn.transaction():
                # Create the main transaction
                sender_balance_after = sender_current_balance + amount_pkr
                
                insert_query = """
                INSERT INTO transactions (
                    account_id, transaction_date, category_id, team_id, 
                    counterparty, description, amount, currency, 
                    exchange_rate, amount_pkr, balance_after
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id, account_id, transaction_date, category_id, team_id, 
                          counterparty, description, amount, currency, exchange_rate, 
                          amount_pkr, balance_after, created_at, updated_at
                """
                
                result = await self.db.fetch_one(
                    insert_query,
                    transaction_data.account_id,
                    transaction_data.transaction_date,
                    transaction_data.category_id,
                    transaction_data.team_id,
                    transaction_data.counterparty,
                    transaction_data.description,
                    amount_pkr,
                    'PKR',
                    Decimal('1.0'),
                    amount_pkr,
                    sender_balance_after
                )
                
                # Update sender account balance
                update_sender_query = "UPDATE accounts SET current_balance = $1 WHERE id = $2"
                await self.db.execute(update_sender_query, sender_balance_after, transaction_data.account_id)
                
                # If this is an inter-account transfer, create the corresponding transaction for receiver
                if is_inter_account_transfer and receiver_account:
                    receiver_balance_after = receiver_account['current_balance'] + abs(amount_pkr)
                    
                    receiver_insert_query = """
                    INSERT INTO transactions (
                        account_id, transaction_date, category_id, team_id, 
                        counterparty, description, amount, currency, 
                        exchange_rate, amount_pkr, balance_after
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """
                    
                    await self.db.execute(
                        receiver_insert_query,
                        receiver_account['id'],
                        transaction_data.transaction_date,
                        transaction_data.category_id,
                        transaction_data.team_id,
                        sender_name,  # Counterparty for receiver is the sender
                        f"Transfer from {sender_name}: {transaction_data.description or ''}",
                        abs(amount_pkr),  # Positive amount for receiver
                        'PKR',
                        Decimal('1.0'),
                        abs(amount_pkr),
                        receiver_balance_after
                    )
                    
                    # Update receiver account balance
                    update_receiver_query = "UPDATE accounts SET current_balance = $1 WHERE id = $2"
                    await self.db.execute(update_receiver_query, receiver_balance_after, receiver_account['id'])
                
                return Transaction(**result)
    
    async def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        query = """
        SELECT id, account_id, transaction_date, category_id, team_id, 
               counterparty, description, amount, currency, exchange_rate, 
               amount_pkr, balance_after, created_at, updated_at
        FROM transactions WHERE id = $1
        """
        
        result = await self.db.fetch_one(query, transaction_id)
        if result:
            return Transaction(**result)
        return None
    
    async def get_transactions(
        self, 
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        team_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions with optional filtering"""
        conditions = []
        params = []
        param_count = 1
        
        if account_id:
            conditions.append(f"account_id = ${param_count}")
            params.append(account_id)
            param_count += 1
        
        if category_id:
            conditions.append(f"category_id = ${param_count}")
            params.append(category_id)
            param_count += 1
        
        if team_id:
            conditions.append(f"team_id = ${param_count}")
            params.append(team_id)
            param_count += 1
        
        if start_date:
            conditions.append(f"transaction_date >= ${param_count}")
            params.append(start_date)
            param_count += 1
        
        if end_date:
            conditions.append(f"transaction_date <= ${param_count}")
            params.append(end_date)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        SELECT id, account_id, transaction_date, category_id, team_id, 
               counterparty, description, amount, currency, exchange_rate, 
               amount_pkr, balance_after, created_at, updated_at
        FROM transactions {where_clause}
        ORDER BY transaction_date DESC, created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        params.extend([limit, offset])
        results = await self.db.fetch_all(query, *params)
        return [Transaction(**result) for result in results]
    
    async def update_transaction(self, transaction_id: int, transaction_data: TransactionUpdate) -> Optional[Transaction]:
        """Update transaction with balance recalculation"""
        # Get current transaction
        current_transaction = await self.get_transaction(transaction_id)
        if not current_transaction:
            raise ValueError("Transaction not found")
        
        # Get account balance before this transaction
        balance_query = "SELECT current_balance FROM accounts WHERE id = $1"
        account_result = await self.db.fetch_one(balance_query, current_transaction.account_id)
        
        if not account_result:
            raise ValueError("Account not found")
        
        current_account_balance = account_result['current_balance']
        
        # Reverse the original transaction amount from account balance
        balance_before_transaction = current_account_balance - current_transaction.amount_pkr
        
        # Build update query dynamically
        set_clauses = []
        params = []
        param_count = 1
        
        # Track if amount or account changed (requires balance recalculation)
        amount_changed = False
        account_changed = False
        
        if transaction_data.amount is not None:
            set_clauses.append(f"amount = ${param_count}")
            set_clauses.append(f"amount_pkr = ${param_count}")
            params.append(transaction_data.amount)
            param_count += 1
            amount_changed = True
        
        if transaction_data.account_id is not None and transaction_data.account_id != current_transaction.account_id:
            set_clauses.append(f"account_id = ${param_count}")
            params.append(transaction_data.account_id)
            param_count += 1
            account_changed = True
        
        # Handle counterparty validation for transfer transactions
        if transaction_data.category_id is not None:
            category_query = "SELECT category_type FROM categories WHERE id = $1"
            category_result = await self.db.fetch_one(category_query, transaction_data.category_id)
            if category_result and category_result['category_type'] == 'transfer':
                counterparty_to_check = transaction_data.counterparty if transaction_data.counterparty is not None else current_transaction.counterparty
                if not counterparty_to_check or counterparty_to_check.strip() == '':
                    raise ValueError("Counterparty is required for transfer transactions")
            
            set_clauses.append(f"category_id = ${param_count}")
            params.append(transaction_data.category_id)
            param_count += 1
        
        # Add other fields that don't require special handling
        simple_fields = ['team_id', 'counterparty', 'description', 'transaction_date']
        for field in simple_fields:
            value = getattr(transaction_data, field)
            if value is not None:
                set_clauses.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1
        
        if not set_clauses:
            return current_transaction
        
        # Calculate new balance
        new_amount = transaction_data.amount if transaction_data.amount is not None else current_transaction.amount_pkr
        new_balance_after = balance_before_transaction + new_amount
        
        set_clauses.append(f"balance_after = ${param_count}")
        params.append(new_balance_after)
        param_count += 1
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add transaction ID for WHERE clause
        params.append(transaction_id)
        
        query = f"""
        UPDATE transactions 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_count}
        RETURNING id, account_id, transaction_date, category_id, team_id, 
                  counterparty, description, amount, currency, exchange_rate, 
                  amount_pkr, balance_after, created_at, updated_at
        """
        
        result = await self.db.fetch_one(query, *params)
        
        # Update account balance if amount or account changed
        if amount_changed or account_changed:
            # Update original account balance (reverse original transaction)
            original_account_new_balance = current_account_balance - current_transaction.amount_pkr
            update_original_query = "UPDATE accounts SET current_balance = $1 WHERE id = $2"
            await self.db.execute(update_original_query, original_account_new_balance, current_transaction.account_id)
            
            # Update new account balance (apply new transaction)
            new_account_id = transaction_data.account_id if transaction_data.account_id is not None else current_transaction.account_id
            if new_account_id != current_transaction.account_id:
                # Get new account balance
                new_account_result = await self.db.fetch_one(balance_query, new_account_id)
                new_account_balance = new_account_result['current_balance'] + new_amount
            else:
                new_account_balance = new_balance_after
            
            update_new_query = "UPDATE accounts SET current_balance = $1 WHERE id = $2"
            await self.db.execute(update_new_query, new_account_balance, new_account_id)
        
        if result:
            return Transaction(**result)
        return None
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction and update account balance"""
        # Get transaction details
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Get current account balance
        balance_query = "SELECT current_balance FROM accounts WHERE id = $1"
        account_result = await self.db.fetch_one(balance_query, transaction.account_id)
        
        if not account_result:
            raise ValueError("Account not found")
        
        # Calculate new balance (reverse the transaction)
        new_balance = account_result['current_balance'] - transaction.amount_pkr
        
        # Start transaction for atomicity
        async with self.db.pool.connection() as conn:
            async with conn.transaction():
                # Delete the transaction
                delete_query = "DELETE FROM transactions WHERE id = $1"
                await self.db.execute(delete_query, transaction_id)
                
                # Update account balance
                update_query = "UPDATE accounts SET current_balance = $1 WHERE id = $2"
                await self.db.execute(update_query, new_balance, transaction.account_id)
        
        return True
