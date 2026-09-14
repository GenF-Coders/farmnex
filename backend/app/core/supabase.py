from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Create one server-side Supabase client per process.

    The backend uses the Supabase secret key and does not persist
    a user session.
    """

    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key.get_secret_value(),
    )