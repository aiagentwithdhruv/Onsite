"""LLM provider API keys: read from app_config (set via Admin UI) first, then env. Only admins can set in UI."""

import logging
from app.core.config import get_settings

log = logging.getLogger(__name__)

_PROVIDERS = ("anthropic", "openai", "openrouter", "moonshot")
_ENV_KEYS = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "openrouter": "openrouter_api_key",
    "moonshot": "moonshot_api_key",
}


def get_llm_api_key(provider: str) -> str:
    """Return API key for provider: from app_config first, then from env. Never log the key."""
    if provider not in _ENV_KEYS:
        return ""
    settings = get_settings()
    env_key = _ENV_KEYS[provider]
    env_val = (getattr(settings, env_key, None) or "").strip()
    try:
        from app.core.supabase_client import get_supabase_admin
        db = get_supabase_admin()
        row = db.table("app_config").select("value").eq("key", env_key).maybe_single().execute()
        if row.data and row.data.get("value"):
            return (row.data["value"] or "").strip()
    except Exception as e:
        log.debug("Read LLM key from app_config %s: %s", provider, e)
    return env_val or ""


def get_llm_config_status() -> dict[str, bool]:
    """Return which providers have a key configured (for admin UI). No keys returned."""
    return {p: bool(get_llm_api_key(p)) for p in _PROVIDERS}


# Model selection (primary / fast / fallback) — stored in app_config
_APP_CONFIG_MODEL_KEYS = ("llm_model_primary", "llm_model_fast", "llm_model_fallback")


def _get_app_config_value(key: str) -> str | None:
    try:
        from app.core.supabase_client import get_supabase_admin
        db = get_supabase_admin()
        row = db.table("app_config").select("value").eq("key", key).maybe_single().execute()
        if row.data and row.data.get("value"):
            return (row.data["value"] or "").strip() or None
    except Exception as e:
        log.debug("Read app_config %s: %s", key, e)
    return None


def get_llm_model_id(which: str) -> str:
    """Return model id for primary, fast, or fallback. From app_config or default."""
    if which not in ("primary", "fast", "fallback"):
        which = "primary"
    key = f"llm_model_{which}"
    val = _get_app_config_value(key)
    from app.core.llm_models import MODEL_IDS, DEFAULT_PRIMARY, DEFAULT_FAST, DEFAULT_FALLBACK
    defaults = {"primary": DEFAULT_PRIMARY, "fast": DEFAULT_FAST, "fallback": DEFAULT_FALLBACK}
    if val and val in MODEL_IDS:
        return val
    return defaults.get(which, DEFAULT_PRIMARY)
