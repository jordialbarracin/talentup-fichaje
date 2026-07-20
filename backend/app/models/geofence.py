"""
TalentUP Fichaje — Geofence model (geocercas para validación de fichaje).
Define zonas válidas donde un empleado puede fichar.

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey, Text
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Coordenadas del centro + radio (círculo simple)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    radius_meters = Column(Numeric(10, 2), default=100)

    # O polígono (GeoJSON) para zonas irregulares
    polygon_geojson = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": _s(self.name),
            "description": _s(self.description),
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "radius_meters": float(self.radius_meters) if self.radius_meters else None,
            "polygon_geojson": _s(self.polygon_geojson),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }