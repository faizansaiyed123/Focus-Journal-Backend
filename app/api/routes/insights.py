from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from crud.insights import (
    generate_journal_insights,
    get_journal_calendar_data,
    get_top_journal_tags,
    search_journal_entries_by_keyword,
)

router = APIRouter(prefix="/checkin", tags=["Journal insights"])


@router.get("/journal/insights")
async def get_journal_insights_route(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.get("ai_processing_consent", False):
        raise HTTPException(
            status_code=403,
            detail=(
                "AI journal analysis is disabled until you explicitly enable it "
                "in your privacy settings"
            ),
        )
    try:
        result = await generate_journal_insights(current_user["id"], db)
        return {"message": "Insights generated successfully", "data": result}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Journal insights could not be generated",
        ) from None


@router.get("/journal/tags")
async def get_journal_tags(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tags = await get_top_journal_tags(current_user["id"], db)
    return {"message": "Tags fetched successfully", "data": {"top_tags": tags}}


@router.get("/journal/search")
async def search_journal_entries_route(
    keyword: str = Query(..., min_length=1, max_length=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await search_journal_entries_by_keyword(
        current_user["id"],
        keyword.strip(),
        db,
    )
    return {
        "message": "Journal entries matching the keyword fetched successfully",
        "data": results,
    }


@router.get("/journal/calendar")
async def get_journal_calendar_route(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_journal_calendar_data(user["id"], db)
    return {"message": "Journal calendar data fetched successfully", "data": data}
