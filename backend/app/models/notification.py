"""
TalentUP Fichaje — Notification model (avisos y notificaciones).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    recipient_type = Column(String(20), nullable=False)  # employee, manager, all_managers, all_employees
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(50), nullable=True)  # clocking, vacation, leave, payroll, incident, system

    action_url = Column(Text, nullable=True)
    action_label = Column(String(100), nullable=True)

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_dismissed = Column(Boolean, default=False)
    sent_via = Column(String(50), nullable=True)  # in_app, email, sms, push

    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "recipient_type": self.recipient_type,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "category": self.category,
            "action_url": self.action_url,
            "action_label": self.action_label,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_dismissed": self.is_dismissed,
            "sent_via": self.sent_via,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
