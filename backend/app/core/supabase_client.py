from supabase import create_client, Client
from app.core.config import get_settings

_client: Client | None = None
_admin_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key (bypasses RLS).
    Use ONLY for server-side operations like sync, scoring, etc."""
    global _admin_client
    if _admin_client is None:
        settings = get_settings()
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client
