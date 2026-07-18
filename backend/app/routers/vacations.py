"""
TalentUP Fichaje — Vacations router.
GET/POST /api/vacations, POST /api/vacations/{id}/approve, POST /api/vacations/{id}/reject
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vacation_request import VacationRequest
from app.models.employee import Employee
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/vacations", tags=["vacations"])


class VacationCreate(BaseModel):
    employee_id: str
    type: str = "vacation"
    start_date: str
    end_date: str
    total_days: float
    days_count_method: str = "working"
    reason: Optional[str] = None
    supporting_doc_url: Optional[str] = None


class VacationApproveReject(BaseModel):
    reason: Optional[str] = None


@router.get("")
async def list_vacations(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(VacationRequest)
    if current_user.role != "super_admin":
        query = query.where(VacationRequest.tenant_id == tenant_id)
    if employee_id:
        query = query.where(VacationRequest.employee_id == employee_id)
    if status:
        query = query.where(VacationRequest.status == status)
    query = query.order_by(VacationRequest.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    # Enrich with employee names
    emp_ids = {v.employee_id for v in items}
    emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    emp_map = {e.id: e.name for e in emp_result.scalars().all()}

    data = []
    for v in items:
        d = v.to_dict()
        d["employee_name"] = emp_map.get(v.employee_id, "Desconocido")
        data.append(d)
    return data


@router.get("/{vacation_id}")
async def get_vacation(
    vacation_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VacationRequest).where(VacationRequest.id == vacation_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if current_user.role != "super_admin" and v.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return v.to_dict()


@router.post("", status_code=201)
async def create_vacation(
    data: VacationCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    tenant_id = current_user.tenant_id

    v = VacationRequest(
        tenant_id=tenant_id,
        employee_id=data.employee_id,
        type=data.type,
        start_date=date.fromisoformat(data.start_date),
        end_date=date.fromisoformat(data.end_date),
        total_days=data.total_days,
        days_count_method=data.days_count_method,
        reason=data.reason,
        supporting_doc_url=data.supporting_doc_url,
        status="pending",
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="create", entity_type="vacation_request", entity_id=v.id,
                     new_value=v.to_dict())
    await db.commit()
    return v.to_dict()


@router.post("/{vacation_id}/approve")
async def approve_vacation(
    vacation_id: str,
    data: VacationApproveReject = VacationApproveReject(),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(select(VacationRequest).where(VacationRequest.id == vacation_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if current_user.role != "super_admin" and v.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if v.status != "pending":
        raise HTTPException(status_code=400, detail=f"La solicitud ya está {v.status}")

    v.status = "approved"
    v.approved_by = current_user.id
    v.approved_at = datetime.now(timezone.utc)

    old_value = v.to_dict()
    await db.commit()
    await db.refresh(v)

    await log_action(db, tenant_id=v.tenant_id, user_id=current_user.id,
                     action="approve", entity_type="vacation_request", entity_id=v.id,
                     old_value=old_value, new_value=v.to_dict())
    await db.commit()
    return v.to_dict()


@router.post("/{vacation_id}/reject")
async def reject_vacation(
    vacation_id: str,
    data: VacationApproveReject = VacationApproveReject(),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(select(VacationRequest).where(VacationRequest.id == vacation_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if current_user.role != "super_admin" and v.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if v.status != "pending":
        raise HTTPException(status_code=400, detail=f"La solicitud ya está {v.status}")

    v.status = "rejected"
    v.rejection_reason = data.reason

    old_value = v.to_dict()
    await db.commit()
    await db.refresh(v)

    await log_action(db, tenant_id=v.tenant_id, user_id=current_user.id,
                     action="reject", entity_type="vacation_request", entity_id=v.id,
                     old_value=old_value, new_value=v.to_dict())
    await db.commit()
    return v.to_dict()
