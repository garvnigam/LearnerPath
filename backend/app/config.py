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

    # Optional: embedding deployment for semantic retrieval
    embeddings_model_endpoint: str = ""
    embeddings_model_key: str = ""
    embeddings_model_deployment: str = "text-embedding-3-small"

    # Optional: YouTube API key (used by ingestor scripts, not runtime)
    youtube_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
