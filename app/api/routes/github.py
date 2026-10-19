from datetime import timedelta
from urllib.parse import urlencode

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies import get_current_user
from core.oauth import get_oauth_provider
from core.security import create_access_token
from db.session import get_db
from services.oauth_users import resolve_oauth_user

router = APIRouter(prefix="/auth/github", tags=["Auth"])


def _frontend_callback(token: str) -> RedirectResponse:
    query = urlencode({"access_token": token, "provider": "github"})
    return RedirectResponse(
        url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/auth/callback?{query}",
        status_code=303,
        headers={"Referrer-Policy": "no-referrer", "Cache-Control": "no-store"},
    )


@router.get("/login")
async def github_login(request: Request):
    provider = get_oauth_provider("github")
    return await provider.authorize_redirect(
        request,
        str(request.url_for("github_callback")),
    )


@router.get("/callback", name="github_callback")
async def github_callback(request: Request, db: AsyncSession = Depends(get_db)):
    provider = get_oauth_provider("github")
    try:
        token = await provider.authorize_access_token(request)
        profile_response = await provider.get("user", token=token)
        if profile_response.is_error:
            raise HTTPException(status_code=400, detail="GitHub profile could not be verified")
        profile = profile_response.json()

        emails_response = await provider.get("user/emails", token=token)
        if emails_response.is_error:
            raise HTTPException(status_code=400, detail="GitHub email could not be verified")
        verified_emails = [
            item
            for item in emails_response.json()
            if item.get("verified") is True and item.get("email")
        ]
        primary = next((item for item in verified_emails if item.get("primary")), None)
        email_record = primary or (verified_emails[0] if verified_emails else None)
    except OAuthError:
        raise HTTPException(status_code=400, detail="GitHub sign-in could not be verified") from None

    if not email_record:
        raise HTTPException(
            status_code=400,
            detail="GitHub must provide a verified email address",
        )
    provider_id = profile.get("id")
    if provider_id is None:
        raise HTTPException(status_code=400, detail="GitHub did not return a valid identity")

    user = await resolve_oauth_user(
        db,
        provider="github",
        provider_id=str(provider_id),
        email=str(email_record["email"]),
        full_name=profile.get("name") or profile.get("login"),
    )
    jwt_token = create_access_token(
        {"sub": str(user["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return _frontend_callback(jwt_token)


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "github_id": current_user.get("github_id"),
    }
