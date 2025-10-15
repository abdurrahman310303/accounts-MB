from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date
from app.database import get_database
from app.services.transaction_service import TransactionService
from app.models import Transaction, TransactionCreate, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=Transaction)
async def create_transaction(
    transaction_data: TransactionCreate,
    db = Depends(get_database)
):
    """Create a new transaction"""
    service = TransactionService(db)
    try:
        return await service.create_transaction(transaction_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Transaction])
async def get_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db = Depends(get_database)
):
    """Get transactions with filtering and pagination"""
    service = TransactionService(db)
    return await service.get_transactions(
        account_id=account_id,
        category_id=category_id,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: int,
    db = Depends(get_database)
):
    """Get transaction by ID"""
    service = TransactionService(db)
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db = Depends(get_database)
):
    """Update transaction"""
    service = TransactionService(db)
    try:
        transaction = await service.update_transaction(transaction_id, transaction_data)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db = Depends(get_database)
):
    """Delete a transaction"""
    service = TransactionService(db)
    try:
        await service.delete_transaction(transaction_id)
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/{account_id}/details")
async def get_account_transactions_with_details(
    account_id: int,
    db = Depends(get_database)
):
    """Get transactions with account and category details"""
    service = TransactionService(db)
    return await service.get_account_transactions_with_details(account_id)

@router.get("/summary/overview")
async def get_transactions_summary(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db = Depends(get_database)
):
    """Get transaction summary with totals"""
    service = TransactionService(db)
    return await service.get_transactions_summary(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )

@router.post("/bulk-import", response_model=List[Transaction])
async def bulk_import_transactions(
    transactions_data: List[TransactionCreate],
    db = Depends(get_database)
):
    """Bulk import transactions"""
    service = TransactionService(db)
    try:
        return await service.bulk_import_transactions(transactions_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
