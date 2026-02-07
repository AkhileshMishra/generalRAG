import os
import uuid
import hashlib
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from src.auth.jwt_middleware import create_access_token
from src.db import get_db, User

router = APIRouter()

# Simple password hashing (use bcrypt in production)
def hash_password(password: str) -> str:
    salt = os.getenv("JWT_SECRET", "dev")[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: dict

# Demo users (in production, store in DB with hashed passwords)
DEMO_USERS = {
    "admin@generalrag.dev": {"password": "admin123", "is_admin": True, "name": "Admin"},
    "user@generalrag.dev": {"password": "user123", "is_admin": False, "name": "Demo User"},
}

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    # Check demo users first
    if req.email in DEMO_USERS:
        user_data = DEMO_USERS[req.email]
        if req.password == user_data["password"]:
            user_id = f"demo-{req.email.split('@')[0]}"
            token = create_access_token(
                user_id=user_id,
                email=req.email,
                is_admin=user_data["is_admin"],
                tenant_id="default"
            )
            response.set_cookie(
                key="auth-token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400 * 7
            )
            return AuthResponse(
                token=token,
                user={"id": user_id, "email": req.email, "name": user_data["name"], "is_admin": user_data["is_admin"]}
            )
    
    raise HTTPException(status_code=401, detail="Invalid email or password")

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("auth-token")
    return {"status": "logged out"}

@router.get("/me")
async def get_me(request):
    from src.auth.jwt_middleware import get_current_user_optional
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
