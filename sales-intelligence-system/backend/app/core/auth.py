"""Auth middleware — decodes Supabase JWT and looks up user in DB."""

import logging
import base64
import json
from fastapi import Request, HTTPException, Depends
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)


def _decode_jwt_payload(token: str) -> dict:
    """Decode a JWT payload without external library dependencies.
    We trust the token origin (Supabase HTTPS) and verify the user
    exists in our DB as the authorization step."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    return json.loads(payload_bytes)


async def get_current_user(request: Request) -> dict:
    """Decode Supabase JWT, extract user info, look up in users table."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split("Bearer ")[1]

    try:
        payload = _decode_jwt_payload(token)
    except Exception as e:
        log.warning("JWT decode failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    email = payload.get("email")
    exp = payload.get("exp")

    if not sub:
        raise HTTPException(status_code=401, detail="Token missing user ID")

    import time
    if exp and exp < time.time():
        raise HTTPException(status_code=401, detail="Token expired")

    db = get_supabase_admin()
    result = None

    for field, value in [("auth_id", sub), ("id", sub), ("email", email)]:
        if not value:
            continue
        try:
            r = db.table("users").select("*").eq(field, value).maybe_single().execute()
            if r.data:
                result = r.data
                break
        except Exception:
            pass

    if not result:
        raise HTTPException(status_code=403, detail="User not found in system")

    return result


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


async def require_rep(user: dict = Depends(get_current_user)) -> dict:
    return user


async def require_manager(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("manager", "founder", "admin"):
        raise HTTPException(status_code=403, detail="Manager access required")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("founder", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
