from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.journal import *
from app.crud.journal import *
from app.core.dependencies import get_current_user
from app.db.tables import Tables
from typing import List
from uuid import UUID

tables = Tables()


router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "/", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_entry(
    entry: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await create_journal_entry(entry=entry, user_id=current_user.id, db=db)


@router.get("/", response_model=List[JournalEntryResponse])
async def list_entries(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    return await get_journal_entries_by_user(user_id=current_user.id, db=db)


@router.get("/stats", summary="Get journal statistics")
async def journal_stats(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        stats = await get_user_journal_stats(user_id=current_user.id, db=db)

        if not stats:
            raise HTTPException(status_code=404, detail="No journal stats found")

        return {"success": True, "message": "Journal stats retrieved", "data": stats}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve journal stats: {str(e)}"
        )


@router.get("/{entry_id}")
async def get_journal_entry_by_id(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_journal_entry_by_id_service(
        entry_id=entry_id, user_id=current_user.id, db=db
    )


@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_entry(
    entry_id: UUID,
    entry: UpdateJournalEntry,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await update_journal_entry_service(
        entry_id=entry_id, user_id=current_user.id, data=entry, db=db
    )


@router.delete("/{entry_id}", status_code=200)
async def delete_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await delete_journal_entry_service(
        entry_id=entry_id, user_id=current_user.id, db=db
    )
    return {"message": "Entry deleted successfully"}


@router.get("/journal/sentiment-analysis")
async def get_sentiment_analysis_route(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = user["id"]
        result = await get_sentiment_analysis_data(user_id, db)
        return {"message": result["message"], "data": result["data"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/journal/summary/weekly")
async def get_weekly_summary_route(
    user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        user_id = user["id"]  # ✅ Extract the UUID only
        result = await get_weekly_summary_data(user_id, db)
        return {"message": result["message"], "data": result["data"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
