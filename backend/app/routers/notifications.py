"""
TalentUP Fichaje — Notifications router.
GET/POST /api/notifications, POST /api/notifications/send
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.models.employee import Employee
from app.models.user import User
from app.auth import require_owner, get_current_user
from app.pagination import paginate

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    recipient_type: str = "employee"
    employee_id: Optional[str] = None
    user_id: Optional[str] = None
    type: str
    title: str
    message: str
    priority: str = "normal"
    category: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    sent_via: Optional[str] = "in_app"


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    query = select(Notification).where(
        Notification.tenant_id == tenant_id,
    )
    if unread_only:
        query = query.where(Notification.is_read == False)
    if category:
        query = query.where(Notification.category == category)
    query = query.order_by(Notification.created_at.desc())
    return await paginate(db, query, page, limit, item_transform=lambda n: n.to_dict())


@router.get("/unread")
async def unread_count(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.tenant_id == tenant_id,
            Notification.is_read == False,
        )
    )
    count = result.scalar()
    return {"unread_count": count}


@router.post("", status_code=201)
async def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    tenant_id = current_user.tenant_id

    n = Notification(
        tenant_id=tenant_id,
        recipient_type=data.recipient_type,
        employee_id=data.employee_id,
        user_id=data.user_id,
        type=data.type,
        title=data.title,
        message=data.message,
        priority=data.priority,
        category=data.category,
        action_url=data.action_url,
        action_label=data.action_label,
        sent_via=data.sent_via,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n.to_dict()


@router.post("/send")
async def send_notification(
    data: NotificationCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Alias for create_notification."""
    from datetime import datetime, timezone
    tenant_id = current_user.tenant_id

    n = Notification(
        tenant_id=tenant_id,
        recipient_type=data.recipient_type,
        employee_id=data.employee_id,
        user_id=data.user_id,
        type=data.type,
        title=data.title,
        message=data.message,
        priority=data.priority,
        category=data.category,
        action_url=data.action_url,
        action_label=data.action_label,
        sent_via=data.sent_via or "in_app",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n.to_dict()


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if current_user.role != "super_admin" and n.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    n.is_read = True
    n.read_at = datetime.now(timezone.utc)
    await db.commit()
    return n.to_dict()


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    tenant_id = current_user.tenant_id
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.is_read == False,
        )
    )
    for n in result.scalars().all():
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok", "marked_read": result.rowcount if hasattr(result, 'rowcount') else 0}
