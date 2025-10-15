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
        sender_query = "SELECT current_balance, name FROM accounts WHERE id = %s"
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
            counterparty_query = "SELECT id, current_balance, name FROM accounts WHERE name = %s"
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
            # Check if category indicates this is an expense
            category_query = "SELECT name, category_type FROM categories WHERE id = %s"
            category_result = await self.db.fetch_one(category_query, transaction_data.category_id)
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
                    account_id, category_id, amount, description, 
                    transaction_date, currency, exchange_rate, amount_pkr, balance_after,
                    team_id, counterparty
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, account_id, category_id, amount, description,
                          transaction_date, currency, exchange_rate, amount_pkr, balance_after,
                          team_id, counterparty, created_at, updated_at
                """
                
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        insert_query,
                        (
                            transaction_data.account_id,
                            transaction_data.category_id,
                            transaction_data.amount,
                            transaction_data.description,
                            transaction_data.transaction_date,
                            'PKR',  # Always PKR
                            Decimal('1.0'),  # Always 1.0 for PKR
                            amount_pkr,
                            sender_balance_after,
                            transaction_data.team_id,
                            transaction_data.counterparty
                        )
                    )
                    row = await cursor.fetchone()
                    columns = [desc[0] for desc in cursor.description]
                    sender_transaction_result = dict(zip(columns, row))
                
                # Update sender account balance
                update_sender_query = "UPDATE accounts SET current_balance = %s WHERE id = %s"
                async with conn.cursor() as cursor:
                    await cursor.execute(update_sender_query, (sender_balance_after, transaction_data.account_id))
                
                # If this is an inter-account transfer, create corresponding transaction for receiver
                if is_inter_account_transfer and receiver_account:
                    receiver_amount = abs(transaction_data.amount)  # Positive amount for receiver
                    receiver_balance_after = receiver_account['current_balance'] + receiver_amount
                    
                    # Create corresponding transaction for receiver account
                    receiver_insert_query = """
                    INSERT INTO transactions (
                        account_id, category_id, amount, description, 
                        transaction_date, currency, exchange_rate, amount_pkr, balance_after,
                        team_id, counterparty
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    receiver_description = f"Transfer from {sender_name}: {transaction_data.description or 'Internal Transfer'}"
                    
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            receiver_insert_query,
                            (
                                receiver_account['id'],
                                transaction_data.category_id,
                                receiver_amount,  # Positive amount for receiver
                                receiver_description,
                                transaction_data.transaction_date,
                                'PKR',  # Always PKR
                                Decimal('1.0'),  # Always 1.0 for PKR
                                receiver_amount,  # Same as amount since it's PKR
                                receiver_balance_after,
                                transaction_data.team_id,
                                sender_name  # Counterparty is the sender account
                            )
                        )
                    
                    # Update receiver account balance
                    update_receiver_query = "UPDATE accounts SET current_balance = %s WHERE id = %s"
                    async with conn.cursor() as cursor:
                        await cursor.execute(update_receiver_query, (receiver_balance_after, receiver_account['id']))
        
        return Transaction(**sender_transaction_result)
    
    async def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        query = """
        SELECT id, account_id, category_id, amount, description,
               transaction_date, currency, exchange_rate, amount_pkr, balance_after,
               team_id, counterparty, created_at, updated_at
        FROM transactions 
        WHERE id = %s
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
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions with filtering and pagination"""
        conditions = []
        params = []
        
        if account_id:
            conditions.append("account_id = %s")
            params.append(account_id)
        
        if category_id:
            conditions.append("category_id = %s")
            params.append(category_id)
        
        if team_id:
            conditions.append("team_id = %s")
            params.append(team_id)
        
        if start_date:
            conditions.append("transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("transaction_date <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.extend([limit, offset])
        
        query = f"""
        SELECT id, account_id, category_id, amount, description,
               transaction_date, currency, exchange_rate, amount_pkr, balance_after,
               team_id, counterparty, created_at, updated_at
        FROM transactions 
        {where_clause}
        ORDER BY transaction_date DESC, created_at DESC
        LIMIT %s OFFSET %s
        """
        
        results = await self.db.fetch_all(query, *params)
        return [Transaction(**result) for result in results]
    
    async def update_transaction(self, transaction_id: int, transaction_data: TransactionUpdate) -> Optional[Transaction]:
        """Update transaction with balance validation"""
        # Get current transaction
        current_transaction = await self.get_transaction(transaction_id)
        if not current_transaction:
            return None
        
        update_data = transaction_data.model_dump(exclude_unset=True)
        
        # If amount is being changed, validate balance
        if 'amount' in update_data:
            new_amount = update_data['amount']
            old_amount = current_transaction.amount
            account_id = update_data.get('account_id', current_transaction.account_id)
            
            # Get account current balance
            balance_query = "SELECT current_balance, name FROM accounts WHERE id = %s"
            account_result = await self.db.fetch_one(balance_query, account_id)
            
            if not account_result:
                raise ValueError(f"Account with ID {account_id} not found")
            
            current_balance = account_result['current_balance']
            account_name = account_result['name']
            
            # All amounts are in PKR - no conversion needed
            old_amount_pkr = old_amount
            new_amount_pkr = new_amount
            
            # Calculate the net change in balance requirement
            balance_change = new_amount_pkr - old_amount_pkr
            
            # For negative transactions (outgoing), check if account has sufficient balance
            if new_amount < 0:
                # Remove the old transaction effect first, then check if new transaction is possible
                balance_without_old_tx = current_balance - old_amount_pkr
                required_balance = abs(new_amount_pkr)
                
                if balance_without_old_tx < required_balance:
                    raise ValueError(
                        f"Insufficient balance in account '{account_name}'. "
                        f"Available (after reversing old transaction): Rs.{balance_without_old_tx:.2f}, "
                        f"Required: Rs.{required_balance:.2f}"
                    )
            
            # Update PKR amount and calculate new balance
            update_data['amount_pkr'] = new_amount_pkr
            update_data['currency'] = 'PKR'  # Always PKR
            update_data['exchange_rate'] = Decimal('1.0')  # Always 1.0 for PKR
            
            # The balance_after will be recalculated based on the net change
            new_balance_after = current_balance - old_amount_pkr + new_amount_pkr
            update_data['balance_after'] = new_balance_after
            
            # Update account's current balance
            async with self.db.pool.connection() as conn:
                async with conn.transaction():
                    # Update the transaction
                    set_clauses = []
                    params = []
                    
                    for field, value in update_data.items():
                        set_clauses.append(f"{field} = %s")
                        params.append(value)
                    
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(transaction_id)
                    
                    query = f"""
                    UPDATE transactions 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                    RETURNING id, account_id, category_id, amount, description,
                              transaction_date, currency, exchange_rate, amount_pkr, balance_after,
                              team_id, counterparty, created_at, updated_at
                    """
                    
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, params)
                        row = await cursor.fetchone()
                        columns = [desc[0] for desc in cursor.description]
                        result = dict(zip(columns, row)) if row else None
                    
                    # Update account balance
                    new_account_balance = current_balance + balance_change
                    update_account_query = "UPDATE accounts SET current_balance = %s WHERE id = %s"
                    async with conn.cursor() as cursor:
                        await cursor.execute(update_account_query, (new_account_balance, account_id))
            
            return Transaction(**result) if result else None
        
        else:
            # Regular update without amount change - ensure currency fields are set to PKR
            update_data['currency'] = 'PKR'
            update_data['exchange_rate'] = Decimal('1.0')
            
            set_clauses = []
            params = []
            
            for field, value in update_data.items():
                set_clauses.append(f"{field} = %s")
                params.append(value)
            
            if not set_clauses:
                return current_transaction
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(transaction_id)
            
            query = f"""
            UPDATE transactions 
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING id, account_id, category_id, amount, description,
                      transaction_date, currency, exchange_rate, amount_pkr, balance_after,
                      team_id, counterparty, created_at, updated_at
            """
            
            result = await self.db.fetch_one(query, *params)
            return Transaction(**result) if result else None
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction and update account balance"""
        # Get transaction details before deletion
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        # Get account current balance
        balance_query = "SELECT current_balance FROM accounts WHERE id = %s"
        account_result = await self.db.fetch_one(balance_query, transaction.account_id)
        
        if not account_result:
            raise ValueError(f"Account with ID {transaction.account_id} not found")
        
        current_balance = account_result['current_balance']
        
        async with self.db.pool.connection() as conn:
            async with conn.transaction():
                # Delete the transaction
                delete_query = "DELETE FROM transactions WHERE id = %s"
                async with conn.cursor() as cursor:
                    await cursor.execute(delete_query, (transaction_id,))
                
                # Update account balance (reverse the transaction effect)
                new_balance = current_balance - transaction.amount_pkr
                update_account_query = "UPDATE accounts SET current_balance = %s WHERE id = %s"
                async with conn.cursor() as cursor:
                    await cursor.execute(update_account_query, (new_balance, transaction.account_id))
                
                # If this was an inter-account transfer, find and delete/update the corresponding transaction
                if transaction.counterparty and transaction.counterparty != 'External':
                    # Find the corresponding transaction in the receiver account
                    counterparty_query = "SELECT id FROM accounts WHERE name = %s"
                    counterparty_result = await self.db.fetch_one(counterparty_query, transaction.counterparty)
                    
                    if counterparty_result:
                        # Find and delete the corresponding transaction
                        find_corresponding_query = """
                        SELECT id, amount_pkr FROM transactions 
                        WHERE account_id = %s AND counterparty = (SELECT name FROM accounts WHERE id = %s)
                        AND transaction_date = %s AND ABS(amount_pkr) = ABS(%s)
                        ORDER BY created_at DESC LIMIT 1
                        """
                        
                        corresponding_result = await self.db.fetch_one(
                            find_corresponding_query, 
                            counterparty_result['id'], 
                            transaction.account_id,
                            transaction.transaction_date,
                            transaction.amount_pkr
                        )
                        
                        if corresponding_result:
                            # Delete corresponding transaction
                            async with conn.cursor() as cursor:
                                await cursor.execute(delete_query, (corresponding_result['id'],))
                            
                            # Update counterparty account balance
                            counterparty_balance_query = "SELECT current_balance FROM accounts WHERE id = %s"
                            counterparty_balance_result = await self.db.fetch_one(
                                counterparty_balance_query, counterparty_result['id']
                            )
                            
                            if counterparty_balance_result:
                                counterparty_new_balance = counterparty_balance_result['current_balance'] - corresponding_result['amount_pkr']
                                async with conn.cursor() as cursor:
                                    await cursor.execute(
                                        update_account_query, 
                                        (counterparty_new_balance, counterparty_result['id'])
                                    )
        
        return True
    
    async def get_transactions_summary(
        self,
        account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary with totals"""
        conditions = []
        params = []
        
        if account_id:
            conditions.append("account_id = %s")
            params.append(account_id)
        
        if start_date:
            conditions.append("transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("transaction_date <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as total_credits,
            SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as total_debits,
            SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) as net_amount
        FROM transactions 
        {where_clause}
        """
        
        result = await self.db.fetch_one(query, *params)
        return dict(result) if result else {}
    
    async def bulk_import_transactions(self, transactions_data: List[TransactionCreate]) -> List[Transaction]:
        """Bulk import transactions"""
        created_transactions = []
        
        for transaction_data in transactions_data:
            # Use the existing create_transaction method for consistency
            transaction = await self.create_transaction(transaction_data)
            created_transactions.append(transaction)
        
        return created_transactions
