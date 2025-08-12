from fastapi import APIRouter, Depends
from crud.analytics import *
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from core.dependencies import get_current_user

router = APIRouter()


@router.get("/weekly-summary", summary="Weekly mood and focus summary")
async def weekly_summary(
    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)
):
    summary_data = await get_user_weekly_summary(user["id"], db)

    return {
        "success": True,
        "message": "Weekly summary retrieved",
        "data": summary_data,
    }


@router.get("/monthly-summary", summary="Monthly mood and focus summary")
async def monthly_summary(
    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)
):
    data = await get_user_monthly_summary(user["id"], db)

    return {"success": True, "message": "Monthly summary retrieved", "data": data}


@router.get("/tag-summary", summary="Get most frequently used tags")
async def tag_summary(
    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)
):
    data = await get_user_tag_summary(user["id"], db)

    return {"success": True, "message": "Tag usage summary retrieved", "data": data}
