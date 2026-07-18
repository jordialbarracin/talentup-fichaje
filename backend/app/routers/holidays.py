"""
TalentUP Fichaje — Holidays router.
GET/POST/PUT/DELETE /api/holidays
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.holiday import Holiday
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


class HolidayCreate(BaseModel):
    date: str
    name: str
    type: str  # national, regional, local
    region: Optional[str] = None
    locality: Optional[str] = None
    is_paid: bool = True
    is_working: bool = False
    year: int


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    region: Optional[str] = None
    locality: Optional[str] = None
    is_paid: Optional[bool] = None
    is_working: Optional[bool] = None


@router.get("")
async def list_holidays(
    year: Optional[int] = None,
    type: Optional[str] = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(Holiday)
    if current_user.role != "super_admin":
        query = query.where(Holiday.tenant_id == tenant_id)
    if year:
        query = query.where(Holiday.year == year)
    if type:
        query = query.where(Holiday.type == type)
    query = query.order_by(Holiday.date)
    result = await db.execute(query)
    holidays = result.scalars().all()
    return [h.to_dict() for h in holidays]


@router.get("/{holiday_id}")
async def get_holiday(
    holiday_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=404, detail="Festivo no encontrado")
    if current_user.role != "super_admin" and holiday.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return holiday.to_dict()


@router.post("", status_code=201)
async def create_holiday(
    data: HolidayCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    tenant_id = current_user.tenant_id

    holiday = Holiday(
        tenant_id=tenant_id,
        date=date.fromisoformat(data.date),
        name=data.name,
        type=data.type,
        region=data.region,
        locality=data.locality,
        is_paid=data.is_paid,
        is_working=data.is_working,
        year=data.year,
    )
    db.add(holiday)
    await db.commit()
    await db.refresh(holiday)

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="create", entity_type="holiday", entity_id=holiday.id,
                     new_value=holiday.to_dict())
    await db.commit()
    return holiday.to_dict()


@router.put("/{holiday_id}")
async def update_holiday(
    holiday_id: str,
    data: HolidayUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=404, detail="Festivo no encontrado")
    if current_user.role != "super_admin" and holiday.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.name is not None: holiday.name = data.name
    if data.type is not None: holiday.type = data.type
    if data.region is not None: holiday.region = data.region
    if data.locality is not None: holiday.locality = data.locality
    if data.is_paid is not None: holiday.is_paid = data.is_paid
    if data.is_working is not None: holiday.is_working = data.is_working

    old_value = holiday.to_dict()
    await db.commit()
    await db.refresh(holiday)

    await log_action(db, tenant_id=holiday.tenant_id, user_id=current_user.id,
                     action="update", entity_type="holiday", entity_id=holiday.id,
                     old_value=old_value, new_value=holiday.to_dict())
    await db.commit()
    return holiday.to_dict()


@router.delete("/{holiday_id}", status_code=204)
async def delete_holiday(
    holiday_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=404, detail="Festivo no encontrado")
    if current_user.role != "super_admin" and holiday.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = holiday.to_dict()
    await db.execute(delete(Holiday).where(Holiday.id == holiday_id))
    await db.commit()

    await log_action(db, tenant_id=holiday.tenant_id, user_id=current_user.id,
                     action="delete", entity_type="holiday", entity_id=holiday.id,
                     old_value=old_value)
    await db.commit()
    return None
