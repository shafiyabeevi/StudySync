from supabase import create_client, Client
from app.core.config import get_settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Returns a singleton Supabase client.
    Uses the anon key for now (single-user mode).
    When auth is added, this can be swapped to create per-request
    clients with the user's JWT for RLS enforcement.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.SUPABASE_URL.strip(),
            settings.SUPABASE_ANON_KEY.strip()
        )
    return _supabase_client
