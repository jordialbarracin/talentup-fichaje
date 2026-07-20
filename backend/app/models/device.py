from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import hashlib


def _hash_token(token: str) -> str:
    """Return SHA-256 hash of a device token for storage/comparison."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    import html
    if value is None:
        return None
    return html.escape(str(value))


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    device_token = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "device_token": _s(self.device_token),
            "name": _s(self.name),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
