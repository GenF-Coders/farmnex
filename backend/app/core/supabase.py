from __future__ import annotations

from functools import lru_cache

from supabase import Client, ClientOptions, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Create the server-side Supabase client used by Storage.

    This client is intentionally independent from FarmNex authentication.
    It uses the server-side Supabase secret key and never persists a user
    session. Storage calls are executed by ``StorageService`` in worker
    threads because the sync Supabase SDK is used there.
    """
    url = settings.supabase_url.strip().rstrip("/")
    secret = settings.supabase_secret_key.get_secret_value().strip()
    if not url or not secret:
        raise RuntimeError("Supabase Storage credentials are not configured.")

    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
        storage_client_timeout=max(3, int(settings.storage_timeout_seconds)),
    )

    return create_client(url, secret, options=options)
