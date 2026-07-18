"""
TalentUP Fichaje — Tenant model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200), nullable=True)
    cif = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    convenio = Column(String(100), default="hosteleria")
    tolerancia_min = Column(Integer, default=5)
    plan = Column(String(20), default="basic")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "legal_name": self.legal_name,
            "cif": self.cif,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "convenio": self.convenio,
            "tolerancia_min": self.tolerancia_min,
            "plan": self.plan,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
