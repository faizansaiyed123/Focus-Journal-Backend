
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse ,RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.oauth import oauth
from app.db.session import get_db
from app.core.security import create_access_token
from app.core.dependencies import get_current_user
from app.db.tables import Tables
import uuid
from datetime import timedelta
router = APIRouter(prefix="/auth/github", tags=["Auth"])
tables = Tables()


@router.get("/login")
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def github_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    profile = resp.json()

    github_id = str(profile["id"])
    email = profile.get("email") or f"{github_id}@github.fake"
    full_name = profile.get("name")

    stmt = select(tables.users).where(tables.users.c.github_id == github_id)
    result = await db.execute(stmt)
    user_row = result.first()

    if not user_row:
        user_id = str(uuid.uuid4())
        insert_stmt = insert(tables.users).values(
            id=user_id,
            email=email,
            github_id=github_id,
            full_name=full_name,
            is_active=True,
        )
        await db.execute(insert_stmt)
        await db.commit()
    else:
        user_id = str(user_row.id)
    access_token = create_access_token({"sub": user_id}, expires_delta=timedelta(minutes=60))
    redirect_url = f"http://localhost:5173/auth/callback?access_token={access_token}"
    return RedirectResponse(url=redirect_url)



@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "github_id": current_user.github_id,
    }
