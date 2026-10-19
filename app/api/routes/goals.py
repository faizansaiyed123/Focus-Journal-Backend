from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from crud.goals import create_or_update_goal_data, get_user_goal_data
from db.session import get_db
from schemas.goals import GoalInout
from utils.dates import user_local_today

router = APIRouter(prefix="/checkin", tags=["Goals"])


@router.get("/goal")
async def get_user_goal_route(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_goal_data(
        user["id"],
        db,
        today=user_local_today(user),
    )


@router.post("/goal")
async def create_or_update_goal_route(
    request: GoalInout,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_or_update_goal_data(
        request,
        user["id"],
        db,
        today=user_local_today(user),
    )
