from typing import List, Optional
from app.database import DatabaseManager
from app.models import Team

class TeamService:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def get_teams(self) -> List[Team]:
        """Get all teams"""
        query = """
        SELECT id, name, description
        FROM teams
        ORDER BY name
        """
        
        results = await self.db.fetch_all(query)
        return [Team(**result) for result in results]
    
    async def get_team(self, team_id: int) -> Optional[Team]:
        """Get team by ID"""
        query = """
        SELECT id, name, description
        FROM teams 
        WHERE id = $1
        """
        
        result = await self.db.fetch_one(query, team_id)
        if result:
            return Team(**result)
        return None
    
    async def create_team(self, team_data: dict) -> Team:
        """Create a new team"""
        query = """
        INSERT INTO teams (name, description)
        VALUES ($1, $2)
        RETURNING id, name, description
        """
        
        result = await self.db.fetch_one(
            query,
            team_data.get('name'),
            team_data.get('description')
        )
        
        return Team(**result)
    
    async def update_team(self, team_id: int, team_data: dict) -> Optional[Team]:
        """Update team"""
        set_clauses = []
        params = []
        param_count = 1
        
        if 'name' in team_data:
            set_clauses.append(f"name = ${param_count}")
            params.append(team_data['name'])
            param_count += 1
        
        if 'description' in team_data:
            set_clauses.append(f"description = ${param_count}")
            params.append(team_data['description'])
            param_count += 1
        
        if not set_clauses:
            return await self.get_team(team_id)
        
        params.append(team_id)
        
        query = f"""
        UPDATE teams 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_count}
        RETURNING id, name, description
        """
        
        result = await self.db.fetch_one(query, *params)
        if result:
            return Team(**result)
        return None
    
    async def delete_team(self, team_id: int) -> bool:
        """Delete a team"""
        delete_query = "DELETE FROM teams WHERE id = $1"
        await self.db.execute(delete_query, team_id)
        return True
