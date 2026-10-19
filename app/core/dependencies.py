from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.session import get_db
from db.tables import Tables

security = HTTPBearer(auto_error=False)
tables = Tables()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(status_code=401, detail="Invalid access token")
        user_id = UUID(str(subject))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    result = await db.execute(select(tables.users).where(tables.users.c.id == user_id))
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = dict(row)
    if not user.get("is_active", False):
        raise HTTPException(status_code=403, detail="This account is inactive")
    return user
