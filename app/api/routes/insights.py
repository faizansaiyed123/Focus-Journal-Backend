from fastapi import APIRouter, Depends, status, Query, Request, HTTPException
from app.db.session import get_db
from app.schemas.checkin import *
from app.crud.insights import *
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/checkin", tags=["journal-insights"])


@router.get("/journal/insights")
async def get_journal_insights_route(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = current_user["id"]
        result = await generate_journal_insights(user_id, db)
        return {"message": "Insights generated successfully.", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/journal/tags")
async def get_journal_tags(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = current_user["id"]
        tags = await get_top_journal_tags(user_id, db)
        return {"message": "Tags fetched successfully.", "data": {"top_tags": tags}}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/journal/search")
async def search_journal_entries_route(
    keyword: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = current_user["id"]
        results = await search_journal_entries_by_keyword(user_id, keyword, db)

        return {
            "message": "Journal entries matching the keyword fetched successfully.",
            "data": results,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/journal/calendar")
async def get_journal_calendar_route(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        calendar_data = await get_journal_calendar_data(user["id"], db)
        return {
            "message": "Journal calendar data fetched successfully.",
            "data": calendar_data,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
