"""
TalentUP Fichaje — Employees router (ampliado con todos los campos nuevos).
GET/POST/PUT/DELETE /api/employees
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.auth import hash_password, compute_pin_hash_fast, require_owner, get_current_user
from app.audit import log_action
from app.pagination import paginate

router = APIRouter(prefix="/api/employees", tags=["employees"])


class EmployeeCreate(BaseModel):
    name: str
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    dni: Optional[str] = None
    nie: Optional[str] = None
    numero_ss: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    categoria_profesional: Optional[str] = None
    tipo_contrato: Optional[str] = None
    fecha_alta: Optional[str] = None
    fecha_baja: Optional[str] = None
    motivo_baja: Optional[str] = None
    tipo_jornada: Optional[str] = None
    horas_semanales: Optional[float] = None
    horas_diarias: Optional[float] = None
    grupo_cotizacion: Optional[str] = None
    base_cotizacion: Optional[float] = None
    pin: str
    nfc_card_id: Optional[str] = None
    nfc_uid: Optional[str] = None
    photo_url: Optional[str] = None
    shift_id: Optional[str] = None
    clock_method: Optional[str] = "pin"
    vacation_annual_days: Optional[float] = 30
    saldo_vacaciones: Optional[float] = 30
    saldo_banco_horas: Optional[float] = 0
    horas_extra_pendientes: Optional[float] = 0
    coste_hora: Optional[float] = None
    iban: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_holder: Optional[str] = None
    education_level: Optional[str] = None
    qualifications: Optional[str] = None
    food_handling_cert: bool = False
    food_handling_expiry: Optional[str] = None
    allergies: Optional[str] = None
    uniform_size: Optional[str] = None
    estado: Optional[str] = "activo"
    is_active: bool = True
    is_available_for_scheduling: bool = True
    employee_code: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    dni: Optional[str] = None
    nie: Optional[str] = None
    numero_ss: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    categoria_profesional: Optional[str] = None
    tipo_contrato: Optional[str] = None
    fecha_alta: Optional[str] = None
    fecha_baja: Optional[str] = None
    motivo_baja: Optional[str] = None
    tipo_jornada: Optional[str] = None
    horas_semanales: Optional[float] = None
    horas_diarias: Optional[float] = None
    grupo_cotizacion: Optional[str] = None
    base_cotizacion: Optional[float] = None
    pin: Optional[str] = None
    nfc_card_id: Optional[str] = None
    nfc_uid: Optional[str] = None
    photo_url: Optional[str] = None
    shift_id: Optional[str] = None
    clock_method: Optional[str] = None
    vacation_annual_days: Optional[float] = None
    saldo_vacaciones: Optional[float] = None
    saldo_banco_horas: Optional[float] = None
    horas_extra_pendientes: Optional[float] = None
    coste_hora: Optional[float] = None
    iban: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_holder: Optional[str] = None
    education_level: Optional[str] = None
    qualifications: Optional[str] = None
    food_handling_cert: Optional[bool] = None
    food_handling_expiry: Optional[str] = None
    allergies: Optional[str] = None
    uniform_size: Optional[str] = None
    estado: Optional[str] = None
    is_active: Optional[bool] = None
    is_available_for_scheduling: Optional[bool] = None
    employee_code: Optional[str] = None


@router.get("")
async def list_employees(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all employees for the current user's tenant."""
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin":
        query = select(Employee)
    else:
        query = select(Employee).where(Employee.tenant_id == tenant_id)

    if search:
        # Literal search only — no SQL interpolation
        query = query.where(Employee.name.ilike(f"%{search}%"))

    query = query.order_by(Employee.name)
    return await paginate(db, query, page, limit, item_transform=lambda e: e.to_dict())


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
    if current_user.role != "super_admin" and emp.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return emp.to_dict()


@router.post("", status_code=201)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee with all fields."""
    from datetime import date
    tenant_id = current_user.tenant_id
    if current_user.role == "super_admin" and not tenant_id:
        raise HTTPException(status_code=400, detail="Super admin debe especificar tenant_id")

    emp = Employee(
        tenant_id=tenant_id,
        name=data.name,
        last_name=data.last_name,
        full_name=data.full_name if data.full_name else (data.name if data.name else None),
        dni=data.dni,
        nie=data.nie,
        numero_ss=data.numero_ss,
        nationality=data.nationality,
        birth_date=date.fromisoformat(data.birth_date) if data.birth_date else None,
        gender=data.gender,
        address=data.address,
        city=data.city,
        province=data.province,
        postal_code=data.postal_code,
        phone=data.phone,
        email=data.email,
        emergency_contact_name=data.emergency_contact_name,
        emergency_contact_phone=data.emergency_contact_phone,
        categoria_profesional=data.categoria_profesional,
        tipo_contrato=data.tipo_contrato,
        fecha_alta=date.fromisoformat(data.fecha_alta) if data.fecha_alta else None,
        fecha_baja=date.fromisoformat(data.fecha_baja) if data.fecha_baja else None,
        motivo_baja=data.motivo_baja,
        tipo_jornada=data.tipo_jornada,
        horas_semanales=data.horas_semanales,
        horas_diarias=data.horas_diarias,
        grupo_cotizacion=data.grupo_cotizacion,
        base_cotizacion=data.base_cotizacion,
        pin_hash=hash_password(data.pin),
        pin_hash_fast=compute_pin_hash_fast(data.pin),
        nfc_card_id=data.nfc_card_id,
        nfc_uid=data.nfc_uid,
        photo_url=data.photo_url,
        shift_id=data.shift_id,
        clock_method=data.clock_method or "pin",
        vacation_annual_days=data.vacation_annual_days or 30,
        saldo_vacaciones=data.saldo_vacaciones or 30,
        saldo_banco_horas=data.saldo_banco_horas or 0,
        horas_extra_pendientes=data.horas_extra_pendientes or 0,
        coste_hora=data.coste_hora,
        iban=data.iban,
        bank_name=data.bank_name,
        bank_account_holder=data.bank_account_holder,
        education_level=data.education_level,
        qualifications=data.qualifications,
        food_handling_cert=data.food_handling_cert,
        food_handling_expiry=date.fromisoformat(data.food_handling_expiry) if data.food_handling_expiry else None,
        allergies=data.allergies,
        uniform_size=data.uniform_size,
        estado=data.estado or "activo",
        is_active=data.is_active,
        is_available_for_scheduling=data.is_available_for_scheduling,
        employee_code=data.employee_code,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

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
    from datetime import date
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if current_user.role != "super_admin" and emp.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if data.name is not None: emp.name = data.name
    if data.last_name is not None: emp.last_name = data.last_name
    if data.full_name is not None: emp.full_name = data.full_name
    if data.dni is not None: emp.dni = data.dni
    if data.nie is not None: emp.nie = data.nie
    if data.numero_ss is not None: emp.numero_ss = data.numero_ss
    if data.nationality is not None: emp.nationality = data.nationality
    if data.birth_date is not None: emp.birth_date = date.fromisoformat(data.birth_date)
    if data.gender is not None: emp.gender = data.gender
    if data.address is not None: emp.address = data.address
    if data.city is not None: emp.city = data.city
    if data.province is not None: emp.province = data.province
    if data.postal_code is not None: emp.postal_code = data.postal_code
    if data.phone is not None: emp.phone = data.phone
    if data.email is not None: emp.email = data.email
    if data.emergency_contact_name is not None: emp.emergency_contact_name = data.emergency_contact_name
    if data.emergency_contact_phone is not None: emp.emergency_contact_phone = data.emergency_contact_phone
    if data.categoria_profesional is not None: emp.categoria_profesional = data.categoria_profesional
    if data.tipo_contrato is not None: emp.tipo_contrato = data.tipo_contrato
    if data.fecha_alta is not None: emp.fecha_alta = date.fromisoformat(data.fecha_alta)
    if data.fecha_baja is not None: emp.fecha_baja = date.fromisoformat(data.fecha_baja)
    if data.motivo_baja is not None: emp.motivo_baja = data.motivo_baja
    if data.tipo_jornada is not None: emp.tipo_jornada = data.tipo_jornada
    if data.horas_semanales is not None: emp.horas_semanales = data.horas_semanales
    if data.horas_diarias is not None: emp.horas_diarias = data.horas_diarias
    if data.grupo_cotizacion is not None: emp.grupo_cotizacion = data.grupo_cotizacion
    if data.base_cotizacion is not None: emp.base_cotizacion = data.base_cotizacion
    if data.pin is not None:
        emp.pin_hash = hash_password(data.pin)
        emp.pin_hash_fast = compute_pin_hash_fast(data.pin)
    if data.nfc_card_id is not None: emp.nfc_card_id = data.nfc_card_id if data.nfc_card_id != "" else None
    if data.nfc_uid is not None: emp.nfc_uid = data.nfc_uid if data.nfc_uid != "" else None
    if data.photo_url is not None: emp.photo_url = data.photo_url
    if data.shift_id is not None: emp.shift_id = data.shift_id
    if data.clock_method is not None: emp.clock_method = data.clock_method
    if data.vacation_annual_days is not None: emp.vacation_annual_days = data.vacation_annual_days
    if data.saldo_vacaciones is not None: emp.saldo_vacaciones = data.saldo_vacaciones
    if data.saldo_banco_horas is not None: emp.saldo_banco_horas = data.saldo_banco_horas
    if data.horas_extra_pendientes is not None: emp.horas_extra_pendientes = data.horas_extra_pendientes
    if data.coste_hora is not None: emp.coste_hora = data.coste_hora
    if data.iban is not None: emp.iban = data.iban
    if data.bank_name is not None: emp.bank_name = data.bank_name
    if data.bank_account_holder is not None: emp.bank_account_holder = data.bank_account_holder
    if data.education_level is not None: emp.education_level = data.education_level
    if data.qualifications is not None: emp.qualifications = data.qualifications
    if data.food_handling_cert is not None: emp.food_handling_cert = data.food_handling_cert
    if data.food_handling_expiry is not None: emp.food_handling_expiry = date.fromisoformat(data.food_handling_expiry)
    if data.allergies is not None: emp.allergies = data.allergies
    if data.uniform_size is not None: emp.uniform_size = data.uniform_size
    if data.estado is not None: emp.estado = data.estado
    if data.is_active is not None: emp.is_active = data.is_active
    if data.is_available_for_scheduling is not None: emp.is_available_for_scheduling = data.is_available_for_scheduling
    if data.employee_code is not None: emp.employee_code = data.employee_code

    old_value = emp.to_dict()
    await db.commit()
    await db.refresh(emp)

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
