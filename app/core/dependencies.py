from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.tables import Tables
from app.db.session import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.future import select
from uuid import UUID

security = HTTPBearer()
tables = Tables()



async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = UUID(user_id_str)

        result = await db.execute(
            select(tables.users).where(tables.users.c.id == user_id)
        )
        user = result.mappings().first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
