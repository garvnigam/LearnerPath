from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role: str = ""

    cors_origins: str = "http://localhost:5173"

    # Microsoft Entra External ID (customer tenant) — used to validate access tokens
    entra_tenant_subdomain: str = ""  # e.g. "contoso" for contoso.ciamlogin.com
    entra_tenant_id: str = ""         # tenant GUID (found in Entra portal overview)
    entra_api_client_id: str = ""     # client ID of the backend API app registration (audience)
    entra_required_scope: str = ""    # optional scp value to require, e.g. "LearnPath.Access"
    entra_auth_disabled: bool = False  # dev escape hatch; when True, all requests are accepted anonymously

    # MVP quotas
    session_ttl_seconds: int = 120                     # auto-logout after this many seconds
    login_allowlist_emails: str = "gk3360836@gmail.com"  # comma-separated, may login multiple times
    login_allowlist_ips: str = "127.0.0.1,::1"         # comma-separated IPs exempted from IP block
    single_login_enforced: bool = True                 # if True, non-allowlisted users can only log in once

    # Optional: embedding deployment for semantic retrieval
    embeddings_model_endpoint: str = ""
    embeddings_model_key: str = ""
    embeddings_model_deployment: str = "text-embedding-3-small"

    # Optional: YouTube API key (used by ingestor scripts, not runtime)
    youtube_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
