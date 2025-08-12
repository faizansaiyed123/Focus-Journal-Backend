from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from core.oauth import oauth
from db.session import get_db
from core.security import create_access_token
from db.tables import Tables
from uuid import uuid4
import httpx

router = APIRouter(prefix="/auth/linkedin", tags=["Auth"])

tables = Tables()  # ✅ Load reflected table definitions

import secrets
from uuid import uuid4

@router.get("/login")
async def linkedin_login(request: Request):
    try:
        # Clear any existing LinkedIn OAuth states from session
        keys_to_remove = [key for key in request.session.keys() if key.startswith('_state_linkedin_')]
        for key in keys_to_remove:
            del request.session[key]
        
        redirect_uri = str(request.url_for("linkedin_callback"))
        
        # Generate nonce manually and store in session
        nonce = secrets.token_urlsafe(32)
        request.session["linkedin_nonce"] = nonce
        
        # Let Authlib handle the state parameter but pass our nonce
        return await oauth.linkedin.authorize_redirect(
            request, 
            redirect_uri,
            nonce=nonce
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate LinkedIn login: {e}")

@router.get("/callback", name="linkedin_callback")
async def linkedin_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        print(f"DEBUG: Query params: {dict(request.query_params)}")
        print(f"DEBUG: Session keys: {list(request.session.keys())}")
        
        # Get the nonce we stored earlier
        nonce = request.session.get("linkedin_nonce")
        print(f"DEBUG: Stored nonce: {nonce}")
        
        # Manual token exchange to avoid OpenID Connect nonce validation issues
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        # Exchange code for token manually
        from core.config import settings
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(request.url_for("linkedin_callback")),
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }
        
        async with httpx.AsyncClient() as client:
            # Get access token
            token_response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_response.text}")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            print(f"DEBUG: Token received: {bool(access_token)}")
            
            # Get user info directly from userinfo endpoint
            user_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"User info failed: {user_response.text}")
            
            userinfo = user_response.json()
            print(f"DEBUG: User info: {userinfo}")

        email = userinfo.get("email")
        name = userinfo.get("name") or f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip()
        linkedin_id = userinfo.get("sub")

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by LinkedIn")

        # Check if user exists
        result = await db.execute(
            select(tables.users).where(tables.users.c.email == email)
        )
        user_row = result.fetchone()

        if not user_row:
            # Create new user
            stmt = (
                insert(tables.users)
                .values(
                    id=str(uuid4()),
                    email=email,
                    full_name=name,
                    linkedin_id=linkedin_id,
                    is_active=True,
                )
                .returning(tables.users)
            )
            result = await db.execute(stmt)
            await db.commit()
            user_row = result.fetchone()

        # Clean up session data
        request.session.pop("linkedin_nonce", None)
        keys_to_remove = [key for key in request.session.keys() if key.startswith('_state_linkedin_')]
        for key in keys_to_remove:
            del request.session[key]

        # Create JWT token
        from datetime import timedelta
        jwt_token = create_access_token({"sub": str(user_row.id)}, expires_delta=timedelta(minutes=60))



        return RedirectResponse(
    url=f"https://focus-journal-frontend.vercel.app/auth/callback?access_token={jwt_token}&provider=linkedin"
)


    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        # Clean up session data on error
        request.session.pop("linkedin_nonce", None)
        keys_to_remove = [key for key in request.session.keys() if key.startswith('_state_linkedin_')]
        for key in keys_to_remove:
            del request.session[key]
        raise HTTPException(status_code=500, detail=f"Authentication failed: {e}")

@router.get("/clear-session")
async def clear_session(request: Request):
    """Helper endpoint to clear LinkedIn OAuth session data for debugging"""
    keys_to_remove = [key for key in request.session.keys() if key.startswith('_state_linkedin_')]
    keys_to_remove.append("linkedin_nonce")
    removed_keys = []
    for key in keys_to_remove:
        if key in request.session:
            del request.session[key]
            removed_keys.append(key)
    return {"message": f"Cleared {len(removed_keys)} LinkedIn OAuth session entries", "keys": removed_keys}

@router.get("/test-session")
async def test_session(request: Request):
    return {"session": dict(request.session)}