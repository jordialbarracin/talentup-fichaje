"""
TalentUP Fichaje — Auth router.
POST /api/auth/login, POST /api/auth/register, GET /api/auth/me
"""
import html
import time as _time
from datetime import datetime, time, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.shift import Shift
from app.rate_limiter import (
    check_rate_limit,
    record_rate,
    _cleanup_and_check,
    _record,
    WINDOW_SECONDS,
    _get_redis_client,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_super_admin,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Rate limiting for registration ---
# Redis-backed when REDIS_URL is available; in-memory fallback for dev/tests.
_register_attempts: dict[str, list[float]] = {}
REGISTER_RATE_LIMIT = 3  # max 3 per hour
REGISTER_RATE_WINDOW = 3600  # 1 hour in seconds


async def _check_register_rate_limit(ip: str):
    """Check if IP has exceeded register rate limit. Raises 429 if so."""
    key = f"register:{ip}"
    allowed = await check_rate_limit(key, REGISTER_RATE_LIMIT, REGISTER_RATE_WINDOW)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de registro. Intenta de nuevo en una hora.",
        )

    # Keep in-memory store accurate when Redis is disabled.
    if _get_redis_client() is None:
        if not _cleanup_and_check(_register_attempts, ip, REGISTER_RATE_LIMIT, REGISTER_RATE_WINDOW):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos de registro. Intenta de nuevo en una hora.",
            )
        _record(_register_attempts, ip)
        return

    await record_rate(key)


# --- Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    restaurant_name: str
    owner_name: str
    email: str
    password: str
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("restaurant_name")
    @classmethod
    def restaurant_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("El nombre del restaurante es obligatorio")
        return v

    @field_validator("owner_name")
    @classmethod
    def owner_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("El nombre del propietario es obligatorio")
        return v


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    tenant_id: Optional[str] = None
    is_new_tenant: bool = False


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    tenant_id: Optional[str] = None


# --- Endpoints ---
@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens (also as httpOnly cookies)."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    })
    refresh_token = create_refresh_token(user)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800,
    )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_dict(),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token from the httpOnly cookie for a new access token.

    The refresh token is read ONLY from the `refresh_token` httpOnly cookie.
    If the cookie is absent, the request is rejected with 401.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token requerido",
        )

    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido para refresh",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    })

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800,
    )

    return RefreshResponse(
        access_token=access_token,
        user=user.to_dict(),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    req: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Self-service registration: creates a new tenant + owner user + default shifts.
    Rate-limited: max 3 per hour per IP.
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    await _check_register_rate_limit(client_ip)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado",
        )

    # 1. Create tenant
    safe_restaurant_name = html.escape(req.restaurant_name)
    safe_owner_name = html.escape(req.owner_name)
    tenant = Tenant(
        name=safe_restaurant_name,
        phone=req.phone,
        email=req.email,
        convenio="hosteleria",
        plan="basic",
        max_employees=50,
        setup_completed=False,
    )
    db.add(tenant)
    await db.flush()

    # 2. Create owner user
    owner = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=hash_password(req.password),
        name=safe_owner_name,
        role="owner",
    )
    db.add(owner)
    await db.flush()

    # 3. Create 3 default shifts
    default_shifts = [
        Shift(
            tenant_id=tenant.id,
            name="Manana",
            code="M",
            shift_type="morning",
            start_time=time(7, 0),
            end_time=time(15, 0),
            break_min=30,
            tolerance_min=5,
            grace_period_min=15,
            is_split=False,
            is_night=False,
            plus_nocturnidad=0,
            plus_festividad=25,
            is_rotativo=False,
            color="#FF6B35",
            sort_order=1,
        ),
        Shift(
            tenant_id=tenant.id,
            name="Tarde",
            code="T",
            shift_type="afternoon",
            start_time=time(15, 0),
            end_time=time(23, 0),
            break_min=30,
            tolerance_min=5,
            grace_period_min=15,
            is_split=False,
            is_night=False,
            plus_nocturnidad=0,
            plus_festividad=25,
            is_rotativo=False,
            color="#0F766E",
            sort_order=2,
        ),
        Shift(
            tenant_id=tenant.id,
            name="Noche",
            code="N",
            shift_type="night",
            start_time=time(23, 0),
            end_time=time(7, 0),
            break_min=30,
            tolerance_min=10,
            grace_period_min=15,
            is_split=False,
            is_night=True,
            plus_nocturnidad=25,
            plus_festividad=25,
            is_rotativo=False,
            color="#1E3A5F",
            sort_order=3,
        ),
    ]
    for s in default_shifts:
        db.add(s)

    await db.commit()
    await db.refresh(tenant)
    await db.refresh(owner)

    # Generate JWT
    access_token = create_access_token({
        "sub": str(owner.id),
        "email": owner.email,
        "role": owner.role,
        "tenant_id": str(owner.tenant_id) if owner.tenant_id else None,
    })
    refresh_token = create_refresh_token(owner)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800,
    )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=owner.to_dict(),
        tenant_id=str(tenant.id),
        is_new_tenant=True,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user.to_dict()
