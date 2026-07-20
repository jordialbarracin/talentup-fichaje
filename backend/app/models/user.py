"""
TalentUP Fichaje — User model (super_admin, owner, manager).
XSS escaping applied in to_dict() for safe API responses.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="owner")  # super_admin, owner, manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "email": _s(self.email),
            "name": _s(self.name),
            "role": _s(self.role),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
