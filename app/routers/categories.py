from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database import get_database
from app.services.category_service import CategoryService
from app.models import Category

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=List[Category])
async def get_categories(
    db = Depends(get_database)
):
    """Get all categories"""
    service = CategoryService(db)
    return await service.get_categories()

@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db = Depends(get_database)
):
    """Get category by ID"""
    service = CategoryService(db)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
