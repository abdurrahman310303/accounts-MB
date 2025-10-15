import psycopg
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
import asyncio
from typing import Optional, Dict, Any, List
from app.config import settings, get_direct_database_url
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = AsyncConnectionPool(
                get_direct_database_url(),
                min_size=settings.db_pool_min,
                max_size=settings.db_pool_max,
                timeout=30
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute(self, query: str, *args) -> None:
        """Execute a query that doesn't return data (INSERT, UPDATE, DELETE)"""
        async with self.pool.connection() as connection:
            try:
                async with connection.cursor() as cursor:
                    await cursor.execute(query, args)
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        async with self.pool.connection() as connection:
            try:
                async with connection.cursor() as cursor:
                    await cursor.execute(query, args)
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))
                    return None
            except Exception as e:
                logger.error(f"Fetch one failed: {e}")
                raise
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        async with self.pool.connection() as connection:
            try:
                async with connection.cursor() as cursor:
                    await cursor.execute(query, args)
                    rows = await cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
                    return []
            except Exception as e:
                logger.error(f"Fetch all failed: {e}")
                raise
    
    async def transaction(self):
        """Get a database transaction context"""
        return self.pool.connection()
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        async with self.pool.connection() as connection:
            async with connection.transaction():
                try:
                    async with connection.cursor() as cursor:
                        for query, args in queries:
                            await cursor.execute(query, args)
                    return True
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise

# Global database instance
db = DatabaseManager()

# Database dependency for FastAPI
async def get_database():
    """FastAPI dependency to get database instance"""
    return db

def get_db_manager():
    """Get database manager instance for dependency injection"""
    return db

# Startup and shutdown events
async def startup_db():
    """Initialize database connection on startup"""
    await db.connect()

async def shutdown_db():
    """Close database connection on shutdown"""
    await db.disconnect()

# SQL Query Templates
class Queries:
    """Centralized SQL queries"""
    
    # Account queries
    GET_ALL_ACCOUNTS = """
        SELECT * FROM accounts WHERE is_active = TRUE ORDER BY name
    """
    
    GET_ACCOUNT_BY_ID = """
        SELECT * FROM accounts WHERE id = $1 AND is_active = TRUE
    """
    
    CREATE_ACCOUNT = """
        INSERT INTO accounts (name, account_type, default_currency, opening_balance, current_balance)
        VALUES ($1, $2, $3, $4, $4)
        RETURNING *
    """
    
    UPDATE_ACCOUNT = """
        UPDATE accounts 
        SET name = $2, account_type = $3, default_currency = $4, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND is_active = TRUE
        RETURNING *
    """
    
    DELETE_ACCOUNT = """
        UPDATE accounts SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """
    
    # Transaction queries
    GET_TRANSACTIONS_BY_ACCOUNT = """
        SELECT t.*, c.name as category_name, tm.name as team_name, 
               a2.name as counterparty_account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN teams tm ON t.team_id = tm.id
        LEFT JOIN accounts a2 ON t.counterparty_account_id = a2.id
        WHERE t.account_id = $1
        ORDER BY t.transaction_date DESC, t.created_at DESC
    """
    
    CREATE_TRANSACTION = """
        INSERT INTO transactions (
            account_id, transaction_date, category_id, team_id, 
            counterparty_account_id, description, amount, currency, 
            exchange_rate, amount_pkr, balance_after, is_transfer, transfer_reference
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING *
    """
    
    # Category queries
    GET_ALL_CATEGORIES = """
        SELECT * FROM categories WHERE is_active = TRUE ORDER BY name
    """
    
    CREATE_CATEGORY = """
        INSERT INTO categories (name, category_type, description)
        VALUES ($1, $2, $3)
        RETURNING *
    """
    
    # Team queries
    GET_ALL_TEAMS = """
        SELECT * FROM teams WHERE is_active = TRUE ORDER BY name
    """
    
    CREATE_TEAM = """
        INSERT INTO teams (name, description)
        VALUES ($1, $2)
        RETURNING *
    """
    
    # Exchange rate queries
    GET_EXCHANGE_RATE = """
        SELECT rate FROM exchange_rates
        WHERE from_currency = $1 AND to_currency = $2 AND effective_date <= $3
        ORDER BY effective_date DESC
        LIMIT 1
    """
    
    CREATE_EXCHANGE_RATE = """
        INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (from_currency, to_currency, effective_date)
        DO UPDATE SET rate = EXCLUDED.rate
        RETURNING *
    """
    
    # Reporting queries
    ACCOUNT_SUMMARY = """
        SELECT * FROM account_summary ORDER BY name
    """
    
    TEAM_EXPENSE_SUMMARY = """
        SELECT * FROM team_expense_summary WHERE total_expense > 0
    """
    
    MONTHLY_PROFIT_LOSS = """
        SELECT * FROM monthly_profit_loss ORDER BY month DESC
    """
    
    BALANCE_SHEET_DATA = """
        SELECT 
            'Assets' as category,
            a.name as account_name,
            a.current_balance,
            a.default_currency
        FROM accounts a
        WHERE a.is_active = TRUE AND a.current_balance >= 0
        
        UNION ALL
        
        SELECT 
            'Liabilities' as category,
            a.name as account_name,
            ABS(a.current_balance) as current_balance,
            a.default_currency
        FROM accounts a
        WHERE a.is_active = TRUE AND a.current_balance < 0
        
        ORDER BY category, account_name
    """
