"""
TalentUP Fichaje — Employee model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    dni = Column(String(20), nullable=True)
    pin_hash = Column(String(200), nullable=False)
    nfc_card_id = Column(String(100), nullable=True)
    photo_url = Column(Text, nullable=True)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": self.name,
            "dni": self.dni,
            "nfc_card_id": self.nfc_card_id,
            "photo_url": self.photo_url,
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
