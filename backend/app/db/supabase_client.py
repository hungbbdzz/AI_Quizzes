from supabase import create_client, Client
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Supabase client với anon key.
    Dùng cho các thao tác thông thường có RLS.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Client:
    """
    Supabase client với service role key.
    Bypass RLS — chỉ dùng cho server-side admin operations
    như tạo embeddings, lưu chunks, storage operations.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
