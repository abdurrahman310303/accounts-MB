from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

class CategoryTypeEnum(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

# Team Model
class Team(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

# Account Models
class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str
    default_currency: str = "PKR"
    opening_balance: Optional[Decimal] = Field(default=Decimal('0.00'))

class AccountCreate(AccountBase):
    pass

class Account(AccountBase):
    id: int
    current_balance: Decimal
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Category Models
class Category(BaseModel):
    id: int
    name: str
    category_type: CategoryTypeEnum
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

# Transaction Models
class TransactionBase(BaseModel):
    account_id: int
    amount: Decimal = Field(..., ne=0)
    description: Optional[str] = None
    transaction_date: date
    category_id: Optional[int] = None
    team_id: Optional[int] = None
    counterparty: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    team_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, ne=0)
    description: Optional[str] = None
    counterparty: Optional[str] = None
    transaction_date: Optional[date] = None

class Transaction(TransactionBase):
    id: int
    amount_pkr: Decimal
    balance_after: Decimal
    currency: str = "PKR"  # Always PKR for display
    exchange_rate: Decimal = Decimal('1.0')  # Always 1.0 for PKR
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True



class BalanceSheetItem(BaseModel):
    category: str  # 'Assets' or 'Liabilities'
    account_name: str
    current_balance: Decimal
    default_currency: str

class BalanceSheet(BaseModel):
    assets: List[BalanceSheetItem]
    liabilities: List[BalanceSheetItem]
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    generated_at: datetime

# Pagination Models
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=1000)

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

# Filter Models
class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    team_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    is_transfer: Optional[bool] = None


