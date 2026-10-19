from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from db.session import get_db
from db.tables import Tables
from schemas.profile import ProfileResponse, ProfileSettingsUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])
tables = Tables()


def _public_profile(user: dict) -> dict:
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "full_name": user.get("full_name"),
        "timezone": user.get("timezone") or "UTC",
        "ai_processing_consent": bool(user.get("ai_processing_consent", False)),
    }


@router.get("", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    return _public_profile(user)


@router.patch("/settings", response_model=ProfileResponse)
async def update_profile_settings(
    payload: ProfileSettingsUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return _public_profile(user)
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=422, detail="Settings values cannot be null")

    values["updated_at"] = datetime.now(timezone.utc)
    result = await db.execute(
        update(tables.users)
        .where(tables.users.c.id == user["id"])
        .values(**values)
        .returning(tables.users)
    )
    row = result.mappings().one()
    await db.commit()
    return _public_profile(dict(row))
