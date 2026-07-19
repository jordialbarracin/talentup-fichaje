"""
TalentUP Fichaje — Contracts router.
GET/POST/PUT/DELETE /api/contracts
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contract import Contract
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.audit import log_action
from app.pagination import paginate

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


class ContractCreate(BaseModel):
    employee_id: str
    contract_type: str
    category: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    is_indefinite: bool = False
    renewal_number: int = 0
    previous_contract_id: Optional[str] = None
    work_day_type: Optional[str] = None
    weekly_hours: Optional[float] = None
    daily_hours: Optional[float] = None
    salary_base: Optional[float] = None
    salary_extras: Optional[float] = None
    prorated_pages: Optional[float] = None
    document_url: Optional[str] = None
    signed_date: Optional[str] = None
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    contract_type: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    is_indefinite: Optional[bool] = None
    renewal_number: Optional[int] = None
    work_day_type: Optional[str] = None
    weekly_hours: Optional[float] = None
    daily_hours: Optional[float] = None
    salary_base: Optional[float] = None
    salary_extras: Optional[float] = None
    prorated_pages: Optional[float] = None
    document_url: Optional[str] = None
    signed_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    termination_date: Optional[str] = None
    termination_reason: Optional[str] = None


@router.get("")
async def list_contracts(
    employee_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all contracts for the current user's tenant."""
    tenant_id = current_user.tenant_id
    query = select(Contract)
    if current_user.role != "super_admin":
        query = query.where(Contract.tenant_id == tenant_id)
    if employee_id:
        query = query.where(Contract.employee_id == employee_id)
    query = query.order_by(Contract.start_date.desc())
    return await paginate(db, query, page, limit, item_transform=lambda c: c.to_dict())


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if current_user.role != "super_admin" and contract.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return contract.to_dict()


@router.post("", status_code=201)
async def create_contract(
    data: ContractCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin" and not tenant_id:
        raise HTTPException(status_code=400, detail="Super admin debe especificar tenant_id")

    contract = Contract(
        tenant_id=tenant_id,
        employee_id=data.employee_id,
        contract_type=data.contract_type,
        category=data.category,
        start_date=date.fromisoformat(data.start_date) if data.start_date else None,
        end_date=date.fromisoformat(data.end_date) if data.end_date else None,
        duration_days=data.duration_days,
        is_indefinite=data.is_indefinite,
        renewal_number=data.renewal_number,
        previous_contract_id=data.previous_contract_id,
        work_day_type=data.work_day_type,
        weekly_hours=data.weekly_hours,
        daily_hours=data.daily_hours,
        salary_base=data.salary_base,
        salary_extras=data.salary_extras,
        prorated_pages=data.prorated_pages,
        document_url=data.document_url,
        signed_date=date.fromisoformat(data.signed_date) if data.signed_date else None,
        notes=data.notes,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    await log_action(db, tenant_id=tenant_id, user_id=current_user.id,
                     action="create", entity_type="contract", entity_id=contract.id,
                     new_value=contract.to_dict())
    await db.commit()
    return contract.to_dict()


@router.put("/{contract_id}")
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if current_user.role != "super_admin" and contract.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.contract_type is not None: contract.contract_type = data.contract_type
    if data.category is not None: contract.category = data.category
    if data.start_date is not None: contract.start_date = date.fromisoformat(data.start_date)
    if data.end_date is not None: contract.end_date = date.fromisoformat(data.end_date)
    if data.duration_days is not None: contract.duration_days = data.duration_days
    if data.is_indefinite is not None: contract.is_indefinite = data.is_indefinite
    if data.renewal_number is not None: contract.renewal_number = data.renewal_number
    if data.work_day_type is not None: contract.work_day_type = data.work_day_type
    if data.weekly_hours is not None: contract.weekly_hours = data.weekly_hours
    if data.daily_hours is not None: contract.daily_hours = data.daily_hours
    if data.salary_base is not None: contract.salary_base = data.salary_base
    if data.salary_extras is not None: contract.salary_extras = data.salary_extras
    if data.prorated_pages is not None: contract.prorated_pages = data.prorated_pages
    if data.document_url is not None: contract.document_url = data.document_url
    if data.signed_date is not None: contract.signed_date = date.fromisoformat(data.signed_date)
    if data.notes is not None: contract.notes = data.notes
    if data.status is not None: contract.status = data.status
    if data.termination_date is not None: contract.termination_date = date.fromisoformat(data.termination_date)
    if data.termination_reason is not None: contract.termination_reason = data.termination_reason

    old_value = contract.to_dict()
    await db.commit()
    await db.refresh(contract)

    await log_action(db, tenant_id=contract.tenant_id, user_id=current_user.id,
                     action="update", entity_type="contract", entity_id=contract.id,
                     old_value=old_value, new_value=contract.to_dict())
    await db.commit()
    return contract.to_dict()


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if current_user.role != "super_admin" and contract.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = contract.to_dict()
    await db.execute(delete(Contract).where(Contract.id == contract_id))
    await db.commit()

    await log_action(db, tenant_id=contract.tenant_id, user_id=current_user.id,
                     action="delete", entity_type="contract", entity_id=contract.id,
                     old_value=old_value)
    await db.commit()
    return None
