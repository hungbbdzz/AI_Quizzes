from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase, get_current_user
from app.models.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, supabase: Client = Depends(get_supabase)):
    """Đăng ký tài khoản mới qua Supabase Auth."""
    try:
        response = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"full_name": body.full_name or ""}},
        })
        if not response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đăng ký thất bại.")

        user = response.user
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.user_metadata.get("full_name") if user.user_metadata else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, supabase: Client = Depends(get_supabase)):
    """Đăng nhập, trả về access_token từ Supabase Auth."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        if not response.session or not response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng.")

        user = response.user
        return AuthResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.user_metadata.get("full_name") if user.user_metadata else None,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Lấy thông tin user đang đăng nhập."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("user_metadata", {}).get("full_name"),
    )


@router.post("/logout")
async def logout(supabase: Client = Depends(get_supabase)):
    """Đăng xuất — invalidate session."""
    try:
        supabase.auth.sign_out()
        return {"message": "Đăng xuất thành công."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
