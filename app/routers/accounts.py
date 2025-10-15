from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.database import get_database
from app.services.account_service import AccountService
from app.models import Account, AccountCreate

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/", response_model=Account)
async def create_account(
    account_data: AccountCreate,
    db = Depends(get_database)
):
    """Create a new account"""
    service = AccountService(db)
    try:
        return await service.create_account(account_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Account])
async def get_accounts(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    db = Depends(get_database)
):
    """Get all accounts with optional filtering"""
    service = AccountService(db)
    return await service.get_accounts(team_id=team_id, account_type=account_type)

@router.get("/{account_id}", response_model=Account)
async def get_account(
    account_id: int,
    db = Depends(get_database)
):
    """Get account by ID"""
    service = AccountService(db)
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.put("/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    account_data: dict,
    db = Depends(get_database)
):
    """Update account information"""
    service = AccountService(db)
    try:
        account = await service.update_account(account_id, account_data)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return account
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    db = Depends(get_database)
):
    """Delete an account"""
    service = AccountService(db)
    try:
        await service.delete_account(account_id)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{account_id}/summary")
async def get_account_summary(
    account_id: int,
    db = Depends(get_database)
):
    """Get account summary with transactions and balance"""
    service = AccountService(db)
    summary = await service.get_account_summary(account_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Account not found")
    return summary

@router.get("/summary/all")
async def get_accounts_summary(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    db = Depends(get_database)
):
    """Get summary for all accounts"""
    service = AccountService(db)
    return await service.get_accounts_summary(team_id=team_id)
