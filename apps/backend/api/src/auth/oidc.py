import os
from typing import Optional
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

async def verify_google_token(token: str) -> Optional[dict]:
    """Verify Google OIDC token and return user info."""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        return {
            "user_id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
        }
    except ValueError:
        return None

async def get_google_userinfo(access_token: str) -> Optional[dict]:
    """Get user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "user_id": data["sub"],
                "email": data["email"],
                "name": data.get("name"),
                "picture": data.get("picture"),
            }
    return None
