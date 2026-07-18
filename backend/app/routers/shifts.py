"""
TalentUP Fichaje — Shifts router (ampliado con plus_nocturnidad, plus_festividad, is_rotativo).
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
    if not _HHMM_RE.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido para '{field_name}': '{value}'. Use HH:MM (ej: 08:00, 16:30).",
        )


class ShiftCreate(BaseModel):
    name: str
    code: Optional[str] = None
    shift_type: str = "morning"
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    break_min: int = 0
    tolerance_min: int = 5
    grace_period_min: int = 15
    overtime_threshold_min: int = 0
    is_split: bool = False
    is_night: bool = False
    plus_nocturnidad: float = 0
    plus_festividad: float = 0
    is_rotativo: bool = False
    color: str = "#FF6B35"
    icon: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    shift_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    break_min: Optional[int] = None
    tolerance_min: Optional[int] = None
    grace_period_min: Optional[int] = None
    overtime_threshold_min: Optional[int] = None
    is_split: Optional[bool] = None
    is_night: Optional[bool] = None
    plus_nocturnidad: Optional[float] = None
    plus_festividad: Optional[float] = None
    is_rotativo: Optional[bool] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("")
async def list_shifts(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
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
    from datetime import time
    _validate_hhmm(data.start_time, "start_time")
    _validate_hhmm(data.end_time, "end_time")
    start_h, start_m = map(int, data.start_time.split(":"))
    end_h, end_m = map(int, data.end_time.split(":"))

    break_start = None
    break_end = None
    if data.break_start:
        _validate_hhmm(data.break_start, "break_start")
        bh, bm = map(int, data.break_start.split(":"))
        break_start = time(bh, bm)
    if data.break_end:
        _validate_hhmm(data.break_end, "break_end")
        bh, bm = map(int, data.break_end.split(":"))
        break_end = time(bh, bm)

    shift = Shift(
        tenant_id=current_user.tenant_id,
        name=data.name,
        code=data.code,
        shift_type=data.shift_type,
        start_time=time(start_h, start_m),
        end_time=time(end_h, end_m),
        break_start=break_start,
        break_end=break_end,
        break_min=data.break_min,
        tolerance_min=data.tolerance_min,
        grace_period_min=data.grace_period_min,
        overtime_threshold_min=data.overtime_threshold_min,
        is_split=data.is_split,
        is_night=data.is_night,
        plus_nocturnidad=data.plus_nocturnidad,
        plus_festividad=data.plus_festividad,
        is_rotativo=data.is_rotativo,
        color=data.color,
        icon=data.icon,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)

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
    from datetime import time
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if current_user.role != "super_admin" and shift.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.name is not None: shift.name = data.name
    if data.code is not None: shift.code = data.code
    if data.shift_type is not None: shift.shift_type = data.shift_type
    if data.start_time is not None:
        _validate_hhmm(data.start_time, "start_time")
        h, m = map(int, data.start_time.split(":"))
        shift.start_time = time(h, m)
    if data.end_time is not None:
        _validate_hhmm(data.end_time, "end_time")
        h, m = map(int, data.end_time.split(":"))
        shift.end_time = time(h, m)
    if data.break_start is not None:
        _validate_hhmm(data.break_start, "break_start")
        h, m = map(int, data.break_start.split(":"))
        shift.break_start = time(h, m)
    if data.break_end is not None:
        _validate_hhmm(data.break_end, "break_end")
        h, m = map(int, data.break_end.split(":"))
        shift.break_end = time(h, m)
    if data.break_min is not None: shift.break_min = data.break_min
    if data.tolerance_min is not None: shift.tolerance_min = data.tolerance_min
    if data.grace_period_min is not None: shift.grace_period_min = data.grace_period_min
    if data.overtime_threshold_min is not None: shift.overtime_threshold_min = data.overtime_threshold_min
    if data.is_split is not None: shift.is_split = data.is_split
    if data.is_night is not None: shift.is_night = data.is_night
    if data.plus_nocturnidad is not None: shift.plus_nocturnidad = data.plus_nocturnidad
    if data.plus_festividad is not None: shift.plus_festividad = data.plus_festividad
    if data.is_rotativo is not None: shift.is_rotativo = data.is_rotativo
    if data.color is not None: shift.color = data.color
    if data.icon is not None: shift.icon = data.icon
    if data.is_active is not None: shift.is_active = data.is_active
    if data.sort_order is not None: shift.sort_order = data.sort_order

    old_value = shift.to_dict()
    await db.commit()
    await db.refresh(shift)

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
