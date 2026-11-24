from supabase import create_client, Client
from app.core.config import get_settings


def get_supabase(access_token: str) -> Client:
    """Create a request-scoped client whose PostgREST requests use the caller's JWT."""
    settings = get_settings()
    client = create_client(
        settings.SUPABASE_URL.strip(),
        settings.SUPABASE_ANON_KEY.strip(),
    )
    client.postgrest.auth(access_token)
    return client
