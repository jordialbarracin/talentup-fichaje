"""
TalentUP Fichaje — Payroll router (nóminas).
GET /api/payroll/{month}/{year}, POST /api/payroll/close
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payroll import Payroll
from app.models.employee import Employee
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action
from app.tasks import schedule_payroll_close
from app.pagination import paginate

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


@router.get("")
async def list_payroll(
    year: Optional[int] = None,
    month: Optional[int] = None,
    employee_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(Payroll)
    if current_user.role != "super_admin":
        query = query.where(Payroll.tenant_id == tenant_id)
    if year:
        query = query.where(Payroll.year == year)
    if month:
        query = query.where(Payroll.month == month)
    if employee_id:
        query = query.where(Payroll.employee_id == employee_id)
    query = query.order_by(Payroll.year.desc(), Payroll.month.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    emp_ids = {p.employee_id for p in items}
    emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    emp_map = {e.id: e.name for e in emp_result.scalars().all()}

    data = []
    for p in items:
        d = p.to_dict()
        d["employee_name"] = emp_map.get(p.employee_id, "Desconocido")
        data.append(d)

    page = max(page, 1)
    limit = max(min(limit, 500), 1)
    total = len(data)
    start = (page - 1) * limit
    end = start + limit
    return {
        "items": data[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/{month}/{year}")
async def get_payroll(
    month: int,
    year: int,
    employee_id: Optional[str] = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get payroll for a specific month/year. If employee_id provided, get single record."""
    tenant_id = current_user.tenant_id
    query = select(Payroll).where(
        Payroll.tenant_id == tenant_id,
        Payroll.year == year,
        Payroll.month == month,
    )
    if employee_id:
        query = query.where(Payroll.employee_id == employee_id)
    result = await db.execute(query)
    items = result.scalars().all()

    if employee_id and not items:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")

    emp_ids = {p.employee_id for p in items}
    emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    emp_map = {e.id: e.name for e in emp_result.scalars().all()}

    data = []
    for p in items:
        d = p.to_dict()
        d["employee_name"] = emp_map.get(p.employee_id, "Desconocido")
        data.append(d)
    return data


@router.post("/close")
async def close_payroll(
    month: int,
    year: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate and close payroll for a month. The heavy calculation is executed in
    the background; the request returns immediately with an accepted message.
    """
    from datetime import date

    tenant_id = current_user.tenant_id

    schedule_payroll_close(
        background_tasks,
        tenant_id=str(tenant_id),
        user_id=str(current_user.id),
        month=month,
        year=year,
    )

    await log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="close_payroll_scheduled",
        entity_type="payroll",
        new_value={"month": month, "year": year},
    )
    await db.commit()

    return {
        "month": month,
        "year": year,
        "status": "accepted",
        "message": "Cierre de nóminas encolado para procesamiento en segundo plano.",
    }
