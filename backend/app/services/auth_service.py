from fastapi import HTTPException, status
from supabase import Client

from app.models.auth import RegisterRequest, LoginRequest, AuthResponse, TokenResponse
from app.config import settings
from jose import jwt
from datetime import datetime, timedelta
import bcrypt


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def register_user(supabase: Client, body: RegisterRequest) -> AuthResponse:
    """Register a new user, store in DB, return user info."""
    # Check if email already exists
    existing = supabase.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    hashed_pw = _hash_password(body.password)
    user_data = {
        "email": body.email,
        "full_name": body.full_name,
        "hashed_password": hashed_pw,
    }

    try:
        result = supabase.table("users").insert(user_data).execute()
        user = result.data[0]
        return AuthResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}",
        )


async def login_user(supabase: Client, body: LoginRequest) -> TokenResponse:
    """Authenticate user credentials and return JWT token."""
    result = supabase.table("users").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = result.data[0]
    if not _verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = _create_access_token(user["id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"],
        ),
    )
