from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def get_profit_loss_statement(
        self,
        team_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        base_currency_id: int = 1  # Default to USD
    ) -> Dict[str, Any]:
        """Generate Profit & Loss statement"""
        conditions = []
        params = []
        
        if team_id:
            conditions.append("a.team_id = %s")
            params.append(team_id)
        
        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(base_currency_id)
        
        query = f"""
        WITH converted_transactions AS (
            SELECT 
                t.amount * COALESCE(er.rate, 1.0) as converted_amount,
                c.category_type,
                c.name as category_name,
                t.transaction_type
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN exchange_rates er ON (
                a.currency_id = er.from_currency_id 
                AND er.to_currency_id = %s 
                AND er.effective_date <= t.transaction_date
            )
            {where_clause}
        ),
        category_totals AS (
            SELECT 
                category_type,
                category_name,
                SUM(CASE WHEN transaction_type = 'credit' THEN converted_amount ELSE 0 END) as credits,
                SUM(CASE WHEN transaction_type = 'debit' THEN converted_amount ELSE 0 END) as debits
            FROM converted_transactions
            WHERE category_type IS NOT NULL
            GROUP BY category_type, category_name
        )
        SELECT 
            category_type,
            category_name,
            credits,
            debits,
            (credits - debits) as net_amount
        FROM category_totals
        ORDER BY category_type, category_name
        """
        
        results = await self.db.fetch_all(query, *params)
        
        # Organize results
        revenue = []
        expenses = []
        total_revenue = Decimal('0')
        total_expenses = Decimal('0')
        
        for row in results:
            row_dict = dict(row)
            if row['category_type'] == 'income':
                revenue.append(row_dict)
                total_revenue += row['net_amount']
            elif row['category_type'] == 'expense':
                expenses.append(row_dict)
                total_expenses += abs(row['net_amount'])
        
        net_profit = total_revenue - total_expenses
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'items': revenue,
                'total': total_revenue
            },
            'expenses': {
                'items': expenses,
                'total': total_expenses
            },
            'net_profit': net_profit,
            'base_currency_id': base_currency_id
        }
    
    async def get_balance_sheet(
        self,
        team_id: Optional[int] = None,
        as_of_date: Optional[date] = None,
        base_currency_id: int = 1
    ) -> Dict[str, Any]:
        """Generate Balance Sheet"""
        conditions = []
        params = []
        
        if team_id:
            conditions.append("a.team_id = %s")
            params.append(team_id)
        
        if as_of_date:
            conditions.append("t.transaction_date <= %s")
            params.append(as_of_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(base_currency_id)
        
        query = f"""
        WITH account_balances AS (
            SELECT 
                a.id,
                a.name,
                a.account_type,
                a.balance * COALESCE(er.rate, 1.0) as converted_balance
            FROM accounts a
            LEFT JOIN exchange_rates er ON (
                a.currency_id = er.from_currency_id 
                AND er.to_currency_id = %s 
                AND er.effective_date = (
                    SELECT MAX(effective_date) 
                    FROM exchange_rates er2 
                    WHERE er2.from_currency_id = a.currency_id 
                    AND er2.to_currency_id = %s
                    AND er2.effective_date <= COALESCE(%s, CURRENT_DATE)
                )
            )
            {where_clause.replace('t.transaction_date', 'CURRENT_DATE') if 't.transaction_date' in where_clause else where_clause}
        )
        SELECT 
            account_type,
            name,
            converted_balance
        FROM account_balances
        ORDER BY account_type, name
        """
        
        # Adjust parameters for the modified query
        balance_params = []
        if team_id:
            balance_params.append(team_id)
        balance_params.extend([base_currency_id, base_currency_id, as_of_date])
        
        results = await self.db.fetch_all(query, *balance_params)
        
        # Organize by account type
        assets = []
        liabilities = []
        equity = []
        
        total_assets = Decimal('0')
        total_liabilities = Decimal('0')
        total_equity = Decimal('0')
        
        for row in results:
            row_dict = dict(row)
            balance = row['converted_balance']
            
            if row['account_type'] in ['checking', 'savings', 'investment', 'cash']:
                assets.append(row_dict)
                total_assets += balance
            elif row['account_type'] in ['credit_card', 'loan', 'liability']:
                liabilities.append(row_dict)
                total_liabilities += balance
            elif row['account_type'] == 'equity':
                equity.append(row_dict)
                total_equity += balance
        
        return {
            'as_of_date': as_of_date or date.today(),
            'assets': {
                'items': assets,
                'total': total_assets
            },
            'liabilities': {
                'items': liabilities,
                'total': total_liabilities
            },
            'equity': {
                'items': equity,
                'total': total_equity
            },
            'total_equity_and_liabilities': total_liabilities + total_equity,
            'base_currency_id': base_currency_id
        }
    
    async def get_cash_flow_statement(
        self,
        team_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        base_currency_id: int = 1
    ) -> Dict[str, Any]:
        """Generate Cash Flow statement"""
        conditions = []
        params = []
        
        if team_id:
            conditions.append("a.team_id = %s")
            params.append(team_id)
        
        if start_date:
            conditions.append("t.transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("t.transaction_date <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(base_currency_id)
        
        query = f"""
        WITH cash_accounts AS (
            SELECT id FROM accounts 
            WHERE account_type IN ('checking', 'savings', 'cash')
            {'AND team_id = %s' if team_id else ''}
        ),
        cash_transactions AS (
            SELECT 
                t.amount * COALESCE(er.rate, 1.0) as converted_amount,
                t.transaction_type,
                c.category_type,
                c.name as category_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN cash_accounts ca ON a.id = ca.id
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN exchange_rates er ON (
                a.currency_id = er.from_currency_id 
                AND er.to_currency_id = %s 
                AND er.effective_date <= t.transaction_date
            )
            {where_clause}
        )
        SELECT 
            category_type,
            category_name,
            SUM(CASE WHEN transaction_type = 'credit' THEN converted_amount ELSE 0 END) as cash_in,
            SUM(CASE WHEN transaction_type = 'debit' THEN converted_amount ELSE 0 END) as cash_out
        FROM cash_transactions
        WHERE category_type IS NOT NULL
        GROUP BY category_type, category_name
        ORDER BY category_type, category_name
        """
        
        results = await self.db.fetch_all(query, *params)
        
        operating_activities = []
        investing_activities = []
        financing_activities = []
        
        total_operating = Decimal('0')
        total_investing = Decimal('0')
        total_financing = Decimal('0')
        
        for row in results:
            row_dict = dict(row)
            net_cash = row['cash_in'] - row['cash_out']
            row_dict['net_cash'] = net_cash
            
            # Categorize cash flows (this is simplified - in practice, you'd need more sophisticated categorization)
            if row['category_type'] in ['income', 'expense']:
                operating_activities.append(row_dict)
                total_operating += net_cash
            elif row['category_type'] == 'investment':
                investing_activities.append(row_dict)
                total_investing += net_cash
            else:
                financing_activities.append(row_dict)
                total_financing += net_cash
        
        net_change_in_cash = total_operating + total_investing + total_financing
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'operating_activities': {
                'items': operating_activities,
                'total': total_operating
            },
            'investing_activities': {
                'items': investing_activities,
                'total': total_investing
            },
            'financing_activities': {
                'items': financing_activities,
                'total': total_financing
            },
            'net_change_in_cash': net_change_in_cash,
            'base_currency_id': base_currency_id
        }
    
    async def get_account_analysis(
        self,
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get detailed account analysis"""
        conditions = ["account_id = %s"]
        params = [account_id]
        
        if start_date:
            conditions.append("transaction_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("transaction_date <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
        SELECT 
            DATE_TRUNC('month', transaction_date) as month,
            COUNT(*) as transaction_count,
            SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as credits,
            SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as debits,
            AVG(amount) as avg_transaction_amount,
            MIN(amount) as min_transaction_amount,
            MAX(amount) as max_transaction_amount
        FROM transactions
        {where_clause}
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY month
        """
        
        results = await self.db.fetch_all(query, *params)
        
        monthly_data = []
        total_credits = Decimal('0')
        total_debits = Decimal('0')
        total_transactions = 0
        
        for row in results:
            row_dict = dict(row)
            row_dict['net_amount'] = row['credits'] - row['debits']
            monthly_data.append(row_dict)
            
            total_credits += row['credits']
            total_debits += row['debits']
            total_transactions += row['transaction_count']
        
        return {
            'account_id': account_id,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_transactions': total_transactions,
                'total_credits': total_credits,
                'total_debits': total_debits,
                'net_amount': total_credits - total_debits
            },
            'monthly_breakdown': monthly_data
        }
