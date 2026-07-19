"""
TalentUP Fichaje — Settings router.
GET/PUT /api/settings — read/update current tenant settings (owner/manager).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.auth import get_current_user, require_owner

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    cif: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    convenio: Optional[str] = None
    ccaa: Optional[str] = None
    locality: Optional[str] = None
    sector: Optional[str] = None
    tolerancia_min: Optional[int] = None
    vacation_days_per_year: Optional[float] = None
    weekly_hours: Optional[float] = None
    work_days: Optional[int] = None
    notif_email: Optional[str] = None
    notif_clock: Optional[int] = None
    notif_vacation: Optional[str] = None
    setup_completed: Optional[bool] = None


@router.get("")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant settings."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="No tenant associated")
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.to_dict()


@router.put("")
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current tenant settings."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="No tenant associated")
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    await db.commit()
    await db.refresh(tenant)
    return tenant.to_dict()
