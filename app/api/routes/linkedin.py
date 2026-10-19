from datetime import timedelta
import secrets
from urllib.parse import urlencode

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.oauth import get_oauth_provider
from core.security import create_access_token
from db.session import get_db
from services.oauth_users import resolve_oauth_user

router = APIRouter(prefix="/auth/linkedin", tags=["Auth"])


def _frontend_callback(token: str) -> RedirectResponse:
    query = urlencode({"access_token": token, "provider": "linkedin"})
    return RedirectResponse(
        url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/auth/callback?{query}",
        status_code=303,
        headers={"Referrer-Policy": "no-referrer", "Cache-Control": "no-store"},
    )


@router.get("/login")
async def linkedin_login(request: Request):
    provider = get_oauth_provider("linkedin")
    return await provider.authorize_redirect(
        request,
        str(request.url_for("linkedin_callback")),
        nonce=secrets.token_urlsafe(32),
    )


@router.get("/callback", name="linkedin_callback")
async def linkedin_callback(request: Request, db: AsyncSession = Depends(get_db)):
    provider = get_oauth_provider("linkedin")
    try:
        token = await provider.authorize_access_token(request)
        info = token.get("userinfo")
        if not info:
            info = await provider.userinfo(token=token)
    except OAuthError:
        raise HTTPException(status_code=400, detail="LinkedIn sign-in could not be verified") from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="LinkedIn sign-in failed") from None

    email = info.get("email")
    provider_id = info.get("sub")
    if not email or not provider_id or info.get("email_verified") is not True:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn must provide a verified email address",
        )

    full_name = info.get("name")
    if not full_name:
        full_name = " ".join(
            part for part in (info.get("given_name"), info.get("family_name")) if part
        )

    user = await resolve_oauth_user(
        db,
        provider="linkedin",
        provider_id=str(provider_id),
        email=str(email),
        full_name=full_name,
    )
    jwt_token = create_access_token(
        {"sub": str(user["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return _frontend_callback(jwt_token)
