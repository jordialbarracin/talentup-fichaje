"""
TalentUP Fichaje — Calendar router (calendario laboral).
GET/POST /api/calendar
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.work_calendar import WorkCalendar
from app.models.holiday import Holiday
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action
from app.pagination import paginate

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class CalendarDayUpdate(BaseModel):
    day_type: Optional[str] = None
    is_working_day: Optional[bool] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    requires_special_schedule: Optional[bool] = None
    notes: Optional[str] = None


@router.get("")
async def get_calendar(
    year: int,
    page: int = Query(1, ge=1),
    limit: int = Query(366, ge=1, le=500),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get work calendar for a given year."""
    tenant_id = current_user.tenant_id
    query = select(WorkCalendar).where(
        WorkCalendar.tenant_id == tenant_id,
        WorkCalendar.year == year,
    ).order_by(WorkCalendar.date)
    return await paginate(db, query, page, limit, item_transform=lambda d: d.to_dict())


@router.post("/generate")
async def generate_calendar(
    year: int,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Generate work calendar for a year, marking weekends and holidays."""
    from datetime import date, time, timedelta
    tenant_id = current_user.tenant_id

    # Check if already exists
    existing = await db.execute(
        select(WorkCalendar).where(
            WorkCalendar.tenant_id == tenant_id,
            WorkCalendar.year == year,
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Calendario para {year} ya existe")

    # Get holidays for this year
    result = await db.execute(
        select(Holiday).where(
            Holiday.tenant_id == tenant_id,
            Holiday.year == year,
        )
    )
    holidays = result.scalars().all()
    holiday_dates = {h.date: h for h in holidays}

    # Generate all days of the year
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    current = start
    days = []
    while current <= end:
        is_weekend = current.weekday() >= 5  # Saturday=5, Sunday=6
        is_holiday = current in holiday_dates
        holiday = holiday_dates.get(current)

        day = WorkCalendar(
            tenant_id=tenant_id,
            year=year,
            date=current,
            day_type="holiday" if is_holiday else ("weekend" if is_weekend else "working"),
            is_working_day=not is_weekend and not is_holiday,
            is_holiday=is_holiday,
            is_weekend=is_weekend,
            holiday_id=holiday.id if holiday else None,
            holiday_name=holiday.name if holiday else None,
        )
        days.append(day)
        current += timedelta(days=1)

    for d in days:
        db.add(d)
    await db.flush()

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="generate_calendar", entity_type="work_calendar",
                     new_value={"year": year, "days": len(days)})
    await db.commit()

    return {"year": year, "days_generated": len(days)}


@router.put("/{calendar_id}")
async def update_calendar_day(
    calendar_id: str,
    data: CalendarDayUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import time
    result = await db.execute(select(WorkCalendar).where(WorkCalendar.id == calendar_id))
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Día no encontrado")
    if current_user.role != "super_admin" and day.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.day_type is not None: day.day_type = data.day_type
    if data.is_working_day is not None: day.is_working_day = data.is_working_day
    if data.opening_time is not None:
        h, m = map(int, data.opening_time.split(":"))
        day.opening_time = time(h, m)
    if data.closing_time is not None:
        h, m = map(int, data.closing_time.split(":"))
        day.closing_time = time(h, m)
    if data.requires_special_schedule is not None: day.requires_special_schedule = data.requires_special_schedule
    if data.notes is not None: day.notes = data.notes

    await db.commit()
    await db.refresh(day)
    return day.to_dict()
