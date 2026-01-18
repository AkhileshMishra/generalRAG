import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))


class JWTMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        token = self._extract_token(request)
        if token:
            user = self._decode_token(token)
            if user:
                request.state.user = user
            else:
                request.state.user = None
        else:
            request.state.user = None

        return await call_next(request)

    def _extract_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return request.cookies.get("access_token")

    def _decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "is_admin": payload.get("is_admin", False),
                "tenant_id": payload.get("tenant_id", "default"),
            }
        except JWTError:
            return None


def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_current_user_optional(request: Request) -> Optional[dict]:
    """Dependency to get current user if authenticated."""
    return getattr(request.state, "user", None)


def require_admin(request: Request) -> dict:
    """Dependency to require admin access."""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def create_access_token(
    user_id: str, 
    email: str, 
    is_admin: bool = False,
    tenant_id: str = "default",
    expires_minutes: int = None
) -> str:
    """Create JWT access token with expiration."""
    expires_minutes = expires_minutes or JWT_EXPIRY_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, expires_days: int = 7) -> str:
    """Create longer-lived refresh token."""
    expire = datetime.utcnow() + timedelta(days=expires_days)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
