from supabase import create_client, Client
from .config import settings

_client: Client | None = None
_init_failed: bool = False


def get_supabase() -> Client | None:
    global _client, _init_failed
    if _init_failed:
        return None
    if not settings.supabase_url or not settings.supabase_service_role:
        return None
    if _client is None:
        try:
            _client = create_client(settings.supabase_url, settings.supabase_service_role)
        except Exception as e:
            _init_failed = True
            print(f"[supabase] init failed, disabling persistence: {e}")
            return None
    return _client


def save_session(user_id: str | None, session_id: str, payload: dict) -> None:
    sb = get_supabase()
    if not sb:
        return
    try:
        sb.table("learning_sessions").upsert({
            "session_id": session_id,
            "user_id": user_id,
            "data": payload,
        }, on_conflict="session_id").execute()
    except Exception as e:
        print(f"[supabase] save_session failed: {e}")
