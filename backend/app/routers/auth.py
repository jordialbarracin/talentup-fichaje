"""
TalentUP Fichaje — Auth router.
POST /api/auth/login, POST /api/auth/register, GET /api/auth/me
"""
import html
import os
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
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Cookie security: env override for local HTTP dev/tests.
# Default True (production). Set COOKIE_SECURE=false for Playwright E2E over HTTP.
_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
# SameSite: default 'lax' (production). Set COOKIE_SAMESITE=none for cross-origin E2E.
_COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

# --- Rate limiting for registration ---
# Redis-backed when REDIS_URL is available; in-memory fallback for dev/tests.
_register_attempts: dict[str, list[float]] = {}
REGISTER_RATE_LIMIT = 3  # max 3 per hour
REGISTER_RATE_WINDOW = 3600  # 1 hour in seconds

# --- Login rate limiting ---
_login_attempts: dict[str, list[float]] = {}
LOGIN_RATE_LIMIT = 10  # max 10 login attempts per 5 minutes
LOGIN_RATE_WINDOW = 300  # 5 minutes in seconds

# --- Refresh token revocation store ---
# Redis-backed when REDIS_URL is available; in-memory fallback for dev/tests.
# Stores revoked token JTI (or token signature) with TTL matching the refresh
# token lifetime so replayed tokens are rejected even if still within expiry.
_revoked_refresh_tokens: set[str] = set()
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


def _revoked_refresh_key(token: str) -> str:
    """Derive a stable key for a refresh token. Uses the last 32 chars of the token."""
    return token[-32:]


async def _revoke_refresh_token(token: str):
    """Add a refresh token to the revocation list."""
    key = _revoked_refresh_key(token)
    client = _get_redis_client()
    if client is not None:
        try:
            redis_key = f"refresh:revoked:{key}"
            await client.setex(redis_key, REFRESH_TOKEN_TTL_SECONDS, "1")
            return
        except Exception:
            pass
    _revoked_refresh_tokens.add(key)


async def _is_refresh_token_revoked(token: str) -> bool:
    """Check whether a refresh token has been revoked."""
    key = _revoked_refresh_key(token)
    client = _get_redis_client()
    if client is not None:
        try:
            redis_key = f"refresh:revoked:{key}"
            return await client.exists(redis_key) > 0
        except Exception:
            pass
    return key in _revoked_refresh_tokens


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
    ok: bool = True
    user: dict
    tenant_id: Optional[str] = None
    is_new_tenant: bool = False


class RefreshResponse(BaseModel):
    ok: bool = True
    user: dict
    tenant_id: Optional[str] = None


# --- Endpoints ---
@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens (also as httpOnly cookies)."""
    # Rate limit login attempts — only count failed attempts, read real IP behind proxy
    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        # Only record FAILED attempts
        allowed = await check_rate_limit(f"login:{client_ip}", LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW)
        if not allowed and not _cleanup_and_check(_login_attempts, f"login:{client_ip}", LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW):
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados intentos de login. Máximo {LOGIN_RATE_LIMIT} por {LOGIN_RATE_WINDOW // 60} minutos.",
                headers={"Retry-After": str(LOGIN_RATE_WINDOW)},
            )
        _record(_login_attempts, f"login:{client_ip}")
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
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=28800,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
    )

    return AuthResponse(
        ok=True,
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

    if await _is_refresh_token_revoked(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revocado",
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

    # Rotate: invalidate the used refresh token and issue a new one.
    await _revoke_refresh_token(refresh_token)
    new_refresh_token = create_refresh_token(user)
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
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=28800,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
    )

    return RefreshResponse(
        ok=True,
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
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=28800,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
    )

    return AuthResponse(
        ok=True,
        user=owner.to_dict(),
        tenant_id=str(tenant.id),
        is_new_tenant=True,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user.to_dict()


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout: read token from cookie or header and clear httpOnly cookies."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]

    # Always clear cookies, even if no token is present
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await _revoke_refresh_token(refresh_token)

    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=0,
    )
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        max_age=0,
    )

    return {"ok": True, "message": "Sesion cerrada"}
