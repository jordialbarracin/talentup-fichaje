"""
TalentUP Fichaje — Clock router.
POST /api/clock (PIN), /api/clock/nfc, /api/clock/qr, GET /api/clock/history, GET /api/clock/today
NFC and QR endpoints require a valid device token.
"""
import hashlib
import json
import time as time_module
from datetime import date, datetime, time, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.clock_in import ClockIn
from app.models.employee import Employee
from app.models.user import User
from app.models.device import Device
from app.models.tenant import Tenant
from app.auth import verify_password, compute_pin_hash_fast, require_manager, get_current_user, decode_token
from app.audit import log_action
from app.pagination import paginate
from app.rate_limiter import (
    check_rate_limit,
    record_rate,
    _cleanup_and_check,
    _record,
    _pin_limits,
    _nfc_limits,
    _qr_limits,
    CLOCK_MAX_PER_MINUTE,
    PIN_FAIL_MAX_PER_MINUTE,
    PIN_BLOCK_MINUTES,
    WINDOW_SECONDS,
    check_pin_block,
    record_pin_failure,
    is_pin_blocked,
    _rate_limit_key as _build_rate_limit_key,
)

router = APIRouter(prefix="/api/clock", tags=["clock"])

# --- Device token dependency ---
DEVICE_TOKEN_HEADER = "Authorization"
DEVICE_TOKEN_PREFIX = "Bearer "


async def require_device_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate the Authorization: Bearer *** header.
    Returns the matching Device (belongs to the request tenant_id in body).
    Raises 401 if missing/invalid and 403 if the device is disabled.
    """
    auth_header = request.headers.get(DEVICE_TOKEN_HEADER, "")
    if not auth_header.startswith(DEVICE_TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autorización requerida: Authorization: Bearer ***",
        )

    token = auth_header[len(DEVICE_TOKEN_PREFIX):].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device token vacío",
        )

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    # Body not yet parsed here; peek the raw JSON for tenant_id. Fast enough for small posts.
    body = await request.body()
    tenant_id = None
    if body:
        try:
            json_body = json.loads(body)
            tenant_id = json_body.get("tenant_id")
        except Exception:
            pass

    result = await db.execute(
        select(Device).where(
            Device.device_token == token_hash,
            Device.is_active == True,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device token no válido",
        )

    if tenant_id and str(device.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device token no pertenece a este tenant",
        )

    return device


# --- Public tenant list for PWA mobile ---
@router.get("/tenants")
async def list_tenants_public(db: AsyncSession = Depends(get_db)):
    """Public endpoint for PWA mobile to list available restaurants."""
    result = await db.execute(select(Tenant.id, Tenant.name))
    rows = result.all()
    return [{"id": str(r[0]), "name": r[1]} for r in rows]


# --- Rate limiting helpers (async, Redis-aware with in-memory fallback) ---
def _rate_limit_key(request: Request, tenant_id: Optional[str]) -> str:
    """Build rate-limit key from IP and tenant."""
    return _build_rate_limit_key(request, tenant_id)


async def _check_method_limit(store: dict, key: str, max_count: int, method: str) -> bool:
    """Async check: Redis when available, otherwise in-memory store."""
    allowed = await check_rate_limit(key, max_count, WINDOW_SECONDS, method=method)
    if not allowed:
        return False
    # Keep per-method memory stores accurate when Redis is disabled.
    if _get_redis_client() is None:
        return _cleanup_and_check(store, key, max_count)
    return True


async def _record_method(store: dict, key: str, method: str):
    """Async record: Redis when available, otherwise in-memory store."""
    await record_rate(key, method=method)
    if _get_redis_client() is None:
        _record(store, key)


def _get_redis_client():
    """Re-export redis-aware helper from rate_limiter."""
    from app.rate_limiter import _get_redis_client as _rl_redis

    return _rl_redis()


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

    # --- Rate limiting by IP+tenant_id, independently for PIN attempts ---
    rate_key = _rate_limit_key(request, data.tenant_id)

    # Check PIN block
    blocked, remaining = await is_pin_blocked(rate_key)
    if blocked:
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados intentos fallidos. Bloqueado {PIN_BLOCK_MINUTES} min. Reintenta en {remaining}s.",
            headers={"Retry-After": str(remaining)},
        )

    # Check PIN clock rate limit (independent from NFC/QR)
    if not await _check_method_limit(_pin_limits, rate_key, CLOCK_MAX_PER_MINUTE, "pin"):
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados fichajes por PIN. Máximo {CLOCK_MAX_PER_MINUTE} por minuto.",
            headers={"Retry-After": "60"},
        )

    # Find employee by PIN within the tenant using indexed pin_hash_fast
    pin_fast = compute_pin_hash_fast(data.pin)
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == data.tenant_id,
            Employee.pin_hash_fast == pin_fast,
            Employee.is_active == True,
        )
    )
    matched_emp = result.scalar_one_or_none()

    # Double-check with bcrypt verify to be safe (defense in depth)
    if matched_emp and not verify_password(data.pin, matched_emp.pin_hash):
        matched_emp = None

    if not matched_emp:
        # Record PIN failure
        should_block = await record_pin_failure(rate_key)
        if should_block:
            _, remaining = await is_pin_blocked(rate_key)
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados PINs erróneos. Bloqueado {PIN_BLOCK_MINUTES} minutos.",
                headers={"Retry-After": str(remaining)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto",
        )

    # Record the clock action for PIN rate limiting
    await _record_method(_pin_limits, rate_key, "pin")

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
    rate_key = _rate_limit_key(request, data.tenant_id)

    if not await _check_method_limit(_nfc_limits, rate_key, CLOCK_MAX_PER_MINUTE, "nfc"):
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados fichajes. Máximo {CLOCK_MAX_PER_MINUTE} por minuto.",
            headers={"Retry-After": "60"},
        )

    # Find employee by nfc_uid within the tenant (normalize UID: accept with or without colons)
    normalized_uid = data.nfc_uid.replace(":", "").upper()
    # Build colon format from normalized: "A1B2C3D4" → "A1:B2:C3:D4"
    colon_uid = ":".join(normalized_uid[i:i+2] for i in range(0, len(normalized_uid), 2))
    # Search with both the original and the colon format
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == data.tenant_id,
            or_(
                Employee.nfc_uid == data.nfc_uid,
                Employee.nfc_uid == normalized_uid,
                Employee.nfc_uid == colon_uid,
            ),
            Employee.is_active == True,
        )
    )
    matched_emp = result.scalars().first()

    if not matched_emp:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta NFC no registrada",
        )

    # Record the clock action for rate limiting
    await _record_method(_nfc_limits, rate_key, "nfc")

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

    # Broadcast NFC event to all connected WebSocket clients
    event = {
        "type": "nfc_read",
        "uid": data.nfc_uid,
        "employee": matched_emp.name,
        "action": data_type,
        "time": clock.timestamp.strftime("%H:%M") if clock.timestamp else None,
    }
    # Fire-and-forget broadcast as a tracked task; avoid orphan ensure_future tasks
    # that can accumulate and saturate the event loop during long test suites.
    nfc_broadcast_task = asyncio.create_task(nfc_manager.broadcast(event))
    # Keep a weak reference so the task is not garbage-collected mid-flight.
    # The router module is long-lived, so a small set of recent tasks is fine.
    _pending_nfc_broadcasts.add(nfc_broadcast_task)
    nfc_broadcast_task.add_done_callback(_pending_nfc_broadcasts.discard)

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
    # --- Rate limiting by IP+tenant_id (same as PIN endpoint) ---
    rate_key = _rate_limit_key(request, data.tenant_id)

    if not await _check_method_limit(_qr_limits, rate_key, CLOCK_MAX_PER_MINUTE, "qr"):
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

    await _record_method(_qr_limits, rate_key, "qr")

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
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated clock-in history for the current tenant."""
    # Super admin can see all or filter by tenant_id
    if current_user.role == "super_admin" and tenant_id:
        query = select(ClockIn).where(ClockIn.tenant_id == tenant_id)
    elif current_user.role == "super_admin":
        query = select(ClockIn)
    else:
        tenant_id_val = current_user.tenant_id
        query = select(ClockIn).where(ClockIn.tenant_id == tenant_id_val)

    if employee_id:
        query = query.where(ClockIn.employee_id == employee_id)

    # Date validation
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_from}. Use ISO 8601.")
        query = query.where(ClockIn.timestamp >= dt_from)
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_to}. Use ISO 8601.")
        query = query.where(ClockIn.timestamp <= dt_to)

    query = query.order_by(ClockIn.timestamp.desc())
    return await paginate(db, query, page, limit, item_transform=lambda c: c.to_dict())


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


# ===== NFC WebSocket Manager =====
import asyncio
import json

# Track in-flight NFC broadcast tasks so they are not garbage-collected
# while running, preventing event-loop saturation in long test runs.
_pending_nfc_broadcasts: set[asyncio.Task] = set()

class NfcWebSocketManager:
    """Manages WebSocket connections for real-time NFC reader status."""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, event: dict):
        """Send an event to all connected WebSocket clients."""
        dead: list[WebSocket] = []
        async with self._lock:
            for ws in self._connections:
                try:
                    await ws.send_json(event)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._connections.discard(ws)

    @property
    def connected_count(self) -> int:
        return len(self._connections)


nfc_manager = NfcWebSocketManager()

# Separate router for NFC WebSocket (no /api/clock prefix)
ws_router = APIRouter(tags=["nfc_ws"])


@ws_router.websocket("/ws/nfc")
async def nfc_websocket(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for real-time NFC reader status.
    Requires a valid JWT access token from the 'access_token' cookie or ?token= query param.
    Rejects unauthenticated connections with code 1008.
    """
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Autenticación requerida")
        return

    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=1008, reason="Token inválido o expirado")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Token inválido")
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        await websocket.close(code=1008, reason="Usuario no encontrado o inactivo")
        return

    # Enforce manager+ role for NFC WebSocket access
    if user.role not in ("super_admin", "owner", "manager"):
        await websocket.close(code=1008, reason="Permisos insuficientes")
        return

    await nfc_manager.connect(websocket)
    try:
        # Send initial connected status
        await websocket.send_json({
            "type": "nfc_connected",
            "message": "Lector NFC conectado"
        })
        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                # Client can send ping to keep alive
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
    except Exception:
        pass
    finally:
        await nfc_manager.disconnect(websocket)
