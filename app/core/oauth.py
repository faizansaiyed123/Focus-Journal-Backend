from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from core.config import settings
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth


config = Config(".env")
oauth = OAuth(config)
oauth = OAuth()
oauth = OAuth(config)


oauth.register(
    name="github",
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)



oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        # Disable state parameter entirely
        "response_type": "code",
    },
    # This is the key - disable state validation
    authorize_params={"access_type": "offline"},
)






# LinkedIn OAuth - Fixed Configuration
oauth.register(
    name="linkedin",
    client_id=settings.LINKEDIN_CLIENT_ID,
    client_secret=settings.LINKEDIN_CLIENT_SECRET,
    server_metadata_url="https://www.linkedin.com/oauth/.well-known/openid-configuration",
    token_endpoint_auth_method="client_secret_post",  # Send credentials in POST body
    client_kwargs={
        "scope": "openid profile email",
        "response_type": "code",
    },
)

