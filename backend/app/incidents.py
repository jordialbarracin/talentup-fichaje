"""
TalentUP Fichaje — Incident detection logic.
Auto-detects: no_clock_in, late, early_leave, extra_hours.
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.shift import Shift
from app.models.schedule import Schedule
from app.models.clock_in import ClockIn
from app.models.incident import Incident


async def detect_incidents(
    db: AsyncSession,
    tenant_id,
    target_date: date = None,
) -> List[Incident]:
    """
    Run all incident detection rules for a given tenant and date.
    Returns the list of newly created incidents.
    """
    if target_date is None:
        target_date = date.today()

    new_incidents: List[Incident] = []

    # Get all active employees for this tenant
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.is_active == True,
        )
    )
    employees = result.scalars().all()

    # Get all schedules for this date
    result = await db.execute(
        select(Schedule).where(
            Schedule.tenant_id == tenant_id,
            Schedule.date == target_date,
        )
    )
    schedules = result.scalars().all()

    # Build a map: employee_id -> schedule
    schedule_map = {s.employee_id: s for s in schedules}

    # Get all clock_ins for this date
    day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
    result = await db.execute(
        select(ClockIn).where(
            ClockIn.tenant_id == tenant_id,
            ClockIn.timestamp >= day_start,
            ClockIn.timestamp <= day_end,
            ClockIn.is_cancelled == False,
        )
    )
    clock_ins = result.scalars().all()

    # Build clock_in map: employee_id -> list of clock_ins
    clock_map: dict = {}
    for ci in clock_ins:
        clock_map.setdefault(ci.employee_id, []).append(ci)

    # Get existing incidents for this date to avoid duplicates
    result = await db.execute(
        select(Incident).where(
            Incident.tenant_id == tenant_id,
            Incident.date == target_date,
        )
    )
    existing = result.scalars().all()
    existing_set = {(e.employee_id, e.type) for e in existing}

    for emp in employees:
        emp_clock = clock_map.get(emp.id, [])
        emp_schedule = schedule_map.get(emp.id)

        # --- no_clock_in: employee has a schedule but no clock-in ---
        if emp_schedule and not emp_clock:
            if (emp.id, "no_clock_in") not in existing_set:
                inc = Incident(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    date=target_date,
                    type="no_clock_in",
                    description=f"{emp.name} no fichó el {target_date}",
                    severity="error",
                )
                db.add(inc)
                new_incidents.append(inc)
                existing_set.add((emp.id, "no_clock_in"))

        if not emp_clock:
            continue

        # Get the shift for this employee (from schedule or default shift)
        shift_id = emp_schedule.shift_id if emp_schedule else emp.shift_id
        if not shift_id:
            continue

        result = await db.execute(select(Shift).where(Shift.id == shift_id))
        shift = result.scalar_one_or_none()
        if not shift:
            continue

        tolerance = shift.tolerance_min or 5

        # Find first "in" and last "out" for the day
        first_in = None
        last_out = None
        for ci in emp_clock:
            if ci.type == "in":
                if first_in is None or ci.timestamp < first_in:
                    first_in = ci.timestamp
            elif ci.type == "out":
                if last_out is None or ci.timestamp > last_out:
                    last_out = ci.timestamp

        # --- late: first clock-in after start_time + tolerance ---
        if first_in and shift.start_time:
            scheduled_start = datetime.combine(
                target_date, shift.start_time, tzinfo=timezone.utc
            )
            grace_end = scheduled_start + timedelta(minutes=tolerance)
            if first_in > grace_end:
                if (emp.id, "late") not in existing_set:
                    late_min = int((first_in - scheduled_start).total_seconds() / 60)
                    inc = Incident(
                        tenant_id=tenant_id,
                        employee_id=emp.id,
                        date=target_date,
                        type="late",
                        description=f"{emp.name} fichó {late_min} min tarde (tolerancia: {tolerance} min)",
                        severity="warning",
                    )
                    db.add(inc)
                    new_incidents.append(inc)
                    existing_set.add((emp.id, "late"))

        # --- early_leave: last clock-out before end_time - tolerance ---
        if last_out and shift.end_time:
            scheduled_end = datetime.combine(
                target_date, shift.end_time, tzinfo=timezone.utc
            )
            # Handle overnight shifts (end_time < start_time means next day)
            if shift.end_time < shift.start_time:
                scheduled_end += timedelta(days=1)
            grace_start = scheduled_end - timedelta(minutes=tolerance)
            if last_out < grace_start:
                if (emp.id, "early_leave") not in existing_set:
                    early_min = int((scheduled_end - last_out).total_seconds() / 60)
                    inc = Incident(
                        tenant_id=tenant_id,
                        employee_id=emp.id,
                        date=target_date,
                        type="early_leave",
                        description=f"{emp.name} salió {early_min} min antes (tolerancia: {tolerance} min)",
                        severity="warning",
                    )
                    db.add(inc)
                    new_incidents.append(inc)
                    existing_set.add((emp.id, "early_leave"))

        # --- extra_hours: worked more than shift duration + 2h ---
        if first_in and last_out:
            worked_seconds = (last_out - first_in).total_seconds()
            # Subtract break time
            if shift.break_min:
                worked_seconds -= shift.break_min * 60
            shift_duration = get_shift_duration_hours(shift)
            max_allowed = shift_duration + 2  # 2 hours extra max
            worked_hours = worked_seconds / 3600
            if worked_hours > max_allowed:
                if (emp.id, "extra_hours") not in existing_set:
                    extra = round(worked_hours - shift_duration, 1)
                    inc = Incident(
                        tenant_id=tenant_id,
                        employee_id=emp.id,
                        date=target_date,
                        type="extra_hours",
                        description=f"{emp.name} trabajó {extra}h extra (turno: {shift_duration}h, real: {worked_hours:.1f}h)",
                        severity="warning",
                    )
                    db.add(inc)
                    new_incidents.append(inc)
                    existing_set.add((emp.id, "extra_hours"))

        # --- no_break: worked more than 6 hours without a break ---
        if first_in and last_out:
            worked_seconds = (last_out - first_in).total_seconds()
            # Check if there was any break_start/break_end pair
            had_break = False
            break_start_time = None
            for ci in emp_clock:
                if ci.type == "break_start":
                    break_start_time = ci.timestamp
                elif ci.type == "break_end" and break_start_time:
                    had_break = True
                    break_start_time = None
            # Also check if there's an active break (break_start without break_end)
            if break_start_time:
                had_break = True  # currently on break, counts as having one

            if worked_seconds > 6 * 3600 and not had_break:
                if (emp.id, "no_break") not in existing_set:
                    worked_hours = worked_seconds / 3600
                    inc = Incident(
                        tenant_id=tenant_id,
                        employee_id=emp.id,
                        date=target_date,
                        type="no_break",
                        description=f"{emp.name} trabajó {worked_hours:.1f}h sin pausa (máx. 6h sin descanso)",
                        severity="warning",
                    )
                    db.add(inc)
                    new_incidents.append(inc)
                    existing_set.add((emp.id, "no_break"))

    await db.flush()
    return new_incidents


def get_shift_duration_hours(shift: Shift) -> float:
    """Calculate shift duration in hours, handling overnight shifts."""
    start = shift.start_time
    end = shift.end_time
    start_min = start.hour * 60 + start.minute
    end_min = end.hour * 60 + end.minute
    if end_min <= start_min:
        end_min += 24 * 60  # overnight
    duration_min = end_min - start_min
    return duration_min / 60
