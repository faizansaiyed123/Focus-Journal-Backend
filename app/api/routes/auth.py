from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies import get_current_user
from core.security import create_access_token, hash_password, verify_password
from db.session import get_db
from db.tables import Tables
from schemas.users import Token, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])
tables = Tables()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    email = str(user_data.email).strip().lower()
    existing = await db.execute(
        select(tables.users.c.id).where(tables.users.c.email.ilike(email))
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        result = await db.execute(
            insert(tables.users)
            .values(
                email=email,
                full_name=user_data.full_name,
                password=hash_password(user_data.password),
                is_active=True,
            )
            .returning(tables.users.c.id)
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None

    return {
        "message": "User registered successfully",
        "user_id": str(result.scalar_one()),
    }


@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(tables.users).where(tables.users.c.email.ilike(str(user_in.email)))
    )
    row = result.mappings().first()
    if row is None or not row.get("is_active", False):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(user_in.password, row.get("password")):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {"sub": str(row["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    # The token field is a short-lived compatibility alias for the existing frontend.
    return {"access_token": token, "token": token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "name": user.get("full_name"),
        "full_name": user.get("full_name"),
        "timezone": user.get("timezone") or "UTC",
        "ai_processing_consent": bool(user.get("ai_processing_consent", False)),
    }
