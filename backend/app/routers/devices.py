"""
TalentUP Fichaje — Devices router.
POST /api/devices to register a new terminal/device.
"""
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device
from app.models.tenant import Tenant
from app.models.user import User
from app.auth import require_manager

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class DeviceCreate(BaseModel):
    tenant_id: str
    name: Optional[str] = None
    device_token: Optional[str] = None
    is_active: bool = True


class DeviceResponse(BaseModel):
    id: str
    tenant_id: str
    device_token: str
    name: Optional[str]
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("", status_code=201, response_model=DeviceResponse)
async def create_device(
    data: DeviceCreate,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new device/terminal for a tenant.
    If no device_token is provided, a secure random token is generated.
    Requires manager+ role.
    """
    # Verify the tenant exists
    result = await db.execute(select(Tenant).where(Tenant.id == data.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Only super_admin can create devices for other tenants
    if current_user.role != "super_admin" and str(current_user.tenant_id) != str(data.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para registrar dispositivos en este tenant",
        )

    token = data.device_token or secrets.token_urlsafe(32)
    token_hash = _hash_token(token)

    # Ensure uniqueness against hashed tokens
    existing = await db.execute(select(Device).where(Device.device_token == token_hash))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="device_token ya existe",
        )

    device = Device(
        tenant_id=data.tenant_id,
        device_token=token_hash,
        name=data.name,
        is_active=data.is_active,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    return DeviceResponse(
        id=str(device.id),
        tenant_id=str(device.tenant_id),
        device_token=token,
        name=device.name,
        is_active=device.is_active,
        created_at=str(device.created_at) if hasattr(device, 'created_at') and device.created_at else None,
        updated_at=str(device.updated_at) if hasattr(device, 'updated_at') and device.updated_at else None,
    )
