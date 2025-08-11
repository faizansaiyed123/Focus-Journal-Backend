from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from app.core.oauth import oauth
from app.db.session import get_db
from app.core.security import create_access_token
import uuid
from app.db.tables import Tables
from datetime import timedelta
import httpx
import urllib.parse
from fastapi.responses import RedirectResponse


tables = Tables()
router = APIRouter(prefix="/auth/google", tags=["Auth"])
from app.core.config import settings
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

import random
import string
from fastapi import Request



@router.get("/login")
async def google_login(request: Request):
    """Initiate Google OAuth login - completely manual"""
    
    # Build the Google OAuth URL manually
    redirect_uri = str(request.url_for("google_callback"))
    
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        # Don't include state parameter at all
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"
    
    logging.debug(f"Redirecting to: {auth_url}")
    return RedirectResponse(auth_url)

@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        logging.debug("=== Google Callback Started (Manual Flow) ===")
        
        # Get authorization code
        code = request.query_params.get("code")
        error = request.query_params.get("error")
        
        if error:
            logging.error(f"OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
            
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")

        logging.debug(f"Received authorization code: {code[:10]}...")

        # Exchange code for token
        redirect_uri = str(request.url_for("google_callback"))
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
        }
        
        logging.debug("Exchanging code for token")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if token_response.status_code != 200:
                logging.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
                
            token = token_response.json()
        
        logging.debug("Token exchange successful")
        
        # Get user info
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token["access_token"]}'}
            )
            
            if user_info_response.status_code != 200:
                logging.error(f"User info fetch failed: {user_info_response.text}")
                raise HTTPException(status_code=400, detail="Failed to fetch user info")
                
            user_data = user_info_response.json()

        logging.debug(f"Fetched user data: {user_data}")

        email = user_data.get("email")
        name = user_data.get("name", "Google User")

        if not email:
            logging.error("Email not provided by Google")
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        logging.debug(f"Processing user with email: {email}")

        # Check if user exists
        select_stmt = select(
            tables.users.c.id,
            tables.users.c.email,
            tables.users.c.full_name
        ).where(tables.users.c.email == email)
        
        result = await db.execute(select_stmt)
        existing_user = result.fetchone()
        
        logging.debug(f"Existing user found: {existing_user is not None}")

        if existing_user:
            # User exists
            user_id = str(existing_user.id)
            user_email = existing_user.email
            user_name = existing_user.full_name
            logging.debug(f"Existing user ID: {user_id}")
        else:
            # Create new user
            logging.debug("Creating new user")
            user_id = str(uuid.uuid4())
            
            try:
                insert_stmt = insert(tables.users).values(
                    id=user_id,
                    email=email,
                    full_name=name,
                    google_id=user_data.get("id"),  # Google returns 'id' not 'sub' for v2 API
                    is_active=True,
                )
                await db.execute(insert_stmt)
                await db.commit()
                logging.debug(f"New user created with ID: {user_id}")
                
                user_email = email
                user_name = name
                
            except Exception as db_error:
                logging.error(f"Database error creating user: {str(db_error)}")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to create user")

        # Create JWT token
        logging.debug("Creating JWT token")
        try:
            jwt_token = create_access_token({"sub": str(user_id)}, expires_delta=timedelta(minutes=60))
            logging.debug("JWT token created successfully")
        except Exception as jwt_error:
            logging.error(f"JWT creation error: {str(jwt_error)}")
            raise HTTPException(status_code=500, detail="Failed to create access token")


        redirect_url = f"http://localhost:5173/auth/callback?access_token={jwt_token}&provider=google"


        logging.debug("=== Google Callback Completed Successfully ===")
        
        return RedirectResponse(url=redirect_url)
        # return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in google callback: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Add this temporary route to your google.py for debugging
@router.get("/debug")
async def debug_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Temporary debug endpoint to test basic functionality"""
    try:
        # Test session
        request.session["test"] = "working"
        session_test = request.session.get("test")
        
        # Test database
        db_test = await db.execute(select(tables.users).limit(1))
        db_result = db_test.fetchone()
        
        # Test OAuth config
        oauth_configured = hasattr(oauth, 'google')
        
        return JSONResponse({
            "status": "debug_ok",
            "session_working": session_test == "working",
            "database_connected": True,
            "oauth_configured": oauth_configured,
            "tables_available": hasattr(tables, 'users')
        })
    except Exception as e:
        logging.error(f"Debug endpoint error: {str(e)}")
        return JSONResponse({
            "status": "debug_error",
            "error": str(e),
            "error_type": type(e).__name__
        }, status_code=500)




from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt    
from app.core.dependencies import get_current_user
from uuid import UUID

security = HTTPBearer()

async def get_current_user_from_token(
    token: HTTPAuthorizationCredentials = Depends(security),  # ✅ Correct
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
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
