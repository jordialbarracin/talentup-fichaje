"""
TalentUP Fichaje — JWT Authentication & Authorization.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User

# --- Config ---
import secrets
import logging

logger = logging.getLogger(__name__)

_jwt_secret = os.environ.get("JWT_SECRET")
_ENV = os.environ.get("APP_ENV", "development").lower()
if _jwt_secret:
    SECRET_KEY = _jwt_secret
else:
    if _ENV in ("production", "prod"):
        raise RuntimeError("JWT_SECRET requerido en produccion")
    # In dev, generate a random secret and log it
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        "⚠️  JWT_SECRET no configurado. Usando clave generada aleatoriamente. "
        "En producción, establece la variable de entorno JWT_SECRET."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRE_DAYS", "30"))  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# --- PIN hash fast (SHA256) ---
# SECRET_SALT for fast PIN hashing — required always.
_PIN_HASH_SALT = os.environ.get("PIN_HASH_SALT")
if not _PIN_HASH_SALT:
    raise RuntimeError("PIN_HASH_SALT requerido")
_SECRET_SALT = _PIN_HASH_SALT


def compute_pin_hash_fast(pin: str) -> str:
    """Compute a fast SHA256 hash of the PIN for indexed lookups.

    This is NOT a replacement for bcrypt — it's a first-pass filter
    so we can query by index instead of iterating all employees.
    The bcrypt verify_password is still used as the authoritative check.
    """
    return hashlib.sha256((pin + _SECRET_SALT).encode("utf-8")).hexdigest()


# --- Password helpers ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT helpers ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived refresh token for the given user."""
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "type": "refresh",
    }
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns the payload or raises."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


# --- Dependencies ---
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token.

    Priority:
      1. httpOnly cookie 'access_token'
      2. HTTP Bearer Authorization header (fallback)
    """
    token = request.cookies.get("access_token")
    if not token and credentials is not None:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
        )
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sin user_id",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    return user


def role_check(*allowed_roles: str):
    """Dependency factory: checks that the current user has one of the allowed roles."""
    async def _role_check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {', '.join(allowed_roles)}",
            )
        return current_user
    return _role_check


# Convenience role dependencies
require_super_admin = role_check("super_admin")
require_owner = role_check("super_admin", "owner")
require_manager = role_check("super_admin", "owner", "manager")
