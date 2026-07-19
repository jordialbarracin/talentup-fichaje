"""
TalentUP Fichaje — Clock router.
POST /api/clock (público, con PIN), GET /api/clock/history, GET /api/clock/today
"""
import time as time_module
from collections import defaultdict
from datetime import date, datetime, time, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.clock_in import ClockIn
from app.models.employee import Employee
from app.models.user import User
from app.auth import verify_password, require_manager, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/clock", tags=["clock"])

# --- Rate limiting (in-memory) ---
# clock_limits: key = f"{ip}:{tenant_id}" -> list of timestamps
_clock_limits: dict[str, list[float]] = defaultdict(list)
# pin_failures: key = f"{ip}:{tenant_id}" -> list of timestamps
_pin_failures: dict[str, list[float]] = defaultdict(list)
# pin_blocks: key = f"{ip}:{tenant_id}" -> unblock timestamp
_pin_blocks: dict[str, float] = {}

CLOCK_MAX_PER_MINUTE = 10
PIN_FAIL_MAX_PER_MINUTE = 5
PIN_BLOCK_MINUTES = 5
WINDOW_SECONDS = 60


def _cleanup_and_check(
    store: dict[str, list[float]],
    key: str,
    max_count: int,
    window: int = WINDOW_SECONDS,
) -> bool:
    """Remove entries older than `window` seconds and check if under limit."""
    now = time_module.time()
    if key in store:
        store[key] = [t for t in store[key] if now - t < window]
    return len(store.get(key, [])) < max_count


def _record(store: dict[str, list[float]], key: str):
    store[key].append(time_module.time())


class ClockRequest(BaseModel):
    pin: str
    type: Literal["in", "out", "break_start", "break_end", "auto"] = "auto"
    tenant_id: str = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_offline: bool = False


class NfcClockRequest(BaseModel):
    nfc_uid: str
    tenant_id: str


class QrClockRequest(BaseModel):
    employee_id: str
    tenant_id: str


class ClockCancelRequest(BaseModel):
    reason: str


@router.post("", status_code=201)
async def clock_in(
    data: ClockRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a clock-in/out. PUBLIC endpoint — no JWT required.
    The terminal uses PIN + tenant_id to identify the employee.
    """
    if not data.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id es requerido")

    # --- Rate limiting by IP+tenant_id ---
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.tenant_id}"

    # Check PIN block
    if rate_key in _pin_blocks:
        if time_module.time() < _pin_blocks[rate_key]:
            remaining = int(_pin_blocks[rate_key] - time_module.time())
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados intentos fallidos. Bloqueado {PIN_BLOCK_MINUTES} min. Reintenta en {remaining}s.",
                headers={"Retry-After": str(remaining)},
            )
        else:
            del _pin_blocks[rate_key]

    # Check clock rate limit
    if not _cleanup_and_check(_clock_limits, rate_key, CLOCK_MAX_PER_MINUTE):
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados fichajes. Máximo {CLOCK_MAX_PER_MINUTE} por minuto.",
            headers={"Retry-After": "60"},
        )

    # Find employee by PIN within the tenant
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == data.tenant_id,
            Employee.is_active == True,
        )
    )
    employees = result.scalars().all()

    # Verify PIN against each employee (we can't query by hash directly)
    matched_emp = None
    for emp in employees:
        if verify_password(data.pin, emp.pin_hash):
            matched_emp = emp
            break

    if not matched_emp:
        # Record PIN failure
        _record(_pin_failures, rate_key)
        if not _cleanup_and_check(_pin_failures, rate_key, PIN_FAIL_MAX_PER_MINUTE):
            _pin_blocks[rate_key] = time_module.time() + PIN_BLOCK_MINUTES * 60
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados PINs erróneos. Bloqueado {PIN_BLOCK_MINUTES} minutos.",
                headers={"Retry-After": str(PIN_BLOCK_MINUTES * 60)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto",
        )

    # Record the clock action for rate limiting (before transition validation)
    _record(_clock_limits, rate_key)

    # --- Transition validation ---
    # Get the last non-cancelled clock-in for this employee
    last_clock_result = await db.execute(
        select(ClockIn).where(
            ClockIn.employee_id == matched_emp.id,
            ClockIn.is_cancelled == False,
        ).order_by(ClockIn.timestamp.desc()).limit(1)
    )
    last_clock = last_clock_result.scalar_one_or_none()

    # --- Auto toggle: determine type based on last clock ---
    if data.type == "auto":
        if not last_clock or last_clock.type == "out":
            data_type = "in"
        elif last_clock.type == "in":
            data_type = "out"
        elif last_clock.type == "break_start":
            data_type = "break_end"
        elif last_clock.type == "break_end":
            data_type = "out"
        else:
            data_type = "in"
    else:
        data_type = data.type

    if data_type == "in":
        if last_clock and last_clock.type in ("in", "break_end"):
            if last_clock.type == "in":
                raise HTTPException(
                    status_code=400,
                    detail=f"{matched_emp.name} ya tiene un fichaje 'in' activo. Debe hacer 'out' o 'break_start' primero.",
                )
            if last_clock.type == "break_end":
                raise HTTPException(
                    status_code=400,
                    detail=f"{matched_emp.name} ya está trabajando. Debe hacer 'out' primero.",
                )
    elif data_type == "out":
        if not last_clock or last_clock.type not in ("in", "break_end"):
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene un fichaje 'in' activo. No puede hacer 'out'.",
            )
    elif data_type == "break_start":
        if not last_clock or last_clock.type not in ("in", "break_end"):
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene un fichaje 'in' activo. No puede iniciar pausa.",
            )
        if last_clock.type == "break_start":
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} ya está en pausa. Debe hacer 'break_end' primero.",
            )
    elif data_type == "break_end":
        if not last_clock or last_clock.type != "break_start":
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene una pausa activa. No puede finalizar pausa.",
            )

    clock = ClockIn(
        tenant_id=data.tenant_id,
        employee_id=matched_emp.id,
        type=data_type,
        timestamp=datetime.now(timezone.utc),
        latitude=data.latitude,
        longitude=data.longitude,
        is_offline=data.is_offline,
    )
    db.add(clock)
    await db.commit()
    await db.refresh(clock)

    # Response labels in Spanish
    _labels = {"in": "Entrada", "out": "Salida", "break_start": "Inicio de pausa", "break_end": "Fin de pausa"}
    return {
        "ok": True,
        "message": f"{matched_emp.name} — {_labels.get(data_type, data_type)} registrada",
        "type": data_type,
        "employee_name": matched_emp.name,
        "time": clock.timestamp.isoformat() if clock.timestamp else None,
        "clock": clock.to_dict(),
    }


@router.post("/nfc", status_code=201)
async def clock_nfc(
    data: NfcClockRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a clock-in/out via NFC. PUBLIC endpoint — no JWT required.
    The terminal uses NFC UID + tenant_id to identify the employee.
    """
    # --- Rate limiting by IP+tenant_id (same as PIN endpoint) ---
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.tenant_id}"

    if not _cleanup_and_check(_clock_limits, rate_key, CLOCK_MAX_PER_MINUTE):
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados fichajes. Máximo {CLOCK_MAX_PER_MINUTE} por minuto.",
            headers={"Retry-After": "60"},
        )

    # Find employee by nfc_uid within the tenant
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == data.tenant_id,
            Employee.nfc_uid == data.nfc_uid,
            Employee.is_active == True,
        )
    )
    matched_emp = result.scalar_one_or_none()

    if not matched_emp:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta NFC no registrada",
        )

    # Record the clock action for rate limiting
    _record(_clock_limits, rate_key)

    # --- Auto toggle (same logic as type='auto' in PIN endpoint) ---
    last_clock_result = await db.execute(
        select(ClockIn).where(
            ClockIn.employee_id == matched_emp.id,
            ClockIn.is_cancelled == False,
        ).order_by(ClockIn.timestamp.desc()).limit(1)
    )
    last_clock = last_clock_result.scalar_one_or_none()

    if not last_clock or last_clock.type == "out":
        data_type = "in"
    elif last_clock.type == "in":
        data_type = "out"
    elif last_clock.type == "break_start":
        data_type = "break_end"
    elif last_clock.type == "break_end":
        data_type = "out"
    else:
        data_type = "in"

    # --- Transition validation ---
    if data_type == "in":
        if last_clock and last_clock.type in ("in", "break_end"):
            if last_clock.type == "in":
                raise HTTPException(
                    status_code=400,
                    detail=f"{matched_emp.name} ya tiene un fichaje 'in' activo. Debe hacer 'out' o 'break_start' primero.",
                )
            if last_clock.type == "break_end":
                raise HTTPException(
                    status_code=400,
                    detail=f"{matched_emp.name} ya está trabajando. Debe hacer 'out' primero.",
                )
    elif data_type == "out":
        if not last_clock or last_clock.type not in ("in", "break_end"):
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene un fichaje 'in' activo. No puede hacer 'out'.",
            )
    elif data_type == "break_start":
        if not last_clock or last_clock.type not in ("in", "break_end"):
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene un fichaje 'in' activo. No puede iniciar pausa.",
            )
        if last_clock.type == "break_start":
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} ya está en pausa. Debe hacer 'break_end' primero.",
            )
    elif data_type == "break_end":
        if not last_clock or last_clock.type != "break_start":
            raise HTTPException(
                status_code=400,
                detail=f"{matched_emp.name} no tiene una pausa activa. No puede finalizar pausa.",
            )

    clock = ClockIn(
        tenant_id=data.tenant_id,
        employee_id=matched_emp.id,
        type=data_type,
        timestamp=datetime.now(timezone.utc),
        is_offline=False,
    )
    db.add(clock)
    await db.commit()
    await db.refresh(clock)

    _labels = {"in": "Entrada", "out": "Salida", "break_start": "Inicio de pausa", "break_end": "Fin de pausa"}
    return {
        "ok": True,
        "message": f"{matched_emp.name} — {_labels.get(data_type, data_type)} registrada",
        "type": data_type,
        "employee_name": matched_emp.name,
        "time": clock.timestamp.isoformat() if clock.timestamp else None,
        "clock": clock.to_dict(),
    }


@router.post("/qr", status_code=201)
async def clock_qr(
    data: QrClockRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a clock-in/out via QR code. PUBLIC endpoint — no JWT required.
    The terminal scans a QR containing the employee_id and posts it here.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.tenant_id}"

    if not _cleanup_and_check(_clock_limits, rate_key, CLOCK_MAX_PER_MINUTE):
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados fichajes. Máximo {CLOCK_MAX_PER_MINUTE} por minuto.",
            headers={"Retry-After": "60"},
        )

    # Find employee by ID within the tenant
    result = await db.execute(
        select(Employee).where(
            Employee.id == data.employee_id,
            Employee.tenant_id == data.tenant_id,
            Employee.is_active == True,
        )
    )
    matched_emp = result.scalar_one_or_none()

    if not matched_emp:
        raise HTTPException(
            status_code=404,
            detail="Código QR no válido o empleado no encontrado",
        )

    _record(_clock_limits, rate_key)

    # --- Auto toggle (same logic as NFC) ---
    last_clock_result = await db.execute(
        select(ClockIn).where(
            ClockIn.employee_id == matched_emp.id,
            ClockIn.is_cancelled == False,
        ).order_by(ClockIn.timestamp.desc()).limit(1)
    )
    last_clock = last_clock_result.scalar_one_or_none()

    if not last_clock or last_clock.type == "out":
        data_type = "in"
    elif last_clock.type == "in":
        data_type = "out"
    elif last_clock.type == "break_start":
        data_type = "break_end"
    elif last_clock.type == "break_end":
        data_type = "out"
    else:
        data_type = "in"

    # --- Transition validation ---
    if data_type == "in":
        if last_clock and last_clock.type in ("in", "break_end"):
            if last_clock.type == "in":
                raise HTTPException(status_code=400, detail=f"{matched_emp.name} ya tiene un fichaje 'in' activo.")
            if last_clock.type == "break_end":
                raise HTTPException(status_code=400, detail=f"{matched_emp.name} ya está trabajando.")
    elif data_type == "out":
        if not last_clock or last_clock.type not in ("in", "break_end"):
            raise HTTPException(status_code=400, detail=f"{matched_emp.name} no tiene un fichaje 'in' activo.")

    clock = ClockIn(
        tenant_id=data.tenant_id,
        employee_id=matched_emp.id,
        type=data_type,
        timestamp=datetime.now(timezone.utc),
        is_offline=False,
    )
    db.add(clock)
    await db.commit()
    await db.refresh(clock)

    _labels = {"in": "Entrada", "out": "Salida", "break_start": "Inicio de pausa", "break_end": "Fin de pausa"}
    return {
        "ok": True,
        "message": f"{matched_emp.name} — {_labels.get(data_type, data_type)} registrada",
        "type": data_type,
        "employee_name": matched_emp.name,
        "time": clock.timestamp.isoformat() if clock.timestamp else None,
        "clock": clock.to_dict(),
    }


@router.get("/history")
async def get_history(
    employee_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tenant_id: Optional[str] = Query(None, description="Solo para super_admin: filtrar por tenant"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Get clock-in history for the current tenant."""
    # Super admin can see all or filter by tenant_id
    if current_user.role == "super_admin" and tenant_id:
        query = select(ClockIn).where(ClockIn.tenant_id == tenant_id)
        count_base = select(ClockIn.id).where(ClockIn.tenant_id == tenant_id)
    elif current_user.role == "super_admin":
        query = select(ClockIn)
        count_base = select(ClockIn.id)
    else:
        tenant_id_val = current_user.tenant_id
        query = select(ClockIn).where(ClockIn.tenant_id == tenant_id_val)
        count_base = select(ClockIn.id).where(ClockIn.tenant_id == tenant_id_val)

    if employee_id:
        query = query.where(ClockIn.employee_id == employee_id)
        count_base = count_base.where(ClockIn.employee_id == employee_id)

    # Date validation
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_from}. Use ISO 8601.")
        query = query.where(ClockIn.timestamp >= dt_from)
        count_base = count_base.where(ClockIn.timestamp >= dt_from)
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_to}. Use ISO 8601.")
        query = query.where(ClockIn.timestamp <= dt_to)
        count_base = count_base.where(ClockIn.timestamp <= dt_to)

    # Count total
    total_result = await db.execute(count_base)
    total = len(total_result.scalars().all())

    query = query.order_by(ClockIn.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    clock_ins = result.scalars().all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [c.to_dict() for c in clock_ins],
    }


@router.get("/today")
async def get_today(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Get all clock-ins for today for the current tenant."""
    tenant_id = current_user.tenant_id
    today_start = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    today_end = datetime.combine(date.today(), time.max, tzinfo=timezone.utc)

    result = await db.execute(
        select(ClockIn).where(
            ClockIn.tenant_id == tenant_id,
            ClockIn.timestamp >= today_start,
            ClockIn.timestamp <= today_end,
        ).order_by(ClockIn.timestamp.desc())
    )
    clock_ins = result.scalars().all()
    return [c.to_dict() for c in clock_ins]


@router.post("/{clock_id}/cancel")
async def cancel_clock(
    clock_id: str,
    data: ClockCancelRequest,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a clock-in (immutable: only cancel, never edit)."""
    result = await db.execute(select(ClockIn).where(ClockIn.id == clock_id))
    clock = result.scalar_one_or_none()
    if not clock:
        raise HTTPException(status_code=404, detail="Fichaje no encontrado")

    if current_user.role != "super_admin" and clock.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if clock.is_cancelled:
        raise HTTPException(status_code=400, detail="Fichaje ya cancelado")

    old_value = clock.to_dict()
    clock.is_cancelled = True
    clock.cancel_reason = data.reason
    clock.cancelled_by = current_user.id
    clock.cancelled_at = datetime.now(timezone.utc)

    # Audit log
    await log_action(
        db,
        tenant_id=clock.tenant_id,
        user_id=current_user.id,
        action="cancel",
        entity_type="clock_in",
        entity_id=clock.id,
        old_value=old_value,
        new_value=clock.to_dict(),
    )

    await db.commit()
    await db.refresh(clock)
    return clock.to_dict()
