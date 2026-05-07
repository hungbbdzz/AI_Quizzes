from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.db.supabase_client import get_supabase_client, get_supabase_admin_client
from supabase import Client

security = HTTPBearer()


async def get_supabase() -> Client:
    """Dependency — trả về Supabase client (anon key, có RLS)."""
    return get_supabase_client()


async def get_supabase_admin() -> Client:
    """Dependency — trả về Supabase admin client (service role, bypass RLS)."""
    return get_supabase_admin_client()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Xác thực JWT token từ Supabase Auth.
    Gọi supabase.auth.get_user() để verify token server-side.
    Trả về user dict nếu hợp lệ, raise 401 nếu không.
    """
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ hoặc đã hết hạn.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không thể xác thực thông tin đăng nhập.",
            headers={"WWW-Authenticate": "Bearer"},
        )
