"""
TalentUP Fichaje — Schedules router.
GET/POST/PUT/DELETE /api/schedules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule import Schedule
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action
from app.pagination import paginate

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    employee_id: str
    shift_id: str
    date: str  # YYYY-MM-DD
    notes: Optional[str] = None


class ScheduleUpdate(BaseModel):
    shift_id: Optional[str] = None
    notes: Optional[str] = None


def _parse_date_safe(value: str, field_name: str) -> date:
    """Parse ISO date string, raise 400 on invalid format."""
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha inválido para '{field_name}': '{value}'. Use YYYY-MM-DD.",
        )


@router.get("")
async def list_schedules(
    employee_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """List schedules with optional filters (paginated)."""
    tenant_id = current_user.tenant_id
    query = select(Schedule)

    if current_user.role == "super_admin":
        pass  # super_admin sees all
    else:
        query = query.where(Schedule.tenant_id == tenant_id)

    if employee_id:
        query = query.where(Schedule.employee_id == employee_id)
    if date_from:
        query = query.where(Schedule.date >= _parse_date_safe(date_from, "date_from"))
    if date_to:
        query = query.where(Schedule.date <= _parse_date_safe(date_to, "date_to"))

    query = query.order_by(Schedule.date.desc())
    return await paginate(db, query, page, limit, item_transform=lambda s: s.to_dict())


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    if current_user.role != "super_admin" and sched.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return sched.to_dict()


@router.post("", status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a new schedule entry."""
    sched_date = _parse_date_safe(data.date, "date")
    sched = Schedule(
        tenant_id=current_user.tenant_id,
        employee_id=data.employee_id,
        shift_id=data.shift_id,
        date=sched_date,
        notes=data.notes,
    )
    db.add(sched)
    try:
        await db.commit()
        await db.refresh(sched)
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "uq_schedule" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="Ya existe un horario para este empleado en esta fecha",
            )
        raise HTTPException(status_code=400, detail=str(e))

    # Audit log
    await log_action(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="create",
        entity_type="schedule",
        entity_id=sched.id,
        new_value=sched.to_dict(),
    )
    await db.commit()

    return sched.to_dict()


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    data: ScheduleUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    if current_user.role != "super_admin" and sched.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.shift_id is not None:
        sched.shift_id = data.shift_id
    if data.notes is not None:
        sched.notes = data.notes

    old_value = sched.to_dict()
    await db.commit()
    await db.refresh(sched)

    # Audit log
    await log_action(
        db,
        tenant_id=sched.tenant_id,
        user_id=current_user.id,
        action="update",
        entity_type="schedule",
        entity_id=sched.id,
        old_value=old_value,
        new_value=sched.to_dict(),
    )
    await db.commit()

    return sched.to_dict()


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = result.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    if current_user.role != "super_admin" and sched.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = sched.to_dict()
    await db.execute(delete(Schedule).where(Schedule.id == schedule_id))
    await db.commit()

    # Audit log
    await log_action(
        db,
        tenant_id=sched.tenant_id,
        user_id=current_user.id,
        action="delete",
        entity_type="schedule",
        entity_id=sched.id,
        old_value=old_value,
    )
    await db.commit()
    return None
