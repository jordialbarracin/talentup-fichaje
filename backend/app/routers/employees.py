"""
TalentUP Fichaje — Employees router.
GET/POST/PUT/DELETE /api/employees (con tenant_id aislamiento)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.auth import hash_password, require_owner, get_current_user
from app.audit import log_action

router = APIRouter(prefix="/api/employees", tags=["employees"])


class EmployeeCreate(BaseModel):
    name: str
    dni: Optional[str] = None
    pin: str
    nfc_card_id: Optional[str] = None
    photo_url: Optional[str] = None
    shift_id: Optional[str] = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    dni: Optional[str] = None
    pin: Optional[str] = None
    nfc_card_id: Optional[str] = None
    photo_url: Optional[str] = None
    shift_id: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_employees(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all employees for the current user's tenant."""
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin":
        result = await db.execute(select(Employee))
    else:
        result = await db.execute(
            select(Employee).where(Employee.tenant_id == tenant_id)
        )
    employees = result.scalars().all()
    return [e.to_dict() for e in employees]


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get a single employee."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    # Tenant isolation
    if current_user.role != "super_admin" and emp.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return emp.to_dict()


@router.post("", status_code=201)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee."""
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin" and not tenant_id:
        raise HTTPException(status_code=400, detail="Super admin debe especificar tenant_id")

    emp = Employee(
        tenant_id=tenant_id,
        name=data.name,
        dni=data.dni,
        pin_hash=hash_password(data.pin),
        nfc_card_id=data.nfc_card_id,
        photo_url=data.photo_url,
        shift_id=data.shift_id,
        is_active=data.is_active,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    # Audit log
    await log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        entity_type="employee",
        entity_id=emp.id,
        new_value=emp.to_dict(),
    )
    await db.commit()

    return emp.to_dict()


@router.put("/{employee_id}")
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update an employee."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if current_user.role != "super_admin" and emp.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.name is not None:
        emp.name = data.name
    if data.dni is not None:
        emp.dni = data.dni
    if data.pin is not None:
        emp.pin_hash = hash_password(data.pin)
    if data.nfc_card_id is not None:
        emp.nfc_card_id = data.nfc_card_id
    if data.photo_url is not None:
        emp.photo_url = data.photo_url
    if data.shift_id is not None:
        emp.shift_id = data.shift_id
    if data.is_active is not None:
        emp.is_active = data.is_active

    old_value = emp.to_dict()
    await db.commit()
    await db.refresh(emp)

    # Audit log
    await log_action(
        db,
        tenant_id=emp.tenant_id,
        user_id=current_user.id,
        action="update",
        entity_type="employee",
        entity_id=emp.id,
        old_value=old_value,
        new_value=emp.to_dict(),
    )
    await db.commit()

    return emp.to_dict()


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Delete an employee."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if current_user.role != "super_admin" and emp.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = emp.to_dict()
    await db.execute(delete(Employee).where(Employee.id == employee_id))
    await db.commit()

    # Audit log
    await log_action(
        db,
        tenant_id=emp.tenant_id,
        user_id=current_user.id,
        action="delete",
        entity_type="employee",
        entity_id=emp.id,
        old_value=old_value,
    )
    await db.commit()
    return None
