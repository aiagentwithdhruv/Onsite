"""Auth middleware — validates Supabase JWT and extracts user role."""

from fastapi import Request, HTTPException, Depends
from app.core.supabase_client import get_supabase_admin


async def get_current_user(request: Request) -> dict:
    """Extract and validate user from Supabase auth token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split("Bearer ")[1]

    try:
        db = get_supabase_admin()
        user_response = db.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        supabase_user_id = str(user_response.user.id)
        supabase_email = user_response.user.email

        # Try multiple lookup strategies (auth_id column may not exist yet)
        result = None

        # 1. Try auth_id
        try:
            r = db.table("users").select("*").eq("auth_id", supabase_user_id).maybe_single().execute()
            if r.data:
                result = r.data
        except Exception:
            pass  # auth_id column may not exist

        # 2. Try matching by id
        if not result:
            try:
                r = db.table("users").select("*").eq("id", supabase_user_id).maybe_single().execute()
                if r.data:
                    result = r.data
            except Exception:
                pass

        # 3. Try matching by email (most reliable fallback)
        if not result and supabase_email:
            try:
                r = db.table("users").select("*").eq("email", supabase_email).maybe_single().execute()
                if r.data:
                    result = r.data
            except Exception:
                pass

        if not result:
            raise HTTPException(status_code=403, detail="User not found in system")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def require_role(*allowed_roles: str):
    """Dependency factory: require user to have one of the specified roles."""
    async def check_role(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user['role']}' not authorized. Required: {allowed_roles}"
            )
        return user
    return check_role


# Convenience dependencies
async def require_rep(user: dict = Depends(get_current_user)) -> dict:
    return user  # Any authenticated user can access rep-level endpoints


async def require_manager(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("manager", "founder", "admin"):
        raise HTTPException(status_code=403, detail="Manager access required")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("founder", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
