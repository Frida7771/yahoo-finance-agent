"""
Google OAuth Authentication Routes
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import User

router = APIRouter()
security = HTTPBearer(auto_error=False)


# Pydantic schemas
class GoogleAuthRequest(BaseModel):
    """Google OAuth token from frontend"""
    credential: str  # Google ID token


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User info response"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None


# Helper functions
def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def verify_google_token(credential: str) -> dict:
    """Verify Google ID token and return user info"""
    import logging
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    
    # Verify token with Google
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        )
        
        if response.status_code != 200:
            logger.error(f"Google token verification failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {response.text}"
            )
        
        token_info = response.json()
        logger.info(f"Google token info - email: {token_info.get('email')}, aud: {token_info.get('aud')}")
        
        # Verify audience (client_id) - skip if not configured
        token_aud = token_info.get("aud")
        if settings.google_client_id:
            if token_aud != settings.google_client_id:
                logger.error(f"Audience mismatch! Token aud: {token_aud}, Expected: {settings.google_client_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token audience. Expected: {settings.google_client_id[:20]}..."
                )
        else:
            logger.warning("GOOGLE_CLIENT_ID not configured, skipping audience verification")
        
        return {
            "google_id": token_info.get("sub"),
            "email": token_info.get("email"),
            "name": token_info.get("name"),
            "picture": token_info.get("picture")
        }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token (optional - returns None if not authenticated)"""
    if not credentials:
        return None
    
    settings = get_settings()
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    return user


async def require_user(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authenticated user (raises 401 if not authenticated)"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


# Routes
@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth.
    
    Frontend should use Google Sign-In and send the credential (ID token) here.
    """
    # Verify Google token
    google_user = await verify_google_token(request.credential)
    
    # Find or create user
    result = await db.execute(
        select(User).where(User.google_id == google_user["google_id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=google_user["email"],
            name=google_user["name"],
            picture=google_user["picture"],
            google_id=google_user["google_id"]
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user info
        user.name = google_user["name"]
        user.picture = google_user["picture"]
        await db.commit()
    
    # Create JWT token
    access_token = create_access_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_user)):
    """Get current user info"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture
    )


@router.post("/logout")
async def logout():
    """
    Logout (client should discard the token).
    This endpoint is mainly for frontend consistency.
    """
    return {"message": "Logged out successfully"}

