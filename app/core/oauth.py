from authlib.integrations.starlette_client import OAuth

from core.config import settings

oauth = OAuth()

if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )

if settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET:
    oauth.register(
        name="linkedin",
        client_id=settings.LINKEDIN_CLIENT_ID,
        client_secret=settings.LINKEDIN_CLIENT_SECRET,
        server_metadata_url=(
            "https://www.linkedin.com/oauth/.well-known/openid-configuration"
        ),
        token_endpoint_auth_method="client_secret_post",
        client_kwargs={"scope": settings.LINKEDIN_SCOPE},
    )


def get_oauth_provider(name: str):
    try:
        return getattr(oauth, name)
    except (AttributeError, KeyError):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail=f"{name.title()} sign-in is not configured",
        ) from None
