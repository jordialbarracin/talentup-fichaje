"""
TalentUP Fichaje — Audit logging helper.
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    tenant_id: Any,
    user_id: Any,
    action: str,
    entity_type: str,
    entity_id: Any = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> AuditLog:
    """Create an audit log entry and add it to the session (does NOT commit)."""
    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    return log
