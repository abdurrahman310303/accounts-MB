from typing import List, Optional
from app.database import DatabaseManager
from app.models import Category

class CategoryService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def get_categories(self) -> List[Category]:
        """Get all categories"""
        query = """
        SELECT id, name, category_type, description
        FROM categories
        ORDER BY name
        """
        
        results = await self.db.fetch_all(query)
        return [Category(**result) for result in results]
    
    async def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        query = """
        SELECT id, name, category_type, description
        FROM categories 
        WHERE id = $1
        """
        
        result = await self.db.fetch_one(query, category_id)
        if result:
            return Category(**result)
        return None
