"""initial_schema

Revision ID: 1badd2ac89ed
Revises: 
Create Date: 2025-10-12 22:23:28.501418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1badd2ac89ed'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create currencies table
    op.execute("""
        CREATE TABLE currencies (
            code VARCHAR(3) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            symbol VARCHAR(5),
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # Create accounts table
    op.execute("""
        CREATE TABLE accounts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            account_type VARCHAR(50) NOT NULL,
            default_currency VARCHAR(3) NOT NULL DEFAULT 'PKR',
            opening_balance DECIMAL(15,2) DEFAULT 0.00,
            current_balance DECIMAL(15,2) DEFAULT 0.00,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create teams table
    op.execute("""
        CREATE TABLE teams (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create categories table
    op.execute("""
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            category_type VARCHAR(20) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create exchange_rates table
    op.execute("""
        CREATE TABLE exchange_rates (
            id SERIAL PRIMARY KEY,
            from_currency VARCHAR(3) REFERENCES currencies(code),
            to_currency VARCHAR(3) REFERENCES currencies(code),
            rate DECIMAL(10,4) NOT NULL,
            effective_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(from_currency, to_currency, effective_date)
        )
    """)
    
    # Create transactions table
    op.execute("""
        CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            account_id INTEGER REFERENCES accounts(id),
            transaction_date DATE NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            team_id INTEGER REFERENCES teams(id),
            counterparty_account_id INTEGER REFERENCES accounts(id),
            description TEXT,
            amount DECIMAL(15,2) NOT NULL,
            currency VARCHAR(3) REFERENCES currencies(code),
            exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
            amount_pkr DECIMAL(15,2) NOT NULL,
            balance_after DECIMAL(15,2) NOT NULL,
            is_transfer BOOLEAN DEFAULT FALSE,
            transfer_reference VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create transfers table
    op.execute("""
        CREATE TABLE transfers (
            id SERIAL PRIMARY KEY,
            reference_id VARCHAR(50) UNIQUE NOT NULL,
            from_account_id INTEGER REFERENCES accounts(id),
            to_account_id INTEGER REFERENCES accounts(id),
            from_transaction_id INTEGER REFERENCES transactions(id),
            to_transaction_id INTEGER REFERENCES transactions(id),
            amount DECIMAL(15,2) NOT NULL,
            currency VARCHAR(3) REFERENCES currencies(code),
            transfer_date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX idx_transactions_account_date ON transactions(account_id, transaction_date)")
    op.execute("CREATE INDEX idx_transactions_category ON transactions(category_id)")
    op.execute("CREATE INDEX idx_transactions_team ON transactions(team_id)")
    op.execute("CREATE INDEX idx_transactions_date ON transactions(transaction_date)")
    op.execute("CREATE INDEX idx_exchange_rates_date ON exchange_rates(effective_date)")
    op.execute("CREATE INDEX idx_transfers_reference ON transfers(reference_id)")
    
    # Insert base currencies
    op.execute("""
        INSERT INTO currencies (code, name, symbol) VALUES 
        ('PKR', 'Pakistani Rupee', '₨'),
        ('USD', 'US Dollar', '$'),
        ('EUR', 'Euro', '€'),
        ('GBP', 'British Pound', '£')
    """)
    
    # Insert sample teams
    op.execute("""
        INSERT INTO teams (name, description) VALUES 
        ('MinorBugs', 'MinorBugs Development Team'),
        ('BraveJackals', 'BraveJackals Team'),
        ('GoJins', 'GoJins Team'),
        ('BuggiesKids', 'BuggiesKids Team'),
        ('GameHippo', 'GameHippo Team'),
        ('Frentech', 'Frentech Team'),
        ('DevBoat', 'DevBoat Team')
    """)
    
    # Insert sample categories
    op.execute("""
        INSERT INTO categories (name, category_type, description) VALUES 
        ('Income', 'income', 'Revenue and income'),
        ('Marketing', 'expense', 'Marketing and advertising expenses'),
        ('AdwordUA', 'expense', 'Google Ads expenses'),
        ('TikTokUA', 'expense', 'TikTok advertising'),
        ('Salaries', 'expense', 'Employee salaries'),
        ('FED', 'expense', 'Federal taxes and fees'),
        ('CompanyExpense', 'expense', 'General company expenses'),
        ('SaadPersonal', 'expense', 'Saad personal expenses'),
        ('KashifPersonal', 'expense', 'Kashif personal expenses'),
        ('NasirPersonal', 'expense', 'Nasir personal expenses'),
        ('OfficeRent', 'expense', 'Office rent'),
        ('Equipments', 'expense', 'Equipment purchases'),
        ('TransferEntry', 'transfer', 'Inter-account transfers'),
        ('ProfitTax', 'expense', 'Profit tax payments'),
        ('Donation', 'expense', 'Donations'),
        ('HomeExpense', 'expense', 'Home related expenses'),
        ('Investments', 'income', 'Investment income'),
        ('UnityUA', 'expense', 'Unity advertising'),
        ('A/C Receivable', 'income', 'Accounts receivable')
    """)
    
    # Insert sample exchange rates
    op.execute("""
        INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date) VALUES 
        ('USD', 'PKR', 283.0000, '2025-01-01'),
        ('PKR', 'PKR', 1.0000, '2025-01-01'),
        ('EUR', 'PKR', 310.0000, '2025-01-01'),
        ('GBP', 'PKR', 350.0000, '2025-01-01')
    """)
    
    # Create views
    op.execute("""
        CREATE VIEW account_summary AS
        SELECT 
            a.id,
            a.name,
            a.account_type,
            a.default_currency,
            a.opening_balance,
            a.current_balance,
            COUNT(t.id) as transaction_count,
            COALESCE(SUM(CASE WHEN t.amount_pkr > 0 THEN t.amount_pkr ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN t.amount_pkr < 0 THEN ABS(t.amount_pkr) ELSE 0 END), 0) as total_expenses,
            COALESCE(SUM(t.amount_pkr), 0) as net_amount
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.account_id
        WHERE a.is_active = TRUE
        GROUP BY a.id, a.name, a.account_type, a.default_currency, a.opening_balance, a.current_balance
    """)
    
    # Create functions
    op.execute("""
        CREATE OR REPLACE FUNCTION get_exchange_rate(
            p_from_currency VARCHAR(3),
            p_to_currency VARCHAR(3),
            p_date DATE
        ) RETURNS DECIMAL(10,4) AS $$
        DECLARE
            rate DECIMAL(10,4);
        BEGIN
            IF p_from_currency = p_to_currency THEN
                RETURN 1.0000;
            END IF;
            
            SELECT er.rate INTO rate
            FROM exchange_rates er
            WHERE er.from_currency = p_from_currency 
            AND er.to_currency = p_to_currency
            AND er.effective_date <= p_date
            ORDER BY er.effective_date DESC
            LIMIT 1;
            
            RETURN COALESCE(rate, 1.0000);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_account_balance()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE accounts 
            SET current_balance = current_balance + NEW.amount_pkr,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.account_id;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    op.execute("""
        CREATE TRIGGER trigger_update_account_balance
            AFTER INSERT ON transactions
            FOR EACH ROW
            EXECUTE FUNCTION update_account_balance();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in reverse order
    op.execute("DROP TRIGGER IF EXISTS trigger_update_account_balance ON transactions")
    op.execute("DROP FUNCTION IF EXISTS update_account_balance()")
    op.execute("DROP FUNCTION IF EXISTS get_exchange_rate(VARCHAR(3), VARCHAR(3), DATE)")
    op.execute("DROP VIEW IF EXISTS account_summary")
    op.execute("DROP TABLE IF EXISTS transfers")
    op.execute("DROP TABLE IF EXISTS transactions")
    op.execute("DROP TABLE IF EXISTS exchange_rates")
    op.execute("DROP TABLE IF EXISTS categories")
    op.execute("DROP TABLE IF EXISTS teams")
    op.execute("DROP TABLE IF EXISTS accounts")
    op.execute("DROP TABLE IF EXISTS currencies")
