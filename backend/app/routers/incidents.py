"""
TalentUP Fichaje — Incidents router.
GET /api/incidents (list with filters)
PATCH /api/incidents/{id}/resolve (mark as resolved)
POST /api/incidents/detect (trigger detection in background)
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import Incident
from app.models.employee import Employee
from app.models.user import User
from app.auth import require_manager, get_current_user
from app.audit import log_action
from app.tasks import schedule_incident_detection

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class ResolveRequest(BaseModel):
    resolution: Optional[str] = None


class DetectRequest(BaseModel):
    target_date: Optional[date] = None


@router.get("")
async def list_incidents(
    date_from: Optional[str] = Query(None, description="Filter: start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter: end date (YYYY-MM-DD)"),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """List incidents for the current tenant with optional filters."""
    tenant_id = current_user.tenant_id

    query = select(Incident)
    if current_user.role != "super_admin":
        query = query.where(Incident.tenant_id == tenant_id)
    if date_from:
        query = query.where(Incident.date >= date.fromisoformat(date_from))
    if date_to:
        query = query.where(Incident.date <= date.fromisoformat(date_to))
    if employee_id:
        query = query.where(Incident.employee_id == employee_id)
    if incident_type:
        query = query.where(Incident.incident_type == incident_type)

    query = query.order_by(Incident.date.desc(), Incident.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    # Enrich with employee names
    emp_ids = {i.employee_id for i in items}
    emp_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    emp_map = {e.id: e.name for e in emp_result.scalars().all()}

    data = []
    for i in items:
        d = i.to_dict()
        d["employee_name"] = emp_map.get(i.employee_id, "Desconocido")
        data.append(d)
    return data


@router.post("/detect")
async def detect_incidents_endpoint(
    background_tasks: BackgroundTasks,
    data: DetectRequest = DetectRequest(),
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Trigger incident detection in the background for the current tenant."""
    tenant_id = current_user.tenant_id

    schedule_incident_detection(
        background_tasks,
        tenant_id=str(tenant_id),
        user_id=str(current_user.id),
        target_date=data.target_date,
    )

    await log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="detect_incidents_scheduled",
        entity_type="incident",
        new_value={"target_date": data.target_date.isoformat() if data.target_date else None},
    )
    await db.commit()

    return {
        "status": "accepted",
        "message": "Detección de incidencias encolada para procesamiento en segundo plano.",
        "target_date": data.target_date.isoformat() if data.target_date else None,
    }


@router.patch("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    data: ResolveRequest,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Mark an incident as resolved."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    if current_user.role != "super_admin" and inc.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    old_value = inc.to_dict()
    inc.is_resolved = True
    inc.resolution = data.resolution
    inc.resolved_by = current_user.id
    from datetime import datetime, timezone
    inc.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(inc)

    await log_action(
        db,
        tenant_id=inc.tenant_id,
        user_id=current_user.id,
        action="resolve",
        entity_type="incident",
        entity_id=inc.id,
        old_value=old_value,
        new_value=inc.to_dict(),
    )
    await db.commit()

    return inc.to_dict()
