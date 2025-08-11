from fastapi import APIRouter, Depends, status, HTTPException
from app.db.session import get_db
from app.schemas.goals import *
from app.crud.goals import *
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/checkin", tags=["goals"])


@router.get("/goal")
async def get_user_goal_route(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = user["id"]
        result = await get_user_goal_data(user_id, db)
        return {"message": result["message"], "data": result["data"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/goal")
async def create_or_update_goal_route(
    request: GoalInout,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = user["id"]
        result = await create_or_update_goal_data(request, user_id, db)
        return {"message": result["message"], "data": result["data"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
