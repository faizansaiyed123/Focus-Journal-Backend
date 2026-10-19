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

router = APIRouter(prefix="/auth/google", tags=["Auth"])


def _frontend_callback(token: str) -> RedirectResponse:
    # Retained temporarily to match the deployed frontend callback contract.
    query = urlencode({"access_token": token, "provider": "google"})
    return RedirectResponse(
        url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/auth/callback?{query}",
        status_code=303,
        headers={"Referrer-Policy": "no-referrer", "Cache-Control": "no-store"},
    )


@router.get("/login")
async def google_login(request: Request):
    provider = get_oauth_provider("google")
    return await provider.authorize_redirect(
        request,
        str(request.url_for("google_callback")),
        nonce=secrets.token_urlsafe(32),
    )


@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    provider = get_oauth_provider("google")
    try:
        token = await provider.authorize_access_token(request)
        info = token.get("userinfo")
        if not info:
            info = await provider.userinfo(token=token)
    except OAuthError:
        raise HTTPException(status_code=400, detail="Google sign-in could not be verified") from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Google sign-in failed") from None

    email = info.get("email")
    provider_id = info.get("sub")
    if not email or not provider_id or info.get("email_verified") is not True:
        raise HTTPException(
            status_code=400,
            detail="Google must provide a verified email address",
        )

    user = await resolve_oauth_user(
        db,
        provider="google",
        provider_id=str(provider_id),
        email=str(email),
        full_name=info.get("name"),
    )
    jwt_token = create_access_token(
        {"sub": str(user["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return _frontend_callback(jwt_token)
