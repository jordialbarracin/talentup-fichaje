"""TalentUP Fichaje — Holiday model (festivos / días no laborables)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Text
from app.database import Base


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
            "name": self.name,
            "date": self.date.isoformat() if self.date else None,
            "type": self.type,
            "year": self.year,
            "region": self.region,
            "locality": self.locality,
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
