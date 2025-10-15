from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database import get_database
from app.services.team_service import TeamService
from app.models import Team

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=List[Team])
async def get_teams(db = Depends(get_database)):
    """Get all teams"""
    service = TeamService(db)
    return await service.get_teams()

@router.get("/{team_id}", response_model=Team)
async def get_team(team_id: int, db = Depends(get_database)):
    """Get team by ID"""
    service = TeamService(db)
    team = await service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/", response_model=Team)
async def create_team(team_data: dict, db = Depends(get_database)):
    """Create a new team"""
    service = TeamService(db)
    try:
        return await service.create_team(team_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{team_id}", response_model=Team)
async def update_team(team_id: int, team_data: dict, db = Depends(get_database)):
    """Update team"""
    service = TeamService(db)
    try:
        team = await service.update_team(team_id, team_data)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{team_id}")
async def delete_team(team_id: int, db = Depends(get_database)):
    """Delete a team"""
    service = TeamService(db)
    try:
        success = await service.delete_team(team_id)
        if not success:
            raise HTTPException(status_code=404, detail="Team not found")
        return {"message": "Team deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
