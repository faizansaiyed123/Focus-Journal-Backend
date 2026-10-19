import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables

tables = Tables()
CODE_LIFETIME = timedelta(minutes=2)


async def issue_oauth_login_code(db: AsyncSession, user_id: UUID) -> str:
    """Create a short-lived exchange code while storing only its SHA-256 digest."""
    now = datetime.now(timezone.utc)
    raw_code = secrets.token_urlsafe(32)
    code_hash = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
    codes = tables.oauth_login_codes

    # Opportunistically prune old records so this small table stays bounded.
    await db.execute(delete(codes).where(codes.c.expires_at < now - timedelta(days=1)))
    await db.execute(
        codes.insert().values(
            code_hash=code_hash,
            user_id=user_id,
            created_at=now,
            expires_at=now + CODE_LIFETIME,
        )
    )
    await db.commit()
    return raw_code


async def consume_oauth_login_code(db: AsyncSession, raw_code: str) -> UUID:
    """Atomically consume a code once, refusing replayed, expired, or unknown codes."""
    code_hash = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    codes = tables.oauth_login_codes

    result = await db.execute(
        update(codes)
        .where(
            codes.c.code_hash == code_hash,
            codes.c.consumed_at.is_(None),
            codes.c.expires_at > now,
        )
        .values(consumed_at=now)
        .returning(codes.c.user_id)
    )
    row = result.first()
    if row is None:
        await db.rollback()
        raise HTTPException(
            status_code=401,
            detail="OAuth sign-in code is invalid, expired, or already used",
        )

    user_id = row[0]
    user_result = await db.execute(
        select(tables.users.c.is_active).where(tables.users.c.id == user_id)
    )
    user = user_result.first()
    # Burn the code even if the account was disabled after it was issued.
    await db.commit()

    if user is None or not user[0]:
        raise HTTPException(status_code=403, detail="This account is inactive")
    return user_id
