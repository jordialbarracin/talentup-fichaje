"""
TalentUP Fichaje — Overtime router (horas extra).
GET/POST /api/overtime, POST /api/overtime/calculate
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.overtime import Overtime
from app.models.employee import Employee
from app.models.clock_in import ClockIn
from app.models.shift import Shift
from app.models.schedule import Schedule
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/overtime", tags=["overtime"])


class OvertimeCreate(BaseModel):
    employee_id: str
    date: str
    shift_id: Optional[str] = None
    overtime_type: str = "structural"
    total_minutes: int
    compensated_minutes: int = 0
    paid_minutes: int = 0
    hourly_rate_multiplier: float = 1.75
    hourly_rate: Optional[float] = None
    overtime_amount: Optional[float] = None
    notes: Optional[str] = None


@router.get("")
async def list_overtime(
    employee_id: Optional[str] = None,
    compensation_type: Optional[str] = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(Overtime)
    if current_user.role != "super_admin":
        query = query.where(Overtime.tenant_id == tenant_id)
    if employee_id:
        query = query.where(Overtime.employee_id == employee_id)
    if compensation_type:
        query = query.where(Overtime.compensation_type == compensation_type)
    query = query.order_by(Overtime.date.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    emp_ids = {o.employee_id for o in items}
    emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    emp_map = {e.id: e.name for e in emp_result.scalars().all()}

    data = []
    for o in items:
        d = o.to_dict()
        d["employee_name"] = emp_map.get(o.employee_id, "Desconocido")
        data.append(d)
    return data


@router.get("/{overtime_id}")
async def get_overtime(
    overtime_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Overtime).where(Overtime.id == overtime_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Hora extra no encontrada")
    if current_user.role != "super_admin" and o.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return o.to_dict()


@router.post("", status_code=201)
async def create_overtime(
    data: OvertimeCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    tenant_id = current_user.tenant_id

    o = Overtime(
        tenant_id=tenant_id,
        employee_id=data.employee_id,
        date=date.fromisoformat(data.date),
        shift_id=data.shift_id,
        overtime_type=data.overtime_type,
        total_minutes=data.total_minutes,
        compensated_minutes=data.compensated_minutes,
        paid_minutes=data.paid_minutes,
        hourly_rate_multiplier=data.hourly_rate_multiplier,
        hourly_rate=data.hourly_rate,
        overtime_amount=data.overtime_amount,
        source="manual",
        notes=data.notes,
    )
    db.add(o)
    await db.commit()
    await db.refresh(o)

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="create", entity_type="overtime", entity_id=o.id,
                     new_value=o.to_dict())
    await db.commit()
    return o.to_dict()


@router.post("/calculate")
async def calculate_overtime(
    employee_id: Optional[str] = None,
    date_from: str = None,
    date_to: str = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate overtime automatically from clock_ins.
    Detects hours worked beyond scheduled shift duration.
    """
    from datetime import date, datetime, time, timedelta, timezone
    tenant_id = current_user.tenant_id

    if not date_from or not date_to:
        raise HTTPException(status_code=400, detail="date_from y date_to son requeridos (YYYY-MM-DD)")

    start_date = date.fromisoformat(date_from)
    end_date = date.fromisoformat(date_to)

    # Get employees
    emp_query = select(Employee).where(Employee.tenant_id == tenant_id, Employee.is_active == True)
    if employee_id:
        emp_query = emp_query.where(Employee.id == employee_id)
    result = await db.execute(emp_query)
    employees = result.scalars().all()

    # Get clock_ins in range
    day_start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    clock_query = select(ClockIn).where(
        ClockIn.tenant_id == tenant_id,
        ClockIn.timestamp >= day_start,
        ClockIn.timestamp <= day_end,
        ClockIn.is_cancelled == False,
    ).order_by(ClockIn.employee_id, ClockIn.timestamp)
    result = await db.execute(clock_query)
    all_clock_ins = result.scalars().all()

    # Get schedules in range
    sched_query = select(Schedule).where(
        Schedule.tenant_id == tenant_id,
        Schedule.date >= start_date,
        Schedule.date <= end_date,
    )
    result = await db.execute(sched_query)
    all_schedules = result.scalars().all()

    # Get shifts
    shift_result = await db.execute(select(Shift).where(Shift.tenant_id == tenant_id))
    all_shifts = {s.id: s for s in shift_result.scalars().all()}

    # Group clock_ins by employee
    from collections import defaultdict
    clock_by_emp = defaultdict(list)
    for ci in all_clock_ins:
        clock_by_emp[ci.employee_id].append(ci)

    # Group schedules by employee+date
    sched_by_emp_date = {}
    for s in all_schedules:
        sched_by_emp_date[(s.employee_id, s.date.isoformat())] = s

    created = []
    for emp in employees:
        emp_clock = clock_by_emp.get(emp.id, [])
        if not emp_clock:
            continue

        # Group by date
        daily_clock = defaultdict(list)
        for ci in emp_clock:
            daily_clock[ci.timestamp.date().isoformat()].append(ci)

        for day_str, day_clock in daily_clock.items():
            day_date = date.fromisoformat(day_str)

            # Get shift for this day
            sched = sched_by_emp_date.get((emp.id, day_str))
            shift_id = sched.shift_id if sched else emp.shift_id
            if not shift_id:
                continue
            shift = all_shifts.get(shift_id)
            if not shift:
                continue

            # Calculate worked hours
            first_in = None
            last_out = None
            for ci in day_clock:
                if ci.type == "in":
                    if first_in is None or ci.timestamp < first_in:
                        first_in = ci.timestamp
                elif ci.type == "out":
                    if last_out is None or ci.timestamp > last_out:
                        last_out = ci.timestamp

            if not first_in or not last_out:
                continue

            worked_seconds = (last_out - first_in).total_seconds()
            if shift.break_min:
                worked_seconds -= shift.break_min * 60

            # Shift duration
            start_m = shift.start_time.hour * 60 + shift.start_time.minute
            end_m = shift.end_time.hour * 60 + shift.end_time.minute
            if end_m <= start_m:
                end_m += 24 * 60
            shift_duration_min = end_m - start_m
            worked_min = worked_seconds / 60

            extra_min = worked_min - shift_duration_min
            if extra_min > 0 and extra_min > (shift.overtime_threshold_min or 0):
                # Check if already exists
                existing = await db.execute(
                    select(Overtime).where(
                        Overtime.tenant_id == tenant_id,
                        Overtime.employee_id == emp.id,
                        Overtime.date == day_date,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                o = Overtime(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    date=day_date,
                    shift_id=shift_id,
                    overtime_type="structural",
                    total_minutes=int(extra_min),
                    source="auto",
                )
                db.add(o)
                created.append(o)

    await db.flush()
    return {"created": len(created), "details": [{"employee_id": str(c.employee_id), "date": c.date.isoformat(), "minutes": c.total_minutes} for c in created]}
