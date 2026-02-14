"""Authentication routes — login, logout, current user."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.supabase_client import get_supabase, get_supabase_admin
from app.core.auth import get_current_user

log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    team: str | None = None
    is_active: bool = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """Sign in with email + password via Supabase Auth."""
    try:
        sb = get_supabase()
        auth_response = sb.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Fetch user record from our users table for role info
        db = get_supabase_admin()
        user_record = (
            db.table("users")
            .select("*")
            .eq("id", str(auth_response.user.id))
            .single()
            .execute()
        )

        if not user_record.data:
            raise HTTPException(
                status_code=403,
                detail="Account exists but is not registered in the system. Contact your admin.",
            )

        if not user_record.data.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated. Contact your admin.")

        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user=user_record.data,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Sign out the current user session."""
    try:
        sb = get_supabase()
        sb.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        log.error(f"Logout error: {e}")
        # Even if sign_out fails server-side, the client should discard the token
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse(
        id=user["id"],
        email=user.get("email", ""),
        full_name=user.get("full_name"),
        role=user["role"],
        team=user.get("team"),
        is_active=user.get("is_active", True),
    )
