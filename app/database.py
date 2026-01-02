from supabase import create_client, Client
from app.config import get_settings


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client using settings from the configuration.

    Returns:
        Client: Supabase client instance.
    """
    settings = get_settings()
    supabase_client = create_client(
        settings.supabase_url, settings.supabase_service_key
    )
    return supabase_client


def get_supabase_admin_client() -> Client:
    """
    Create and return a Supabase admin client.

    This uses the service role key which bypasses RLS.
    Use this for admin operations only!
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)
