"""
TalentUP Fichaje — DocumentTemplate model (plantillas de documentos legales).
Contratos, recibos de nómina, partes de baja, certificados.

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # contract, payroll_receipt, leave_report, certificate
    description = Column(Text, nullable=True)

    # Plantilla HTML con placeholders {{variable}}
    template_html = Column(Text, nullable=False)

    # Metadatos
    language = Column(String(10), default="es")
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": _s(self.name),
            "type": _s(self.type),
            "description": _s(self.description),
            "template_html": _s(self.template_html[:200] + "..." if self.template_html and len(self.template_html) > 200 else self.template_html),
            "language": _s(self.language),
            "version": _s(self.version),
            "is_active": self.is_active,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }