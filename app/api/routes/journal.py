from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from schemas.journal import JournalEntryCreate, JournalEntryResponse, UpdateJournalEntry
from crud.journal import (
    create_journal_entry,
    delete_journal_entry_service,
    get_journal_entries_by_user,
    get_journal_entry_by_id_service as fetch_journal_entry_by_id,
    get_sentiment_analysis_data,
    get_user_journal_stats,
    get_weekly_summary_data,
    update_journal_entry_service,
)

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await create_journal_entry(entry, current_user["id"], db)


@router.get("/", response_model=List[JournalEntryResponse])
async def list_entries(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await get_journal_entries_by_user(current_user["id"], db)


@router.get("/stats", summary="Get journal statistics")
async def journal_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    stats = await get_user_journal_stats(current_user["id"], db)
    return {"success": True, "message": "Journal stats retrieved", "data": stats}


@router.get("/sentiment-analysis")
async def sentiment_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await get_sentiment_analysis_data(current_user["id"], db)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Sentiment analysis is not available in this deployment",
        ) from None


@router.get("/summary/weekly")
async def weekly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await get_weekly_summary_data(
        current_user["id"],
        db,
        current_user.get("timezone") or "UTC",
    )
    return {"message": result["message"], "data": result["data"], **result["data"]}


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry_by_id(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await fetch_journal_entry_by_id(entry_id, current_user["id"], db)


@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_entry(
    entry_id: UUID,
    entry: UpdateJournalEntry,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await update_journal_entry_service(
        entry_id,
        current_user["id"],
        entry,
        db,
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await delete_journal_entry_service(entry_id, current_user["id"], db)
    return None
