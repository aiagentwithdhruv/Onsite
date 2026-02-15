from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Zoho
    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_api_domain: str = "https://www.zohoapis.in"

    # WhatsApp
    gupshup_api_key: str = ""
    gupshup_app_name: str = ""
    gupshup_source_number: str = ""

    # Email
    resend_api_key: str = ""
    from_email: str = "alerts@onsite.team"

    # App
    app_env: str = "development"
    secret_key: str = "change-this"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "sales-intelligence"

    # Direct DB connection (optional, for future use)
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
