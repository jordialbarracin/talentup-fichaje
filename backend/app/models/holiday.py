"""TalentUP Fichaje — Holiday model (festivos / días no laborables)."""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Text
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String(50), default="national")  # national, regional, local
    year = Column(String(10))  # e.g. "2026"
    region = Column(String(100))
    locality = Column(String(100))
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": _s(self.name),
            "date": self.date.isoformat() if self.date else None,
            "type": _s(self.type),
            "year": _s(self.year),
            "region": _s(self.region),
            "locality": _s(self.locality),
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
