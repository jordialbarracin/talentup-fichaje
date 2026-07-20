"""
TalentUP Fichaje — Tenants router.
GET/POST/PUT/DELETE /api/tenants (super_admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.auth import require_super_admin, get_current_user
from app.pagination import paginate

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str
    legal_name: Optional[str] = None
    cif: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    convenio: str = "hosteleria"
    tolerancia_min: int = 5
    plan: str = "basic"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    cif: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    convenio: Optional[str] = None
    tolerancia_min: Optional[int] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_tenants(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants (super_admin only) with pagination."""
    query = select(Tenant).order_by(Tenant.name)
    return await paginate(db, query, page, limit, item_transform=lambda t: t.to_dict())


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant.to_dict()


@router.post("", status_code=201)
async def create_tenant(
    data: TenantCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant (super_admin only)."""
    tenant = Tenant(
        name=data.name,
        legal_name=data.legal_name,
        cif=data.cif,
        address=data.address,
        phone=data.phone,
        email=data.email,
        convenio=data.convenio,
        tolerancia_min=data.tolerancia_min,
        plan=data.plan,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant.to_dict()


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if data.name is not None:
        tenant.name = data.name
    if data.legal_name is not None:
        tenant.legal_name = data.legal_name
    if data.cif is not None:
        tenant.cif = data.cif
    if data.address is not None:
        tenant.address = data.address
    if data.phone is not None:
        tenant.phone = data.phone
    if data.email is not None:
        tenant.email = data.email
    if data.convenio is not None:
        tenant.convenio = data.convenio
    if data.tolerancia_min is not None:
        tenant.tolerancia_min = data.tolerancia_min
    if data.plan is not None:
        tenant.plan = data.plan
    if data.is_active is not None:
        tenant.is_active = data.is_active

    await db.commit()
    await db.refresh(tenant)
    return tenant.to_dict()


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
    await db.commit()
    return None
