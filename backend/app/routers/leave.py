"""
TalentUP Fichaje — Leave router (bajas IT).
GET/POST/PUT/DELETE /api/leave
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.leave import Leave
from app.models.employee import Employee
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action
from app.pagination import paginate

router = APIRouter(prefix="/api/leave", tags=["leave"])


class LeaveCreate(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: Optional[str] = None
    expected_end_date: Optional[str] = None
    total_days: Optional[int] = None
    diagnosis_code: Optional[str] = None
    medical_center: Optional[str] = None
    doctor_name: Optional[str] = None
    part_number: Optional[str] = None
    mutua: Optional[str] = None
    is_work_accident: bool = False
    is_professional_illness: bool = False
    document_url: Optional[str] = None


class LeaveUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    expected_end_date: Optional[str] = None
    total_days: Optional[int] = None
    diagnosis_code: Optional[str] = None
    medical_center: Optional[str] = None
    doctor_name: Optional[str] = None
    part_number: Optional[str] = None
    mutua: Optional[str] = None
    is_work_accident: Optional[bool] = None
    is_professional_illness: Optional[bool] = None
    document_url: Optional[str] = None
    status: Optional[str] = None
    extension_count: Optional[int] = None
    notified_to_employee: Optional[bool] = None
    notified_to_ss: Optional[bool] = None
    ss_communication_date: Optional[str] = None


@router.get("")
async def list_leave(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(Leave)
    if current_user.role != "super_admin":
        query = query.where(Leave.tenant_id == tenant_id)
    if employee_id:
        query = query.where(Leave.employee_id == employee_id)
    if status:
        query = query.where(Leave.status == status)
    query = query.order_by(Leave.start_date.desc())
    page_result = await paginate(
        db, query, page, limit,
        item_transform=lambda l: l.to_dict(),
    )
    items = page_result["items"]
    emp_ids = {l.get("employee_id") for l in items if l.get("employee_id")}
    if emp_ids:
        emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
        emp_map = {e.id: e.name for e in emp_result.scalars().all()}
        for l in items:
            l["employee_name"] = emp_map.get(l.get("employee_id"), "Desconocido")
    else:
        for l in items:
            l["employee_name"] = "Desconocido"
    return page_result


@router.get("/{leave_id}")
async def get_leave(
    leave_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    l = result.scalar_one_or_none()
    if not l:
        raise HTTPException(status_code=404, detail="Baja no encontrada")
    if current_user.role != "super_admin" and l.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return l.to_dict()


@router.post("", status_code=201)
async def create_leave(
    data: LeaveCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    tenant_id = current_user.tenant_id

    l = Leave(
        tenant_id=tenant_id,
        employee_id=data.employee_id,
        leave_type=data.leave_type,
        type=data.leave_type,
        start_date=date.fromisoformat(data.start_date),
        end_date=date.fromisoformat(data.end_date) if data.end_date else None,
        expected_end_date=date.fromisoformat(data.expected_end_date) if data.expected_end_date else None,
        total_days=data.total_days,
        diagnosis_code=data.diagnosis_code,
        medical_center=data.medical_center,
        doctor_name=data.doctor_name,
        part_number=data.part_number,
        mutua=data.mutua,
        is_work_accident=data.is_work_accident,
        is_professional_illness=data.is_professional_illness,
        document_url=data.document_url,
        created_by=current_user.id,
    )
    db.add(l)
    await db.commit()
    await db.refresh(l)

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="create", entity_type="leave", entity_id=l.id,
                     new_value=l.to_dict())
    await db.commit()
    return l.to_dict()


@router.put("/{leave_id}")
async def update_leave(
    leave_id: str,
    data: LeaveUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    l = result.scalar_one_or_none()
    if not l:
        raise HTTPException(status_code=404, detail="Baja no encontrada")
    if current_user.role != "super_admin" and l.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.leave_type is not None: l.leave_type = data.leave_type
    if data.start_date is not None: l.start_date = date.fromisoformat(data.start_date)
    if data.end_date is not None: l.end_date = date.fromisoformat(data.end_date)
    if data.expected_end_date is not None: l.expected_end_date = date.fromisoformat(data.expected_end_date)
    if data.total_days is not None: l.total_days = data.total_days
    if data.diagnosis_code is not None: l.diagnosis_code = data.diagnosis_code
    if data.medical_center is not None: l.medical_center = data.medical_center
    if data.doctor_name is not None: l.doctor_name = data.doctor_name
    if data.part_number is not None: l.part_number = data.part_number
    if data.mutua is not None: l.mutua = data.mutua
    if data.is_work_accident is not None: l.is_work_accident = data.is_work_accident
    if data.is_professional_illness is not None: l.is_professional_illness = data.is_professional_illness
    if data.document_url is not None: l.document_url = data.document_url
    if data.status is not None: l.status = data.status
    if data.extension_count is not None: l.extension_count = data.extension_count
    if data.notified_to_employee is not None: l.notified_to_employee = data.notified_to_employee
    if data.notified_to_ss is not None: l.notified_to_ss = data.notified_to_ss
    if data.ss_communication_date is not None: l.ss_communication_date = date.fromisoformat(data.ss_communication_date)

    old_value = l.to_dict()
    await db.commit()
    await db.refresh(l)

    await log_action(db, tenant_id=l.tenant_id, user_id=current_user.id,
                     action="update", entity_type="leave", entity_id=l.id,
                     old_value=old_value, new_value=l.to_dict())
    await db.commit()
    return l.to_dict()


@router.delete("/{leave_id}", status_code=204)
async def delete_leave(
    leave_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    l = result.scalar_one_or_none()
    if not l:
        raise HTTPException(status_code=404, detail="Baja no encontrada")
    if current_user.role != "super_admin" and l.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = l.to_dict()
    await db.execute(delete(Leave).where(Leave.id == leave_id))
    await db.commit()

    await log_action(db, tenant_id=l.tenant_id, user_id=current_user.id,
                     action="delete", entity_type="leave", entity_id=l.id,
                     old_value=old_value)
    await db.commit()
    return None
