"""
TalentUP Fichaje — Shifts router.
GET/POST/PUT/DELETE /api/shifts
"""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.shift import Shift
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/shifts", tags=["shifts"])

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _validate_hhmm(value: str, field_name: str) -> None:
    """Validate HH:MM format, raise 400 if invalid."""
    if not _HHMM_RE.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido para '{field_name}': '{value}'. Use HH:MM (ej: 08:00, 16:30).",
        )


class ShiftCreate(BaseModel):
    name: str
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    tolerance_min: int = 5
    is_split: bool = False
    break_min: int = 0
    color: str = "#FF6B35"


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    tolerance_min: Optional[int] = None
    is_split: Optional[bool] = None
    break_min: Optional[int] = None
    color: Optional[str] = None


@router.get("")
async def list_shifts(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all shifts for the current user's tenant."""
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin":
        result = await db.execute(select(Shift))
    else:
        result = await db.execute(
            select(Shift).where(Shift.tenant_id == tenant_id)
        )
    shifts = result.scalars().all()
    return [s.to_dict() for s in shifts]


@router.get("/{shift_id}")
async def get_shift(
    shift_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if current_user.role != "super_admin" and shift.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return shift.to_dict()


@router.post("", status_code=201)
async def create_shift(
    data: ShiftCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a new shift."""
    from datetime import time
    _validate_hhmm(data.start_time, "start_time")
    _validate_hhmm(data.end_time, "end_time")
    start_h, start_m = map(int, data.start_time.split(":"))
    end_h, end_m = map(int, data.end_time.split(":"))

    shift = Shift(
        tenant_id=current_user.tenant_id,
        name=data.name,
        start_time=time(start_h, start_m),
        end_time=time(end_h, end_m),
        tolerance_min=data.tolerance_min,
        is_split=data.is_split,
        break_min=data.break_min,
        color=data.color,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)

    # Audit log
    await log_action(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="create",
        entity_type="shift",
        entity_id=shift.id,
        new_value=shift.to_dict(),
    )
    await db.commit()

    return shift.to_dict()


@router.put("/{shift_id}")
async def update_shift(
    shift_id: str,
    data: ShiftUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if current_user.role != "super_admin" and shift.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    from datetime import time
    if data.name is not None:
        shift.name = data.name
    if data.start_time is not None:
        _validate_hhmm(data.start_time, "start_time")
        h, m = map(int, data.start_time.split(":"))
        shift.start_time = time(h, m)
    if data.end_time is not None:
        _validate_hhmm(data.end_time, "end_time")
        h, m = map(int, data.end_time.split(":"))
        shift.end_time = time(h, m)
    if data.tolerance_min is not None:
        shift.tolerance_min = data.tolerance_min
    if data.is_split is not None:
        shift.is_split = data.is_split
    if data.break_min is not None:
        shift.break_min = data.break_min
    if data.color is not None:
        shift.color = data.color

    old_value = shift.to_dict()
    await db.commit()
    await db.refresh(shift)

    # Audit log
    await log_action(
        db,
        tenant_id=shift.tenant_id,
        user_id=current_user.id,
        action="update",
        entity_type="shift",
        entity_id=shift.id,
        old_value=old_value,
        new_value=shift.to_dict(),
    )
    await db.commit()

    return shift.to_dict()


@router.delete("/{shift_id}", status_code=204)
async def delete_shift(
    shift_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if current_user.role != "super_admin" and shift.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = shift.to_dict()
    await db.execute(delete(Shift).where(Shift.id == shift_id))
    await db.commit()

    # Audit log
    await log_action(
        db,
        tenant_id=shift.tenant_id,
        user_id=current_user.id,
        action="delete",
        entity_type="shift",
        entity_id=shift.id,
        old_value=old_value,
    )
    await db.commit()
    return None
