from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from db.session import get_db
from db.tables import Tables
from schemas.users import UserCreate, UserLogin, Token
from core.security import hash_password, verify_password, create_access_token
from core.config import settings
from datetime import timedelta
from api.routes.google import get_current_user_from_token
tables = Tables()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    result = await db.execute(
        select(tables.users).where(tables.users.c.email == user_data.email)
    )
    existing_user = result.first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_pw = hash_password(user_data.password)
    stmt = (
        insert(tables.users)
        .values(
            email=user_data.email,
            full_name=user_data.full_name,
            password=hashed_pw,
        )
        .returning(tables.users.c.id)
    )

    try:
        result = await db.execute(stmt)
        await db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Failed to register user")

    new_user_id = result.scalar_one()
    return {"message": "User registered successfully", "user_id": new_user_id}


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(tables.users).where(tables.users.c.email == user_in.email)
    result = await db.execute(stmt)
    user_row = result.fetchone()

    if not user_row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_data = user_row._mapping  # Access as dict
    if not verify_password(user_in.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": str(user_data["id"])},  # use user_data id here
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}

from core.dependencies import get_current_user

@router.get("/me")
async def get_current_user_info(user=Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.full_name,
    }